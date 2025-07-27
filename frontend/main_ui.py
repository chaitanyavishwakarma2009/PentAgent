# frontend/main_ui.py
from nicegui import ui, app
import sys
from pathlib import Path
import logging
import asyncio

# --- Project Path Setup ---
project_root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(project_root))

# --- Imports ---
from backend.main import run_vapt_agent_stream
from frontend.state import SharedState # Import the state management class
from frontend.components.control_panel import create_control_panel
from frontend.components.approval_panel import create_approval_panel
from frontend.components.reporting_panel import create_reporting_panel
from frontend.components.history_panel import create_history_panel

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

@ui.page('/')
def main_page():
    
    # Create an instance of our state object for this user session.
    state = SharedState()

    # Create the history drawer, passing it the state object
    history_drawer, build_history_list = create_history_panel(state)

    def handle_history_click():
        """Builds the history list right before opening the drawer."""
        if not history_drawer.value:
            build_history_list()
        history_drawer.toggle()

    # --- HEADER DEFINITION ---
    with ui.header(elevated=True).classes('bg-primary text-white'):
        with ui.row().classes('w-full items-center'):
            ui.label('AI-Powered VAPT Agent').classes('text-h5')
            ui.space() 
            ui.button(icon='history', on_click=handle_history_click).props('flat color=white') \
                .tooltip('Toggle Command History')

    # --- MAIN PAGE CONTENT ---
    mode_dialog = ui.dialog()
    target_input, start_button, stop_button = create_control_panel(state, mode_dialog)
    create_approval_panel(state)
    analysis_view, log, status_label = create_reporting_panel()

    # --- LOGIC AND CALLBACKS ---
    def update_button_states():
        start_button.set_enabled(not state.is_scan_running.value)
        stop_button.set_enabled(state.is_scan_running.value)

    async def start_scan(target: str, mode: str):
        # Reset parts of the state for a clean run
        state.reset()
        log.clear()
        analysis_view.set_content('')
        
        state.is_scan_running.value = True
        state.scan_mode.value = mode
        update_button_states()
        
        state.stop_event.clear()
        state.approval_event.clear()

        # Using the state object for temporary history storage
        state.scan_id_counter += 1
        scan_id_counter = state.scan_id_counter
        state.scan_id.value = scan_id_counter
        
        # Create an empty list for this new scan's history within the state
        state.scan_histories[scan_id_counter] = []
        
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

                # --- NEW LOGIC TO CORRECTLY SAVE HISTORY AND ANALYSIS ---

                # 1. When a command is EXECUTED, create its history entry with a placeholder.
                if node_output and node_name == 'execute':
                    history_entry = {
                        "command": node_output.get("executed_command", "N/A"),
                        "output": node_output.get("command_output") or node_output.get("command_error", "No output."),
                        "analysis": "" # Add a placeholder for the analysis report
                    }
                    state.scan_histories[state.scan_id.value].append(history_entry)

                # 2. When the result is ANALYZED, update the main view AND the last history entry.
                if node_output and node_name == 'analyze':
                    interpretive_analysis = node_output.get('detailed_analysis', 'No analysis available.')
                    analysis_view.set_content(interpretive_analysis) # Update main UI panel
                    
                    # Find the history for the current scan
                    current_scan_history = state.scan_histories.get(state.scan_id.value)
                    # If history exists, update the 'analysis' field of the LAST entry
                    if current_scan_history:
                        current_scan_history[-1]['analysis'] = interpretive_analysis

                # --- END NEW LOGIC ---

                # This logging is separate and provides a simple, chronological feed.
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
                
                # Manual approval logic remains unchanged
                nodes_that_propose_commands = ["planner", "decide", "error_handler"]
                if node_output and node_name in nodes_that_propose_commands and state.scan_mode.value == 'manual':
                    command = node_output.get("current_command")
                    if command and command != "END":
                        status_label.set_text("Waiting for your approval...")
                        state.command_to_approve.value = command
                        state.approval_needed.value = True
            
        except Exception as e:
            logging.exception("An error occurred during scan")
            status_label.set_text("An error occurred!")
            log.push(f"\n--- ERROR ---\n{e}")
        
        finally:
            state.is_scan_running.value = False
            state.approval_needed.value = False
            update_button_states()
            status_label.text = "Scan Finished or Stopped."


    async def handle_autonomous_click():
        mode_dialog.close()
        await start_scan(target_input.value, 'autonomous')

    async def handle_manual_click():
        mode_dialog.close()
        await start_scan(target_input.value, 'manual')

    with mode_dialog, ui.card():
        ui.label('Select Scan Mode').classes('text-h6')
        ui.button('Fully Autonomous', on_click=handle_autonomous_click)
        ui.button('Manual Approval', on_click=handle_manual_click)

ui.run(title='VAPT Agent UI', host='0.0.0.0', storage_secret='a_very_secret_key_for_this_app')