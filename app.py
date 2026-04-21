from flask import Flask, jsonify
import requests
import os
import uuid

app = Flask(__name__)

# =========================
# CONFIG
# =========================
AUDIO_DIR = "static/audio"
os.makedirs(AUDIO_DIR, exist_ok=True)

# =========================
# TESTE DE DEPLOY
# =========================
@app.route("/")
def home():
    return "OK NOVO"

@app.route("/teste")
def teste():
    return "ROTA OK"

# =========================
# TESTE ELEVENLABS
# =========================
@app.route("/teste-eleven")
def teste_eleven():
    api_key = os.getenv("ELEVEN_API_KEY")

    if not api_key:
        return {"erro": "API KEY NÃO CARREGADA"}

    url = "https://api.elevenlabs.io/v1/text-to-speech/21m00Tcm4TlvDq8ikWAM"

    headers = {
        "xi-api-key": api_key.strip(),
        "Content-Type": "application/json"
    }

    data = {
        "text": "Teste simples funcionando",
        "model_id": "eleven_multilingual_v2"
    }

    response = requests.post(url, json=data, headers=headers)

    debug = {
        "status": response.status_code,
        "content_type": response.headers.get("Content-Type"),
        "bytes": len(response.content),
        "preview": response.text[:200]
    }

    # salva arquivo para validar
    nome = f"{uuid.uuid4().hex}.mp3"
    caminho = os.path.join(AUDIO_DIR, nome)

    with open(caminho, "wb") as f:
        f.write(response.content)

    return jsonify(debug)

# =========================
# RUN
# =========================
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
