"use strict";
const WebSocket = require("./node_modules/ws");
const { exec, spawn } = require("child_process");
const fs = require("fs");
const path = require("path");
const os = require("os");
const http = require("http");

const IS_WIN = os.platform() === "win32";
const LOG = IS_WIN
  ? path.join(os.tmpdir(), "jiggler4.log")
  : "/tmp/jiggler4.log";
const PID_FILE = IS_WIN
  ? path.join(os.tmpdir(), "mouse_jiggler.pid")
  : "/tmp/mouse_jiggler.pid";

const log = (m) =>
  fs.appendFileSync(LOG, new Date().toISOString().slice(11, 19) + " " + m + "\n");

const PLUGIN_DIR = path.resolve(__dirname, "..");

// Write the Windows PowerShell jiggler script to temp dir on startup
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
const STATUS_POLL_INTERVAL = 5000; // Check WPC status every 5 seconds

// Per-context settings store (maps context -> { remoteHost })
const contextSettings = {};
// Track all visible contexts: context -> { isRemote }
const activeContexts = {};
// In-memory state
const state = { wpcOn: false, localOn: false };
// Track if we have pending status check
let statusCheckPending = false;

const args = process.argv;
const port = args[args.indexOf("-port") + 1];
const pluginUUID = args[args.indexOf("-pluginUUID") + 1];
const registerEvent = args[args.indexOf("-registerEvent") + 1];

const ws = new WebSocket(`ws://localhost:${port}`);

ws.on("open", () => {
  ws.send(JSON.stringify({ event: registerEvent, uuid: pluginUUID }));
  // Start polling WPC jiggler status
  pollWpcStatus();
  setInterval(pollWpcStatus, STATUS_POLL_INTERVAL);
});

// ── Remote HTTP helpers ──────────────────────────────────────────────

function queueRemoteAction(machine, action, cb) {
  const body = JSON.stringify({ machine, action });
  const req = http.request({
    hostname: "localhost",
    port: QUEUE_PORT,
    path: "/queue",
    method: "POST",
    headers: { "Content-Type": "application/json", "Content-Length": Buffer.byteLength(body) },
    timeout: 5000,
  }, (res) => {
    res.resume();
    log("queued " + action + " for " + machine);
    if (cb) cb(true);
  });
  req.on("error", (e) => {
    log("queue error: " + e.message);
    if (cb) cb(false);
  });
  req.write(body);
  req.end();
}

function remoteJigglerToggle(host, cb) {
  const machine = host === "192.168.1.101" ? "pc2" : "pc3";
  queueRemoteAction(machine, "jiggler_toggle", cb);
}

// ── Poll WPC jiggler status directly ────────────────────────────────
// Instead of trusting saved state, we ask the command queue to check
// the actual jiggler_status on the Work PC. The response comes back
// via a special status endpoint we add, OR we queue a status check
// and poll for the result.
//
// Simpler approach: HTTP GET to a status file the poller updates.
// Simplest approach: just check if we can reach the queue and
// queue a status request, then read the response.

function pollWpcStatus() {
  if (statusCheckPending) return;
  statusCheckPending = true;

  // Query the command queue's status endpoint
  const req = http.request({
    hostname: "localhost",
    port: QUEUE_PORT,
    path: "/status/pc2",
    method: "GET",
    timeout: 3000,
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
            log("pollWpcStatus: wpcOn changed " + wasOn + " -> " + state.wpcOn);
            syncAllContexts();
            // Save to global settings
            broadcastState();
          }
        }
      } catch (e) {
        // Status endpoint not available, that's ok
      }
    });
  });
  req.on("error", () => { statusCheckPending = false; });
  req.end();
}

// ── State broadcast ──────────────────────────────────────────────────

function broadcastState() {
  ws.send(JSON.stringify({
    event: "setGlobalSettings",
    context: pluginUUID,
    payload: { wpcOn: state.wpcOn, localOn: state.localOn },
  }));
  syncAllContexts();
}

function syncAllContexts() {
  const ctxList = Object.keys(activeContexts);
  log("syncAll contexts=" + ctxList.length + " wpcOn=" + state.wpcOn + " localOn=" + state.localOn);
  for (const [ctx, info] of Object.entries(activeContexts)) {
    const isOn = info.isRemote ? state.wpcOn : state.localOn;
    setIcon(ctx, isOn);
  }
}

// ── WebSocket message handler ────────────────────────────────────────

