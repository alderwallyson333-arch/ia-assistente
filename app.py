from flask import Flask, render_template, request, jsonify
from groq import Groq
import edge_tts
import asyncio
import uuid
import os
import re
import requests

app = Flask(__name__)

# =========================
# 🔑 API KEYS
# =========================
GROQ_API_KEY = os.getenv("GROQ_API_KEY")
ELEVEN_API_KEY = os.getenv("ELEVEN_API_KEY")

if not GROQ_API_KEY:
    raise Exception("GROQ_API_KEY não configurada")

client = Groq(api_key=GROQ_API_KEY)

# =========================
# 📁 ÁUDIOS
# =========================
AUDIO_DIR = "static/audio"
os.makedirs(AUDIO_DIR, exist_ok=True)

# =========================
# 🧹 LIMPA ÁUDIOS
# =========================
def limpar_audios():
    for f in os.listdir(AUDIO_DIR):
        caminho = os.path.join(AUDIO_DIR, f)
        if os.path.isfile(caminho):
            os.remove(caminho)

# =========================
# 🎙️ CONFIG NARRADORES
# =========================
NARRADORES = {
    "br": {
        "type": "edge",
        "voice": "pt-BR-AntonioNeural",
        "rate": "+5%",
        "pitch": "+5%"
    },
    "br_11": {
        "type": "eleven"
    }
}

# =========================
# 🧹 COMANDOS
# =========================
def aplicar_comandos(texto):
    comandos = {
        "pause": '<break time="400ms"/>',
        "long": '<break time="800ms"/>'
    }

    partes = re.split(r'(\(.*?\))', texto)
    resultado = ""

    for parte in partes:
        if parte.startswith("(") and parte.endswith(")"):
            cmd = parte[1:-1]
            if cmd in comandos:
                resultado += comandos[cmd]
        else:
            resultado += parte

    return resultado

# =========================
# 🔊 EDGE TTS
# =========================
async def gerar_edge(texto, arquivo, config):
    texto = aplicar_comandos(texto)

    ssml = f"""
<speak>
    <prosody rate="{config['rate']}" pitch="{config['pitch']}">
        {texto}
    </prosody>
</speak>
"""

    communicate = edge_tts.Communicate(
        ssml,
        voice=config["voice"]
    )

    await communicate.save(arquivo)

# =========================
# 🔥 ELEVENLABS (CORRIGIDO)
# =========================
def gerar_eleven(texto, caminho):
    if not ELEVEN_API_KEY:
        raise Exception("ELEVEN_API_KEY não configurada")

    url = "https://api.elevenlabs.io/v1/text-to-speech/21m00Tcm4TlvDq8ikWAM"

    headers = {
        "xi-api-key": ELEVEN_API_KEY.strip(),
        "Accept": "audio/mpeg",
        "Content-Type": "application/json"
    }

    data = {
        "text": texto.strip(),
        "model_id": "eleven_multilingual_v2"
    }

    response = requests.post(url, json=data, headers=headers)

    # 🔴 DEBUG REAL (vai aparecer no Render logs)
    print("STATUS:", response.status_code)
    print("HEADERS:", response.headers)

    if response.status_code != 200:
        raise Exception(f"ElevenLabs ERRO: {response.status_code} - {response.text}")

    content_type = response.headers.get("Content-Type", "")

    # 🔴 GARANTE QUE É ÁUDIO REAL
    if "audio" not in content_type:
        raise Exception(f"Resposta inválida (não é áudio): {response.text[:200]}")

    # 🔴 BLOQUEIA FALSO POSITIVO
    if len(response.content) < 2000:
        raise Exception("Áudio inválido ou muito pequeno")

    with open(caminho, "wb") as f:
        f.write(response.content)

# =========================
# 🔁 GERADOR
# =========================
def gerar_audio(texto, config):
    limpar_audios()

    nome = f"{uuid.uuid4().hex}.mp3"
    caminho = os.path.join(AUDIO_DIR, nome)

    if config["type"] == "edge":
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        loop.run_until_complete(gerar_edge(texto, caminho, config))
        loop.close()

    elif config["type"] == "eleven":
        try:
            gerar_eleven(texto, caminho)
        except Exception as e:
            raise Exception(f"Falha ElevenLabs: {str(e)}")

    return f"/static/audio/{nome}"

# =========================
# 🧠 ASSISTENTE
# =========================
@app.route("/")
def home():
    return render_template("index.html")

@app.route("/perguntar", methods=["POST"])
def perguntar():
    mensagem = request.form.get("mensagem")

    try:
        chat = client.chat.completions.create(
            model="llama-3.1-8b-instant",
            messages=[
                {"role": "system", "content": "Você é um assistente por voz direto."},
                {"role": "user", "content": mensagem}
            ]
        )

        resposta = chat.choices[0].message.content
        audio = gerar_audio(resposta, NARRADORES["br"])

        return jsonify({
            "resposta": resposta,
            "audio": audio
        })

    except Exception as e:
        return jsonify({"erro": str(e)})

# =========================
# 🎙️ NARRADOR PAGE
# =========================
@app.route("/narrador")
def narrador_page():
    return render_template("narrador.html")

# =========================
# 🎙️ NARRAR
# =========================
@app.route("/narrar", methods=["POST"])
def narrar():
    mensagem = request.form.get("mensagem")
    modo = request.form.get("modo", "br")

    try:
        config = NARRADORES.get(modo, NARRADORES["br"])
        audio = gerar_audio(mensagem, config)

        return jsonify({
            "resposta": mensagem,
            "audio": audio
        })

    except Exception as e:
        return jsonify({"erro": str(e)})

# =========================
# 🧪 TESTE DIRETO ELEVEN
# =========================
@app.route("/teste-eleven")
def teste_eleven():
    caminho = os.path.join(AUDIO_DIR, "teste.mp3")
    gerar_eleven("Teste direto funcionando", caminho)
    return {"ok": True}

# =========================
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
