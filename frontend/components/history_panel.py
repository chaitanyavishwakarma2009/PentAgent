from nicegui import ui
from frontend.state import SharedState

def create_history_panel(state: SharedState):
    with ui.right_drawer(value=False).classes('p-2 border-l bg-gray-100 dark:bg-gray-900') as history_drawer:
        history_container = ui.column().classes('w-full gap-2')

        def build_history_list():
            history_container.clear()
            with history_container:
                ui.label('Command History').classes('text-xl font-bold text-gray-700 dark:text-white p-2')
                ui.separator()

                histories = state.scan_histories
                if not histories:
                    ui.label('No commands have been executed in this session.').classes('dark:text-white')
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
                        analysis = entry.get('analysis')

                        with ui.card().classes('w-full bg dark:bg-gray-800 text-black dark:text-white'):
                            with ui.card_section():
                                ui.label(command).classes('font-mono font-bold text-md dark:text-white')
                                ui.label(f'From Scan #{scan_id}').classes('text-xs dark:text-white')

                            if analysis:
                                with ui.card_section().classes('border-y'):
                                    ui.label('Analysis Report').classes('text-sm font-semibold dark:text-white')
                                    ui.markdown(analysis).classes('text-sm dark:text-white')

                            with ui.expansion('Show Output', icon='visibility').classes('w-full'):
                                ui.code(output, language='bash').classes('w-full text-xs rounded dark:text-white')

                if not command_found:
                    ui.label('No commands have been executed in this session.').classes('dark:text-white')

    return history_drawer, build_history_list
