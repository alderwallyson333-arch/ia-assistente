from flask import Flask, render_template, request, jsonify
from groq import Groq
import edge_tts
import asyncio
import uuid
import os
import re

app = Flask(__name__)

# =========================
# 🔥 DEBUG (PROVA DE DEPLOY)
# =========================
@app.route("/debug")
def debug():
    return "VERSAO NOVA ATIVA"

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
# 🎙️ VOZ
# =========================
NARRADOR = {
    "voice": "pt-BR-AntonioNeural",
    "rate": "+5%",
    "pitch": "+5%"
}

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

async def gerar_edge(texto, arquivo):
    texto = aplicar_comandos(texto)

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
# 🧠 ASSISTENTE
# =========================
@app.route("/")
def home():
    return "HOME OK"

@app.route("/perguntar", methods=["POST"])
def perguntar():
    mensagem = request.form.get("mensagem")

    chat = client.chat.completions.create(
        model="llama-3.1-8b-instant",
        messages=[
            {"role": "system", "content": "Assistente direto"},
            {"role": "user", "content": mensagem}
        ]
    )

    resposta = chat.choices[0].message.content
    audio = gerar_audio(resposta)

    return jsonify({
        "resposta": resposta,
        "audio": audio
    })

# =========================
# 🎙️ NARRADOR
# =========================
@app.route("/narrador")
def narrador_page():
    return "NARRADOR OK"

@app.route("/narrar", methods=["POST"])
def narrar():
    mensagem = request.form.get("mensagem")

    audio = gerar_audio(mensagem)

    return jsonify({
        "resposta": mensagem,
        "audio": audio
    })

# =========================
# 🎓 EDUCAÇÃO (BASE)
# =========================
def executar_modulo_educacao(modulo, mensagem):
    if modulo == "ingles":
        return "MODULO INGLES OK"
    return "MODULO NAO ENCONTRADO"

@app.route("/educacao")
def educacao_get():
    return "EDUCACAO OK"

@app.route("/educacao", methods=["POST"])
def educacao_post():
    mensagem = request.form.get("mensagem")
    modulo = request.form.get("modulo", "ingles")

    resposta = executar_modulo_educacao(modulo, mensagem)

    return jsonify({
        "resposta": resposta
    })

# =========================
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
