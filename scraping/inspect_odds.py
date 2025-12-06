from curl_cffi import requests
from sqlalchemy import create_engine, text

DATABASE_URL = "postgresql://admin:password@localhost:5432/betbot"
engine = create_engine(DATABASE_URL)

def inspect_market_names():
    print("🕵️‍♂️ Iniciando inspeção de nomes de mercados...")
    
    with engine.connect() as conn:
        # Pega 1 jogo qualquer que tenha ID do SofaScore para usar de cobaia
        query = text("SELECT match_name, external_id FROM tb_match WHERE external_id IS NOT NULL LIMIT 1")
        game = conn.execute(query).fetchone()
        
        if not game:
            print("❌ Nenhum jogo com ID externo encontrado no banco.")
            return

        name, sofa_id = game
        print(f"🔬 Analisando jogo: {name} (ID: {sofa_id})")
        
        url = f"https://api.sofascore.com/api/v1/event/{sofa_id}/odds/1/all"
        
        try:
            response = requests.get(url, impersonate="chrome120", timeout=15)
            data = response.json()
            markets = data.get('markets', [])
            
            print(f"\n📋 Lista de Mercados encontrados no JSON:")
            print("="*50)
            
            found_corners = False
            found_goals = False

            for market in markets:
                m_name = market.get('marketName')
                choices = market.get('choices', [])
                
                # Mostra o nome e as 2 primeiras opções para entendermos o que é
                example_choices = [c.get('name') for c in choices[:2]]
                print(f"• [Nome: '{m_name}'] -> Opções: {example_choices}")

                if "corner" in m_name.lower(): found_corners = True
                if "total" in m_name.lower() or "goal" in m_name.lower(): found_goals = True

            print("="*50)
            
            if not found_corners:
                print("⚠️  AVISO: Nenhum mercado com nome 'Corner' foi encontrado neste endpoint.")
            if not found_goals:
                print("⚠️  AVISO: Mercados de Gols parecem estar com nome diferente do esperado.")
                
        except Exception as e:
            print(f"❌ Erro: {e}")

if __name__ == "__main__":
    inspect_market_names()