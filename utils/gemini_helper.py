from google import genai
import time

API_KEY = "YOUR_KEY"
MODEL_NAME = "models/gemini-2.5-flash"

client = genai.Client(api_key=API_KEY)

def safe_generate(prompt):
    for _ in range(3):
        try:
            return client.models.generate_content(
                model=MODEL_NAME,
                contents=prompt
            ).text
        except Exception as e:
            if "429" in str(e):
                time.sleep(20)
            else:
                raise e
    return "AI busy"