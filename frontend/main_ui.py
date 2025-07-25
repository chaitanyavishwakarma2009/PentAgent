# frontend/main_ui.py
from nicegui import ui, app
import sys
from pathlib import Path
import logging
import asyncio
import json

# --- Project Path Setup ---
project_root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(project_root))

# --- Imports ---
from backend.main import run_vapt_agent_stream
from frontend.state import SharedState
from frontend.components.control_panel import create_control_panel
from frontend.components.approval_panel import create_approval_panel
from frontend.components.reporting_panel import create_reporting_panel
from frontend import history_page 

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

@ui.page('/')
def main_page():
    
    state = SharedState()

    # --- UI LAYOUT AND CREATION ---
    with ui.header(elevated=True).classes('bg-primary text-white'):
        ui.label('AI-Powered VAPT Agent').classes('text-h5')

    mode_dialog = ui.dialog()
    target_input, start_button, stop_button = create_control_panel(state, mode_dialog)
    create_approval_panel(state)
    analysis_view, log, status_label = create_reporting_panel()

    # --- LOGIC AND CALLBACKS ---
    def update_button_states():
        start_button.set_enabled(not state.is_scan_running.value)
        stop_button.set_enabled(state.is_scan_running.value)

    async def start_scan(target: str, mode: str):
        # This function is correct and does not need to change
        log.clear()
        analysis_view.set_content('')
        state.is_scan_running.value = True
        state.scan_mode.value = mode
        update_button_states()
        
        state.stop_event.clear()
        state.approval_event.clear()

        scan_id_counter = app.storage.user.get('scan_id_counter', 0) + 1
        app.storage.user['scan_id_counter'] = scan_id_counter
        state.scan_id.value = scan_id_counter
        
        if 'scan_histories' not in app.storage.user:
            app.storage.user['scan_histories'] = {}
        app.storage.user['scan_histories'][state.scan_id.value] = []
        
        config = {
            "configurable": { "scan_mode": mode, "approval_event": state.approval_event, "stop_event": state.stop_event, "user_choice": state.user_choice }
        }

        try:
            async for update in run_vapt_agent_stream(target, config):
                node_name = list(update.keys())[0]
                if node_name == "__end__":
                    log.push(f"\n--- SCAN COMPLETE ---\n{update['__end__'].get('report')}")
                    break

                node_output = update[node_name]
                log_message = f">>> Node '{node_name}' finished."
                if node_output:
                    if 'current_command' in node_output and node_output['current_command']:
                        log_message += f"\n   - AI decided on command: {node_output['current_command']}"
                    if 'command_output' in node_output and node_output['command_output']:
                        truncated_output = node_output['command_output'][:200].strip()
                        log_message += f"\n   - Command Output (truncated):\n---\n{truncated_output}\n---"
                    if 'detailed_analysis' in node_output:
                        log_message += "\n   - Analysis report updated."
                log.push(log_message)
                
                if node_output and node_name == 'execute':
                    history_entry = {
                        "command": node_output.get("executed_command", "N/A"),
                        "output": node_output.get("command_output") or node_output.get("command_error", "No output.")
                    }
                    app.storage.user['scan_histories'][state.scan_id.value].append(history_entry)

                nodes_that_propose_commands = ["planner", "decide", "error_handler"]
                if node_output and node_name in nodes_that_propose_commands and state.scan_mode.value == 'manual':
                    command = node_output.get("current_command")
                    if command and command != "END":
                        status_label.set_text("Waiting for your approval...")
                        state.command_to_approve.value = command
                        state.approval_needed.value = True
                
                if node_output and node_name == 'analyze':
                    interpretive_analysis = node_output.get('detailed_analysis', 'No analysis available.')
                    analysis_view.set_content(interpretive_analysis)
            
        except Exception as e:
            logging.exception("An error occurred during scan")
            status_label.set_text("An error occurred!")
            log.push(f"\n--- ERROR ---\n{e}")
        
        finally:
            state.is_scan_running.value = False
            state.approval_needed.value = False
            update_button_states()
            status_label.text = "Scan Finished or Stopped."


    # --- FINAL FIX ---
    # Define proper async functions to handle the button clicks.
    # We pass these functions directly to on_click, NOT a lambda.
    async def handle_autonomous_click():
        mode_dialog.close()
        await start_scan(target_input.value, 'autonomous')

    async def handle_manual_click():
        mode_dialog.close()
        await start_scan(target_input.value, 'manual')

    # Populate the dialog with buttons that call these new handler functions.
    with mode_dialog, ui.card():
        ui.label('Select Scan Mode').classes('text-h6')
        ui.button('Fully Autonomous', on_click=handle_autonomous_click)
        ui.button('Manual Approval', on_click=handle_manual_click)

# --- Start the App ---
ui.run(title='VAPT Agent UI', host='0.0.0.0', storage_secret='a_very_secret_key_for_this_app')