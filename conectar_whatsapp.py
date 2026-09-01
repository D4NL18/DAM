import requests
import webbrowser
import os
import time

# Configurações do Servidor Evolution Go no GCP
EVOLUTION_URL = "http://35.254.233.21:8080"
GLOBAL_API_KEY = "DamBot2026SecureKey!"
INSTANCE_NAME = "dam_bot"

# Configurações do Webhook (Nosso Backend em Python)
WEBHOOK_URL = "http://backend_ia:8000/api/whatsapp/webhook"

headers = {
    "apikey": GLOBAL_API_KEY,
    "Content-Type": "application/json"
}

def main():
    print("Conectando ao Evolution Go no Google Cloud...")
    
    # 1. Criar a instância
    payload_create = {
        "instanceName": INSTANCE_NAME,
        "qrcode": True,
        "integration": "WHATSAPP-BAILEYS",
        "syncFullHistory": False,
        "readMessages": False
    }
    
    print(f"Criando instancia '{INSTANCE_NAME}'...")
    res_create = requests.post(f"{EVOLUTION_URL}/instance/create", headers=headers, json=payload_create)
    
    if res_create.status_code not in [200, 201]:
        print("A instancia talvez ja exista. Tentando pegar o QR Code...")
    
    # 2. Configurar o Webhook com Autenticação (Ajuste do SecOps)
    print("Configurando Webhook de recebimento...")
    payload_webhook = {
        "webhook": {
            "enabled": True,
            "url": WEBHOOK_URL,
            "headers": {
                "apikey": GLOBAL_API_KEY
            },
            "events": ["MESSAGES_UPSERT"]
        }
    }
    # Adicionando o header de autenticação que o SecOps configurou
    requests.post(f"{EVOLUTION_URL}/webhook/set/{INSTANCE_NAME}", headers=headers, json=payload_webhook)
    
    # 3. Solicitar a conexão (QR Code)
    print("Solicitando QR Code do WhatsApp...")
    res_connect = requests.get(f"{EVOLUTION_URL}/instance/connect/{INSTANCE_NAME}", headers=headers)
    
    data = res_connect.json()
    if "base64" in data:
        html_content = f"""
        <html>
            <body style="display:flex; justify-content:center; align-items:center; height:100vh; background:#222; color:#fff; font-family:sans-serif; flex-direction:column;">
                <h2>Escaneie o QR Code com seu WhatsApp</h2>
                <img src="{data['base64']}" style="border: 10px solid white; border-radius: 10px;" />
                <p>O Bot começará a responder automaticamente após a conexão.</p>
            </body>
        </html>
        """
        html_path = os.path.abspath("qrcode.html")
        with open(html_path, "w", encoding="utf-8") as f:
            f.write(html_content)
        
        print("✅ QR Code gerado com sucesso! Abrindo no seu navegador...")
        webbrowser.open("file://" + html_path)
    else:
        print("⚠️ QR Code não retornado. Verifique se a instância já não está conectada.")

if __name__ == "__main__":
    main()
