from curl_cffi import requests
from sqlalchemy import create_engine, text
import time
import random

DATABASE_URL = "postgresql://admin:password@localhost:5432/betbot"
engine = create_engine(DATABASE_URL)

def get_db_connection():
    return engine.connect()

def fractional_to_decimal(fraction_str):
    """Converte '4/6' para 1.67"""
    try:
        if not fraction_str: return 0.0
        numerator, denominator = map(int, fraction_str.split('/'))
        return round(1 + (numerator / denominator), 2)
    except:
        return 0.0

def fetch_and_save_odds():
    print("💰 Iniciando coleta de ODDS REAIS (Match Goals & Corners)...")
    conn = get_db_connection()
    
    try:
        # Pega jogos com ID externo (SofaScore)
        query_games = text("""
            SELECT m.id, m.external_id, m.match_name 
            FROM tb_match m
            WHERE m.external_id IS NOT NULL
        """)
        
        games = conn.execute(query_games).fetchall()
        print(f"🔍 {len(games)} jogos na fila.")
        
        # SQL para limpar odds antigas desse jogo antes de salvar novas (evita duplicidade no dia)
        delete_query = text("DELETE FROM tb_match_odds WHERE match_id = :mid")
        
        insert_query = text("""
            INSERT INTO tb_match_odds (match_id, market_name, choice_name, fractional_value, decimal_value)
            VALUES (:mid, :mkt, :choice, :frac, :dec)
        """)

        for game in games:
            internal_id, sofa_id, name = game
            print(f"   >> Cotando: {name} (ID: {sofa_id})")
            
            # Limpa dados velhos deste jogo
            conn.execute(delete_query, {"mid": internal_id})

            url = f"https://api.sofascore.com/api/v1/event/{sofa_id}/odds/1/all"
            
            try:
                response = requests.get(url, impersonate="chrome120", timeout=15)
                
                if response.status_code == 200:
                    data = response.json()
                    markets = data.get('markets', [])
                    
                    saved_count = 0
                    
                    for market in markets:
                        raw_name = market.get('marketName')     # Ex: "Match goals"
                        choice_group = market.get('choiceGroup') # Ex: "2.5"
                        choices = market.get('choices', [])
                        
                        # --- FILTRO DE PRIORIDADES ---
                        is_relevant = False
                        market_label = raw_name # Nome que vamos salvar no banco
                        
                        # 1. GOLS (Match goals)
                        if raw_name == "Match goals" or raw_name == "Alternative Match Goals":
                            is_relevant = True
                            # Padroniza o nome para o Banco: "Total Goals"
                            market_label = "Total Goals" 
                        
                        # 2. ESCANTEIOS (Corners 2-Way)
                        elif "Corner" in raw_name: # Pega "Corners 2-Way", "Total Corners", etc
                            is_relevant = True
                            market_label = "Corners"

                        # 3. AMBAS MARCAM
                        elif raw_name == "Both teams to score":
                            is_relevant = True
                            market_label = "BTTS"
                        
                        # 4. CARTÕES
                        elif "Cards" in raw_name:
                            is_relevant = True
                            market_label = "Cards"

                        # 5. VENCEDOR (1X2)
                        elif raw_name == "Full time":
                            is_relevant = True
                            market_label = "1x2"

                        if is_relevant:
                            for choice in choices:
                                label = choice.get('name') # "Over", "Under", "Yes", "1"
                                fractional = choice.get('fractionalValue')
                                decimal = fractional_to_decimal(fractional)
                                
                                # TRATAMENTO ESPECIAL PARA LINHAS (Group)
                                # Se tiver grupo (ex: 2.5), concatenamos no nome: "Over 2.5"
                                final_choice_name = label
                                if choice_group:
                                    final_choice_name = f"{label} {choice_group}"
                                
                                # Só salva odds válidas (> 1.0)
                                if decimal > 1.0:
                                    conn.execute(insert_query, {
                                        "mid": internal_id,
                                        "mkt": market_label,     # Ex: "Total Goals"
                                        "choice": final_choice_name, # Ex: "Over 2.5"
                                        "frac": fractional,
                                        "dec": decimal
                                    })
                                    saved_count += 1
                    
                    conn.commit()
                    print(f"      ✅ {saved_count} odds salvas.")
                
                elif response.status_code == 404:
                    print("      ⚠️ Odds indisponíveis.")
                
                time.sleep(random.uniform(0.5, 1.0))

            except Exception as e:
                print(f"      ❌ Erro: {e}")

    except Exception as e:
        print(f"❌ Erro Geral: {e}")
    finally:
        conn.close()

if __name__ == "__main__":
    fetch_and_save_odds()