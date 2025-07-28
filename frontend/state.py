# frontend/state.py
import asyncio
from typing import Any

class Ref:
    def __init__(self, value: Any): 
        self.value = value

class SharedState:
    def __init__(self):
        self.scan_mode = Ref('autonomous')
        self.is_scan_running = Ref(False)
        self.approval_needed = Ref(False)
        self.command_to_approve = Ref("")
        self.user_choice = Ref("")
        self.scan_id = Ref(0)

        self.stop_event = asyncio.Event()
        self.approval_event = asyncio.Event()

        self.scan_id_counter = 0
        self.scan_histories = {}

    def reset(self):
        print("[UI State] Resetting for new scan.")
        self.approval_needed.value = False
        self.command_to_approve.value = ""
        self.user_choice.value = ""

    def cleanup(self):
        """Signal all events to unblock any waiting tasks and allow clean exit."""
        print("Running shutdown cleanup...")
        self.stop_event.set()
        self.approval_event.set()