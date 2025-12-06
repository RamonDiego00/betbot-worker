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
    print("📊 Buscando Estatísticas DETALHADAS (Season Stats)...")
    conn = get_db_connection()
    
    try:
        # Trazemos todas as chaves necessárias
        query_games = text("""
            SELECT m.id, m.match_name, m.home_team_id, m.away_team_id, m.season_id, m.tournament_unique_id 
            FROM tb_match m
            LEFT JOIN tb_match_stats s ON m.id = s.match_id
            WHERE s.id IS NULL AND m.season_id IS NOT NULL
        """)
        
        games = conn.execute(query_games).fetchall()
        print(f"🔍 {len(games)} jogos na fila.")
        
        for game in games:
            internal_id, name, hid, aid, sid, tid = game
            
            print(f"   >> Analisando: {name}")
            
            # Precisamos fazer 2 chamadas: Uma para o time da Casa, outra para Visitante
            # Endpoint Mágico: /team/{id}/unique-tournament/{id}/season/{id}/statistics/overall
            
            home_stats = fetch_team_season_stats(hid, tid, sid, "Casa")
            time.sleep(random.uniform(0.5, 1.5)) # Respeito à API
            
            away_stats = fetch_team_season_stats(aid, tid, sid, "Fora")
            time.sleep(random.uniform(0.5, 1.5))
            
            # Salva
            save_query = text("""
                INSERT INTO tb_match_stats (match_id, home_team_form, away_team_form)
                VALUES (:mid, :home, :away)
            """)
            
            conn.execute(save_query, {
                "mid": internal_id,
                "home": json.dumps(home_stats),
                "away": json.dumps(away_stats)
            })
            conn.commit()
            print(f"      ✅ Dados salvos!")

    except Exception as e:
        print(f"❌ Erro Geral: {e}")
    finally:
        conn.close()

def fetch_team_season_stats(team_id, tourn_id, season_id, label):
    url = f"https://api.sofascore.com/api/v1/team/{team_id}/unique-tournament/{tourn_id}/season/{season_id}/statistics/overall"
    
    try:
        response = requests.get(url, impersonate="chrome120", timeout=20)
        if response.status_code == 200:
            data = response.json()
            stats = data.get('statistics', {})
            
            # Vamos filtrar só o "filé mignon" para a IA não se perder com lixo
            # Aqui mapeamos o que você pediu:
            relevant_data = {
                "goalsScoredPerMatch": stats.get('goalsScored', 0) / stats.get('matches', 1),
                "goalsConcededPerMatch": stats.get('goalsConceded', 0) / stats.get('matches', 1),
                "bigChancesPerMatch": stats.get('bigChances', 0) / stats.get('matches', 1),
                "shotsOnTargetPerMatch": stats.get('shotsOnTarget', 0) / stats.get('matches', 1),
                "cornersPerMatch": stats.get('corners', 0) / stats.get('matches', 1),
                "possession": stats.get('ballPossession', 0),
                "cleanSheets": stats.get('cleanSheets', 0),
                "matchesPlayed": stats.get('matches', 0)
            }
            return relevant_data
        else:
            print(f"      ⚠️ Erro API ({label}): {response.status_code}")
            return {}
    except Exception as e:
        print(f"      ❌ Erro Req ({label}): {e}")
        return {}

if __name__ == "__main__":
    fetch_and_save_stats()