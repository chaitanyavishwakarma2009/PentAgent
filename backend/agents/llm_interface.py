import os
import asyncio
import google.generativeai as genai
from dotenv import load_dotenv

# --- All API-specific setup is now centralized here ---
load_dotenv()
genai.configure(api_key=os.getenv("GEMINI_API_KEY"))

# We can pre-configure different models
gemini_flash = genai.GenerativeModel('gemini-2.0-flash')
# In the future, you could add:
# openai_gpt4 = ...

def _blocking_gemini_call(prompt: str) -> str:
    """The actual, private blocking call to the Gemini API."""
    safety_settings = {
        'HARM_CATEGORY_HARASSMENT': 'BLOCK_NONE',
        'HARM_CATEGORY_HATE_SPEECH': 'BLOCK_NONE',
        'HARM_CATEGORY_SEXUALLY_EXPLICIT': 'BLOCK_NONE',
        'HARM_CATEGORY_DANGEROUS_CONTENT': 'BLOCK_NONE',
    }
    response = gemini_flash.generate_content(prompt, safety_settings=safety_settings)
    return response.text.strip()

# --- This is the ONLY function other agents will ever call ---
async def call_generative_model(prompt: str) -> str:
    """
    The universal AI interface. It takes a prompt and returns a response.
    It handles running the blocking API call in a separate thread.
    """
    try:
        # This function knows how to call the right model (for now, only Gemini)
        # and handles the async part.
        response_text = await asyncio.to_thread(_blocking_gemini_call, prompt)
        
        if not response_text:
            print("[⚠] AI model returned an empty response.")
            return "" # Return empty string to be handled by the agent
            
        return response_text
        
    except Exception as e:
        print(f"\n[✖] Critical error in AI model call: {e}")
        # On a major failure, return an empty string so the agent can use a fallback.
        return ""