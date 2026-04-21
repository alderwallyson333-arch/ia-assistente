from flask import Flask, render_template, request, jsonify
from groq import Groq
import edge_tts
import asyncio
import uuid
import os
import re

app = Flask(__name__)

# =========================
# 🔑 API KEY
# =========================
GROQ_API_KEY = os.getenv("GROQ_API_KEY")
client = Groq(api_key=GROQ_API_KEY)

# =========================
# 📁 ÁUDIO
# =========================
AUDIO_DIR = "static/audio"
os.makedirs(AUDIO_DIR, exist_ok=True)

def limpar_audios():
    for f in os.listdir(AUDIO_DIR):
        caminho = os.path.join(AUDIO_DIR, f)
        if os.path.isfile(caminho):
            os.remove(caminho)

# =========================
# 🎙️ CONFIG VOZ
# =========================
NARRADOR = {
    "voice": "pt-BR-AntonioNeural",
    "rate": "+5%",
    "pitch": "+5%"
}

# =========================
# 🔊 EDGE TTS
# =========================
async def gerar_edge(texto, arquivo):
    ssml = f"""
<speak>
    <prosody rate="{NARRADOR['rate']}" pitch="{NARRADOR['pitch']}">
        {texto}
    </prosody>
</speak>
"""

    communicate = edge_tts.Communicate(ssml, voice=NARRADOR["voice"])
    await communicate.save(arquivo)

def gerar_audio(texto):
    limpar_audios()

    nome = f"{uuid.uuid4().hex}.mp3"
    caminho = os.path.join(AUDIO_DIR, nome)

    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    loop.run_until_complete(gerar_edge(texto, caminho))
    loop.close()

    return f"/static/audio/{nome}"

# =========================
# 🧠 ASSISTENTE PRINCIPAL
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
                {"role": "system", "content": "Você é um assistente direto e útil."},
                {"role": "user", "content": mensagem}
            ]
        )

        resposta = chat.choices[0].message.content
        audio = gerar_audio(resposta)

        return jsonify({
            "resposta": resposta,
            "audio": audio
        })

    except Exception as e:
        return jsonify({"erro": str(e)})

# =========================
# 🎙️ NARRADOR
# =========================
@app.route("/narrador")
def narrador_page():
    return render_template("narrador.html")

@app.route("/narrar", methods=["POST"])
def narrar():
    mensagem = request.form.get("mensagem")

    try:
        audio = gerar_audio(mensagem)

        return jsonify({
            "resposta": mensagem,
            "audio": audio
        })

    except Exception as e:
        return jsonify({"erro": str(e)})

# =========================
# 🎓 EDUCAÇÃO (INGLÊS SIMPLES)
# =========================
def professor_ingles(mensagem):
    chat = client.chat.completions.create(
        model="llama-3.1-8b-instant",
        messages=[
            {
                "role": "system",
                "content": "Você é um professor de inglês direto e prático. Corrija erros e explique de forma simples."
            },
            {
                "role": "user",
                "content": mensagem
            }
        ]
    )

    return chat.choices[0].message.content

# =========================
# 🎓 ROTA EDUCAÇÃO
# =========================
@app.route("/educacao", methods=["POST"])
def educacao():
    mensagem = request.form.get("mensagem")
    modulo = request.form.get("modulo", "ingles")

    try:
        if modulo == "ingles":
            resposta = professor_ingles(mensagem)
        else:
            resposta = "Módulo não encontrado"

        audio = gerar_audio(resposta)

        return jsonify({
            "resposta": resposta,
            "audio": audio
        })

    except Exception as e:
        return jsonify({"erro": str(e)})

# =========================
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
