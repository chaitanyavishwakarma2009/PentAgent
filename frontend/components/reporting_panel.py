# frontend/components/reporting_panel.py
from nicegui import ui

def create_reporting_panel():
    """Creates the UI panels for displaying results."""
    with ui.card().classes('w-full max-w-2xl mx-auto'):
        ui.label('Per-Step Analysis Report').classes('text-h6')
        analysis_view = ui.markdown().classes('w-full')
        analysis_view.set_content('*Analysis will appear here...*')

    with ui.expansion('Live Execution Log', icon='terminal').classes('w-full max-w-2xl mx-auto rounded-xl shadow-md'):
        log = ui.log().classes('w-full')
        status_label = ui.label('Awaiting scan start...').classes('text-italic p-2')
            
    return analysis_view, log, status_label