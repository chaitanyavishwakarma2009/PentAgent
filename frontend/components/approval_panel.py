from nicegui import ui

def create_approval_panel(state):
    """Creates the panel for manual command approval, compatible with dark mode."""
    with ui.card().classes(
         'w-full'
        
     ).bind_visibility_from(state.approval_needed, 'value'):
        
        ui.label("The AI wants to run the following command. Please approve or disapprove.")\
            .classes('text-subtitle2 dark:text-gray-300')
    
        ui.label().classes(
               'w-full p-3 rounded-md break-words '  
    'bg-gray-200 dark:bg-gray-800 '       
    'text dark:text-white '         
    'border border-gray-300 dark:border-gray-600'
        ).bind_text_from(state.command_to_approve, 'value').props('outlined')

        with ui.row():
            def _approve():
                state.user_choice.value = 'approve'
                state.approval_event.set()
                state.approval_needed.value = False
                state.command_to_approve.value = "" 
                ui.notify('Command Approved. Executing...', type='positive')

            def _disapprove():
                state.user_choice.value = 'disapprove'
                state.approval_event.set()
                state.approval_needed.value = False
                state.command_to_approve.value = ""
                ui.notify('Command Disapproved. Ending run.', type='negative')

            # Buttons are styled for visibility in both light and dark modes
            ui.button('Approve', on_click=_approve).classes('bg-green-500 hover:bg-green-600 text-white')
            ui.button('Disapprove', on_click=_disapprove).classes('bg-red-500 hover:bg-red-600 text-white')