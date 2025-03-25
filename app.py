import os
import requests
from flask import Flask, request, jsonify
#from dotenv import load_dotenv
from flask import render_template

#load_dotenv()

app = Flask(__name__)

#API_KEY = os.getenv("GEMINI_API_KEY")

API_KEY = "AIzaSyD_Ksifg6LvyLRXNrz53nAyqRvCY3hlUjc"
GEMINI_API_URL = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent?key={API_KEY}"

@app.route("/")
def home():
    return render_template("index.html")

@app.route("/saludo", methods=["GET"])
def saludo():
    return jsonify({'saludo': 'Hola, ¿cómo puedo ayudarte?'})

@app.route("/chat", methods=["POST"])
def chat():
    data = request.get_json()
    user_message = data.get("message")

    if not user_message:
        return jsonify({"error": "Mensaje vacío"}), 400

    response = requests.post(
        GEMINI_API_URL,
        headers={"Content-Type": "application/json"},
        json={"contents": [{"parts": [{"text": user_message}]}]}
    )

    if response.status_code == 200:
        try:
            gemini_response = response.json()["candidates"][0]["content"]["parts"][0]["text"]
        except KeyError:
            gemini_response = "Error en la respuesta del modelo."

        return jsonify({"response": gemini_response})
    
    return jsonify({"error": "Error al conectar con Gemini"}), response.status_code



# MAIN
if __name__ == "__main__":
    app.run(debug=True)
