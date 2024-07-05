import os
import pathlib
from flask import Flask, request, jsonify
from azure.storage.blob import BlobServiceClient, BlobClient, ContainerClient
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
import google.generativeai as genai
import requests
from dotenv import load_dotenv
import webbrowser
import time
from flask import Flask, jsonify
from flask_cors import CORS
from pathlib import Path
from PIL import Image
import io

load_dotenv()


genai.configure(api_key=os.getenv("API_KEY"))


model = genai.GenerativeModel('gemini-1.5-flash', generation_config={"response_mime_type": "application/json"})


app = Flask(__name__)
CORS(app)

@app.route('/generate', methods=['POST'])
def generate():
    try:
        # Verifica se os arquivos de imagem foram enviados
        if 'image1' not in request.files:
            return jsonify({'error': 'uma imagem é necessária'}), 400
       
        image1_file = request.files['image1']
        #image2_file = request.files['image2']
       
        
        imagem = Image.open(image1_file)
        buffer_jpg = io.BytesIO()
        imagem.save(buffer_jpg, format='JPEG')
        buffer_jpg.seek(0)
        bytes_jpg = buffer_jpg.read()
       
        #Lê os bytes das imagens
        # image1 = {
        #     'mime_type': image1_file.content_type,
        #     'data': image1_file.read()
        # }
        #Lê os bytes das imagens
        image1 = {
            'mime_type': 'image/jpeg',
            'data': bytes_jpg
        }


       
        # image2 = {
        #     'mime_type': image2_file.content_type,
        #     'data': image2_file.read()
        # }


        # Lê o texto do prompt
        prompt_template = request.form.get('prompt', 'Recomende uma música baseada nessa imagem.')


        prompt = f'Recomende uma música baseada nessa imagem e no seguinte gênero ou artista ou nome de música {prompt_template}'


        # Gera o conteúdo usando o modelo
        response = model.generate_content([prompt, image1])
        nome_musica = response.text


        # Endpoint da API do Spotify para buscar músicas
        url = 'https://api.spotify.com/v1/search'
        # access_token = os.getenv("SPOTIFY_ACCESS_TOKEN")
        access_token = os.getenv("SPOTIFY_ACCESS_TOKEN")


        # Parâmetros da requisição (busca por tipo 'track' e nome da música 'Post')
        params = {
            'q': nome_musica,
            'type': 'track',
            'market': 'US',
            'limit': 1,
        }


        # Cabeçalho da requisição com o token de acesso
        headers = {
            'Authorization': 'Bearer ' + access_token
        }


        # Fazendo a requisição GET
        spotify_response = requests.get(url, headers=headers, params=params)


        # Verifica se a requisição foi bem-sucedida
        if spotify_response.status_code == 200:
            # Exibe o resultado da busca
            data = spotify_response.json()
            items = data['tracks']['items']
            link = items[0]['external_urls']['spotify']
           
            webbrowser.open(link)

            filename = f"output-{items[0]['id']}-{time.time() * 1000}.pdf"
 
            # Cria um canvas com tamanho de página letter
            c = canvas.Canvas(filename, pagesize=letter)
 
            # Define a posição inicial
            x = 100
            y = 750
 
            # Adiciona dados ao PDF, um embaixo do outro
            data = [
                f'ID: {items[0]['id']}',
                f'Nome da Música: {items[0]['name']}',
                f'Popularidade: {items[0]['popularity']}',
                f'Artista: {items[0]['artists'][0]['name']}'
            ]
 
            for line in data:
                c.drawString(x, y, line)
                y -= 20  # Move para a próxima linha (ajuste conforme necessário)
 
            # Salva o PDF
            c.save()

            blob_service_client = BlobServiceClient.from_connection_string('CONNECTION_STRING')

            container_name = 'prompts'
            container_client = blob_service_client.get_container_client(container_name)
           
            file_path = rf'C:\Users\ss1091318\OneDrive - SESISENAISP - Corporativo\Documentos\mariana\musiqapp\py\{filename}'

            with open(file_path, "rb") as data:
                container_client.upload_blob(filename, data)
            print(f"Arquivo {filename} enviado para o contêiner {container_name}.")

            return jsonify({'response': 'ok'}), 200
        else:
            return jsonify({'error': 'Erro na requisição Spotify', 'details': spotify_response.text}), spotify_response.status_code
   
    except Exception as e:
        return jsonify({'error': str(e)}), 500


if __name__ == '__main__':
    app.run(debug=True, host='172.16.23.195', port=5000)

