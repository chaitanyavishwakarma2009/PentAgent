from nicegui import ui
from frontend.state import SharedState

def create_control_panel(state: SharedState, mode_dialog: ui.dialog):
    """
    Creates the main user control panel with target input, a new scan type
    dropdown, and start/stop buttons.
    """
    with ui.card().classes('w-full no-shadow border-[1px]'):
        with ui.row().classes('w-full items-center'):
            # --- Target Input (Unchanged) ---
            target_input = ui.input(
                placeholder='Enter target (e.g., example.com or 192.168.1.1)'
            ).props('outlined dense').classes('flex-grow')

            # --- NEW: Scan Type Dropdown ---
            # This is a ui.select element, which acts as a dropdown menu.
            scan_type_options = [
                'Full Scan', 
                'Vulnerability Assessment', 
                'Reconnaissance Only', 
                'Web Application Scan'
            ]
            scan_type_select = ui.select(
                options=scan_type_options, 
                value='Full Scan' # Set a default value
            ).props('outlined dense').classes('w-64 ml-2') \
             .tooltip('Select the type of scan to perform')

            # --- Start/Stop Buttons (Unchanged) ---
            start_button = ui.button('Start Scan', on_click=mode_dialog.open) \
                .props('color=primary icon=play_arrow')
            stop_button = ui.button('Stop Scan', on_click=state.stop_event.set) \
                .props('color=red icon=stop')

    # This function is returned and used by main_ui.py
    def update_button_states():
        start_button.set_enabled(not state.is_scan_running.value)
        stop_button.set_enabled(state.is_scan_running.value)

    # We need to return the new dropdown select as well
    return target_input, scan_type_select, start_button, stop_button