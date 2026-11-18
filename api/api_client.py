import os
import requests
from dotenv import load_dotenv

load_dotenv()


class APIClient:
    """Cliente encargado de consumir la API pública de datos.gov.co (SODA)."""

    def __init__(self):
        recurso = os.getenv("API_RESOURCE_ID", "").strip()
        if not recurso:
            raise ValueError(
                "No se encontró API_RESOURCE_ID configurado en el archivo .env."
            )
        self.recurso = recurso
        self.url = f"https://www.datos.gov.co/resource/{recurso}.json"

    def obtener_registros(self, limite=100):
        """Realiza la petición HTTP GET a la API y devuelve la lista de registros JSON."""
        parametros = {"$limit": limite}
        headers = {
            "Accept": "application/json",
            "User-Agent": "ConsultaDatosAbiertos/1.0 (Python requests)",
        }
        respuesta = requests.get(
            self.url,
            params=parametros,
            headers=headers,
            timeout=30,
        )
        respuesta.raise_for_status()
        datos = respuesta.json()

        if not isinstance(datos, list):
            raise ValueError("La API no devolvió una lista de registros JSON.")

        return datos
