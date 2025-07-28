from nicegui import ui
from frontend.state import SharedState

def create_control_panel(state: SharedState, mode_dialog: ui.dialog):
    with ui.card().classes('w-full no-shadow border-[1px]'):
        with ui.row().classes('w-full items-center'):
            target_input = ui.input(
                placeholder='Enter target (e.g., example.com or 192.168.1.1)'
            ).props('outlined dense').classes('flex-grow bg-gray-100 dark:bg-gray-700 text-black dark:text-white')

            scan_type_options = [
                'Full Scan', 
                'Vulnerability Assessment', 
                'Reconnaissance Only', 
                'Web Application Scan'
            ]
            scan_type_select = ui.select(
                options=scan_type_options, 
                value='Full Scan'
            ).props('outlined dense').classes('w-64 ml-2 bg-gray-100 dark:bg-gray-700 text-black dark:text-white') \
             .tooltip('Select the type of scan to perform')

            start_button = ui.button('Start Scan', on_click=mode_dialog.open) \
                .props('color=primary icon=play_arrow') \
                .classes('bg-blue-600 hover:bg-blue-700 text-white dark:bg-blue-500')
            
            stop_button = ui.button('Stop Scan', on_click=state.stop_event.set) \
                .props('color=red icon=stop') \
                .classes('bg-red-600 hover:bg-red-700 text-white dark:bg-red-500')

    def update_button_states():
        start_button.set_enabled(not state.is_scan_running.value)
        stop_button.set_enabled(state.is_scan_running.value)

    return target_input, scan_type_select, start_button, stop_button
