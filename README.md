Chatbot con Gemini - Flask

Este proyecto es un chatbot basado en Flask que utiliza la API de Gemini para generar respuestas.

📌 Requisitos

Python 3.8 o superior

pip (administrador de paquetes de Python)

Acceso a Internet

Clave API de Gemini

🚀 Instalación y Configuración

1️⃣ Clonar el repositorio

'''
git clone https://github.com/tu_usuario/geminiBot.git
cd geminiBot
'''

2️⃣ Crear y activar entorno virtual
'''
python -m venv venv
venv\Scripts\activate
'''

3️⃣ Instalar dependencias
'''
pip install -r requirements.txt
'''

4️⃣ Configurar clave API de Gemini

Edita el archivo app.py y reemplaza TU_CLAVE con tu clave API de Gemini:

'''
API_KEY = "TU_CLAVE"
'''

5️⃣ Ejecutar la aplicación

'''
python app.py
'''

La aplicación se ejecutará en http://127.0.0.1:5000/.

📂 Estructura del Proyecto

'''
geminiBot/
│── static/            # Archivos estáticos (CSS, JS, imágenes)
│   ├── style.css      # Estilos CSS
│── templates/         # Plantillas HTML
│   ├── index.html     # Página principal
│── venv/              # Entorno virtual (no se sube al repositorio)
│── app.py             # Código del backend con Flask
│── requirements.txt   # Lista de dependencias
│── README.md          # Documentación del proyecto
'''

📌 Dependencias principales

Flask

Requests

🛠 Desactivar el entorno virtual

Cuando termines de trabajar en el proyecto, puedes desactivar el entorno virtual con:

deactivate

💡 Notas:

Si encuentras errores con las dependencias, intenta reinstalarlas con:

pip install --upgrade pip
pip install -r requirements.txt

Para ejecutar en Linux/macOS, la activación del entorno virtual es:

source venv/bin/activate

🚀 ¡Listo! Ahora puedes chatear con Gemini desde tu navegador. 😃