import os
import streamlit as st
import base64
from openai import OpenAI
import openai
from PIL import Image
import paho.mqtt.client as mqtt
import json

# Function to encode the image to base64
def encode_image(image_file):
    return base64.b64encode(image_file.getvalue()).decode("utf-8")

# Function to send MQTT message
def send_mqtt_message(topic, message):
    try:
        # Configuración del broker MQTT
        broker = "broker.mqttdashboard.com"
        port = 1883
        
        # Crear cliente MQTT
        client = mqtt.Client()
        
        # Conectar al broker
        client.connect(broker, port, 60)
        
        # Publicar mensaje
        client.publish(topic, message)
        
        # Desconectar
        client.disconnect()
        
        return True
    except Exception as e:
        st.error(f"Error al enviar mensaje MQTT: {e}")
        return False

st.set_page_config(page_title="Analisis de imagen", layout="centered", initial_sidebar_state="collapsed")
# Streamlit page setup
st.title("Análisis de Imagen:🤖🏞️")
#image = Image.open('OIG4.jpg')
#st.image(image, width=350)

with st.sidebar:
    st.subheader("Este Agente analiza el contenido de la imagen y responde tus preguntas.")
    st.divider()
    st.subheader("Configuración MQTT")
    mqtt_topic = st.text_input('Tópico MQTT', value='control_remoto')
    
ke = st.text_input('Ingresa tu Clave')
os.environ['OPENAI_API_KEY'] = ke

# Retrieve the OpenAI API Key from secrets
api_key = os.environ['OPENAI_API_KEY']

# Initialize the OpenAI client with the API key
client = OpenAI(api_key=api_key)

# File uploader allows user to add their own image
uploaded_file = st.file_uploader("Upload an image", type=["jpg", "png", "jpeg"])

if uploaded_file:
    # Display the uploaded image
    with st.expander("Image", expanded = True):
        st.image(uploaded_file, caption=uploaded_file.name, use_container_width=True)

# Toggle for showing additional details input
show_details = st.toggle("Adiciona detalles sobre la imagen", value=False)

if show_details:
    # Text input for additional details about the image, shown only if toggle is True
    additional_details = st.text_area(
        "Adiciona contexto de la imagen aqui:",
        disabled=not show_details
    )

# Button to trigger the analysis
analyze_button = st.button("Analiza la imagen", type="secondary")

# Check if an image has been uploaded, if the API key is available, and if the button has been pressed
if uploaded_file is not None and api_key and analyze_button:

    with st.spinner("Analizando ..."):
        # Encode the image
        base64_image = encode_image(uploaded_file)
    
        prompt_text = ("Describe what you see in the image in spanish")
    
        if show_details and additional_details:
            prompt_text += (
                f"\n\nAdditional Context Provided by the User:\n{additional_details}"
            )
    
        # Create the payload for the completion request
        messages = [
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": prompt_text},
                    {
                        "type": "image_url",
                        "image_url": f"data:image/jpeg;base64,{base64_image}",
                    },
                ],
            }
        ]
    
        # Make the request to the OpenAI API
        try:
            full_response = ""
            message_placeholder = st.empty()
            response = openai.chat.completions.create(
              model= "gpt-4o",
              messages=[
                {
                   "role": "user",
                   "content": [
                     {"type": "text", "text": prompt_text},
                     {
                       "type": "image_url",
                       "image_url": {
                         "url": f"data:image/jpeg;base64,{base64_image}",
                       },
                     },
                   ],
                  }
                ],
              max_tokens=300,
              )
            
            if response.choices[0].message.content is not None:
                    full_response += response.choices[0].message.content
                    message_placeholder.markdown(full_response + "▌")
            
            # Final update to placeholder after the stream ends
            message_placeholder.markdown(full_response)
            
            # Enviar mensaje MQTT con la estructura solicitada
            mqtt_message = {"msg": full_response}
            
            if send_mqtt_message(mqtt_topic, json.dumps(mqtt_message)):
                st.success(f"✅ Mensaje enviado exitosamente al tópico '{mqtt_topic}'")
            
        except Exception as e:
            st.error(f"An error occurred: {e}")
            
else:
    # Warnings for user action required
    if not uploaded_file and analyze_button:
        st.warning("Please upload an image.")
    if not api_key:
        st.warning("Por favor ingresa tu API key.")
