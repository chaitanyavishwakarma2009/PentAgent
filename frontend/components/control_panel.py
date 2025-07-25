# frontend/components/control_panel.py
from nicegui import ui

def create_control_panel(state, mode_dialog):
    """
    Creates the main user input and control buttons.
    The 'start_button' now only needs to open the dialog.
    """
    with ui.card().classes('w-full'):
        with ui.row().classes('w-full items-center'):
            target_input = ui.input(
                placeholder='Enter target IP or domain'
            ).classes('flex-grow')

            start_button = ui.button(
                'Start Scan', 
                on_click=lambda: mode_dialog.open() if target_input.value else ui.notify('Please enter a target.', type='negative')
            )
            
            def stop_scan():
                ui.notify('Stop signal sent.')
                state.stop_event.set()
                
            stop_button = ui.button('Stop Scan', on_click=stop_scan)
            
    # Initial button states
    start_button.set_enabled(True)
    stop_button.set_enabled(False)
    
    return target_input, start_button, stop_button