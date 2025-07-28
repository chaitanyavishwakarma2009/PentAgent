# frontend/main_ui.py
from nicegui import ui, app
import sys
from pathlib import Path
import logging
import asyncio

project_root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(project_root))

from backend.main import run_vapt_agent_stream
from frontend.state import SharedState
from frontend.components.control_panel import create_control_panel
from frontend.components.approval_panel import create_approval_panel
from frontend.components.reporting_panel import create_reporting_panel
from frontend.components.history_panel import create_history_panel
from frontend.components.settings_panel import create_settings_panel

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

@ui.page('/')
def main_page():
    state = SharedState()
    history_drawer, build_history_list = create_history_panel(state)

    def handle_history_click():
        if not history_drawer.value:
            build_history_list()
        history_drawer.toggle()

    settings_dialog = create_settings_panel()
    
    dark_mode = ui.dark_mode()

    with ui.header(elevated=True).classes('bg-gray-900 text-white'):
        with ui.row().classes('w-full items-center'):
            ui.label('PentAgent').classes('text-h5')
            ui.space() 
            ui.button(icon='history', on_click=handle_history_click).props('flat color=white').tooltip('Toggle Command History')
            ui.button(icon='settings', on_click=settings_dialog.open).props('flat color=white').tooltip('AI Model Settings')
            ui.button(icon="dark_mode", on_click=dark_mode.toggle).props('flat color=white')

    mode_dialog = ui.dialog()
    target_input, scan_type_select, start_button, stop_button = create_control_panel(state, mode_dialog)
    create_approval_panel(state)
    analysis_view, log, status_label = create_reporting_panel()

    def update_button_states():
        start_button.set_enabled(not state.is_scan_running.value)
        stop_button.set_enabled(state.is_scan_running.value)

    async def start_scan(target: str, scan_type: str, mode: str):
        logging.info(f"--- Starting New Scan ---")
        logging.info(f"Target: {target}")
        logging.info(f"Scan Type: {scan_type}")
        logging.info(f"Mode: {mode}")

        state.reset()
        log.clear()
        analysis_view.set_content('')
        
        state.is_scan_running.value = True
        state.scan_mode.value = mode
        update_button_states()
        
        state.stop_event.clear()
        state.approval_event.clear()
        state.scan_id_counter += 1
        scan_id_counter = state.scan_id_counter
        state.scan_id.value = scan_id_counter
        state.scan_histories[scan_id_counter] = []

        selected_model = app.storage.user.get('selected_ai_model', 'Gemini')
        api_key = app.storage.user.get('ai_api_key')

        if not api_key:
            ui.notify('API Key is not set! Please set it in the settings panel.', color='negative')
            state.is_scan_running.value = False
            update_button_states()      
            return

        config = {
            "configurable": { 
                "scan_mode": mode,
                "scan_type": scan_type,
                "approval_event": state.approval_event, 
                "stop_event": state.stop_event, 
                "user_choice": state.user_choice, 
                "selected_ai_model": selected_model,
                "ai_api_key": api_key,
            }               
        }

        try:
            async for update in run_vapt_agent_stream(target, config):
                node_name = list(update.keys())[0]
                if node_name == "__end__":
                    log.push(f"\n--- SCAN COMPLETE ---\n{update['__end__'].get('report')}")
                    break

                node_output = update[node_name]

                if node_output and node_name == 'execute':
                    history_entry = {
                        "command": node_output.get("executed_command", "N/A"),
                        "output": node_output.get("command_output") or node_output.get("command_error", "No output."),
                        "analysis": ""
                    }
                    state.scan_histories[state.scan_id.value].append(history_entry)

                if node_output and node_name == 'analyze':
                    interpretive_analysis = node_output.get('detailed_analysis', 'No analysis available.')
                    analysis_view.set_content(interpretive_analysis)
                    current_scan_history = state.scan_histories.get(state.scan_id.value)
                    if current_scan_history:
                        current_scan_history[-1]['analysis'] = interpretive_analysis

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
        if not target_input.value or not target_input.value.strip():
            ui.notify('Target input cannot be empty!', color='negative')
            return
        mode_dialog.close()
        await start_scan(target_input.value, scan_type_select.value, 'autonomous')

    async def handle_manual_click():
        if not target_input.value or not target_input.value.strip():
            ui.notify('Target input cannot be empty!', color='negative')
            return
        mode_dialog.close()
        await start_scan(target_input.value, scan_type_select.value, 'manual')

    with mode_dialog, ui.card():
        ui.label('Select Scan Mode').classes('text-h6')
        ui.button('Fully Autonomous', on_click=handle_autonomous_click)
        ui.button('Manual Approval', on_click=handle_manual_click)

ui.run(title='VAPT Agent UI', host='0.0.0.0', storage_secret='a_very_secret_key_for_this_app')
