from .llm_interface import call_generative_model
from ..types import VaptState

async def create_initial_plan(state: VaptState) -> str:
    user_query = state['user_query']
    scan_type = state['scan_type']
    tried_commands = state.get('tried_commands', [])
    
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

    NEVER give command's in which user (like control c) have to interact and command does not end by it self.

    Return ONLY the single, complete command to run. Do not add any explanation or markdown.
    """
    
    initial_command = await call_generative_model(prompt, state)

    if not initial_command:
        print(f"[⚠] AI interface returned an empty command for '{scan_type}'. Using fallback.")
        return f"nmap -T4 -A -v {user_query}"
        
    print(f"\n[💡] Planner's Decision: {initial_command}")
    return initial_command
