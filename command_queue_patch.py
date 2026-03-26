#!/usr/bin/env python3
"""
Patches command_queue.py to add a /status/<machine> endpoint that returns
the last known jiggler status reported by the poller.
"""
import os, sys

queue_path = os.path.expanduser("~/Documents/Software/kvm-setup/scripts/command_queue.py")
code = open(queue_path).read()

# Add status tracking dict after QUEUES
if "STATUS = {}" not in code:
    code = code.replace(
        "QUEUES = defaultdict(list)",
        "QUEUES = defaultdict(list)\nSTATUS = {}  # Last known status per machine"
    )

# Add status reporting in do_POST
if "/status_report" not in code:
    old_post_404 = '''        else:
            self.send_response(404)
            self.end_headers()'''

    # Find the one in do_POST (after the /queue handler)
    # We need to add a new endpoint
    new_post = '''        elif self.path == "/status_report":
            length = int(self.headers.get("Content-Length", 0))
            body = json.loads(self.rfile.read(length))
            machine = body.get("machine", "")
            with LOCK:
                STATUS[machine] = body.get("status", {})
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(json.dumps({"ok": True}).encode())
        else:
            self.send_response(404)
            self.end_headers()'''

    # Replace the last else in do_POST
    # Find do_POST's else block
    code = code.replace(old_post_404, new_post, 1)

# Add status GET endpoint in do_GET
if "/status/" not in code:
    old_get_404 = '''        else:
            self.send_response(404)
            self.end_headers()'''

    new_get = '''        elif self.path.startswith("/status/"):
            machine = self.path.split("/status/")[1]
            with LOCK:
                status = STATUS.get(machine, {})
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(json.dumps(status).encode())
        else:
            self.send_response(404)
            self.end_headers()'''

    code = code.replace(old_get_404, new_get, 1)

open(queue_path, "w").write(code)
print("Patched command_queue.py with /status endpoints")
