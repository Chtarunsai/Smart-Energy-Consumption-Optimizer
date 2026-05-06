import google.generativeai as genai

genai.configure(api_key="AIzaSyBbPJZ5HiPF95JntPrxo8XcDMFR9R6487U")

for m in genai.list_models():
    print(m.name)