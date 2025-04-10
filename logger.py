import logging
from datetime import datetime

# Configuración básica del logger
logging.basicConfig(
    level=logging.INFO,
    format='[%(asctime)s] %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("chatbot.log"),       # Archivo de logs
        logging.StreamHandler()                   # También en consola
    ]
)

# Funciones para registrar eventos

def log_inicio():
    logging.info("🤖 Chatbot iniciado correctamente.")

def log_mensaje_recibido(numero, mensaje):
    logging.info(f"📥 Mensaje recibido de {numero}: {mensaje}")

def log_respuesta_enviada(numero, respuesta):
    logging.info(f"📤 Respuesta enviada a {numero}: {respuesta}")

def log_error(error):
    logging.error(f"⚠️ Error: {str(error)}")

def log_api_llamada(servicio, detalles=""):
    logging.info(f"🔗 Llamada a API {servicio} realizada. {detalles}")
