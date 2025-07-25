# frontend/state.py
import asyncio
from typing import Any

# This custom Ref class is fine if you are using it for your UI elements.
class Ref:
    def __init__(self, value: Any): self.value = value

class SharedState:
    def __init__(self):
        self.scan_mode = Ref('autonomous')
        self.is_scan_running = Ref(False)
        self.approval_needed = Ref(False)
        self.command_to_approve = Ref("")
        self.user_choice = Ref("")
        self.scan_id = Ref(0)
        
        # Ensure BOTH events are asyncio events for the async backend.
        self.stop_event = asyncio.Event()
        self.approval_event = asyncio.Event()

    def reset(self):
        """
        Resets the state for the beginning of a new scan to prevent
        displaying stale data from a previous run.
        """
        print("[UI State] Resetting for new scan.")
        # We don't touch is_scan_running here, as it's set immediately after.
        self.approval_needed.value = False
        self.command_to_approve.value = ""
        self.user_choice.value = ""
        # We also don't touch scan_id or scan_mode, as they are set by the new scan.