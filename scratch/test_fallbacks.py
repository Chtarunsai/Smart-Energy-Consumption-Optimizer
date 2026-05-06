import os
from google import genai
from dotenv import load_dotenv

load_dotenv()
api_key = os.environ.get("GEMINI_API_KEY")

client = genai.Client(api_key=api_key)

models_to_test = ['gemini-1.5-flash', 'gemini-2.0-flash-lite']

for model in models_to_test:
    try:
        response = client.models.generate_content(
            model=model,
            contents="Test"
        )
        print(f"{model} is working: {response.text[:20]}...")
    except Exception as e:
        print(f"{model} failed: {e}")
