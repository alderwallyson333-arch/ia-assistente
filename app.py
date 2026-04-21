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

ELEVEN_API_KEY = os.getenv("ELEVEN_API_KEY")

# =========================
# TESTE SIMPLES (DEPLOY)
# =========================
@app.route("/teste")
def teste():
    return "funcionando"

# =========================
# ELEVENLABS (ISOLADO)
# =========================
def gerar_eleven(texto, caminho):
    if not ELEVEN_API_KEY:
        raise Exception("API KEY NÃO CARREGADA")

    url = "https://api.elevenlabs.io/v1/text-to-speech/21m00Tcm4TlvDq8ikWAM"

    headers = {
        "xi-api-key": ELEVEN_API_KEY.strip(),
        "Content-Type": "application/json"
    }

    data = {
        "text": texto,
        "model_id": "eleven_multilingual_v2"
    }

    response = requests.post(url, json=data, headers=headers)

    # 🔴 LOG REAL (vai aparecer no Render)
    print("\n===== DEBUG ELEVEN =====")
    print("STATUS:", response.status_code)
    print("HEADERS:", response.headers)
    print("BYTES:", len(response.content))
    print("TEXT:", response.text[:200])
    print("========================\n")

    if response.status_code != 200:
        raise Exception(f"Erro ElevenLabs: {response.status_code} - {response.text}")

    content_type = response.headers.get("Content-Type", "")

    if "audio" not in content_type:
        raise Exception("Resposta não é áudio válido")

    if len(response.content) < 2000:
        raise Exception("Áudio inválido (muito pequeno)")

    with open(caminho, "wb") as f:
        f.write(response.content)

# =========================
# TESTE ELEVEN
# =========================
@app.route("/teste-eleven")
def teste_eleven():
    try:
        caminho = os.path.join(AUDIO_DIR, f"{uuid.uuid4().hex}.mp3")
        gerar_eleven("Teste de áudio funcionando", caminho)

        return jsonify({
            "status": "ok",
            "arquivo": caminho
        })

    except Exception as e:
        return jsonify({
            "erro": str(e)
        })

# =========================
# RUN
# =========================
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
