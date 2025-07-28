# backend/main.py

from langgraph.graph import StateGraph, END
from typing import TypedDict, List, Annotated
import asyncio
import logging
import os

from .shell_command import run_command
from .agents.analyser import analyze_and_summarize
from .agents.decider import decide_next_action
from .agents.error_handler import fix_command
from .agents.planner import create_initial_plan
from .agents.sanitizer import sanitize_command 
from .types import VaptState

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

async def planner_node(state: VaptState):
    logging.info("--- STRATEGY: PLANNING INITIAL ATTACK ---")
    target = state["user_query"]
    scan_type = state["scan_type"]
    command = await create_initial_plan(state)

    update_tried_command = state["tried_commands"] + [command]
    return {"current_command": command, "target": target, "tried_commands": update_tried_command}

async def execute_node(state: VaptState, config: dict):
    logging.info("--- ACTION: EXECUTING COMMAND ---")
    proposed_command = state["current_command"]
    sanitized_command = sanitize_command(proposed_command)

    if proposed_command != sanitized_command:
        logging.info(f"Sanitizer corrected command from '{proposed_command}' to '{sanitized_command}'")

    command_to_run = sanitized_command.replace("{target}", state["target"])
    stop_event = config['configurable'].get('stop_event')
    result = await run_command(command_to_run, stop_event)
    
    output = result.get("output", "")
    error = result.get("error")

    if error is None and ("Host seems down." in output or "Transfer failed." in output):
        logging.warning("Logical error detected. Triggering error handler.")
        error = output
            
    return {
        "executed_command": command_to_run,
        "command_output": output,
        "command_error": error,
        "history": [f"Attempted: {command_to_run}"]
    }

async def analyze_node(state: VaptState):
    logging.info("--- SENSE: ANALYZING AND SUMMARIZING ---")
    command_output = state.get("command_output", "").strip()

    if not command_output:
        logging.warning("Command produced no output. Skipping analysis.")
        return {
            "history": ["Command executed successfully but produced no output. No new findings."]
        }

    analysis_results = await analyze_and_summarize(state)
    
    return {
        "detailed_analysis": analysis_results.get("detailed_analysis", {}),
        "findings_summary": analysis_results.get("findings_summary", state["findings_summary"]),
        "history": ["Analysis successful. Detailed analysis added to state."]
    }

async def error_handler_node(state: VaptState):
    logging.info("--- RECOVER: HANDLING EXECUTION ERROR ---")
    decision = await fix_command(state)

    if decision.upper() == "ABORT":
        return {"current_command": "END"}
    
    if decision.upper() == "CONTINUE":
        return {"current_command": "CONTINUE"}

    return {
        "current_command": decision,
        "history": [f"Error on command '{state['current_command']}'. Retrying with '{decision}'."]
    }

async def decide_node(state: VaptState):
    logging.info("--- DECIDE: CHOOSING NEXT TOOL ---")
    next_command = await decide_next_action(state)

    update_tried_command = state["tried_commands"] + [next_command]
    return {"current_command": next_command, "tried_commands": update_tried_command}

def report_node(state: VaptState):
    logging.info("--- REPORT: COMPILING FINAL FINDINGS ---")
    full_history = "\n".join(state["history"])
    return {
        "report": (
            f"VAPT Assessment Final Report for Target: {state['target']}\n\n"
            f"=== Final Findings Summary ===\n{state['findings_summary']}\n\n"
            f"=== Full Execution History ===\n{full_history}"
        )
    }

async def human_approval_gate(state: VaptState, config: dict):
    logging.info("--- AWAITING HUMAN APPROVAL ---")
    approval_event = config['configurable'].get('approval_event')
    user_choice = config['configurable'].get('user_choice')

    if not approval_event or not user_choice:
        logging.error("Approval event/choice not found in config.")
        return {"current_command": "END"} 
        
    approval_event.clear()
    await approval_event.wait()

    if user_choice.value == "approve":
        logging.info("Approved.")
    else:
        logging.info("Denied. Asking AI for a different command.")
        
    return {}

