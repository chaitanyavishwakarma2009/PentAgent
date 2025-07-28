from .llm_interface import call_generative_model
from ..types import VaptState

async def fix_command(state: VaptState) -> str:
    """
    Analyzes a failed command by calling the universal generative model interface.
    """

    failed_command = state['current_command']
    error_message = state['command_error']

    print("\n[🧠] Analyzing command error...")

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

    response = await call_generative_model(prompt, state)

    if not response:
        print(f"\n[✖] AI interface returned an empty response during error handling. Aborting.")
        return "ABORT"

    cleaned_response = response.replace("`", "").strip()
    print(f"\n[💡] Error Handler's Decision: {cleaned_response}")
    return cleaned_response
