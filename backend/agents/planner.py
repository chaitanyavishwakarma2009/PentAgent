#backend/agents/planner.py
import os
import asyncio
import google.generativeai as genai
from dotenv import load_dotenv

load_dotenv()
genai.configure(api_key=os.getenv("GEMINI_API_KEY"))
model = genai.GenerativeModel('gemini-2.0-flash')

def _blocking_create_plan(prompt: str) -> str:
    """The actual blocking API call."""
    response = model.generate_content(prompt)
    return response.text.strip()

async def create_initial_plan(user_query: str) -> str:
    """
    Takes a high-level user query and decides the best initial command asynchronously.
    """
    print("\n[🧠] Creating initial plan with Gemini...")
    prompt = f"""
    You are a VAPT (Vulnerability Assessment and Penetration Testing) Chief Strategist.
    Your role is to take a user's objective and determine the best single, initial Kali Linux command to start a reconnaissance scan.
    User Objective: "{user_query}"
    Based on this, what is the most appropriate and effective first command to run?
    Respond with ONLY the command.
    """
    try:
        # Run the blocking call in a separate thread to not freeze the UI
        initial_command = await asyncio.to_thread(_blocking_create_plan, prompt)
        if not initial_command or not initial_command.strip():
            print("[⚠] Gemini returned empty command. Using fallback.")
            return f"nmap -T4 -A -v {user_query}"
        print(f"\n[💡] Planner's Decision: {initial_command}")
        return initial_command.strip()
    except Exception as e:
        print(f"\n[✖] Error during planning: {e}")
        return f"nmap -T4 -A -v {user_query}"
