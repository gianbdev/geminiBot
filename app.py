import os
import requests
import pyodbc
from flask import Flask, logging, request, jsonify
from dotenv import load_dotenv
from flask import render_template

load_dotenv()

app = Flask(__name__)

# Cargar credenciales desde el .env
DB_CONFIG = {
    "server": os.getenv("DB_HOST"),  # Cambiado de "host" a "server" para pyodbc
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
            f"DRIVER={{ODBC Driver 17 for SQL Server}};"
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

# Ruta para consultar la API externa
def consultar_api_externa(user_message):
    triggers_usuario = ["usuario", "mis datos", "perfil", "info del usuario", "mis datos de usuario", "quién soy"]
    triggers_guias = ["guía", "guías", "guias", "guia", "tour", "tours", "guiatur", "guías disponibles"]
    
    if any(trigger in user_message.lower() for trigger in triggers_usuario):
        api_url = "https://api-function-hhtp-turism-sem.onrender.com/api/usuarios/67e9ef27eaba75fb074b082a"
        tipo = "usuario"
    elif any(trigger in user_message.lower() for trigger in triggers_guias):
        api_url = "https://api-function-hhtp-turism-sem.onrender.com/api/guias"
        tipo = "guias"
    else:
        return None  # Cambiado para que no devuelva respuesta inmediata
    
    try:
        response = requests.get(api_url, timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            
            if tipo == "usuario":
                return (
                    f"Información del usuario:\n"
                    f"- Nombre: {data.get('nombre', 'No disponible')}\n"
                    f"- Email: {data.get('email', 'No disponible')}\n"
                    f"- Rol: {data.get('rol', 'No disponible')}"
                )
            elif tipo == "guias":
                if isinstance(data, list):
                    if len(data) == 0:
                        return "No hay guías disponibles actualmente."
                    
                    respuesta = "Guías disponibles:\n"
                    for guia in data[:5]:
                        respuesta += (
                            f"\n- Nombre: {guia.get('nombre', 'N/A')}\n"
                            f"  Especialidad: {guia.get('especialidad', 'N/A')}\n"
                            f"  Idiomas: {', '.join(guia.get('idiomas', []))}\n"
                            f"  Experiencia: {guia.get('experiencia', 'N/A')} años"
                        )
                    if len(data) > 5:
                        respuesta += f"\n\nHay {len(data) - 5} guías más disponibles."
                    return respuesta
                else:
                    return "Formato de respuesta inesperado de la API de guías."
        else:
            return f"No pude obtener la información (Error {response.status_code})"
    
    except requests.Timeout:
        return "El servicio no respondió a tiempo. Por favor intenta nuevamente."
    except requests.RequestException as e:
        app.logger.error(f"Error en API: {str(e)}")
        return f"Error al conectar con el servicio: {str(e)}"

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

    # Consultar API externa
    respuesta_api = consultar_api_externa(user_message)
    if respuesta_api is not None:
        return jsonify({"response": respuesta_api})

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