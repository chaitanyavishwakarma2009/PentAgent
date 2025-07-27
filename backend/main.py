# backend/main.py
from langgraph.graph import StateGraph, END
from typing import TypedDict, List, Annotated
import asyncio
import logging

# Import your agents and shell command runner
from .shell_command import run_command
from .agents.analyser import analyze_and_summarize
from .agents.decider import decide_next_action
from .agents.error_handler import fix_command
from .agents.planner import create_initial_plan
from .agents.sanitizer import sanitize_command 

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# --- State Definition ---
class VaptState(TypedDict):
    user_query: str
    target: str
    current_command: Annotated[str, lambda x, y: y]
    command_output: str
    command_error: str
    executed_command: str
    detailed_analysis: dict
    findings_summary: str
    history: Annotated[List[str], lambda x, y: x + y]
    tried_commands: Annotated[List[str], lambda x, y: x + y]
    report: str
    scan_type: str

# --- Node Functions ---
async def planner_node(state: VaptState):
    print("\n--- DEBUG: Inside PLANNER_NODE (Start of a new scan) ---") # <-- ADD THIS
    logging.info("--- STRATEGY: PLANNING INITIAL ATTACK ---")
    target = state["user_query"]
    scan_type = state["scan_type"]
    command = await create_initial_plan(target, scan_type, [])
    return {"current_command": command, "target": target, "tried _commands":[command]}

# The NEW, smarter version
async def execute_node(state: VaptState, config: dict):
    logging.info("--- ACTION: EXECUTING COMMAND ---")
    
    # 1. Get the raw command proposed by the AI
    proposed_command = state["current_command"]
    
    # 2. Clean and correct the command using your sanitizer
    sanitized_command = sanitize_command(proposed_command)
    
    # 3. Log if the sanitizer made a change (optional but good for debugging)
    if proposed_command != sanitized_command:
        logging.info(f"Sanitizer corrected command from '{proposed_command}' to '{sanitized_command}'")
    
    # 4. Use the SAFE, sanitized command for the rest of the execution
    command_to_run = sanitized_command

    command_with_target = command_to_run.replace("{target}", state["target"])
    
    stop_event = config['configurable'].get('stop_event')
    result = await run_command(command_with_target, stop_event)
    
    output = result.get("output", "")
    error = result.get("error")

    if error is None:
        if "Note: Host seems down." in output or "Transfer failed." in output:
            logging.warning("Logical error detected. Triggering error handler.")
            error = output
            
    return {
        # Return the final command that was actually run
        "executed_command": command_with_target,
        "command_output": output,
        "command_error": error,
        "history": [f"Attempted: {command_with_target}"]
    }


async def analyze_node(state: VaptState):
    logging.info("--- SENSE: ANALYZING AND SUMMARIZING ---")
    
    command_output = state.get("command_output", "").strip()

    # --- THIS IS THE FIX: THE GUARD CLAUSE ---
    # If the command output is empty, don't waste an AI call.
    if not command_output:
        logging.warning("Command produced no output. Skipping analysis.")
        # We return the state as-is, with a note in the history.
        return {
            "history": ["Command executed successfully but produced no output. No new findings."]
        }
    # --- END FIX ---

    # If we get here, it means we have real output to analyze.
    analysis_results = await analyze_and_summarize(command_output, state["findings_summary"])
    
    detailed_analysis = analysis_results.get("detailed_analysis", {})
    findings_summary = analysis_results.get("findings_summary", state["findings_summary"])
    
    return {
        "detailed_analysis": detailed_analysis,
        "findings_summary": findings_summary,
        "history": [f"Analysis successful. Detailed analysis added to state."]
    }

async def error_handler_node(state: VaptState):
    logging.info("--- RECOVER: HANDLING EXECUTION ERROR ---")
    
    decision = await fix_command(state["current_command"], state["command_error"])
    
    # If the AI wants to abort, we set the command to END to stop the graph.
    if decision.upper() == "ABORT":
        return {"current_command": "END"}
    
    # If the AI says to continue, we set a special keyword.
    # The router will see this and send us to the Decider for a fresh idea.
    if decision.upper() == "CONTINUE":
        return {"current_command": "CONTINUE"}

    # Otherwise, the decision is a corrected command to try next.
    return {
        "current_command": decision,
        "history": [f"Error on command '{state['current_command']}'. Retrying with '{decision}'."]
    }
async def decide_node(state: VaptState):
    print("\n--- DEBUG: Inside DECIDE_NODE ---")
    print(f"--- DEBUG: Findings summary passed to decider: '{state.get('findings_summary')}'")
    logging.info("--- DECIDE: CHOOSING NEXT TOOL ---")
    
    # 1. Get the scan_type from the current state.
    scan_type = state["scan_type"]
    tried_command = state["tried_commands"]
    
    # 2. Pass it as the third argument to your agent.
    next_command = await decide_next_action(state["findings_summary"], state["target"], scan_type, tried_command)
    
    return {"current_command": next_command, "tried_command":[next_command]}
