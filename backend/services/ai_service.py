import os
import google.generativeai as genai
from dotenv import load_dotenv

# Load environment variables for standalone testing
load_dotenv()

api_key = os.getenv("GEMINI_API_KEY")
if not api_key:
    # In production/FastAPI, this might be loaded in main.py, 
    # but for standalone test we need it here if not already in env.
    pass

genai.configure(api_key=api_key)

def call_gemini(prompt: str) -> str:
    """Sends a prompt to Gemini and returns the text response."""
    model = genai.GenerativeModel("gemini-2.5-flash")
    response = model.generate_content(prompt)
    return response.text

if __name__ == "__main__":
    if not api_key:
        print("Error: GEMINI_API_KEY not found in environment variables.")
    else:
        try:
            result = call_gemini("Respond with only the words: Gemini is working")
            print(result.strip())
        except Exception as e:
            print(f"Error calling Gemini: {e}")
