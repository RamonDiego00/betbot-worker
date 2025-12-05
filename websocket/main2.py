import websocket
import json
import subprocess
import os
import time
import xml.etree.ElementTree as ET # <--- Importante para ler o relatório

# CONFIGURAÇÃO DE CAMINHOS
BASE_DIR = "/Users/ramondiegodossantosferreira/Documents/projects/automation/maestro"
LOADER_PATH = os.path.join(BASE_DIR, "jsons/loader.js")
FLOW_PATH = os.path.join(BASE_DIR, "main2.yaml")
REPORT_PATH = os.path.join(BASE_DIR, "report.xml") # <--- Onde salvaremos o log de erro

def get_failure_details():
    """Lê o arquivo report.xml e extrai a mensagem de erro do Maestro"""
    try:
        if not os.path.exists(REPORT_PATH):
            return "Erro desconhecido (Arquivo de relatório não gerado)."
        
        tree = ET.parse(REPORT_PATH)
        root = tree.getroot()
        
        # Procura por falhas no XML
        # O formato JUnit geralmente é <testcase> -> <failure message="...">
        for testcase in root.iter('testcase'):
            failure = testcase.find('failure')
            if failure is not None:
                # Retorna a mensagem do atributo 'message' ou o texto interno
                return failure.get('message') or failure.text or "Falha sem mensagem detalhada."
                
        return "Falha detectada, mas nenhum detalhe específico encontrado no relatório."
        
    except Exception as e:
        return f"Erro ao ler relatório de falhas: {str(e)}"

def on_message(ws, message):
    print(f"\n[WS] Mensagem recebida...")
    
    try:
        data = json.loads(message)
        batch_id = data.get('batch_id')
        
        # ... (Lógica de gerar loader.js continua igual) ...
        # (Vou omitir para economizar espaço, mantenha seu código anterior aqui)
        js_content = f"""
// ARQUIVO GERADO PELO PYTHON
output.jsonData = {json.dumps(data, indent=2)};
if (!output.jsonData || !output.jsonData.matches) {{ throw new Error("CRÍTICO: JSON vazio."); }}
output._internalMatchList = output.jsonData.matches;
output.totalMatches = output._internalMatchList.length;
output.matchIndex = 0;
"""
        with open(LOADER_PATH, "w", encoding="utf-8") as f:
            f.write(js_content)

        # LÓGICA DE RETRY
        max_retries = 3
        success = False
        last_error_message = "" # Variável para guardar o último erro
        
        for attempt in range(1, max_retries + 1):
            print(f"\n>>> [MAESTRO] Tentativa {attempt}/{max_retries} para Batch {batch_id}")
            
            # --- MUDANÇA AQUI ---
            # Adicionamos --format junit --output report.xml
            command = f"maestro test {FLOW_PATH} --format junit --output {REPORT_PATH}"
            
            result = subprocess.run(command, shell=True)
            
            if result.returncode == 0:
                print(f"✅ [SUCESSO] Batch {batch_id} finalizado.")
                success = True
                ws.send(json.dumps({
                    "type": "BET_RESULT",
                    "batch_id": batch_id,
                    "status": "SUCCESS",
                    "message": "Apostas realizadas com sucesso."
                }))
                break
            else:
                # CAPTURA O MOTIVO DA FALHA
                last_error_message = get_failure_details()
                print(f"❌ [ERRO] Falha na tentativa {attempt}: {last_error_message}")
                
                if attempt < max_retries:
                    print("⏳ Aguardando 5 segundos...")
                    time.sleep(5)
        
        if not success:
            print(f"💀 [FALHA CRÍTICA] Desistindo após {max_retries} tentativas.")
            
            # RESPOSTA REFINADA
            response = {
                "type": "BET_RESULT",
                "batch_id": batch_id,
                "status": "FAILED",
                "message": f"Falha após 3 tentativas. Último erro: {last_error_message}"
            }
            ws.send(json.dumps(response))

    except Exception as e:
        print(f"[ERRO CRÍTICO NO PYTHON]: {e}")
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