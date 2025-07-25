# frontend/components/approval_panel.py
from nicegui import ui

def create_approval_panel(state):
    """Creates the panel for manual command approval."""
    with ui.card().classes('w-full').bind_visibility_from(state.approval_needed, 'value'):
        ui.label("The AI wants to run the following command. Please approve or disapprove.").classes('text-subtitle2')
        
        # This label displays the command from the shared state
        ui.label().classes('text-mono bg-grey-3 p-2 rounded').bind_text_from(state.command_to_approve, 'value')
        
        with ui.row():
            def _approve():
                state.user_choice.value = 'approve'
                state.approval_event.set()
                state.approval_needed.value = False
                state.command_to_approve.value = "" # <-- THIS IS THE FIX
                ui.notify('Command Approved. Executing...', type='positive')

            def _disapprove():
                state.user_choice.value = 'disapprove'
                state.approval_event.set()
                state.approval_needed.value = False
                state.command_to_approve.value = ""
                ui.notify('Command Disapproved. Ending run.', type='negative')

            ui.button('Approve', on_click=_approve)
            ui.button('Disapprove', on_click=_disapprove)