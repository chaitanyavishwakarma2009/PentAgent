from nicegui import ui

@ui.page('/history')
def history_page():
    """Displays a page with the history of all scans."""
    ui.label('Raw Command History').classes('text-h4 p-4')

    # Retrieve the shared history data from app storage
    scan_histories = app.storage.user.get('scan_histories', {})

    if not scan_histories:
        ui.label('No scan history has been recorded yet.').classes('p-4')
        return

    # Display history for each scan, newest first
    for scan_id, history_entries in sorted(scan_histories.items(), reverse=True):
        with ui.expansion(f'Scan ID: {scan_id}').classes('w-full text-lg m-2'):
            if not history_entries:
                ui.label('No commands were executed in this scan.')
                continue
            
            for i, entry in enumerate(history_entries):
                with ui.card().classes('w-full'):
                    ui.label(f"Step {i+1}: {entry['command']}").classes('text-bold font-mono')
                    with ui.expansion('Show Raw Output', icon='visibility').classes('w-full'):
                        # Use ui.code for preserving formatting of raw output
                        ui.code(entry['output']).classes('w-full bg-gray-200 text-xs p-2')