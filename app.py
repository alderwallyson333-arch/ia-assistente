from flask import Flask, render_template, request, jsonify
from groq import Groq
import edge_tts
import asyncio
import uuid
import os

app = Flask(__name__)

# 🔑 API
client = Groq(api_key=os.getenv("GROQ_API_KEY"))

# 📁 ÁUDIO
AUDIO_DIR = "static/audio"
os.makedirs(AUDIO_DIR, exist_ok=True)

# =========================
# 🧠 ESTADO GLOBAL
# =========================
estado = {
    "modulo": "assistente",
    "submodulo": None
}

# =========================
# 📦 MÓDULOS
# =========================
MODULOS = {
    "assistente": {
        "system": "Você é um assistente direto e natural."
    },

    "educacao": {
        "system": "Você é um assistente educacional.",
        "submodulos": {

            "portugues": {
                "system": "Você é um especialista em Língua Portuguesa. Explique de forma clara, simples e direta."
            }

        }
    }
}

# =========================
# 🔊 VOZ
# =========================
async def gerar_audio_async(texto, arquivo):
    communicate = edge_tts.Communicate(
        texto,
        voice="pt-BR-AntonioNeural"
    )
    await communicate.save(arquivo)

def gerar_audio(texto):
    nome = f"{uuid.uuid4().hex}.mp3"
    caminho = os.path.join(AUDIO_DIR, nome)

    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    loop.run_until_complete(gerar_audio_async(texto, caminho))
    loop.close()

    return f"/static/audio/{nome}"

# =========================
# 🧠 RESOLVER CONTEXTO
# =========================
def obter_system():
    modulo = estado["modulo"]
    sub = estado["submodulo"]

    if sub:
        return MODULOS[modulo]["submodulos"][sub]["system"]

    return MODULOS[modulo]["system"]

# =========================
# 🎮 TROCA DE MODO
# =========================
def processar_comando(mensagem):
    msg = mensagem.lower()

    if "modo educação" in msg:
        estado["modulo"] = "educacao"
        estado["submodulo"] = None
        return "Modo educação ativado."

    if "modo português" in msg:
        estado["modulo"] = "educacao"
        estado["submodulo"] = "portugues"
        return "Especialista em língua portuguesa ativado."

    if "modo assistente" in msg:
        estado["modulo"] = "assistente"
        estado["submodulo"] = None
        return "Modo assistente ativado."

    return None

# =========================
# 🏠 ROTAS
# =========================
@app.route("/")
def home():
    return render_template("index.html")

@app.route("/perguntar", methods=["POST"])
def perguntar():
    mensagem = request.form.get("mensagem")

    try:
        # 🔄 verifica comando
        comando = processar_comando(mensagem)
        if comando:
            audio = gerar_audio(comando)
            return jsonify({
                "resposta": comando,
                "audio": audio
            })

        # 🧠 pega contexto do módulo
        system = obter_system()

        chat = client.chat.completions.create(
            model="llama-3.1-8b-instant",
            messages=[
                {"role": "system", "content": system},
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
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
