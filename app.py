from flask import Flask, render_template, request
from groq import Groq
import edge_tts
import asyncio
import uuid
import os

app = Flask(__name__)

# 🔑 SUA CHAVE GROQ (Render já configurado)
client = Groq(api_key=os.getenv("GROQ_API_KEY"))

# 🎤 FUNÇÃO PARA GERAR ÁUDIO
async def gerar_audio_async(texto, arquivo):
    communicate = edge_tts.Communicate(texto, voice="pt-BR-AntonioNeural")
    await communicate.save(arquivo)

def gerar_audio(texto):
    nome = f"static/audio_{uuid.uuid4().hex}.mp3"
    asyncio.run(gerar_audio_async(texto, nome))
    return nome

# 🧠 ROTA PRINCIPAL
@app.route("/", methods=["GET", "POST"])
def home():
    resposta = ""
    audio = ""

    if request.method == "POST":
        mensagem = request.form.get("mensagem")

        try:
            chat = client.chat.completions.create(
                model="llama3-70b-8192",
                messages=[
                    {"role": "user", "content": mensagem}
                ]
            )

            resposta = chat.choices[0].message.content

            # 🔊 GERAR ÁUDIO
            audio = gerar_audio(resposta)

        except Exception as e:
            resposta = f"Erro: {str(e)}"

    return render_template("index.html", resposta=resposta, audio=audio)

# 🚀 RODAR APP
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
