from flask import Flask, render_template, request, jsonify
from groq import Groq
import edge_tts
import asyncio
import uuid
import os

app = Flask(__name__)

# 🔑 API KEY
client = Groq(api_key=os.getenv("GROQ_API_KEY"))

# 📁 PASTA DE ÁUDIO
AUDIO_DIR = "static/audio"
os.makedirs(AUDIO_DIR, exist_ok=True)

# 🧹 LIMPAR ÁUDIOS ANTIGOS
def limpar_audios():
    for f in os.listdir(AUDIO_DIR):
        caminho = os.path.join(AUDIO_DIR, f)
        if os.path.isfile(caminho):
            os.remove(caminho)

# 🔊 GERAR ÁUDIO (CORRIGIDO)
async def gerar_audio_async(texto, arquivo):
    communicate = edge_tts.Communicate(texto, voice="pt-BR-AntonioNeural")
    await communicate.save(arquivo)

def gerar_audio(texto):
    limpar_audios()
    nome = f"{uuid.uuid4().hex}.mp3"
    caminho = os.path.join(AUDIO_DIR, nome)

    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    loop.run_until_complete(gerar_audio_async(texto, caminho))
    loop.close()

    return f"/static/audio/{nome}"

# =========================
# ASSISTENTE (NORMAL)
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
                {
                    "role": "system",
                    "content": "Você é um assistente por voz, natural, direto e objetivo. Responda em até 2 frases curtas."
                },
                {
                    "role": "user",
                    "content": mensagem
                }
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
        chat = client.chat.completions.create(
            model="llama-3.1-8b-instant",
            messages=[
                {
                    "role": "system",
                    "content": """
Você é um narrador esportivo profissional brasileiro.

REGRAS:
- Narre com emoção intensa
- Use frases curtas
- Não explique nada
- Não converse
- Não responda perguntas
- Apenas narre como se estivesse AO VIVO

Exemplo:
GOOOOOOL! É DO FLAMENGO! QUE MOMENTO!
"""
                },
                {
                    "role": "user",
                    "content": mensagem
                }
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

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
