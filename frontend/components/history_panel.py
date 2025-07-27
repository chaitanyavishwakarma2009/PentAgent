from nicegui import ui
from frontend.state import SharedState

def create_history_panel(state: SharedState):
    """
    Creates a drawer to display scan history from the provided state object.
    """
    with ui.right_drawer(value=False).classes('bg-gray-100 p-2 border-l') as history_drawer:
        
        history_container = ui.column().classes('w-full gap-2')

        def build_history_list():
            """This function clears and rebuilds the content of the history drawer."""
            history_container.clear()
            with history_container:
                ui.label('Command History').classes('text-xl font-bold text-gray-700 p-2')
                ui.separator()
                
                histories = state.scan_histories
                
                if not histories:
                    ui.label('No commands have been executed in this session.')
                    return

                command_found = False
                for scan_id in reversed(list(histories.keys())):
                    scan_data = histories[scan_id]
                    if not scan_data:
                        continue
                    for entry in scan_data:
                        command_found = True
                        command = entry.get('command', 'N/A')
                        output = entry.get('output', 'No output.') or "No output."
                        # --- Get the new analysis data ---
                        analysis = entry.get('analysis')

                        with ui.card().classes('w-full'):
                            # --- Command Title Section ---
                            with ui.card_section():
                                ui.label(command).classes('font-mono font-bold text-md')
                                ui.label(f'From Scan #{scan_id}').classes('text-xs text-gray-500')
                            
                            # --- NEW: Analysis Report Section ---
                            # Only show this section if an analysis report exists.
                            if analysis:
                                with ui.card_section().classes('bg-blue-50 border-y'): # Styled differently to stand out
                                    ui.label('Analysis Report').classes('text-sm font-semibold text-blue-800')
                                    # Use markdown for nice formatting of the report
                                    ui.markdown(analysis).classes('text-sm')
                            
                            # --- Output Section ---
                            with ui.expansion('Show Output', icon='visibility').classes('w-full'):
                                ui.code(output, language='bash').classes('w-full text-xs bg-gray-800 text-white rounded')
                
                if not command_found:
                    ui.label('No commands have been executed in this session.')

    return history_drawer, build_history_list