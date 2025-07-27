#backend/agents/decider.py
import os
import asyncio
import google.generativeai as genai
from dotenv import load_dotenv

load_dotenv()
genai.configure(api_key=os.getenv("GEMINI_API_KEY"))
model = genai.GenerativeModel('gemini-1.5-flash')

def _blocking_decide_action(prompt: str) -> str:
    """The actual blocking API call."""
    safety_settings = {
        'HARM_CATEGORY_HARASSMENT': 'BLOCK_NONE',
        'HARM_CATEGORY_HATE_SPEECH': 'BLOCK_NONE',
        'HARM_CATEGORY_SEXUALLY_EXPLICIT': 'BLOCK_NONE',
        'HARM_CATEGORY_DANGEROUS_CONTENT': 'BLOCK_NONE',
    }
    response = model.generate_content(prompt, safety_settings=safety_settings)
    return response.text.strip()

async def decide_next_action(summary: str, target: str) -> str:
    """
    Acts as a reconnaissance specialist. This version ALWAYS returns a command.
    The scan only stops when the user clicks the 'Stop' button.
    """
    print("\n[🤔] Deciding next recon capability with Gemini...")

    # --- THIS IS THE FIX: THE AI IS NO LONGER ALLOWED TO END THE SCAN ---
    prompt = f"""
    You are a senior VAPT (Vulnerability Assessment and Penetration Testing) specialist. Your role is to continue an ongoing reconnaissance scan.
    Your target is: `{target}`

    **Your Goal:**
    Based on the findings so far, determine the single best command to run for the **very next step**. The scan must continue.

    **Reasoning Process:**
    1.  **Analyze Gaps:** Review the 'CUMULATIVE FINDINGS' to see what information is missing.
    2.  **Identify Next Step:** Determine the most logical capability needed next. Even if a lot of information has been gathered, there is always another step (e.g., check for different vulnerabilities, try a different wordlist, check DNS records, etc.).
    3.  **Construct Command:** Formulate the best single-line Kali Linux command for that next step.

    **CUMULATIVE FINDINGS SO FAR:**
    ---
    {summary}
    ---

    **OUTPUT INSTRUCTIONS:**
    Your response MUST be ONLY the single, runnable command to execute next.
    - DO NOT use the word "END". The scan will only be stopped by the user.
    - DO NOT include any explanation, reasoning, or markdown formatting.

    **Your Next Command:**
    """

    try:
        next_command = await asyncio.to_thread(_blocking_decide_action, prompt)
        
        # Cleanup and a fallback just in case the AI returns an empty response
        cleaned_command = next_command.replace("```bash", "").replace("```", "").strip()
        
        if not cleaned_command or cleaned_command.upper() == "END":
            print("[⚠] Decider returned an invalid empty/END command. Falling back to a safe nmap scan.")
            return f"nmap -T4 -sV {target}"

        print(f"\n[💡] Decider's next command: {cleaned_command}")
        return cleaned_command
    except Exception as e:
        print(f"\n[✖] Error during decision: {e}. Falling back to a safe nmap scan.")
        return f"nmap -T4 -sV {target}" # Fallback on error