import os
import logging
import requests
from flask import Flask, request
from openai import OpenAI

# --- Configuração e clientes ---
logging.basicConfig(level=logging.INFO)
app = Flask(__name__)

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
WHATSAPP_TOKEN = os.getenv("WHATSAPP_TOKEN")
PHONE_ID = os.getenv("PHONE_ID")
VERIFY_TOKEN = os.getenv("VERIFY_TOKEN")
GRAPH_API_VERSION = os.getenv("GRAPH_API_VERSION", "v18.0")  # pode ajustar no Render futuramente

if not OPENAI_API_KEY:
    app.logger.warning("OPENAI_API_KEY não definida!")
if not WHATSAPP_TOKEN:
    app.logger.warning("WHATSAPP_TOKEN não definida!")
if not PHONE_ID:
    app.logger.warning("PHONE_ID não definida!")
if not VERIFY_TOKEN:
    app.logger.warning("VERIFY_TOKEN não definida!")

client = OpenAI(api_key=OPENAI_API_KEY)

# --- Utilitários ---
def send_whatsapp_text(to: str, body: str):
    url = f"https://graph.facebook.com/{GRAPH_API_VERSION}/{PHONE_ID}/messages"
    headers = {
        "Authorization": f"Bearer {WHATSAPP_TOKEN}",
        "Content-Type": "application/json",
    }
    payload = {
        "messaging_product": "whatsapp",
        "to": to,
        "type": "text",
        "text": {"body": body[:4000]},
    }
    resp = requests.post(url, headers=headers, json=payload, timeout=20)
    if resp.status_code >= 300:
        app.logger.error("Erro ao enviar WhatsApp: %s %s", resp.status_code, resp.text)
    return resp

def extract_text(message: dict) -> str:
    """
    Extrai texto de diferentes tipos de mensagens do WhatsApp.
    Mantém simples: prioriza 'text', mas tenta outros campos comuns.
    """
    if not message:
        return ""
    if message.get("type") == "text" and "text" in message and "body" in message["text"]:
        return message["text"]["body"]
    # Botões/Interações
    if message.get("type") == "interactive":
        interactive = message.get("interactive", {})
        # botão
        button_reply = interactive.get("button_reply") or {}
        if "title" in button_reply:
            return button_reply["title"]
        # lista
        list_reply = interactive.get("list_reply") or {}
        if "title" in list_reply:
            return list_reply["title"]
    # fallback
    return ""

# --- Rotas ---
@app.route("/", methods=["GET"])
def health():
    return "ok", 200

# Verificação do webhook (desafio do Meta)
@app.route("/webhook", methods=["GET"])
def verify():
    mode = request.args.get("hub.mode")
    token = request.args.get("hub.verify_token")
    challenge = request.args.get("hub.challenge")
    if mode == "subscribe" and token == VERIFY_TOKEN:
        return challenge, 200
    return "Erro de verificação", 403

# Recebimento de mensagens
@app.route("/webhook", methods=["POST"])
def webhook():
    payload = request.get_json(silent=True) or {}
    app.logger.info("Recebido: %s", payload)

    try:
        entries = payload.get("entry", [])
        for entry in entries:
            changes = entry.get("changes", [])
            for change in changes:
                value = change.get("value", {})
                messages = value.get("messages", [])
                for msg in messages:
                    sender = msg.get("from")
                    text = extract_text(msg)

                    if not sender:
                        continue

                    if not text:
                        # Mensagens sem texto (áudio, mídia etc.) – responder educadamente
                        send_whatsapp_text(sender, "Recebi sua mensagem! Para já te ajudar, manda em texto o que você precisa 😊")
                        continue

                    # Chama o GPT para gerar a resposta
                    try:
                        completion = client.chat.completions.create(
                            model="gpt-4o-mini",
                            messages=[
                                {"role": "system", "content": "Você é um assistente da Exclusiva Tech, cordial, objetivo e prestativo. Responda em PT-BR."},
                                {"role": "user", "content": text},
                            ],
                        )
                        reply = completion.choices[0].message.content.strip()
                    except Exception as gen_err:
                        app.logger.exception("Erro ao consultar OpenAI: %s", gen_err)
                        reply = "Estou com uma instabilidade temporária para responder agora. Pode repetir sua pergunta daqui a pouco? 🙏"

                    send_whatsapp_text(sender, reply)

    except Exception as e:
        app.logger.exception("Erro no processamento do webhook: %s", e)

    # Sempre 200 rapidamente para não estourar timeout do Meta
    return "ok", 200

if __name__ == "__main__":
    port = int(os.getenv("PORT", "5000"))
    app.run(host="0.0.0.0", port=port, debug=True)
