import google.generativeai as genai
import os
from dotenv import load_dotenv

load_dotenv()

def find_working_model():
    api_key = os.getenv("GEMINI_API_KEY")
    genai.configure(api_key=api_key)
    
    # List of models to try in order of preference
    models_to_try = [
        "gemini-2.0-flash-lite",
        "gemini-2.0-flash",
        "gemini-1.5-flash",
        "gemini-1.5-flash-8b",
        "gemini-1.5-pro",
        "gemini-flash-latest"
    ]
    
    print(f"API Key: {api_key[:10]}...")
    
    for model_name in models_to_try:
        print(f"Testing {model_name}...", end=" ", flush=True)
        try:
            model = genai.GenerativeModel(model_name=model_name)
            response = model.generate_content("Say 'OK'")
            print(f"✅ WORKS: {response.text.strip()}")
            return model_name
        except Exception as e:
            err = str(e)
            if "not found" in err.lower():
                print("❌ Not Found")
            elif "quota" in err.lower() or "429" in err:
                print("❌ Quota Exceeded")
            else:
                print(f"❌ Error: {err[:50]}...")
                
    return None

if __name__ == "__main__":
    working = find_working_model()
    if working:
        print(f"\nRecommended model for .env: {working}")
    else:
        print("\n❌ No models currently have available quota. Please check your AI Studio console or try a new API key.")
