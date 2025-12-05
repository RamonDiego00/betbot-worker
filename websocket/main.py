import websocket
import json
import subprocess
import os
import time

# CONFIGURAÇÃO DE CAMINHOS
BASE_DIR = "/Users/ramondiegodossantosferreira/Documents/projects/automation/maestro"
LOADER_PATH = os.path.join(BASE_DIR, "jsons/loader.js")
FLOW_PATH = os.path.join(BASE_DIR, "flows/main2.yaml")

def on_message(ws, message):
    print(f"\n[WS] Mensagem recebida...")
    
    try:
        data = json.loads(message)
        batch_id = data.get('batch_id')
        
        # 1. GERA O LOADER (Igual fizemos antes)
        js_content = f"""
        // ARQUIVO GERADO PELO PYTHON
        output.jsonData = {json.dumps(data, indent=2)};

        if (!output.jsonData || !output.jsonData.matches) {{
            throw new Error("CRÍTICO: JSON vazio.");
        }}
        output._internalMatchList = output.jsonData.matches;
        output.totalMatches = output._internalMatchList.length;
        output.matchIndex = 0;
        """
        with open(LOADER_PATH, "w", encoding="utf-8") as f:
            f.write(js_content)
        
        # 2. LÓGICA DE RETRY (3 TENTATIVAS)
        max_retries = 1
        success = False
        
        for attempt in range(1, max_retries + 1):
            print(f"\n>>> [MAESTRO] Tentativa {attempt}/{max_retries} para Batch {batch_id}")
            
            # Executa o Maestro e captura o resultado
            # check=False permite que o script continue mesmo se o maestro der erro
            result = subprocess.run(f"maestro test {FLOW_PATH}", shell=True)
            
            if result.returncode == 0:
                print(f"✅ [SUCESSO] Batch {batch_id} finalizado na tentativa {attempt}.")
                success = True
                
                # Notifica SUCESSO ao Backend
                response = {
                    "type": "BET_RESULT",
                    "batch_id": batch_id,
                    "status": "SUCCESS",
                    "message": "Apostas realizadas com sucesso."
                }
                ws.send(json.dumps(response))
                break # Sai do loop
            else:
                print(f"❌ [ERRO] Falha na tentativa {attempt}.")
                # Se não for a última tentativa, espera um pouco antes de tentar de novo
                if attempt < max_retries:
                    print("⏳ Aguardando 5 segundos para reiniciar...")
                    time.sleep(5) 
        
        # 3. FALHA FINAL (Se saiu do loop sem sucesso)
        if not success:
            print(f"💀 [FALHA CRÍTICA] Todas as {max_retries} tentativas falharam.")
            
            # Notifica ERRO ao Backend
            response = {
                "type": "BET_RESULT",
                "batch_id": batch_id,
                "status": "FAILED",
                "message": "Não foi possível realizar as apostas após 3 tentativas."
            }
            ws.send(json.dumps(response))

    except Exception as e:
        print(f"[ERRO NO SCRIPT PYTHON]: {e}")
        # Envia erro de processamento interno
        ws.send(json.dumps({"type": "ERROR", "message": str(e)}))

def on_error(ws, error):
    print(f"[WS ERRO]: {error}")

def on_close(ws, close_status_code, close_msg):
    print("[WS] Conexão encerrada")

def on_open(ws):
    print("[WS] Conectado e aguardando...")

if __name__ == "__main__":
    url = "ws://localhost:8080/ws-bets" 
    ws = websocket.WebSocketApp(url,
                                on_open=on_open,
                                on_message=on_message,
                                on_error=on_error,
                                on_close=on_close)
    ws.run_forever()