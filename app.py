import os
import requests
import mysql.connector
from flask import Flask, request, jsonify
from dotenv import load_dotenv
from flask import render_template

load_dotenv()

app = Flask(__name__)

# Cargar credenciales desde el .env
DB_CONFIG = {
    "host": os.getenv("DB_HOST"),
    "port": os.getenv("DB_PORT"),
    "user": os.getenv("DB_USER"),
    "password": os.getenv("DB_PASSWORD"),
    "database": os.getenv("DB_NAME"),
}

#API_KEY = os.getenv("GEMINI_API_KEY")

API_KEY = "AIzaSyD_Ksifg6LvyLRXNrz53nAyqRvCY3hlUjc"
GEMINI_API_URL = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent?key={API_KEY}"

@app.route("/")
def home():
    return render_template("index.html")

@app.route("/saludo", methods=["GET"])
def saludo():
    return jsonify({'saludo': 'Hola, ¿cómo puedo ayudarte?'})

# Función para conectar a la base de datos
def get_db_connection():
    try:
        conn = mysql.connector.connect(**DB_CONFIG)
        return conn
    except mysql.connector.Error as err:
        print(f"Error al conectar a la base de datos: {err}")
        return None

# Función para analizar la base de datos y obtener información relevante
def consultar_db(user_message):
    conn = get_db_connection()
    if not conn:
        return "Error al conectar con la base de datos."

    cursor = conn.cursor(dictionary=True)
    respuesta = "No encontré información relevante."

    # Buscar información sobre clientes
    if "cliente" in user_message.lower():
        cursor.execute("SELECT cliente_id, nombre_cliente, email_cliente FROM clientes LIMIT 5")
        clientes = cursor.fetchall()
        if clientes:
            respuesta = "Aquí tienes algunos clientes:\n"
            for cliente in clientes:
                respuesta += f"- {cliente['nombre_cliente']} (Email: {cliente['email_cliente']})\n"

    # Buscar información sobre sedes
    elif "sede" in user_message.lower():
        cursor.execute("SELECT id_sede, nombre, direccion FROM sedes LIMIT 5")
        sedes = cursor.fetchall()
        if sedes:
            respuesta = "Aquí tienes algunas sedes:\n"
            for sede in sedes:
                respuesta += f"- {sede['nombre']} (Dirección: {sede['direccion']})\n"

    cursor.close()
    conn.close()
    return respuesta

# Ruta de chat que consulta la base de datos antes de usar Gemini
@app.route("/chat", methods=["POST"])
def chat():
    data = request.get_json()
    user_message = data.get("message")

    if not user_message:
        return jsonify({"error": "Mensaje vacío"}), 400

    # 1️⃣ Primero consulta la base de datos
    respuesta_db = consultar_db(user_message)
    if respuesta_db and "No encontré información" not in respuesta_db:
        return jsonify({"response": respuesta_db})

    # 2️⃣ Luego consulta la API externa
    respuesta_api = consultar_api_externa(user_message)
    if respuesta_api and "No encontré información" not in respuesta_api:
        return jsonify({"response": respuesta_api})

    # 3️⃣ Si no encuentra nada, consulta a Gemini
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

# Ruta para consultar la API externa
def consultar_api_externa(user_message):
    api_url = "https://api-function-http-turism-sem.onrender.com/api/usuario"
    
    try:
        response = requests.get(api_url, timeout=5)  # Timeout para evitar bloqueos

        if response.status_code == 200:
            data = response.json()

            # Supongamos que la API devuelve una lista de usuarios
            if isinstance(data, list) and len(data) > 0:
                respuesta = "Aquí tienes algunos usuarios:\n"
                for usuario in data[:5]:  # Limitar a 5 usuarios
                    respuesta += f"- {usuario.get('nombre', 'Sin nombre')} (Email: {usuario.get('email', 'No disponible')})\n"
                return respuesta

            return "No encontré información en la API externa."

        return "Error al obtener datos de la API externa."
    
    except requests.RequestException as e:
        return f"Error al conectar con la API externa: {e}"



# MAIN
if __name__ == "__main__":
    app.run(debug=True)
