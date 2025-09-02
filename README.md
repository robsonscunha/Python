
# WhatsApp + GPT Bot (Render.com)

Este projeto é um webhook Flask para integrar WhatsApp Business API com OpenAI (GPT). Preparado para deploy no Render.com.

## Passos Rápidos

1. **Edite os segredos no Render** (NÃO commitar .env):
   - `OPENAI_API_KEY`
   - `WHATSAPP_TOKEN`
   - `PHONE_ID`
   - `VERIFY_TOKEN` (crie você mesmo, ex.: `exclusiva-tech-2025`)
   - `GRAPH_API_VERSION` (opcional, padrão `v18.0`)

2. **Deploy no Render**
   - Build Command: `pip install -r requirements.txt`
   - Start Command: `gunicorn app:app --bind 0.0.0.0:$PORT --workers 2 --threads 4 --timeout 60`

3. **Configurar Webhook no Meta Developers**
   - Callback URL: `https://SEU-SERVICE.onrender.com/webhook`
   - Verify Token: use o mesmo `VERIFY_TOKEN`
   - Assinar o campo `messages` nas assinaturas de Webhook do produto WhatsApp

4. **Testar**
   - Envie mensagem para o número de teste do WhatsApp (no painel do Meta)
   - Veja os logs no Render

## Desenvolvimento Local

- Rode: `python app.py`
- Se quiser testar Webhook sem deploy, use ngrok: `ngrok http 5000` e depois configure a URL do webhook no Meta.
