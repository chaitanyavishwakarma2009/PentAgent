# The analyser is now much cleaner and only focuses on prompt engineering.

# --- It only needs to import our universal interface ---
from .llm_interface import call_generative_model

async def analyze_and_summarize(command_output: str, existing_summary: str) -> dict:
    """
    Analyzes command output by calling the universal generative model interface twice.
    """
    print("\n[🧠] Extracting key facts and updating summary...")

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

        **Tool Output:**
        ---
        {command_output}
        ---

        **Extracted Findings:**
        """

    # --- The AI call is now simple and clean ---
    interpretive_analysis = await call_generative_model(interpretive_analysis_prompt)
    if not interpretive_analysis:
        interpretive_analysis = "Error: Failed to analyze tool output."
    
    print(f"\n[📊] Extracted Facts:\n{interpretive_analysis}")


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
    
    # --- The second AI call is also simple and clean ---
    updated_summary = await call_generative_model(summary_prompt)
    if not updated_summary:
        updated_summary = existing_summary # On error, don't lose the old summary

    print(f"\n[📝] Updated Cumulative Summary:\n{updated_summary}")

    return {"detailed_analysis": interpretive_analysis, "findings_summary": updated_summary}