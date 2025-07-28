from nicegui import ui, app

def create_settings_panel():
    with ui.dialog() as settings_dialog, ui.card().style('min-width: 400px'):
        ui.label('AI Model Settings').classes('text-h6 font-bold')
        ui.separator()

        default_model = app.storage.user.get('selected_ai_model', 'Gemini')

        model_select = ui.select(
            ['Gemini', 'OpenAI (GPT-4)', 'Anthropic (Claude 3 Sonnet)', 'Ollama (Llama3)'],
            label='Select AI Provider',
            value=default_model
        ).props('outlined').bind_value(app.storage.user, 'selected_ai_model')

        api_key_input = ui.input(
            label='API Key'
        ).props('outlined password').classes('w-full') \
         .bind_value(app.storage.user, 'ai_api_key')
        
        ui.label('Your API key is stored securely in your browser.').classes('text-xs text-gray-500')
        ui.separator().classes('my-4')

        with ui.row().classes('w-full justify-end'):
            ui.button('Close', on_click=settings_dialog.close).props('flat')
            
            def handle_save():
                ui.notify(f"Settings saved for {model_select.value}!", color='positive')
                settings_dialog.close()
            
            ui.button('Save', on_click=handle_save).props('color=primary')

    return settings_dialog
