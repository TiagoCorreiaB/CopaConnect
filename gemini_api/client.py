import os
from google import genai
from dotenv import load_dotenv

load_dotenv()

GEMINI_API_KEY = os.environ.get('GEMINI_API_KEY')

client = genai.Client(api_key=GEMINI_API_KEY)

def get_descricao_bolao(time_1, time_2, data, fase):
    prompt = f'Escreva uma descrição técnica e direta para um bolão da partida: {time_1} x {time_2} (Fase: {fase} | Data: {data}). A descrição deve focar no estilo de jogo das equipes ou na pressão do confronto. Restrição: Exatamente de 100 a 200 caracteres. Vá direto para a análise, sem frases de introdução.'

    response = client.models.generate_content(
        model='gemini-2.5-flash',
        contents=prompt
    )

    return response.text