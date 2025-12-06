from curl_cffi import requests
import json
from datetime import date, timedelta
from database import save_matches_to_db

# --- CONFIGURAÇÃO DE DATA ---
# Para testes, você pode somar dias: date.today() + timedelta(days=1)
# Ou fixar uma string: "2025-12-06"
DATE_SEARCH = date.today().strftime("%Y-%m-%d")

URL = f"https://api.sofascore.com/api/v1/sport/football/scheduled-events/{DATE_SEARCH}"

# Lista de Ligas Permitidas
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

def fetch_games():
    print(f"🌍 Buscando jogos para a data: {DATE_SEARCH}...")

    try:
        response = requests.get(URL, impersonate="chrome120", timeout=30)
        
        if response.status_code != 200:
            print(f"❌ Erro na requisição: {response.status_code}")
            return

        data = response.json()
        events = data.get('events', [])
        print(f"🔍 Total de eventos brutos: {len(events)}. Filtrando...")

        extracted_matches = []
        
        for event in events:
            # 1. Extração segura dos nomes para o filtro
            tournament = event.get('tournament', {})
            tournament_name = tournament.get('name', '')
            category = tournament.get('category', {})
            category_name = category.get('name', '')
            
            # DEFINIÇÃO DA VARIÁVEL FALTANTE
            full_league_name = f"{category_name} - {tournament_name}"

            # 2. Filtro de Ligas
            is_allowed = False
            for target in TARGET_LEAGUES:
                if target.lower() in full_league_name.lower(): 
                    is_allowed = True
                    break
            
            if not is_allowed:
                continue 

            # 3. Extração dos IDs (Season, TournamentUnique, Teams)
            home_team = event.get('homeTeam', {})
            away_team = event.get('awayTeam', {})
            season = event.get('season', {})
            unique_tournament = tournament.get('uniqueTournament', {})
            
            game_id = event.get('id')

            # 4. Validação e Adição
            # Só salvamos se tivermos TODOS os IDs necessários para as estatísticas
            if (home_team.get('name') and away_team.get('name') and game_id 
                and home_team.get('id') and away_team.get('id') 
                and season.get('id') and unique_tournament.get('id')):
                
                match_name = f"{home_team['name']} v {away_team['name']}"
                
                print(f"   ✅ Adicionado: {match_name} (ID: {game_id})")
                
                extracted_matches.append({
                    "name": match_name,
                    "tournament": full_league_name, # Agora a variável existe!
                    "external_id": str(game_id),
                    "home_team_id": str(home_team['id']),
                    "away_team_id": str(away_team['id']),
                    "season_id": str(season['id']),
                    "tournament_unique_id": str(unique_tournament['id'])
                })

        # 5. Salva no banco
        if extracted_matches:
            print(f"\n📦 Salvando {len(extracted_matches)} jogos filtrados...")
            save_matches_to_db(extracted_matches)
        else:
            print(f"\n⚠️ Nenhum jogo das ligas principais encontrado para {DATE_SEARCH}.")

    except Exception as e:
        print(f"❌ Erro crítico no scraper: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    fetch_games()