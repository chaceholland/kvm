#!/bin/bash
# ONE SCRIPT TO FIX EVERYTHING
# Run from Windows: ssh chace@192.168.1.100 "bash /tmp/fix_jiggler_button.sh"

set -e
SD_PLUGIN="$HOME/Library/Application Support/com.elgato.StreamDeck/Plugins/com.chace.jiggler.sdPlugin"
KVM="$HOME/Documents/Software/kvm-setup"

echo "=== Step 1: Fix manifest (state 0=off, state 1=on) ==="
python3 -c "
import json
f = '$SD_PLUGIN/manifest.json'
m = json.load(open(f))
s = m['Actions'][0]['States']
s[0] = {'Image': 'icons/action-off', 'Name': 'Off'}
s[1] = {'Image': 'icons/action-on', 'Name': 'On'}
json.dump(m, open(f, 'w'), indent=4)
print('  manifest.json fixed')
"

echo "=== Step 2: Patch command_queue.py with /status endpoint ==="
python3 -c "
import os
f = '$KVM/scripts/command_queue.py'
code = open(f).read()
if '/status/' in code:
    print('  already patched')
else:
    # Add STATUS dict
    code = code.replace(
        'QUEUES = defaultdict(list)',
        'QUEUES = defaultdict(list)\nSTATUS = {}')
    # Add status_report POST endpoint before the do_POST 404
    old = '''        else:\n            self.send_response(404)\n            self.end_headers()'''
    # We need to be careful - there are two 'else: 404' blocks (one in GET, one in POST)
    # Add GET /status/<machine> endpoint
    code = code.replace(
        '        elif self.path == \"/ping\":',
        '''        elif self.path.startswith(\"/status/\"):
            machine = self.path.split(\"/status/\")[1]
            with LOCK:
                status = STATUS.get(machine, {})
            self.send_response(200)
            self.send_header(\"Content-Type\", \"application/json\")
            self.end_headers()
            self.wfile.write(json.dumps(status).encode())
        elif self.path == \"/ping\":''')
    # Add POST /status_report endpoint
    code = code.replace(
        '            print(f\"  Queued: {action} for {machine}\")',
        '''            print(f\"  Queued: {action} for {machine}\")
        elif self.path == \"/status_report\":
            length = int(self.headers.get(\"Content-Length\", 0))
            body = json.loads(self.rfile.read(length))
            machine = body.get(\"machine\", \"\")
            with LOCK:
                STATUS[machine] = body.get(\"status\", {})
            self.send_response(200)
            self.send_header(\"Content-Type\", \"application/json\")
            self.end_headers()
            self.wfile.write(json.dumps({\"ok\": True}).encode())''')
    open(f, 'w').write(code)
    print('  command_queue.py patched')
"

echo "=== Step 3: Patch poll_commands.py with status reporting ==="
python3 -c "
import os
f = '$KVM/scripts/poll_commands.py'
code = open(f).read()
if 'report_status' in code:
    print('  already patched')
else:
    status_fn = '''
def report_status(mac_ip, port, machine):
    pid_file = os.path.join(os.environ.get(\"TEMP\", \"/tmp\"), \"mouse_jiggler.pid\")
    running = False
    if os.path.exists(pid_file):
        with open(pid_file) as fp:
            pid = fp.read().strip()
        try:
            if PLATFORM == \"Windows\":
                ok, out = run([\"tasklist\", \"/FI\", f\"PID eq {pid}\", \"/NH\"])
                running = pid in out
            else:
                os.kill(int(pid), 0)
                running = True
        except Exception:
            running = False
    url = f\"http://{mac_ip}:{port}/status_report\"
    try:
        data = json.dumps({\"machine\": machine, \"status\": {\"jiggler_running\": running}}).encode()
        req = urllib.request.Request(url, data=data, headers={\"Content-Type\": \"application/json\"})
        urllib.request.urlopen(req, timeout=3)
    except Exception:
        pass

'''
    code = code.replace('\\ndef main():', status_fn + '\\ndef main():')
    code = code.replace(
        '        time.sleep(args.interval)',
        '        report_status(args.mac_ip, args.port, args.machine)\\n        time.sleep(args.interval)')
    open(f, 'w').write(code)
    print('  poll_commands.py patched')
"

echo "=== Step 4: Replace plugin.js with fixed version ==="
cat > "$SD_PLUGIN/bin/plugin.js" << 'PLUGINEOF'
"use strict";
const WebSocket = require("./node_modules/ws");
const { exec, spawn } = require("child_process");
const fs = require("fs");
const path = require("path");
const os = require("os");
const http = require("http");

