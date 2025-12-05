from playwright.sync_api import sync_playwright
import psycopg2

ALLOWED_LEAGUES = [
    "Premier League",
    "LaLiga",
    "Champions League",
    "Copa Betano do Brasil"
]


def main():
    teste = "teste"

# Generic methods

async def get_text_from_xpath(xpath_selector: str, page):
       try:
                elemento = page.query_selector(f'xpath={xpath_selector}')
                
                if elemento:
                    # Verificar se o elemento está visível e tem conteúdo
                    if elemento.is_visible():
                        texto = elemento.text_content().strip()
                        if texto:
                          return texto                 
        except Exception as e:
                print(f"Erro ao processar: {e}")
                continue
            return None

# Generic methods



def get_games_for_league(xpath:str, league_name:str):

    # Regex remove after {i} the xpath parameter 
    //*[@id="__next"]/main/div/div/div[1]/div[4]/div[1]/div[1]/div[1]/div[2]/div[1]/div[{i}]  %  /div/div[2]/a[2]/bdi  %

    # //*[@id="__next"]/main/div/div/div[1]/div[4]/div[1]/div[1]/div[1]/div[2]/div[1]/div[{i}] base de cada grupo

    base_xpath_league = ""
    # Deve vir um Xpath de base da estrutura do confronto para então pegar os dados do time

    # Metodo que incrementa 

    base_xpath_match_time = '{base_xpath_league}/a/div/div/div[2]/bdi'


    base_xpath_match_team_a = '{base_xpath_league}/a/div/div/div[4]/div/div[1]/div[1]/bdi'
    base_xpath_match_team_b = '{base_xpath_league}/a/div/div/div[4]/div/div[1]/div[2]/bdi'

    team_a = get_text_from_xpath(base_xpath_match_time)
    team_b = get_text_from_xpath(base_xpath_match_team_a)
    time = get_text_from_xpath(base_xpath_match_team_b)

    data_match = {
        "league":league_name,
        "team_a":team_a,
        "team_b":team_b,
        "time": time
    }

    # save in table in postgress

    

def get_list_all_leagues():
    resultados = {}
    
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        
        page.goto('https://www.sofascore.com/pt/futebol/2025-09-10')
        page.wait_for_timeout(1000)

        # Iterar de 1 até 150
        for i in range(1, 151):
            # Construir o XPath com o número variável
            xpath_alvo = f'//*[@id="__next"]/main/div/div/div[1]/div[4]/div[1]/div[1]/div[1]/div[2]/div[1]/div[{i}]/div/div[2]/a[2]/bdi'
            
            try:
                # Buscar o elemento
                elemento = page.query_selector(f'xpath={xpath_alvo}')
                
                if elemento:
                    # Verificar se o elemento está visível e tem conteúdo
                    if elemento.is_visible():
                        texto = elemento.text_content().strip()
                        if texto:
                            resultados[xpath_alvo] = texto
                            print(f"✅ [{i}/150] Texto capturado: '{texto}'")
                        else:
                            print(f"⚠️ [{i}/150] Elemento encontrado mas texto vazio")
                    else:
                        print(f"⚠️ [{i}/150] Elemento encontrado mas não visível")
                    
            except Exception as e:
                print(f"❌ [{i}/150] Erro ao processar: {e}")
                continue
        
        browser.close()

    print(resultados)
    
    return resultados



def get_period(time_str: str) -> str:
    """
    Retorna o período do dia baseado no horário do jogo.
    time_str: string no formato HH:MM
    """
    try:
        hora = int(time_str.split(":")[0])
        minuto = int(time_str.split(":")[1])

        total_minutos = hora * 60 + minuto

        if 7*60 <= total_minutos < 12*60 + 30:
            return "manhã"
        elif 12*60 + 30 <= total_minutos < 18*60:
            return "tarde"
        elif 18*60 <= total_minutos < 23*60:
            return "noite"
        else:
            return "fora do intervalo"
    except Exception:
        return "indefinido"

def filter_games_allowed(url: str) -> dict:
    values = get_list_all_leagues()
    print("\nTotal capturados:", len(values))
    allowed_matches = {}

    for xpath_alvo, texto in values.items():
        if texto in ALLOWED_LEAGUES:
            print(f"✅ Campeonato permitido encontrado: {texto} | xpath: {xpath_alvo}")
            allowed_matches[xpath_alvo] = texto
            get_games_for_league(xpath_alvo,texto)

    if not allowed_matches:
        print("❌ Nenhum campeonato permitido encontrado")

    print(allowed_matches)

    return allowed_matches

if __name__ == "__main__":
    url = "https://www.sofascore.com/football/2025-09-10" 
    filter_games_allowed(url)

# if __name__ == "__main__":
#     url = "https://www.sofascore.com/football/2025-09-10" 
#     get_list_all_leagues()

