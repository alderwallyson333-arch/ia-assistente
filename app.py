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

# 🧹 LIMPAR ÁUDIOS
def limpar_audios():
    for f in os.listdir(AUDIO_DIR):
        caminho = os.path.join(AUDIO_DIR, f)
        if os.path.isfile(caminho):
            os.remove(caminho)

# 🔊 GERAR ÁUDIO
async def gerar_audio_async(texto, arquivo):
    communicate = edge_tts.Communicate(texto, voice="pt-BR-AntonioNeural")
    await communicate.save(arquivo)

def gerar_audio(texto):
    limpar_audios()
    nome = f"{uuid.uuid4().hex}.mp3"
    caminho = os.path.join(AUDIO_DIR, nome)

    asyncio.run(gerar_audio_async(texto, caminho))

    return f"/static/audio/{nome}"

# 🌐 PÁGINA
@app.route("/")
def home():
    return render_template("index.html")

# 🤖 PERGUNTA
@app.route("/perguntar", methods=["POST"])
def perguntar():
    mensagem = request.form.get("mensagem")

    try:
        chat = client.chat.completions.create(
            model="llama-3.1-8b-instant",
            messages=[
                {
                    "role": "system",
                    "content": "Você é um assistente virtual por voz, direto, rápido e natural. Responda como uma pessoa falando, com no máximo 2 frases curtas."
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

# 🚀 RUN
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
