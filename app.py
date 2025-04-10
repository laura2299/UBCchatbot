from flask import Flask, request, jsonify
from openai import OpenAI
import requests
import time
from datetime import datetime
import os
import csv
import logger
from dotenv import load_dotenv
import os

load_dotenv()  # Carga las variables del archivo .env

# Ahora accedes a ellas con os.getenv()
openai_api_key = os.getenv("OPENAI_API_KEY")
whatsapp_token = os.getenv("WHATSAPP_TOKEN")
phone_id = os.getenv("WHATSAPP_PHONE_ID")
verify_token = os.getenv("VERIFY_TOKEN")

app = Flask(__name__)
logger.log_inicio()
# OpenAI
client = OpenAI(api_key=openai_api_key)

# Datos CSV
with open("costos_servicos.csv", encoding="Windows-1252") as f:
    costos_csv = f.read()
with open("formas_de_pago.csv", encoding="Windows-1252") as f:
    formas_de_pago_csv = f.read()
with open("requisitos_ubc.csv", encoding="Windows-1252") as f:
    requisitos_csv = f.read()
with open("tiempo_entrega.csv", encoding="Windows-1252") as f:
    tiempo_entrega_csv = f.read()

# Reglas
reglas = """
Tu eres UBCBot un chatbot para atencion de servicios en estudios del Instituto de Investigacion de la unidad de biologia celular. \
Primero saludas al cliente presentandote como UBCbot, luego consultas mediante un menu de opciones si quiere saber costos de los servicios, las formas de pago, los requisitos para los servicios o el tiempo de entrega. \
preguntale cual es su duda y si tiene algunas ideas de lo que necesita de lo contrario dale sugrencias \
Respondes en un estilo amigable breve y muy conversacional.\
pregunta que tipo de estudio esta buscando e informale cual es el tiempo de entrega. \
si  pregunta sobre qué días pueder recoger los resultados dile que el horario de atención es de lunes a viernes de 9:30 a 17:15. \
el tiempo de demora de estudios  de inmunofenotipo es de 24 horas, de Biología molecular y FISH 15 días y biología molecular PCR cuantitativos 1 mes.\
si pregunta sobre los costos de algun tipo de estudio informale los costos (obtenlos de costos_csv)\
consulta si el usuario quiere consultar algo mas \
si quiere hacer un estudio dale esta direccion de formulario para la solicitud de estudio: https://institutobiologiacelular.org/wp-content/uploads/2022/07/Ficha-lab-2022.pdf, dile que este formulario lo debe llenar su doctor encargado \
En caso de pago efectivo, dale esta direccion:Caja recaudadora,
Planta baja de la Facultad de Medicina – UMSA
Av. Saavedra N° 2246, Miraflores (frente Hospital General)\
en caso de pago por deposito A la siguiente cuenta bancaria:
Banco Unión S.A. Cta: 1-4714130  Facultad de Medicina – UMSA y dile que debe  enviar boleta original del depósito bancario junto a la muestra\
en caso de transferencia bancaria A la siguiente cuenta bancaria: Banco Unión S.A. Cta: 1-4714130 NIT: 1020071028 Facultad de Medicina – UMSA y dile que debe  enviar comprobante de transferencia bancaria al WhatsApp +591-65556287\
costo de servicios en csv: \
formas de pago en csv: \
requisitos en csv: \
tiempo de entrega en csv: \
si quiere comunicarse con una persona humana, dile que puede contactar al siguiente número: +591-65556287. \
"""
contexto = [
    {"role": "system", "content": f"{reglas} {costos_csv} {formas_de_pago_csv} {requisitos_csv} {tiempo_entrega_csv}"}
]
def guardar_feedback(telefono, mensaje_usuario, respuesta_bot):
    ahora = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    with open("registro_chatbot.csv", mode="a", newline="", encoding="utf-8") as archivo:
        escritor = csv.writer(archivo,delimiter=";")
        escritor.writerow([ahora, telefono, mensaje_usuario, respuesta_bot])

def obtener_respuesta(mensaje_usuario):
    contexto.append({"role": "user", "content": mensaje_usuario})
    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=contexto,
        temperature=0.5
    )
    logger.log_api_llamada("OpenAI", "Respuesta generada correctamente.")

    respuesta = response.choices[0].message.content
    contexto.append({"role": "assistant", "content": respuesta})
    return respuesta

@app.route('/webhook', methods=['GET'])
def verificar():
    
    token = request.args.get("hub.verify_token")
    challenge = request.args.get("hub.challenge")
    if token == verify_token:
        return challenge
    return "Token inválido", 403

@app.route('/webhook', methods=['POST'])
def recibir_mensaje():
    data = request.get_json()

    try:
        entry = data.get("entry", [])[0]
        changes = entry.get("changes", [])[0]
        value = changes.get("value", {})

        # ⚠️ Verifica si hay mensajes antes de acceder
        messages = value.get("messages", [])

        if messages:
            mensaje = messages[0]
            texto = mensaje["text"]["body"]
            telefono = mensaje["from"]
            
            logger.log_mensaje_recibido(telefono, texto)

            respuesta = obtener_respuesta(texto)
            logger.log_respuesta_enviada(telefono, respuesta)
            enviar_mensaje(telefono, respuesta)
            # ✅ Guarda en el archivo CSV
            guardar_feedback(telefono, texto, respuesta)

    except Exception as e:
        logger.log_error(f"Error al procesar el mensaje: {str(e)}")

    return jsonify({"status": "ok"}), 200

def enviar_mensaje(telefono, mensaje):
    url = "https://graph.facebook.com/v17.0/{phone_id}/messages"
    headers = {
        "Authorization": "Bearer {whatsapp_token}",
        "Content-Type": "application/json"
    }
    payload = {
        "messaging_product": "whatsapp",
        "to": telefono,
        "text": {"body": mensaje}
    }
    response = requests.post(url, json=payload, headers=headers)
    logger.log_api_llamada("WhatsApp", f"Status: {response.status_code} - Respuesta: {response.text}")

if __name__ == '__main__':
    app.run(port=5000, debug=True)
