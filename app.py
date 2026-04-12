from flask import Flask, render_template, request
from groq import Groq
import subprocess
import os

# ------------------------
# APP FLASK
# ------------------------
app = Flask(__name__)

# 🔐 API KEY vinda do Render (variável de ambiente)
client = Groq(api_key=os.getenv("GROQ_API_KEY"))


# ------------------------
# ÁUDIO (Edge TTS)
# ------------------------
def gerar_audio(texto):
    try:
        if not os.path.exists("static"):
            os.makedirs("static")

        nome_arquivo = "static/resposta.mp3"

        subprocess.run([
            "edge-tts",
            "--text", texto,
            "--voice", "pt-BR-AntonioNeural",
            "--write-media", nome_arquivo
        ], check=True)

        return nome_arquivo

    except Exception as e:
        print("❌ erro áudio:", e)
        return None


# ------------------------
# ROTA PRINCIPAL
# ------------------------
@app.route("/", methods=["GET", "POST"])
def home():
    resposta = ""
    audio = None

    if request.method == "POST":
        mensagem = request.form.get("mensagem", "").strip()

        if not mensagem:
            return render_template("index.html", resposta="", audio=None)

        print("📩 mensagem:", mensagem)

        try:
            chat = client.chat.completions.create(
                messages=[
                    {
                        "role": "system",
                        "content": "Responda de forma direta, natural e sem usar histórico."
                    },
                    {
                        "role": "user",
                        "content": mensagem
                    }
                ],
                model="llama-3.1-8b-instant",
                max_tokens=180,
                temperature=0.7
            )

            resposta = chat.choices[0].message.content
            print("🤖 resposta:", resposta)

            # 🔊 gera áudio
            audio = gerar_audio(resposta)

        except Exception as e:
            resposta = f"Erro IA: {str(e)}"

    return render_template("index.html", resposta=resposta, audio=audio)


# ------------------------
# EXECUÇÃO LOCAL
# ------------------------
if __name__ == "__main__":
    app.run()
