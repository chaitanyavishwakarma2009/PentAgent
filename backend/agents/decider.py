from .llm_interface import call_generative_model
from ..types import VaptState

async def decide_next_action(state: VaptState) -> str:
    """
    Uses AI to determine the next best command to run based on current findings,
    scan type, and commands already attempted.
    """

    findings_summary = state['findings_summary']
    target = state['target']
    scan_type = state['scan_type']
    tried_commands = state.get('tried_commands', [])

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

    NEVER give command's in which user (like control c) have to interact and command does not end by it self.
    Return ONLY the single, complete command to run. Do not add any explanation or markdown.
    """

    next_command = await call_generative_model(prompt, state)

    if not next_command:
        print("[⚠] AI interface returned an empty command. Ending scan.")
        return "END"
        
    print(f"\n[💡] Decider's Decision: {next_command}")
    return next_command
