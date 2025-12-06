import time
import subprocess
import sys

# Lista de scripts na ordem exata de execução
# Ajuste os nomes se necessário
PIPELINE = [
    # 1. Coleta a Agenda (IDs)
    {"script": "scraping/sofascore.py", "desc": "Coleta de Agenda"},
    
    # 2. Coleta Estatísticas (Precisa dos IDs do passo 1)
    {"script": "scraping/stats.py", "desc": "Coleta de Estatísticas"},
    
    # 3. Coleta Odds (Precisa dos IDs do passo 1)
    {"script": "scraping/odds.py", "desc": "Coleta de Preços (Odds)"},
    
    # 4. Inteligência e Envio (Precisa de Stats + Odds)
    {"script": "agent_strategy.py", "desc": "Agente de Decisão (Múltiplas)"}
]

def run_step(step_info):
    script = step_info["script"]
    desc = step_info["desc"]
    
    print(f"\n{'='*40}")
    print(f"▶️  INICIANDO: {desc} ({script})")
    print(f"{'='*40}")
    
    start_time = time.time()
    
    try:
        # Roda o script python como um subprocesso
        # sys.executable garante que usamos o mesmo Python do venv atual
        result = subprocess.run([sys.executable, script], check=True)
        
        elapsed = time.time() - start_time
        print(f"✅ {desc} finalizado com sucesso em {elapsed:.2f}s.")
        return True
        
    except subprocess.CalledProcessError as e:
        print(f"❌ ERRO CRÍTICO em {desc}. O pipeline foi interrompido.")
        return False

def main():
    print("🤖 BETBOT WORKER INICIADO")
    print("📅 Hora do sistema:", time.strftime("%Y-%m-%d %H:%M:%S"))
    
    for step in PIPELINE:
        success = run_step(step)
        if not success:
            print("\n💀 Pipeline abortado devido a erro.")
            sys.exit(1)
        
        # Pausa de segurança entre scripts
        time.sleep(2)

    print("\n🎉 CICLO COMPLETO! As apostas foram enviadas para o Maestro.")

if __name__ == "__main__":
    main()