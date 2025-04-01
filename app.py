import os
import requests
import pyodbc
from flask import Flask, logging, request, jsonify
from dotenv import load_dotenv
from flask import render_template

load_dotenv()

app = Flask(__name__)

DB_CONFIG = {
    "server": os.getenv("DB_HOST"),  
    "database": os.getenv("DB_NAME"),
    "username": os.getenv("DB_USER"),
    "password": os.getenv("DB_PASSWORD"),
}

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
        conn = pyodbc.connect(
            f"DRIVER={{FreeTDS}};"
            f"SERVER={DB_CONFIG['server']};"
            f"DATABASE={DB_CONFIG['database']};"
            f"UID={DB_CONFIG['username']};"
            f"PWD={DB_CONFIG['password']};"
            "TrustServerCertificate=yes"
        )
        return conn
    except pyodbc.Error as err:
        print(f"Error al conectar a la base de datos: {err}")
        return None 

# Función para analizar la base de datos y obtener información relevante
def consultar_db(user_message):
    user_message_lower = user_message.lower()

    if any(palabra in user_message_lower for palabra in ["guía número", "guia numero", "primer guía", "primer guia", "primer guía", "guia 1"]):
        try:
            # Extraer el número solicitado (1 por defecto)
            numero = 1
            if "número 2" in user_message_lower or "numero 2" in user_message_lower:
                numero = 2
            elif "número 3" in user_message_lower or "numero 3" in user_message_lower:
                numero = 3
            
            query = f"""
            SELECT nombre, descripcion, anios_experiencia 
            FROM (
                SELECT ROW_NUMBER() OVER (ORDER BY nombre) as row_num, 
                       nombre, descripcion, anios_experiencia 
                FROM guia
            ) as numbered_guides
            WHERE row_num = {numero}
            """
            modo = "unico"
        except:
            return "No pude entender qué número de guía necesitas."
    
    # Detectar si pide información detallada de guías
    elif any(palabra in user_message_lower for palabra in ["datos del guia", "info del guia", "información del guía", "sobre el guia"]):
        query = "SELECT TOP 5 nombre, descripcion, anios_experiencia FROM guia ORDER BY nombre"
        modo = "detallado"
    
    # Detectar si pide todos los guías
    elif any(palabra in user_message_lower for palabra in ["todos los guias", "todos los guías", "listado de guias", "guías", "guias"]):
        query = "SELECT TOP 5 nombre, descripcion, anios_experiencia FROM guia ORDER BY nombre"
        modo = "multiple"
    
    # Detectar si pide ciudades
    elif "ciudad" in user_message_lower:
        query = "SELECT TOP 5 nombre, pais FROM ciudad ORDER BY nombre"
        modo = "ciudades"
    
    else:
        return "No encontré información relevante."

    conn = get_db_connection()
    if not conn:
        return "Error al conectar con la base de datos."

    cursor = conn.cursor()
    try:
        cursor.execute(query)
        resultados = cursor.fetchall()

        if not resultados:
            return "No encontré información disponible."

        if modo == "unico":
            guia = resultados[0]
            return (
                f"Información del guía solicitado:\n\n"
                f"• Nombre: {guia[0]}\n"
                f"• Descripción: {guia[1]}\n"
                f"• Años de experiencia: {guia[2]}\n"
            )
        
        elif modo == "detallado":
            respuesta = "Información detallada de guías:\n\n"
            for guia in resultados:
                respuesta += (
                    f"✦ {guia[0]} ✦\n"
                    f"Descripción: {guia[1]}\n"
                    f"Experiencia: {guia[2]} años\n\n"
                )
            return respuesta
        
        elif modo == "multiple":
            respuesta = "Listado de guías disponibles:\n\n"
            for i, guia in enumerate(resultados, 1):
                respuesta += (
                    f"{i}. {guia[0]}\n"
                    f"   - {guia[1]}\n"
                    f"   - Experiencia: {guia[2]} años\n\n"
                )
            return respuesta
        
        elif modo == "ciudades":
            respuesta = "Ciudades disponibles:\n\n"
            for ciudad in resultados:
                respuesta += f"• {ciudad[0]}, {ciudad[1]}\n"
            return respuesta


    except pyodbc.Error as err:
        print(f"Error en consulta SQL: {err}")
        return "Ocurrió un error al consultar los guías."
    finally:
        cursor.close()
        conn.close()

# Chatbot con lógica mejorada
@app.route("/chat", methods=["POST"])
def chat():
    data = request.get_json()
    user_message = data.get("message", "").strip()  # Añadido strip() para eliminar espacios en blanco

    if not user_message:
        return jsonify({"response": "Por favor, escribe un mensaje para poder ayudarte."})

    # Primero verificar si es un saludo simple
    saludos = ["hola", "hola!", "hi", "hello", "buenos días", "buenas tardes"]
    if user_message.lower() in saludos:
        return jsonify({"response": "¡Hola! Soy TuTourAssistant, tu asistente virtual. ¿En qué puedo ayudarte hoy?"})

    # Consultar base de datos
    respuesta_db = consultar_db(user_message)
    if not respuesta_db.startswith("No encontré información"):
        return jsonify({"response": respuesta_db})

    # Llamar a Gemini como último recurso
    try:
        response = requests.post(
            GEMINI_API_URL,
            headers={"Content-Type": "application/json"},
            json={"contents": [{"parts": [{"text": user_message}]}]},
            timeout=10
        )

        if response.status_code == 200:
            try:
                gemini_response = response.json()["candidates"][0]["content"]["parts"][0]["text"]
                return jsonify({"response": gemini_response})
            except KeyError:
                return jsonify({"response": "Lo siento, no pude entender tu pregunta. ¿Podrías reformularla?"})
        
        return jsonify({"response": "Lo siento, estoy teniendo problemas para conectarme con el servicio de asistencia. Por favor intenta más tarde."})

    except requests.RequestException as e:
        return jsonify({"response": "Estoy teniendo dificultades técnicas. Por favor intenta nuevamente más tarde."})

if __name__ == "__main__":
    app.run(debug=True)