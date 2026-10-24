import os
import time

from dotenv import load_dotenv
try:
    from mistralai import Mistral          # versions 1.x
except ImportError:
    from mistralai.client import Mistral   # versions 2.x et suivantes

load_dotenv()
_api_key = os.getenv("MISTRAL_API_KEY")
if not _api_key:
    raise RuntimeError("MISTRAL_API_KEY n'est pas défini dans .env")

client = Mistral(api_key=_api_key)


def chat(model: str, messages: list, temperature: float = 0.1,
         json_mode: bool = False, retries: int = 5) -> str:
    """Appelle l'API Mistral et renvoie le texte de la réponse."""
    kwargs = {"model": model, "messages": messages, "temperature": temperature}
    if json_mode:
        kwargs["response_format"] = {"type": "json_object"}

    for attempt in range(retries):
        try:
            response = client.chat.complete(**kwargs)
            return response.choices[0].message.content
        except Exception as e:
            if "429" in str(e) and attempt < retries - 1:
                time.sleep(2 ** attempt)
                continue
            raise