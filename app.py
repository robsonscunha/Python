import os
import requests
from flask import Flask, request, jsonify

app = Flask(__name__)

# Variáveis de ambiente no Render
WHATSAPP_TOKEN = os.getenv("WHATSAPP_TOKEN")              # Token longo prazo
VERIFY_TOKEN = os.getenv("VERIFY_TOKEN")                  # Token usado para validação do webhook

@app.route("/webhook", methods=["GET"])
def verify():
    """Valida o webhook do WhatsApp"""
    mode = request.args.get("hub.mode")
    token = request.args.get("hub.verify_token")
    challenge = request.args.get("hub.challenge")

    if mode == "subscribe" and token == VERIFY_TOKEN:
        print("✅ Webhook validado com sucesso")
        return challenge, 200
    return "Erro de verificação", 403


@app.route("/webhook", methods=["POST"])
def webhook():
    """Recebe mensagens do WhatsApp e envia resposta fixa"""
    data = request.get_json()
    print("📩 Recebido:", data)

    try:
        entry = data["entry"][0]["changes"][0]["value"]
        phone_number_id = entry["metadata"]["phone_number_id"]      # ID correto do número
        from_number = entry["messages"][0]["from"]                  # Número do cliente
        msg_body = entry["messages"][0]["text"]["body"]

        # Mensagem fixa de resposta
        resposta = f"Recebi sua mensagem: {msg_body} ✅"

        # Enviar mensagem de volta
        send_whatsapp_message(phone_number_id, from_number, resposta)

    except KeyError:
        print("⚠️ Nenhuma mensagem encontrada neste payload")
    except Exception as e:
        print("❌ Erro no processamento:", e)

    return jsonify({"status": "ok"}), 200


def send_whatsapp_message(phone_number_id, to, message):
    """Função que envia mensagem via WhatsApp Cloud API"""
    url = f"https://graph.facebook.com/v21.0/{phone_number_id}/messages"
    headers = {
        "Authorization": f"Bearer {WHATSAPP_TOKEN}",
        "Content-Type": "application/json"
    }
    payload = {
        "messaging_product": "whatsapp",
        "to": to,
        "type": "text",
        "text": {"body": message}
    }

    response = requests.post(url, headers=headers, json=payload)
    print("📤 Resposta WhatsApp:", response.status_code, response.text)
    return response.json()


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
