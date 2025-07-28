# PentAgent/backend/types.py
from typing import TypedDict, List, Annotated

class VaptState(TypedDict):
    user_query: str
    target: str
    scan_type: str
    selected_ai_model: str
    ai_api_key: str
    current_command: Annotated[str, lambda x, y: y] 
    command_output: str
    command_error: str
    executed_command: str
    detailed_analysis: dict
    findings_summary: str
    history: Annotated[List[str], lambda x, y: x + y] 
    tried_commands: Annotated[List[str], lambda x, y: x + y] 
    report: str