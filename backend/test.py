import google.generativeai as genai
import os
from dotenv import load_dotenv

load_dotenv()

api_key = os.getenv("GEMINI_API_KEY")
genai.configure(api_key=api_key)

if api_key:
    for m in genai.list_models():
        print(m.name)
else:
    print("Error: GEMINI_API_KEY not found in environment.")