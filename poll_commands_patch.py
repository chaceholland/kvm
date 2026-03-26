#!/usr/bin/env python3
"""
Patches poll_commands.py to report jiggler status back to the command queue
after every poll cycle.
"""
import os

poller_path = os.path.expanduser("~/Documents/Software/kvm-setup/scripts/poll_commands.py")
code = open(poller_path).read()

if "report_status" not in code:
    # Add status reporting function after the poll() function
    status_fn = '''
def report_status(mac_ip, port, machine):
    """Report current jiggler status back to the command queue server."""
    pid_file = os.path.join(os.environ.get("TEMP", "/tmp"), "mouse_jiggler.pid")
    running = False
    if os.path.exists(pid_file):
        with open(pid_file) as f:
            pid = f.read().strip()
        try:
            if PLATFORM == "Windows":
                import subprocess as sp
                result = sp.run(["tasklist", "/FI", f"PID eq {pid}", "/NH"],
                               capture_output=True, text=True, timeout=5)
                running = pid in result.stdout
            else:
                os.kill(int(pid), 0)
                running = True
        except Exception:
            running = False

    url = f"http://{mac_ip}:{port}/status_report"
    try:
        data = json.dumps({"machine": machine, "status": {"jiggler_running": running}}).encode()
        req = urllib.request.Request(url, data=data, headers={"Content-Type": "application/json"})
        urllib.request.urlopen(req, timeout=3)
    except Exception:
        pass

'''

    # Insert before the main() function
    code = code.replace("\ndef main():", status_fn + "\ndef main():")

    # Add status reporting call in the main loop after processing commands
    code = code.replace(
        "        time.sleep(args.interval)",
        "        report_status(args.mac_ip, args.port, args.machine)\n        time.sleep(args.interval)"
    )

    open(poller_path, "w").write(code)
    print("Patched poll_commands.py with status reporting")
else:
    print("poll_commands.py already patched")