ws.on("message", (data) => {
  const msg = JSON.parse(data);

  switch (msg.event) {
    case "willAppear": {
      const settings = (msg.payload && msg.payload.settings) || {};
      contextSettings[msg.context] = settings;
      const isRemote = !!(settings.remoteHost);
      activeContexts[msg.context] = { isRemote };
      log("willAppear ctx=" + msg.context.slice(0, 8) + " remote=" + isRemote);
      // Immediately sync icon to current known state
      const isOn = isRemote ? state.wpcOn : state.localOn;
      setIcon(msg.context, isOn);
      // Also trigger a fresh status poll
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
      // Only trust localOn from saved settings; wpcOn comes from live polling
      state.localOn = !!gs.localOn;
      log("didReceiveGlobalSettings localOn=" + state.localOn + " (wpcOn from poll only)");
      syncAllContexts();
      break;
    }

    case "keyDown": {
      log("keyDown ctx=" + msg.context.slice(0, 8));
      const settings = contextSettings[msg.context] || {};
      const host = settings.remoteHost;

      if (host) {
        // Remote toggle — flip optimistically, then broadcast
        const newState = !state.wpcOn;
        state.wpcOn = newState;
        const pressedCtx = msg.context;
        broadcastState();

        // Re-assert state after SD's press animation
        setTimeout(() => {
          ws.send(JSON.stringify({ event: "setState", context: pressedCtx, payload: { state: newState ? 1 : 0 } }));
        }, 200);

        remoteJigglerToggle(host, (ok) => {
          if (!ok) {
            state.wpcOn = !newState;
            broadcastState();
            log("queue failed, reverted wpcOn=" + state.wpcOn);
          }
        });
      } else {
        isJigglerRunning((running) => {
          if (running) {
            stopJiggler(() => {
              state.localOn = false;
              broadcastState();
            });
          } else {
            startJiggler(() => {
              setTimeout(() => {
                isJigglerRunning((nowRunning) => {
                  log("after start running=" + nowRunning);
                  state.localOn = nowRunning;
                  broadcastState();
                });
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
      const isRemote = !!(settings.remoteHost);
      if (activeContexts[msg.context]) {
        activeContexts[msg.context].isRemote = isRemote;
      }
      log("didReceiveSettings ctx=" + msg.context.slice(0, 8) + " host=" + (settings.remoteHost || "local"));
      break;
    }
  }
});

// ── Local jiggler control ────────────────────────────────────────────

function startJiggler(cb) {
  if (IS_WIN) {
    const proc = spawn(
      "powershell.exe",
      ["-WindowStyle", "Hidden", "-ExecutionPolicy", "Bypass", "-File", WIN_PS1],
      { detached: true, stdio: "ignore" },
    );
    proc.unref();
    fs.writeFileSync(PID_FILE, String(proc.pid));
    log("started win jiggler pid=" + proc.pid);
    if (cb) cb();
  } else {
    exec("/usr/local/bin/jiggler_toggle.sh", (err, out) => {
      log("mac start err=" + err + " out=" + (out || "").trim());
      if (cb) cb();
    });
  }
}

function stopJiggler(cb) {
  if (IS_WIN) {
    const pid = readPid();
    if (pid) {
      exec(`taskkill /F /T /PID ${pid}`, (err) => {
        log("killed pid=" + pid + " err=" + err);
        try { fs.unlinkSync(PID_FILE); } catch (_) {}
        if (cb) cb();
      });
    } else {
      if (cb) cb();
    }
  } else {
    exec("/usr/local/bin/jiggler_toggle.sh", (err, out) => {
      log("mac stop err=" + err + " out=" + (out || "").trim());
      if (cb) cb();
    });
  }
}

function readPid() {
  try {
    return parseInt(fs.readFileSync(PID_FILE, "utf8").trim(), 10);
  } catch (_) {
    return null;
  }
}

function isJigglerRunning(cb) {
  if (IS_WIN) {
    const pid = readPid();
    if (!pid) { cb(false); return; }
    exec(`tasklist /FI "PID eq ${pid}" /NH`, (err, stdout) => {
      const alive = (stdout || "").includes(String(pid));
      log("jigglerCheck pid=" + pid + " alive=" + alive);
      cb(alive);
    });
  } else {
    exec(
      'PID=$(cat /tmp/mouse_jiggler.pid 2>/dev/null); [ -n "$PID" ] && kill -0 $PID 2>/dev/null && echo yes || echo no',
      (err, stdout) => {
        cb((stdout || "").trim() === "yes");
      },
    );
  }
}

function setIcon(context, isOn) {
  ws.send(
    JSON.stringify({ event: "setState", context, payload: { state: isOn ? 1 : 0 } }),
    (err) => { if (err) log("setState error: " + err); },
  );
}

ws.on("error", (e) => log("WS error: " + e.message));
