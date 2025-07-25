# backend/agents/error_handler.py
import os
import asyncio
import google.generativeai as genai
from dotenv import load_dotenv

load_dotenv()
genai.configure(api_key=os.getenv("GEMINI_API_KEY"))
model = genai.GenerativeModel('gemini-1.5-flash')

def _blocking_fix_command(prompt: str) -> str:
    """The actual blocking API call."""
    safety_settings = {
        'HARM_CATEGORY_HARASSMENT': 'BLOCK_NONE',
        'HARM_CATEGORY_HATE_SPEECH': 'BLOCK_NONE',
        'HARM_CATEGORY_SEXUALLY_EXPLICIT': 'BLOCK_NONE',
        'HARM_CATEGORY_DANGEROUS_CONTENT': 'BLOCK_NONE',
    }
    response = model.generate_content(prompt, safety_settings=safety_settings)
    return response.text.strip()

async def fix_command(failed_command: str, error_message: str) -> str:
    """
    Analyzes a failed command and suggests a fix, or decides to continue or abort.
    """
    print("\n[🧠] Analyzing command error with Gemini...")

    # --- THIS IS THE FIX: A NEW PROMPT WITH A 'CONTINUE' OPTION ---
    prompt = f"""
    You are a command-line expert fixing a failed command in a VAPT scan.
    Analyze the 'Failed Command' and its 'Error Message'.

    **YOUR TASK:**
    1.  If you can correct the command with a high degree of certainty (e.g., adding a missing `-Pn` flag to nmap based on the error), respond with the corrected, runnable command.
    2.  If the error indicates a common, expected failure that is a dead end but not critical (e.g., "Connection refused", "Transfer failed", "Host seems down"), respond with the single keyword "CONTINUE". This tells the agent to stop trying this path and move on to a different reconnaissance step.
    3.  If the error is fundamental and unrecoverable (e.g., a nonsensical command like "END", "tool not found"), respond with the single keyword "ABORT".

    **CRITICAL RULES:**
    - Your response MUST be either a real, executable command, "CONTINUE", or "ABORT".
    - DO NOT use the word "exit".

    **Analysis Data:**
    - Failed Command: `{failed_command}`
    - Error Message: `{error_message}`

    **Your Response (Corrected Command, "CONTINUE", or "ABORT"):**
    """
    try:
        response = await asyncio.to_thread(_blocking_fix_command, prompt)
        cleaned_response = response.replace("`", "").strip()
        
        print(f"\n[💡] Error Handler's Decision: {cleaned_response}")
        return cleaned_response

    except Exception as e:
        print(f"\n[✖] Error during error handling: {e}")
        return "ABORT" # If the AI itself fails, we should abort