def compile_graph():
    def route_after_command_proposal(state: VaptState, config: dict):
        command = state.get("current_command", "")
        if command.upper() == "CONTINUE":
            return "decide"
        if command.upper() == "END":
            return "report"
        scan_mode = config['configurable'].get('scan_mode', 'auto')
        return "human_approval_gate" if scan_mode == 'manual' else "execute"

    def route_after_approval(state: VaptState, config: dict):
        choice = config['configurable'].get('user_choice').value
        return "execute" if choice == 'approve' else "replan"

    def check_for_errors(state: VaptState):
        return "error_handler" if state.get("command_error") else "analyze"

    builder = StateGraph(VaptState)

    builder.add_node("planner", planner_node)
    builder.add_node("execute", execute_node, config_key="configurable")
    builder.add_node("analyze", analyze_node)
    builder.add_node("decide", decide_node)
    builder.add_node("error_handler", error_handler_node)
    builder.add_node("report", report_node)
    builder.add_node("human_approval_gate", human_approval_gate)

    def replan_node(state: VaptState):
        command_denied = state["current_command"]
        logging.info(f"Adding denied command to memory: {command_denied}")

        updated_tried_command = state["tried_commands"] + [command_denied]
        return {"tried_commands": updated_tried_command}
    builder.add_node("replan", replan_node)

    builder.set_entry_point("planner")

    builder.add_conditional_edges("planner", route_after_command_proposal, {
        "human_approval_gate": "human_approval_gate",
        "execute": "execute",
        "report": "report"
    })
    builder.add_conditional_edges("decide", route_after_command_proposal, {
        "human_approval_gate": "human_approval_gate",
        "execute": "execute",
        "report": "report"
    })
    builder.add_conditional_edges("error_handler", route_after_command_proposal, {
        "decide": "decide",
        "human_approval_gate": "human_approval_gate",
        "execute": "execute",
        "report": "report"
    })
    builder.add_conditional_edges("human_approval_gate", route_after_approval, {
        "execute": "execute",
        "replan": "replan"
    })
    builder.add_edge("replan", "decide")
    builder.add_conditional_edges("execute", check_for_errors, {
        "error_handler": "error_handler",
        "analyze": "analyze"
    })
    builder.add_edge("analyze", "decide")
    builder.add_edge("report", END)

    return builder.compile()

async def run_vapt_agent_stream(target_query: str, config: dict):
    graph = compile_graph()
    selected_model = config['configurable'].get('selected_ai_model', 'Gemini')
    api_key_from_ui = config['configurable'].get('ai_api_key')
    final_api_key = api_key_from_ui

    if not final_api_key:
        if selected_model == 'Gemini':
            final_api_key = os.getenv("GEMINI_API_KEY")
        elif selected_model == 'OpenAI (GPT-4)':
            final_api_key = os.getenv("OPENAI_API_KEY")
        elif selected_model == 'Anthropic (Claude 3 Sonnet)':
            final_api_key = os.getenv("ANTHROPIC_API_KEY")

    scan_type = config['configurable'].get('scan_type', 'Full Scan')

    initial_state = {
        "user_query": target_query,
        "target": "",
        "current_command": "",
        "command_output": "",
        "command_error": "",
        "executed_command": "",
        "scan_type": scan_type,
        "tried_commands": [],
        "detailed_analysis": {},
        "findings_summary": "No findings yet.",
        "history": [],
        "selected_ai_model": selected_model,
        "ai_api_key": final_api_key,
        "report": ""
    }
    
    stop_event = config['configurable'].get('stop_event')
    
    async for update in graph.astream(initial_state, config=config):
        if stop_event and stop_event.is_set():
            logging.warning("--- SCAN STOPPED BY USER ---")
            yield {"__end__": {"report": "Scan was manually stopped by the user."}}
            break
        yield update
