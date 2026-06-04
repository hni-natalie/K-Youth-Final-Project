import logging
import os
import sys
import requests
from google import genai
from dotenv import load_dotenv

logger = logging.getLogger(__name__)

def prompt_gemini(model: str, prompt: str) -> str:
    """
        Handle Gemini model requests
    """
    
    try:
        load_dotenv()

        api_key = os.getenv("GOOGLE_API_KEY") or os.getenv("GEMINI_API_KEY")
        if not api_key:
            raise ValueError("No Gemini API key found (GOOGLE_API_KEY / GEMINI_API_KEY)")

        client = genai.Client(api_key=api_key)

        response = client.models.generate_content(
            model=model,
            contents=prompt
        )

        return response.text

    except Exception as e:
        logger.error("Gemini model %s failed: %s", model, e, exc_info=True)
        return f"[Gemini Error] {str(e)}"
    

def prompt_ollama(model: str, prompt: str) -> str:
    """
        Handle Ollama model requests
    """

    try:
        res = requests.post(
            "http://localhost:11434/api/generate",
            json={
                "model": model,
                "prompt": prompt,
                "stream": False
            }
        )

        data = res.json()

        if "error" in data:
            return f"[Ollama Error] {data['error']}"

        return data.get("response", "[No response field returned]")

    except Exception as e:
        logger.error("Ollama model %s failed: %s", model, e, exc_info=True)
        return f"[Ollama Error] {str(e)}"


def prompt_model(model: str, prompt: str) -> str:
    """
        Route request to the correct model provider
    """
        
    if model.startswith("gemini-"):
        return prompt_gemini(model, prompt)
    
    return prompt_ollama(model, prompt)


def test_prompt():
    if len(sys.argv) != 3:
        return f'Usage: uv run prompt_model.py <model> <prompt>'
    
    else:        
        model = sys.argv[1]
        prompt = sys.argv[2]
        output = prompt_model(model, prompt)
        return output

if __name__ == "__main__":
    print(test_prompt())