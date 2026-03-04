import logging
import requests
from django.conf import settings
from openai import OpenAI

logger = logging.getLogger(__name__)


class GeocodingService:
    @staticmethod
    def get_coordinates(raw_address: str):
        if not raw_address:
            return None, None
        
        # 1. Limpar endereço com LLM
        try:
            client = OpenAI(api_key=settings.OPENAI_API_KEY, base_url=settings.OPENAI_API_BASE)
            response = client.chat.completions.create(
                model=settings.LLM_MODEL,
                messages=[
                    {
                        "role": "system",
                        "content": (
                            "Você formata endereços. Extraia o local do relato e retorne EXATAMENTE no formato: "
                            "'Logradouro, Bairro, Mogi das Cruzes, SP'. Não adicione CEP nem explicações. "
                            "Se a rua não for clara, retorne o bairro e a cidade."
                        ),
                    },
                    {"role": "user", "content": raw_address},
                ],
                temperature=0.1,
                max_tokens=50,
            )
            clean_address = response.choices[0].message.content.strip()
            logger.info(f"Geocoding: Endereço formatado pelo LLM: {clean_address}")
        except Exception as e:
            logger.error(f"Erro ao formatar endereço com LLM: {e}")
            clean_address = f"{raw_address}, Mogi das Cruzes, SP"

        # 2. Buscar coordenadas no Nominatim (OpenStreetMap)
        try:
            headers = {"User-Agent": "Mova-Ouvidoria-Mogi/1.0"}
            url = "https://nominatim.openstreetmap.org/search"
            params = {
                "q": clean_address,
                "format": "json",
                "limit": 1,
            }
            res = requests.get(url, headers=headers, params=params, timeout=10)
            res.raise_for_status()
            data = res.json()

            if data and len(data) > 0:
                logger.info(
                    f"Geocoding: Coordenadas encontradas: Lat {data[0]['lat']}, Lon {data[0]['lon']}"
                )
                return data[0]["lat"], data[0]["lon"]

            logger.warning(f"Geocoding: Coordenadas não encontradas para: {clean_address}")
            return None, None
        except Exception as e:
            logger.error(f"Erro ao buscar no Nominatim: {e}")
            return None, None