def report_node(state: VaptState):
    logging.info("--- REPORT: COMPILING FINAL FINDINGS ---")
    full_history = "\n".join(state["history"])
    report_content = (
        f"VAPT Assessment Final Report for Target: {state['target']}\n\n"
        f"=== Final Findings Summary ===\n{state['findings_summary']}\n\n"
        f"=== Full Execution History ===\n{full_history}"
    )
    return {"report": report_content}

async def human_approval_gate(state: VaptState, config: dict):
    logging.info("--- AWAITING HUMAN APPROVAL ---")
    approval_event = config['configurable'].get('approval_event')
    user_choice = config['configurable'].get('user_choice')
    if not approval_event or not user_choice:
        logging.error("Approval event/choice not found in config.")
        # We can still end the graph here if the config is broken
        return {"current_command": "END"} 
        
    approval_event.clear()
    await approval_event.wait() # Wait for the user to click Approve or Disapprove
    
    # --- THIS IS THE FIX ---
    # We no longer change the state here. We just log the action.
    # The new router will handle the logic.
    if user_choice.value == "approve":
        logging.info("Approved.")
    else:
        logging.info("Denied. Asking AI for a different command.")
        
    return {}

# --- Graph Compilation ---

# In backend/main.py
# This is the corrected compile_graph function for backend/main.py

def compile_graph():
    # This router is for nodes that PROPOSE commands (no changes here)
    def route_after_command_proposal(state: VaptState, config: dict):
        command = state.get("current_command", "")
        if command.upper() == "CONTINUE":
            return "decide"
        if command.upper() == "END":
            return "report"
        scan_mode = config['configurable'].get('scan_mode', 'auto')
        if scan_mode == 'manual':
            return "human_approval_gate"
        return "execute"

    # --- THIS IS THE FIX (Part 1): Update the approval router ---
    # It no longer goes directly to 'decide'. It goes to our new 'replan' node.
    def route_after_approval(state: VaptState, config: dict):
        user_choice = config['configurable'].get('user_choice').value
        if user_choice == 'approve':
            return "execute"
        else: # This path is for 'disapprove'
            return "replan" # Go to the replan node to record the denied command

    # This router is unchanged
    def check_for_errors(state: VaptState):
        if state.get("command_error"):
            return "error_handler"
        return "analyze"

    builder = StateGraph(VaptState)

    # Add all your existing nodes...
    builder.add_node("planner", planner_node)
    builder.add_node("execute", execute_node, config_key="configurable")
    builder.add_node("analyze", analyze_node)
    builder.add_node("decide", decide_node)
    builder.add_node("error_handler", error_handler_node)
    builder.add_node("report", report_node)
    builder.add_node("human_approval_gate", human_approval_gate)

    # --- THIS IS THE FIX (Part 2): Add the new node ---
    # This node's only job is to add the denied command to the 'tried' list.
    def replan_node(state: VaptState):
        command_denied = state["current_command"]
        logging.info(f"Adding denied command to memory: {command_denied}")
        return {"tried_commands": [command_denied]}
    builder.add_node("replan", replan_node)
    # --- END FIX ---

    builder.set_entry_point("planner")

    # Edges from command proposers are unchanged
    builder.add_conditional_edges("planner", route_after_command_proposal, {
        "human_approval_gate": "human_approval_gate", "execute": "execute", "report": "report"
    })
    builder.add_conditional_edges("decide", route_after_command_proposal, {
        "human_approval_gate": "human_approval_gate", "execute": "execute", "report": "report"
    })
    builder.add_conditional_edges("error_handler", route_after_command_proposal, {
       "decide":"decide" , "human_approval_gate": "human_approval_gate", "execute": "execute", "report": "report"
    })

    # --- THIS IS THE FIX (Part 3): Update the edges from the approval gate ---
    builder.add_conditional_edges("human_approval_gate", route_after_approval, {
        "execute": "execute", 
        "replan": "replan"    # On 'disapprove', go to the new replan node
    })
    
    # --- THIS IS THE FIX (Part 4): Add the edge from the new node ---
    # After the replan_node runs, always go to the decider.
    builder.add_edge("replan", "decide")
    
    # The rest of the graph is unchanged
    builder.add_conditional_edges("execute", check_for_errors, {
        "error_handler": "error_handler", "analyze": "analyze"
    })
    builder.add_edge("analyze", "decide")
    builder.add_edge("report", END)

    return builder.compile()   
   # --- Stream Runner ---
async def run_vapt_agent_stream(target_query: str, config: dict):
    graph = compile_graph()
    
    scan_type = config['configurable'].get('scan_type', 'Full Scan')
    
    initial_state = {
        "user_query": target_query,
        "target": "", # Will be set by planner
        "current_command": "",
        "command_output": "",
        "command_error": "",
        "executed_command": "",
        "scan_type":scan_type,
            "tried_commands": [],
        "detailed_analysis": {},
        "findings_summary": "No findings yet.",
        "history": [],
        "report": ""
    }
    
    stop_event = config['configurable'].get('stop_event')
    
    async for update in graph.astream(initial_state, config=config):
        if stop_event and stop_event.is_set():
            logging.warning("--- SCAN STOPPED BY USER ---")
            yield {"__end__": {"report": "Scan was manually stopped by the user."}}
            break
        yield update