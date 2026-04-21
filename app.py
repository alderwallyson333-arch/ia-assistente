from flask import Flask, jsonify
import requests
import os

app = Flask(__name__)

@app.route("/")
def home():
    return "Servidor ativo"

@app.route("/teste-eleven")
def teste_eleven():
    api_key = os.getenv("ELEVEN_API_KEY")

    if not api_key:
        return {"erro": "API KEY NÃO CARREGADA"}

    url = "https://api.elevenlabs.io/v1/text-to-speech/21m00Tcm4TlvDq8ikWAM"

    headers = {
        "xi-api-key": api_key.strip(),
        "Content-Type": "application/json"
    }

    data = {
        "text": "Teste simples de áudio funcionando",
        "model_id": "eleven_multilingual_v2"
    }

    try:
        response = requests.post(url, json=data, headers=headers)

        debug = {
            "status": response.status_code,
            "content_type": response.headers.get("Content-Type"),
            "bytes": len(response.content),
            "preview": response.text[:200]
        }

        # salva o arquivo SEM validação (para inspeção)
        with open("teste.mp3", "wb") as f:
            f.write(response.content)

        return jsonify(debug)

    except Exception as e:
        return {"erro": str(e)}

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
