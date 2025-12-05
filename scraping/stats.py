from curl_cffi import requests
from sqlalchemy import create_engine, text
import json
import time
import random

DATABASE_URL = "postgresql://admin:password@localhost:5432/betbot"
engine = create_engine(DATABASE_URL)

def get_db_connection():
    return engine.connect()

def fetch_and_save_stats():
    print("📊 Iniciando coleta de estatísticas pré-jogo...")
    
    conn = get_db_connection()
    
    try:
        # 1. Busca jogos que ainda não têm estatísticas
        # (Fazemos um LEFT JOIN para pegar só quem é NULL na tabela de stats)
        query_games = text("""
            SELECT m.id, m.external_id, m.match_name 
            FROM tb_match m
            LEFT JOIN tb_match_stats s ON m.id = s.match_id
            WHERE s.id IS NULL AND m.external_id IS NOT NULL
        """)
        
        result = conn.execute(query_games)
        games_to_process = result.fetchall()
        
        print(f"🔍 Encontrados {len(games_to_process)} jogos sem estatísticas.")
        
        for game in games_to_process:
            internal_id = game[0]
            sofa_id = game[1]
            match_name = game[2]
            
            print(f"   >> Processando: {match_name} (ID: {sofa_id})")
            
            # 2. Chama API do SofaScore (Pregame Form)
            url = f"https://api.sofascore.com/api/v1/event/{sofa_id}/pregame-form"
            
            try:
                response = requests.get(
                    url, 
                    impersonate="chrome120", 
                    timeout=20
                )
                
                if response.status_code == 200:
                    data = response.json()
                    
                    # Extrai dados (Home e Away)
                    home_form = json.dumps(data.get('homeTeam', {}))
                    away_form = json.dumps(data.get('awayTeam', {}))
                    
                    # Opcional: Pegar votos da torcida (outro endpoint, mas vamos simplificar)
                    
                    # 3. Salva no Banco
                    save_query = text("""
                        INSERT INTO tb_match_stats (match_id, home_team_form, away_team_form)
                        VALUES (:mid, :home, :away)
                    """)
                    
                    conn.execute(save_query, {
                        "mid": internal_id,
                        "home": home_form,
                        "away": away_form
                    })
                    conn.commit() # Salva a cada jogo para não perder progresso
                    
                    print("      ✅ Estatísticas salvas.")
                    
                elif response.status_code == 404:
                    print("      ⚠️ Jogo sem dados prévios disponíveis.")
                else:
                    print(f"      ❌ Erro API: {response.status_code}")

                # Delay para não tomar bloqueio (importante!)
                time.sleep(random.uniform(1.0, 3.0))
                
            except Exception as e:
                print(f"      ❌ Erro de conexão: {e}")

    except Exception as e:
        print(f"❌ Erro Geral: {e}")
    finally:
        conn.close()

if __name__ == "__main__":
    fetch_and_save_stats()