from flask import Flask, request, jsonify
import requests
import os

app = Flask(__name__)

# ⚙️ Configurações do ambiente
VERIFY_TOKEN = os.getenv("VERIFY_TOKEN", "meu_token_verificacao")
WHATSAPP_TOKEN = os.getenv("WHATSAPP_TOKEN")
PHONE_NUMBER_ID = os.getenv("PHONE_NUMBER_ID")

# ✅ Endpoint de verificação do webhook
@app.route("/webhook", methods=["GET"])
def verify_webhook():
    mode = request.args.get("hub.mode")
    token = request.args.get("hub.verify_token")
    challenge = request.args.get("hub.challenge")

    if mode == "subscribe" and token == VERIFY_TOKEN:
        print("✅ Webhook verificado com sucesso!")
        return challenge, 200
    else:
        return "Erro de verificação", 403

# 📩 Recebimento de mensagens + status
@app.route("/webhook", methods=["POST"])
def webhook():
    data = request.get_json()

    try:
        changes = data["entry"][0]["changes"][0]["value"]

        # Caso seja mensagem recebida
        if "messages" in changes:
            for message in changes["messages"]:
                sender = message["from"]
                text = message.get("text", {}).get("body", "")
                print(f"📩 Mensagem recebida de {sender}: {text}")

                # responde automaticamente
                send_message(sender, f"Recebi sua mensagem: {text} ✅")

        # Caso seja atualização de status
        elif "statuses" in changes:
            for status in changes["statuses"]:
                msg_id = status["id"]
                status_name = status["status"]
                print(f"📊 Status da mensagem {msg_id}: {status_name}")

    except Exception as e:
        print(f"⚠️ Erro ao processar webhook: {e}")

    return jsonify({"status": "ok"}), 200

# 📤 Função para enviar mensagens
def send_message(to, text):
    url = f"https://graph.facebook.com/v19.0/{PHONE_NUMBER_ID}/messages"
    headers = {
        "Authorization": f"Bearer {WHATSAPP_TOKEN}",
        "Content-Type": "application/json"
    }
    payload = {
        "messaging_product": "whatsapp",
        "to": to,
        "type": "text",
        "text": {"body": text}
    }

    response = requests.post(url, headers=headers, json=payload)
    if response.status_code == 200:
        print("📤 Mensagem enviada com sucesso")
    else:
        print(f"❌ Erro ao enviar mensagem: {response.status_code} {response.text}")


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)

