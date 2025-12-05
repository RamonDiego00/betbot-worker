class Postgress():
    def save_to_postgres(matches):
        conn = psycopg2.connect(
            dbname="matches_db",
            user="postgres",
            password="sua_senha",
            host="localhost",
            port="5432"
        )
        cur = conn.cursor()

        # Criação da tabela se não existir
        cur.execute("""
            CREATE TABLE IF NOT EXISTS matches (
                id SERIAL PRIMARY KEY,
                home_team VARCHAR(100),
                away_team VARCHAR(100),
                match_time VARCHAR(10),
                match_date DATE
            )
        """)

        for match in matches:
            cur.execute("""
                INSERT INTO matches (home_team, away_team, match_time, match_date)
                VALUES (%s, %s, %s, %s)
            """, match)

        conn.commit()
        cur.close()
        conn.close()
