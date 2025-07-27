# --- It only needs to import our new, universal interface ---
from .llm_interface import call_generative_model

async def create_initial_plan(user_query: str, scan_type: str, tried_commands: list) -> str:
    """
    Creates an initial plan by calling the universal generative model interface.
    """
    print(f"\n[🧠] Creating initial plan for a '{scan_type}' on '{user_query}'...")
    
    prompt = f"""
    You are a VAPT Strategist. Your mission is to choose the single best *initial* command to run against the target '{user_query}'.

    The specific mission goal for this scan is: **{scan_type}**
    The following commands have already been tried or suggested, do not repeat them: {tried_commands}

    Based on the mission, and avoiding the tried commands, select the most appropriate command. For example:
    - If the mission is "Vulnerability Assessment", a good start is a deep script scan like: `nmap -sV --script vuln {user_query}`
    - If the mission is "Reconnaissance Only", a good start is information gathering: `dig ANY {user_query}`
    - If the mission is "Web Application Scan", a good start is a web scanner: `nikto -h {user_query}`
    - For a "Full Scan", a balanced initial scan is best: `nmap -T4 -A -v {user_query}`

    Return ONLY the single, complete command to run. Do not add any explanation or markdown.
    """
    
    # --- The AI call is now simple and clean ---
    initial_command = await call_generative_model(prompt)
    
    # The agent is still responsible for its own logic, like fallbacks.
    if not initial_command:
        print(f"[⚠] AI interface returned an empty command for '{scan_type}'. Using fallback.")
        return f"nmap -T4 -A -v {user_query}"
        
    print(f"\n[💡] Planner's Decision: {initial_command}")
    return initial_command