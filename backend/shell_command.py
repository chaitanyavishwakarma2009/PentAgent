# backend/shell_command.py
import asyncio
import shlex
import logging

async def run_command(command_str: str, stop_event: asyncio.Event) -> dict:
    """
    Runs a shell command asynchronously and can be interrupted by a stop_event.
    """
    try:
        logging.info(f"\n📌 Running Interruptible Command: {command_str}")
        
        command_parts = shlex.split(command_str)
        
        proc = await asyncio.create_subprocess_exec(
            *command_parts,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )

        # --- THIS IS THE FIX ---
        # Create two tasks: one for the command to finish, one for the stop signal.
        comm_task = asyncio.create_task(proc.communicate(), name=f"comm_{proc.pid}")
        stop_task = asyncio.create_task(stop_event.wait(), name=f"stop_{proc.pid}")

        # Wait for EITHER task to complete.
        done, pending = await asyncio.wait(
            [comm_task, stop_task], 
            return_when=asyncio.FIRST_COMPLETED
        )

        # If the stop task finished first, the user clicked the stop button.
        if stop_task in done:
            logging.warning(f"--- Stop signal received for command: {command_str} ---")
            # We must kill the running process and cancel the communication task.
            comm_task.cancel()
            try:
                proc.terminate()
                await proc.wait() # Clean up the terminated process
                logging.warning("--- Subprocess terminated successfully. ---")
            except ProcessLookupError:
                logging.warning("--- Subprocess already finished. ---")
            return {"command": command_str, "output": "Command was terminated by user.", "error": "User Interruption"}
        
        # If we get here, it means the command finished normally.
        # We must cancel the stop task to prevent it from lingering.
        stop_task.cancel()

        stdout, stderr = await comm_task # Get the results from the completed task
        output = stdout.decode().strip()
        error = stderr.decode().strip()

        if proc.returncode == 0:
            logging.info("\n[✔] Command Output:\n" + output)
            return {"command": command_str, "output": output, "error": None}
        else:
            logging.error(f"\n[✖] Error (Code {proc.returncode}):\n" + error)
            return {"command": command_str, "output": output, "error": error}

    except asyncio.CancelledError:
        logging.warning("Command execution was cancelled.")
        return {"command": command_str, "output": None, "error": "Cancelled"}
    except Exception as e:
        logging.error(f"[!] Exception during command execution: {e}")
        return {"command": command_str, "output": None, "error": str(e)}