const IS_WIN = os.platform() === "win32";
const LOG = IS_WIN ? path.join(os.tmpdir(), "jiggler4.log") : "/tmp/jiggler4.log";
const PID_FILE = IS_WIN ? path.join(os.tmpdir(), "mouse_jiggler.pid") : "/tmp/mouse_jiggler.pid";
const log = (m) => fs.appendFileSync(LOG, new Date().toISOString().slice(11, 19) + " " + m + "\n");
const PLUGIN_DIR = path.resolve(__dirname, "..");

const WIN_PS1 = path.join(os.tmpdir(), "mouse_jiggler.ps1");
if (IS_WIN) {
  fs.writeFileSync(WIN_PS1,
`Add-Type -AssemblyName System.Windows.Forms
Add-Type -AssemblyName System.Drawing
while ($true) {
  $pos = [System.Windows.Forms.Cursor]::Position
  [System.Windows.Forms.Cursor]::Position = [System.Drawing.Point]::new($pos.X + 60, $pos.Y)
  Start-Sleep -Milliseconds 100
  [System.Windows.Forms.Cursor]::Position = $pos
  Start-Sleep -Seconds 10
}
`);
}

const QUEUE_PORT = 9002;
const STATUS_POLL_INTERVAL = 5000;
const contextSettings = {};
const activeContexts = {};
const state = { wpcOn: false, localOn: false };
let statusCheckPending = false;

const args = process.argv;
const port = args[args.indexOf("-port") + 1];
const pluginUUID = args[args.indexOf("-pluginUUID") + 1];
const registerEvent = args[args.indexOf("-registerEvent") + 1];
const ws = new WebSocket(`ws://localhost:${port}`);

ws.on("open", () => {
  ws.send(JSON.stringify({ event: registerEvent, uuid: pluginUUID }));
  pollWpcStatus();
  setInterval(pollWpcStatus, STATUS_POLL_INTERVAL);
});

function queueRemoteAction(machine, action, cb) {
  const body = JSON.stringify({ machine, action });
  const req = http.request({
    hostname: "localhost", port: QUEUE_PORT, path: "/queue", method: "POST",
    headers: { "Content-Type": "application/json", "Content-Length": Buffer.byteLength(body) },
    timeout: 5000,
  }, (res) => { res.resume(); log("queued " + action); if (cb) cb(true); });
  req.on("error", (e) => { log("queue error: " + e.message); if (cb) cb(false); });
  req.write(body); req.end();
}

function remoteJigglerToggle(host, cb) {
  const machine = host === "192.168.1.101" ? "pc2" : "pc3";
  queueRemoteAction(machine, "jiggler_toggle", cb);
}

function pollWpcStatus() {
  if (statusCheckPending) return;
  statusCheckPending = true;
  const req = http.request({
    hostname: "localhost", port: QUEUE_PORT, path: "/status/pc2", method: "GET", timeout: 3000,
  }, (res) => {
    let data = "";
    res.on("data", (chunk) => data += chunk);
    res.on("end", () => {
      statusCheckPending = false;
      try {
        const result = JSON.parse(data);
        if (typeof result.jiggler_running === "boolean") {
          const wasOn = state.wpcOn;
          state.wpcOn = result.jiggler_running;
          if (wasOn !== state.wpcOn) {
            log("pollStatus: wpcOn " + wasOn + " -> " + state.wpcOn);
            syncAllContexts();
          }
        }
      } catch (e) { /* status endpoint not ready yet */ }
    });
  });
  req.on("error", () => { statusCheckPending = false; });
  req.end();
}

function broadcastState() {
  ws.send(JSON.stringify({
    event: "setGlobalSettings", context: pluginUUID,
    payload: { wpcOn: state.wpcOn, localOn: state.localOn },
  }));
  syncAllContexts();
}

function syncAllContexts() {
  for (const [ctx, info] of Object.entries(activeContexts)) {
    const isOn = info.isRemote ? state.wpcOn : state.localOn;
    setIcon(ctx, isOn);
  }
}

