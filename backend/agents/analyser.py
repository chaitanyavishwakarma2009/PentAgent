# backend/agents/analyser.py
import os
import json
import asyncio
import google.generativeai as genai
from google.generativeai.types import HarmCategory, HarmBlockThreshold
from dotenv import load_dotenv

load_dotenv()
genai.configure(api_key=os.getenv("GEMINI_API_KEY"))
model = genai.GenerativeModel('gemini-1.5-flash')
safety_settings = {
    HarmCategory.HARM_CATEGORY_HARASSMENT: HarmBlockThreshold.BLOCK_NONE,
    HarmCategory.HARM_CATEGORY_HATE_SPEECH: HarmBlockThreshold.BLOCK_NONE,
    HarmCategory.HARM_CATEGORY_SEXUALLY_EXPLICIT: HarmBlockThreshold.BLOCK_NONE,
    HarmCategory.HARM_CATEGORY_DANGEROUS_CONTENT: HarmBlockThreshold.BLOCK_NONE,
}

def _blocking_generate(prompt: str) -> str:
    """Helper function for the actual blocking API call."""
    response = model.generate_content(prompt, safety_settings=safety_settings)
    return response.text.strip()

async def analyze_and_summarize(command_output: str, existing_summary: str) -> dict:
    """
    Analyzes command output, extracting key facts and noting failed attempts.
    """
    print("\n[🧠] Extracting key facts and updating summary with Gemini...")

    # --- THIS IS THE FIX: A PROMPT THAT RECOGNIZES FAILED ATTEMPTS ---
    interpretive_analysis_prompt = f"""
        You are a fact-extraction engine for a VAPT agent.
        Your task is to analyze the 'Tool Output' and extract ONLY the most critical findings.
        
        **OUTPUT INSTRUCTIONS:**
        - Your response MUST be a human-readable, bulleted list.
        - Each bullet MUST include:
            • Severity level with emoji (🔴 Critical, 🟠 Medium, 🟢 Low, 🔵 Info)
            • Key fact(s) (e.g., IP, open port, software version, etc.)
            • A brief reason why it’s relevant or how it could be exploited.
        - If the output indicates a logical failure (e.g., "Transfer failed", "Host seems down", "Connection refused"), you MUST report it with (⚠️ Failed).
        - DO NOT suggest "next steps".
        - DO NOT explain the tool or its options.
        - If there are no positive findings AND no logical failures, respond with: **No significant findings.**
        
        **Example of a failed attempt output:**
        - ⚠️ Failed: The attempt to perform a DNS zone transfer (AXFR) failed.
        
        **Tool Output:**
        ---
        {command_output}
        ---
        
        **Extracted Findings:**
        """

    try:
        interpretive_analysis = await asyncio.to_thread(_blocking_generate, interpretive_analysis_prompt)
        print(f"\n[📊] Extracted Facts:\n{interpretive_analysis}")
    except Exception as e:
        print(f"\n[✖] Error during fact extraction: {e}")
        interpretive_analysis = f"Error: Failed to analyze tool output. Reason: {str(e)}"

    # The summary prompt does not need to change. It will correctly consolidate the new facts.
    summary_prompt = f"""
    You are a VAPT agent's memory manager. Update the 'Previous Cumulative Summary' with the key information from the 'Newly Extracted Facts'.
    - Your response MUST be a single, consolidated, bulleted list.
    - Do not repeat information.
    - Be as concise as possible.

    **Previous Cumulative Summary:**
    ---
    {existing_summary}
    ---

    **Newly Extracted Facts to Incorporate:**
    ---
    {interpretive_analysis}
    ---

    **New Cumulative Summary:**
    """
    try:
        updated_summary = await asyncio.to_thread(_blocking_generate, summary_prompt)
        print(f"\n[📝] Updated Cumulative Summary:\n{updated_summary}")
    except Exception as e:
        print(f"\n[✖] Error updating summary: {e}")
        updated_summary = existing_summary 

    return {"detailed_analysis": interpretive_analysis, "findings_summary": updated_summary}