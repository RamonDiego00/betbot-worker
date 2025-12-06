import json
import requests
from sqlalchemy import create_engine, text
from datetime import datetime

# Configurações
DATABASE_URL = "postgresql://admin:password@localhost:5432/betbot"
# URL do seu Backend Kotlin (que vai receber a ordem e mandar pro Maestro)
BACKEND_API_URL = "http://localhost:8080/api/automation/start"

engine = create_engine(DATABASE_URL)

def get_games_for_analysis():
    """Busca jogos que têm estatísticas de temporada salvas"""
    # Note que pegamos home_team_form e away_team_form onde salvamos o JSON
    query = text("""
        SELECT 
            m.match_name, 
            s.home_team_form, 
            s.away_team_form
        FROM tb_match m
        JOIN tb_match_stats s ON m.id = s.match_id
        WHERE s.home_team_form IS NOT NULL
    """)
    
    with engine.connect() as conn:
        result = conn.execute(query)
        return result.fetchall()

def calculate_goal_expectancy(home_stats, away_stats):
    """
    Usa os dados da temporada para prever gols.
    """
    try:
        # Extrai médias (com valor default 0 para evitar erros)
        h_scored = home_stats.get('goalsScoredPerMatch', 0)
        h_conceded = home_stats.get('goalsConcededPerMatch', 0)
        
        a_scored = away_stats.get('goalsScoredPerMatch', 0)
        a_conceded = away_stats.get('goalsConcededPerMatch', 0)
        
        # Lógica Simples de Poisson (Média Cruzada)
        # O quanto o Casa deve fazer = (Ataque Casa + Defesa Fora) / 2
        exp_home_goals = (h_scored + a_conceded) / 2
        
        # O quanto o Fora deve fazer = (Ataque Fora + Defesa Casa) / 2
        exp_away_goals = (a_scored + h_conceded) / 2
        
        total_expected = exp_home_goals + exp_away_goals
        
        return total_expected
        
    except Exception as e:
        print(f"Erro no calculo: {e}")
        return 0

def run_agent_v1():
    print("🤖 Agente V1 (Season Stats) iniciado...")
    
    games = get_games_for_analysis()
    print(f"🔍 Analisando {len(games)} partidas disponíveis...")
    
    bets_to_make = []

    for game in games:
        match_name = game[0]
        # O banco retorna String (JSON), precisamos converter para Dict
        try:
            home_stats = json.loads(game[1])
            away_stats = json.loads(game[2])
        except:
            print(f"⚠️ Erro ao ler JSON de {match_name}")
            continue

        # 1. O Cérebro pensa
        expected_goals = calculate_goal_expectancy(home_stats, away_stats)
        
        print(f"   ⚽ {match_name} -> Expectativa de Gols: {expected_goals:.2f}")

        # 2. A Regra de Negócio (Limiar de Aposta)
        # Se a IA acha que vai sair quase 3 gols (2.85), apostar em "Mais de 1.5" é seguro.
        if expected_goals >= 2.85:
            print(f"      ✅ OPORTUNIDADE DETECTADA (Over 1.5)!")
            
            bets_to_make.append({
                "match_name": match_name,
                "markets": [
                    {
                        "market_name": "Total de Gols",
                        "selections": [
                            {
                                "visual_target": "1 Gols", # O Maestro vai clicar onde diz "1 Gols" (Over 1.5)
                                "previous_visual_target": "0 Gols",
                                "column_index": 0,
                                "description": f"Over 1.5 Gols (IA: {expected_goals:.2f})"
                            }
                        ]
                    }
                ]
            })

    # 3. Execução
    if not bets_to_make:
        print("zzz A IA decidiu não apostar em nada hoje (Critérios não atingidos).")
        return

    batch_id = f"AI-V1-{datetime.now().strftime('%Y%m%d%H%M')}"
    
    payload = {
        "batch_id": batch_id,
        "global_stake": 0.50, # Stake de teste
        "matches": bets_to_make
    }
    
    print(f"\n🚀 Enviando {len(bets_to_make)} apostas para o Backend...")
    
    try:
        response = requests.post(BACKEND_API_URL, json=payload)
        if response.status_code == 200:
            print("✅ SUCESSO! O Maestro deve começar a trabalhar em breve.")
        else:
            print(f"❌ Erro no Backend: {response.text}")
    except Exception as e:
        print(f"❌ Erro de conexão com API: {e}")

if __name__ == "__main__":
    run_agent_v1()