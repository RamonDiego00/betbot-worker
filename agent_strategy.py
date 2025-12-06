import json
import requests
import itertools
from sqlalchemy import create_engine, text
from datetime import datetime

# --- CONFIGURAÇÕES ---
DATABASE_URL = "postgresql://admin:password@localhost:5432/betbot"
BACKEND_API_URL = "http://localhost:8080/api/automation/start"

# Regras do Usuário
TARGET_MIN_ODD = 1.70
TARGET_MAX_ODD = 2.50
MIN_BETS = 3
MAX_BETS = 10

engine = create_engine(DATABASE_URL)

def get_analyzable_matches():
    """
    Busca jogos que tenham TUDO: Stats e Odds.
    Retorna uma lista crua do banco.
    """
    query = text("""
        SELECT 
            m.id, 
            m.match_name, 
            s.home_team_form, 
            s.away_team_form
        FROM tb_match m
        JOIN tb_match_stats s ON m.id = s.match_id
        -- Só pega se tiver estatística salva
        WHERE s.home_team_form IS NOT NULL
    """)
    with engine.connect() as conn:
        return conn.execute(query).fetchall()

def get_odd_for_market(match_id, market_label, choice_label):
    """
    Busca no banco a odd específica. Ex: Market='Total Goals', Choice='Over 1.5'
    """
    query = text("""
        SELECT decimal_value 
        FROM tb_match_odds 
        WHERE match_id = :mid 
          AND market_name = :mkt 
          AND choice_name = :choice
        LIMIT 1
    """)
    with engine.connect() as conn:
        result = conn.execute(query, {"mid": match_id, "mkt": market_label, "choice": choice_label}).fetchone()
        if result:
            return float(result[0])
    return None

def analyze_candidates():
    matches = get_analyzable_matches()
    print(f"🧠 Analisando {len(matches)} partidas para encontrar oportunidades...")
    
    candidates = []

    for match in matches:
        match_id, name, home_json, away_json = match
        
        try:
            h_stats = json.loads(home_json)
            a_stats = json.loads(away_json)
            
            # 1. ANÁLISE TÉCNICA (GOLS)
            # Média de gols totais do confronto (Ataque + Defesa Cruzada)
            exp_goals = (
                (h_stats.get('goalsScoredPerMatch', 0) + a_stats.get('goalsConcededPerMatch', 0)) / 2 +
                (a_stats.get('goalsScoredPerMatch', 0) + h_stats.get('goalsConcededPerMatch', 0)) / 2
            )
            
            # --- ESTRATÉGIA: OVER GOLS ---
            # Se a expectativa é alta (> 2.8), o Over 1.5 é muito seguro.
            if exp_goals >= 2.8:
                # Tenta pegar a odd do Over 1.5 (Segurança)
                odd_val = get_odd_for_market(match_id, "Total Goals", "Over 1.5")
                
                # Se achou a odd e ela não é "lixo" (tipo 1.01)
                if odd_val and odd_val > 1.15:
                    candidates.append({
                        "match_name": name,
                        "market": "Total Goals",
                        "selection": "Over 1.5", # O Maestro vai clicar aqui
                        "odd": odd_val,
                        "desc": f"Over 1.5 (Exp: {exp_goals:.2f})"
                    })
            
            # --- ESTRATÉGIA: AMBAS MARCAM (BTTS) ---
            # Se ambos marcam e sofrem muito (> 1.4 cada)
            if (h_stats.get('goalsScoredPerMatch', 0) > 1.4 and h_stats.get('goalsConcededPerMatch', 0) > 1.2 and
                a_stats.get('goalsScoredPerMatch', 0) > 1.4 and a_stats.get('goalsConcededPerMatch', 0) > 1.2):
                
                odd_val = get_odd_for_market(match_id, "BTTS", "Yes")
                if odd_val and odd_val > 1.45:
                     candidates.append({
                        "match_name": name,
                        "market": "Both teams to score",
                        "selection": "Yes",
                        "odd": odd_val,
                        "desc": "BTTS - Sim"
                    })

        except Exception as e:
            print(f"⚠️ Erro ao processar {name}: {e}")
            continue

    return candidates

def generate_multiples_payload(candidates):
    print(f"🧩 Gerando combinações com {len(candidates)} palpites aprovados...")
    
    # Gera todas as duplas possíveis
    combinations = list(itertools.combinations(candidates, 2))
    
    valid_batches = []
    
    for p1, p2 in combinations:
        # Não repetir jogo
        if p1['match_name'] == p2['match_name']: continue
        
        total_odd = p1['odd'] * p2['odd']
        
        # O FILTRO DE OURO: 1.70 a 2.50
        if TARGET_MIN_ODD <= total_odd <= TARGET_MAX_ODD:
            
            # Monta o objeto que o Backend espera
            # IMPORTANTE: Adaptamos para mandar uma lista de matches
            # O Maestro terá que lidar com o loop de selecionar um, voltar, selecionar outro.
            batch = {
                "batch_id": f"MULTI-{datetime.now().strftime('%H%M%S')}-{len(valid_batches)}",
                "global_stake": 1.00, # Sua stake fixa
                "is_multiple": True,  # Flag pro Maestro
                "matches": [
                    {
                        "match_name": p1['match_name'],
                        "markets": [{
                            "market_name": p1['market'],
                            "selections": [{
                                "visual_target": p1['selection'],
                                "previous_visual_target": "", # Opcional
                                "column_index": 0,
                                "description": f"{p1['desc']} (@{p1['odd']})"
                            }]
                        }]
                    },
                    {
                        "match_name": p2['match_name'],
                        "markets": [{
                            "market_name": p2['market'],
                            "selections": [{
                                "visual_target": p2['selection'],
                                "previous_visual_target": "",
                                "column_index": 0,
                                "description": f"{p2['desc']} (@{p2['odd']})"
                            }]
                        }]
                    }
                ]
            }
            valid_batches.append(batch)
            
            # Se atingimos o máximo de bilhetes do dia, paramos
            if len(valid_batches) >= MAX_BETS:
                break
    
    return valid_batches

def execute():
    candidates = analyze_candidates()
    if not candidates:
        print("zzz Nenhuma aposta segura encontrada hoje.")
        return

    batches = generate_multiples_payload(candidates)
    
    if not batches:
        print(f"zzz {len(candidates)} candidatos encontrados, mas nenhuma Dupla bateu a odd {TARGET_MIN_ODD}-{TARGET_MAX_ODD}.")
        return

    print(f"\n🚀 {len(batches)} Múltiplas geradas! Enviando para o Backend...")

    for i, batch in enumerate(batches):
        print(f"   📨 Enviando Bilhete {i+1}/{len(batches)}...")
        try:
            # Envia para a API
            requests.post(BACKEND_API_URL, json=batch)
            # Pequeno delay para não engasgar o WebSocket
            import time
            time.sleep(1) 
        except Exception as e:
            print(f"   ❌ Falha ao enviar: {e}")

if __name__ == "__main__":
    execute()