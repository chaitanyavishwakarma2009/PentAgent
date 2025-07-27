# The decider is also much cleaner.

# --- It only needs to import our new, universal interface ---
from .llm_interface import call_generative_model

# --- THIS IS THE CORRECTED FUNCTION NAME ---
async def decide_next_action(findings_summary: str, target: str, scan_type: str, tried_commands: list) -> str:
    """
    Decides the next action by calling the universal generative model interface.
    """
    print(f"\n[🧠] Deciding next step for '{scan_type}' on '{target}'...")
    
    prompt = f"""
    You are an expert VAPT agent deciding the next step.
    The overall mission is: **{scan_type}**
    The target is: {target}
    Findings so far: "{findings_summary}"

    CRITICAL: The following commands have already been tried or suggested in this session. You MUST NOT suggest them again:
    {tried_commands}

    Based on the mission, the findings, and avoiding the commands listed above, what is the single best next command to run?
    If you have no other ideas or the mission is complete, return the single word "END".
    Otherwise, return only the single, complete next command to run.
    """

    # --- The AI call is now simple and clean ---
    next_command = await call_generative_model(prompt)

    # The agent is still responsible for its own logic.
    if not next_command:
        print("[⚠] AI interface returned an empty command. Ending scan.")
        return "END"
        
    print(f"\n[💡] Decider's Decision: {next_command}")
    return next_command