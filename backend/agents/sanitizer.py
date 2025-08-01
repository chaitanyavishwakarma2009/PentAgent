# backend/agents/sanitizer.py
import re

def sanitize_command(command: str) -> str:
    """
    Cleans a command generated by the AI to ensure it's syntactically valid.
    Fixes common issues like markdown artifacts or wrong protocol usage.
    """
    cleaned_command = command.strip().replace("`", "").replace("bash", "").strip()

    protocol_agnostic_tools = ['nmap', 'dig', 'whatweb', 'nikto']

    for tool in protocol_agnostic_tools:
        if re.search(fr'^\s*(sudo\s+)?{tool}', cleaned_command):
            print(f"[Sanitizer] Detected '{tool}'. Removing protocols from: '{cleaned_command}'")
            cleaned_command = re.sub(r'https?://', '', cleaned_command)
            break

    return cleaned_command
