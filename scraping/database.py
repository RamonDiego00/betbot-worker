from sqlalchemy import create_engine, text
from datetime import datetime

DATABASE_URL = "postgresql://admin:password@localhost:5432/betbot"
engine = create_engine(DATABASE_URL)

def save_matches_to_db(matches_list):
    """
    Recebe uma lista de dicionários com os dados do jogo e salva no banco.
    Cria um 'Batch' de Importação para agrupar esses jogos.
    """
    with engine.connect() as connection:
        trans = connection.begin() # Inicia transação
        try:
            # 1. Criar um Batch para identificar essa importação (Ex: Jogos do Dia)
            # Estamos inserindo direto nas tabelas criadas pelo Kotlin (snake_case)
            batch_query = text("""
                INSERT INTO tb_bet_batch (batch_external_id, global_stake, status, created_at)
                VALUES (:batch_id, 0, 'PENDING', :created_at)  
                RETURNING id
            """)
            
            # Geramos um ID único baseado na data/hora
            import_id = f"SOFA-{datetime.now().strftime('%Y%m%d-%H%M%S')}"
            
            result = connection.execute(batch_query, {
                "batch_id": import_id,
                "created_at": datetime.now()
            })
            batch_db_id = result.fetchone()[0] # Pega o ID numérico gerado (PK)

            # 2. Inserir os Jogos vinculados a esse Batch
            match_query = text("""
                INSERT INTO tb_match (match_name, batch_id, external_id)
                VALUES (:match_name, :batch_id, :external_id)
            """)

            print(f"📦 Criando Batch {import_id} com {len(matches_list)} jogos...")

            for match in matches_list:
                connection.execute(match_query, {
                    "match_name": match['name'],
                    "batch_id": batch_db_id,
                    "external_id": match['external_id']
                })

            trans.commit() # Confirma tudo
            print("✅ Sucesso! Jogos salvos no banco.")
            
        except Exception as e:
            trans.rollback() # Desfaz se der erro
            print(f"❌ Erro ao salvar no banco: {e}")
            raise e

def testar_conexao():
    try:
        with engine.connect() as connection:
            result = connection.execute(text("SELECT 1"))
            print("✅ Conexão com o Banco (Docker) realizada com sucesso!")
    except Exception as e:
        print(f"❌ Erro ao conectar no banco: {e}")





if __name__ == "__main__":
    testar_conexao()