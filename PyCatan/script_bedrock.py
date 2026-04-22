import boto3
import json
import os 

# Importante: antes de ejecutar el script, abre un terminal y escribe:
# export AWS_BEARER_TOKEN_BEDROCK="TU CLAVE"

token = os.getenv('AWS_BEARER_TOKEN_BEDROCK')

if not token:
    raise ValueError("ERROR: No se encuentra la variable de entorno AWS_BEARER_TOKEN_BEDROCK")

REGION = "us-west-2"
MODEL_ID = "us.amazon.nova-micro-v1:0"
#MODEL_ID = "mistral.mistral-7b-instruct-v0:2"
#MODEL_ID = "us.meta.llama3-3-70b-instruct-v1:0"

client = boto3.client("bedrock-runtime", region_name=REGION)

human_prompt = """
YOUR PROMPT

Assistant:
"""

# Cuerpo de la invocación
body = {
    "prompt": human_prompt,
    "max_tokens" : 250,
    "temperature": 0
}

response = client.converse(
    modelId=MODEL_ID,
    messages=[{"role": "user", "content": [{"text": human_prompt}]}]
)

texto_respuesta = response['output']['message']['content'][0]['text']

# Métricas de tokens
input_tokens = response['usage']['inputTokens']
output_tokens = response['usage']['outputTokens']
total_tokens = response['usage']['totalTokens']

# Latencia (proporcionada por Bedrock en milisegundos)
latencia = response['metrics']['latencyMs']

print(f"Texto: {texto_respuesta}")
print(f"Tokens -> In: {input_tokens} | Out: {output_tokens} | Total: {total_tokens}")
print(f"Latencia: {latencia}ms")

# Limpiamos posibles espacios o saltos de línea
raw_text = response['output']['message']['content'][0]['text'].strip()

try:
    # 2Convertimos el string en un diccionario de Python
    datos_json = json.loads(raw_text)
    print(datos_json)    
    
except json.JSONDecodeError:
    print("Error: El modelo no devolvió un JSON válido. Revisa el prompt.")