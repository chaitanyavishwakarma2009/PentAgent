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
    report: str

# --- Node Functions ---
async def planner_node(state: VaptState):
    print("\n--- DEBUG: Inside PLANNER_NODE (Start of a new scan) ---") # <-- ADD THIS
    logging.info("--- STRATEGY: PLANNING INITIAL ATTACK ---")
    target = state["user_query"]
    command = await create_initial_plan(target)
    return {"current_command": command, "target": target}

# The NEW, smarter version
async def execute_node(state: VaptState, config: dict):
    logging.info("--- ACTION: EXECUTING COMMAND ---")
    command_to_run = state["current_command"]
    command_with_target = command_to_run.replace("{target}", state["target"])
    
    stop_event = config['configurable'].get('stop_event')
    result = await run_command(command_with_target, stop_event)
    
    output = result.get("output", "")
    error = result.get("error")

    # --- THIS IS THE FIX: A GUARD CLAUSE FOR LOGICAL ERRORS ---
    # Check for specific "failure-in-success" strings in the output,
    # even if the command returned a success exit code (error is None).
    if error is None:
        if "Note: Host seems down." in output:
            logging.warning("Logical error detected: Host seems down. Triggering error handler.")
            # We treat the entire output as the error so the AI can see the suggestion.
            error = output
        elif "Transfer failed." in output:
            logging.warning("Logical error detected: DNS transfer failed. Triggering error handler.")
            error = output
            
    return {
        "executed_command": command_to_run,
        "command_output": output,
        "command_error": error, # This is now populated even on logical failures
        "history": [f"Attempted: {command_with_target}"]
    }

# The NEW, more robust version
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
    print("\n--- DEBUG: Inside DECIDE_NODE ---") # <-- ADD THIS
    # This print will show us the exact summary the AI is seeing
    print(f"--- DEBUG: Findings summary passed to decider: '{state.get('findings_summary')}'") # <-- ADD THIS
    logging.info("--- DECIDE: CHOOSING NEXT TOOL ---")
    next_command = await decide_next_action(state["findings_summary"], state["target"])
    return {"current_command": next_command}

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

def compile_graph():
    # This router is for nodes that PROPOSE commands
   # The NEW, correct version
    def route_after_command_proposal(state: VaptState, config: dict):
        # This line was missing. It defines the 'command' variable.
        command = state.get("current_command", "")
        
        if command.upper() == "CONTINUE":
            return "decide"
    
        if command.upper() == "END":
            return "report"
        
        scan_mode = config['configurable'].get('scan_mode', 'auto')
        if scan_mode == 'manual':
            return "human_approval_gate"
        return "execute"

    # --- THIS IS THE FIX ---
    # A new router specifically for after the user clicks a button.
    # It checks the user's choice from the config.
    def route_after_approval(state: VaptState, config: dict):
        user_choice = config['configurable'].get('user_choice').value
        if user_choice == 'approve':
            return "execute"
        else: # This path is for 'disapprove'
            return "decide" # Go back to the Decider to get a new command

    def check_for_errors(state: VaptState):
        if state.get("command_error"):
            return "error_handler"
        return "analyze"

    builder = StateGraph(VaptState)

    # Add all your nodes...
    builder.add_node("planner", planner_node)
    # The NEW way, binding the config
    builder.add_node("execute", execute_node, config_key="configurable")
    builder.add_node("analyze", analyze_node)
    builder.add_node("decide", decide_node)
    builder.add_node("error_handler", error_handler_node)
    builder.add_node("report", report_node)
    builder.add_node("human_approval_gate", human_approval_gate)

    builder.set_entry_point("planner")

    # Edges that propose a command use the main router
    builder.add_conditional_edges("planner", route_after_command_proposal, {
        "human_approval_gate": "human_approval_gate", "execute": "execute", "report": "report"
    })
    builder.add_conditional_edges("decide", route_after_command_proposal, {
        "human_approval_gate": "human_approval_gate", "execute": "execute", "report": "report"
    })
    builder.add_conditional_edges("error_handler", route_after_command_proposal, {
        "human_approval_gate": "human_approval_gate", "execute": "execute", "report": "report"
    })

    # The edge from the approval gate uses the NEW router
    builder.add_conditional_edges("human_approval_gate", route_after_approval, {
        "execute": "execute", # On 'approve', go to execute
        "decide": "decide"    # On 'disapprove', go back to decide
    })
    
    # The rest of the graph
    builder.add_conditional_edges("execute", check_for_errors, {
        "error_handler": "error_handler", "analyze": "analyze"
    })
    
    builder.add_edge("analyze", "decide")
    builder.add_edge("report", END)

    return builder.compile()    
   # --- Stream Runner ---
async def run_vapt_agent_stream(target_query: str, config: dict):
    # This function is the entrypoint for every scan.
    # The fix is to ensure the initial_state is always created fresh here.
    
    graph = compile_graph()
    
    # --- THIS IS THE FIX ---
    # We explicitly define a pristine initial state for every single run.
    # This prevents any "state leakage" from a previous, disapproved run.
    initial_state = {
        "user_query": target_query,
        "target": "", # Will be set by planner
        "current_command": "",
        "command_output": "",
        "command_error": "",
        "executed_command": "",
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