from curl_cffi import requests
import json
from datetime import date
from database import save_matches_to_db

# Data de hoje
DATE_TODAY = date.today().strftime("%Y-%m-%d")
URL = f"https://api.sofascore.com/api/v1/sport/football/scheduled-events/{DATE_TODAY}"

# Lista de Ligas Permitidas (Filtro)
# Formato: "País - Liga" (Case sensitive na verificação, mas ajustamos no loop)
TARGET_LEAGUES = [
    "England - Premier League",
    "Spain - LaLiga",
    "Germany - Bundesliga",
    "France - Ligue 1",
    "Italy - Serie A",
    "Brazil - Brasileirão Série A",
    "Europe - UEFA Champions League",
    "Europe - UEFA Europa League"
]

def fetch_todays_games():
    print(f"🌍 Buscando jogos de hoje ({DATE_TODAY}) no SofaScore via curl_cffi...")

    try:
        # Impersonate Chrome 120 para passar pelo Cloudflare
        response = requests.get(
            URL, 
            impersonate="chrome120", 
            timeout=30
        )
        
        if response.status_code != 200:
            print(f"❌ Erro na requisição: {response.status_code}")
            return

        data = response.json()
        events = data.get('events', [])
        
        print(f"🔍 Total de eventos brutos: {len(events)}. Filtrando ligas principais...")

        extracted_matches = []
        
        for event in events:
            # 1. Extração segura dos dados básicos para o filtro
            tournament = event.get('tournament', {})
            tournament_name = tournament.get('name', '')
            category = tournament.get('category', {})
            category_name = category.get('name', '') 
            
            # Monta a string completa da liga ex: "England - Premier League"
            full_league_name = f"{category_name} - {tournament_name}"

            # 2. Lógica de Filtro
            is_allowed = False
            for target in TARGET_LEAGUES:
                # Verifica se a liga alvo está contida no nome do torneio deste jogo
                if target.lower() in full_league_name.lower(): 
                    is_allowed = True
                    break
            
            # Se não for uma liga permitida, pula para o próximo jogo IMEDIATAMENTE
            if not is_allowed:
                continue 

            # 3. Extração dos Times e ID (Só acontece se passar pelo filtro)
            home_team = event.get('homeTeam', {}).get('name')
            away_team = event.get('awayTeam', {}).get('name')
            game_id = event.get('id')

            # 4. Validação final e Adição à lista
            if home_team and away_team and game_id:
                match_name = f"{home_team} v {away_team}"
                
                print(f"   ✅ Adicionado: {match_name} [{full_league_name}] (ID: {game_id})")
                
                extracted_matches.append({
                    "name": match_name,
                    "tournament": full_league_name,
                    "external_id": str(game_id)
                })

        # 5. Salva no banco
        if extracted_matches:
            print(f"\n📦 Salvando {len(extracted_matches)} jogos filtrados no banco...")
            save_matches_to_db(extracted_matches)
        else:
            print("\n⚠️ Nenhum jogo das ligas principais encontrado hoje.")

    except Exception as e:
        print(f"❌ Erro crítico no scraper: {e}")
        import traceback
        traceback.print_exc() # Isso ajuda a ver a linha exata do erro se acontecer de novo

if __name__ == "__main__":
    fetch_todays_games()