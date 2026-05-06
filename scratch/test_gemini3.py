import os
from google import genai
from dotenv import load_dotenv

load_dotenv()
api_key = os.environ.get("GEMINI_API_KEY")

client = genai.Client(api_key=api_key)

try:
    response = client.models.generate_content(
        model='gemini-3-flash-preview',
        contents="Hello, are you online?"
    )
    print(f"Response: {response.text}")
except Exception as e:
    print(f"Error: {e}")