ws.on("message", (data) => {
  const msg = JSON.parse(data);
  switch (msg.event) {
    case "willAppear": {
      const settings = (msg.payload && msg.payload.settings) || {};
      contextSettings[msg.context] = settings;
      const isRemote = !!(settings.remoteHost);
      activeContexts[msg.context] = { isRemote };
      const isOn = isRemote ? state.wpcOn : state.localOn;
      setIcon(msg.context, isOn);
      pollWpcStatus();
      break;
    }
    case "willDisappear": {
      delete activeContexts[msg.context];
      delete contextSettings[msg.context];
      break;
    }
    case "didReceiveGlobalSettings": {
      const gs = (msg.payload && msg.payload.settings) || {};
      state.localOn = !!gs.localOn;
      // wpcOn comes ONLY from live polling, not stale saved state
      syncAllContexts();
      break;
    }
    case "keyDown": {
      const settings = contextSettings[msg.context] || {};
      const host = settings.remoteHost;
      if (host) {
        const newState = !state.wpcOn;
        state.wpcOn = newState;
        const pressedCtx = msg.context;
        broadcastState();
        setTimeout(() => {
          ws.send(JSON.stringify({ event: "setState", context: pressedCtx, payload: { state: newState ? 1 : 0 } }));
        }, 200);
        remoteJigglerToggle(host, (ok) => {
          if (!ok) { state.wpcOn = !newState; broadcastState(); }
          // After toggle, poll status to confirm actual state
          setTimeout(pollWpcStatus, 3000);
        });
      } else {
        isJigglerRunning((running) => {
          if (running) {
            stopJiggler(() => { state.localOn = false; broadcastState(); });
          } else {
            startJiggler(() => {
              setTimeout(() => {
                isJigglerRunning((nowRunning) => { state.localOn = nowRunning; broadcastState(); });
              }, 600);
            });
          }
        });
      }
      break;
    }
    case "didReceiveSettings": {
      const settings = (msg.payload && msg.payload.settings) || {};
      contextSettings[msg.context] = settings;
      if (activeContexts[msg.context]) {
        activeContexts[msg.context].isRemote = !!(settings.remoteHost);
      }
      break;
    }
  }
});

function startJiggler(cb) {
  if (IS_WIN) {
    const proc = spawn("powershell.exe",
      ["-WindowStyle", "Hidden", "-ExecutionPolicy", "Bypass", "-File", WIN_PS1],
      { detached: true, stdio: "ignore" });
    proc.unref();
    fs.writeFileSync(PID_FILE, String(proc.pid));
    if (cb) cb();
  } else {
    exec("/usr/local/bin/jiggler_toggle.sh", () => { if (cb) cb(); });
  }
}

function stopJiggler(cb) {
  if (IS_WIN) {
    const pid = readPid();
    if (pid) {
      exec(`taskkill /F /T /PID ${pid}`, () => {
        try { fs.unlinkSync(PID_FILE); } catch (_) {}
        if (cb) cb();
      });
    } else { if (cb) cb(); }
  } else {
    exec("/usr/local/bin/jiggler_toggle.sh", () => { if (cb) cb(); });
  }
}

function readPid() {
  try { return parseInt(fs.readFileSync(PID_FILE, "utf8").trim(), 10); }
  catch (_) { return null; }
}

function isJigglerRunning(cb) {
  if (IS_WIN) {
    const pid = readPid();
    if (!pid) { cb(false); return; }
    exec(`tasklist /FI "PID eq ${pid}" /NH`, (err, stdout) => {
      cb((stdout || "").includes(String(pid)));
    });
  } else {
    exec('PID=$(cat /tmp/mouse_jiggler.pid 2>/dev/null); [ -n "$PID" ] && kill -0 $PID 2>/dev/null && echo yes || echo no',
      (err, stdout) => { cb((stdout || "").trim() === "yes"); });
  }
}

function setIcon(context, isOn) {
  ws.send(
    JSON.stringify({ event: "setState", context, payload: { state: isOn ? 1 : 0 } }),
    (err) => { if (err) log("setState error: " + err); });
}

ws.on("error", (e) => log("WS error: " + e.message));
PLUGINEOF

echo "=== Step 5: Restart command queue ==="
# Kill old command queue and restart
pkill -f "command_queue.py --port 9002" 2>/dev/null || true
sleep 1
nohup python3 "$KVM/scripts/command_queue.py" --port 9002 > /tmp/kvm-queue.log 2>&1 &
echo "  command queue restarted (pid $!)"

echo "=== Step 6: Restart Stream Deck ==="
pkill -f "MacOS/Stream Deck" 2>/dev/null || true
sleep 3
open -a "Elgato Stream Deck"
sleep 5

echo ""
echo "=== ALL DONE ==="
echo "The plugin now polls the Work PC jiggler status every 5 seconds."
echo "The button will auto-sync to the real state."
echo ""
echo "NEXT: Restart the KVM Poller on the Work PC so it picks up the status reporting patch."
echo "  On Windows PowerShell run: Stop-ScheduledTask 'KVM Poller'; Start-ScheduledTask 'KVM Poller'"
