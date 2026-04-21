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
# 🔁 GERADOR ÁUDIO
# =========================
def gerar_audio(texto, config):
    limpar_audios()

    nome = f"{uuid.uuid4().hex}.mp3"
    caminho = os.path.join(AUDIO_DIR, nome)

    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    loop.run_until_complete(gerar_edge(texto, caminho, config))
    loop.close()

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
                {"role": "system", "content": "Você é um assistente direto."},
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
        return jsonify({
            "erro": str(e)
        })

# =========================
# 🎓 MÓDULO EDUCAÇÃO (BASE)
# =========================
def executar_modulo_educacao(modulo, mensagem):

    if modulo == "ingles":
        return "Módulo inglês funcionando"

    return "Módulo não encontrado"

# =========================
# 🎓 ROTA EDUCAÇÃO
# =========================
@app.route("/educacao", methods=["POST"])
def educacao():
    mensagem = request.form.get("mensagem")
    modulo = request.form.get("modulo", "ingles")

    resposta = executar_modulo_educacao(modulo, mensagem)

    return jsonify({
        "resposta": resposta
    })

# =========================
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
