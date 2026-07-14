import os
import logging
from google import genai
from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger(__name__)

def get_descricao_bolao(time_1, time_2, data, fase):
    api_key = os.environ.get('GEMINI_API_KEY')
    
    if not api_key:
        logger.warning("GEMINI_API_KEY não encontrada. Retornando descrição padrão para o bolão.")
        return f"Bolão para o grande confronto entre {time_1} e {time_2} pela fase {fase}. Quem sairá vencedor deste duelo histórico?"

    try:
        client = genai.Client(api_key=api_key)
        prompt = f'Escreva uma descrição técnica e direta para um bolão da partida: {time_1} x {time_2} (Fase: {fase} | Data: {data}). A descrição deve focar no estilo de jogo das equipes ou na pressão do confronto. Restrição: Exatamente de 100 a 200 caracteres. Vá direto para a análise, sem frases de introdução.'

        response = client.models.generate_content(
            model='gemini-2.5-flash',
            contents=prompt
        )
        return response.text
    except Exception as e:
        logger.error(f"Erro ao gerar descrição com Gemini: {e}")
        return f"Bolão do jogo {time_1} x {time_2} pela fase {fase}. Faça seus palpites e mostre seus conhecimentos sobre futebol!"