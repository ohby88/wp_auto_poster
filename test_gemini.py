import os
import google.generativeai as genai
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

api_key = os.getenv("GEMINI_API_KEY")
if not api_key:
    print("Error: GEMINI_API_KEY not found in .env")
    exit(1)

print(f"Loaded API Key starting with: {api_key[:10]}...")

try:
    genai.configure(api_key=api_key)
    # Using the latest model
    model = genai.GenerativeModel('gemini-2.5-flash')
    response = model.generate_content("Hello, this is a test. Answer with 'API is working!'.")
    print("\nAPI Connection Successful!")
    print(f"Response: {response.text}")
except Exception as e:
    print(f"\nAPI Connection Failed!")
    print(f"Error: {e}")
