# KVM Setup Guide: 2× Samsung S65UC + 3 Computers + Stream Deck

## Table of Contents

1. [System Overview](#system-overview)
2. [Hardware Inventory](#hardware-inventory)
3. [Physical Connection Map](#physical-connection-map)
4. [Cable Shopping List](#cable-shopping-list)
5. [Software Installation Guide](#software-installation-guide)
6. [Phase 1: DDC/CI Testing (DO THIS FIRST)](#phase-1-ddcci-testing)
7. [Phase 2: Physical Cabling](#phase-2-physical-cabling)
8. [Phase 3: EDID Emulators](#phase-3-edid-emulators)
9. [Phase 4: Software Installation](#phase-4-software-installation)
10. [Phase 5: Input Leap (Keyboard/Mouse Sharing)](#phase-5-input-leap)
11. [Phase 6: Stream Deck Configuration](#phase-6-stream-deck-configuration)
12. [Phase 7: Automation Scripts](#phase-7-automation-scripts)
13. [Phase 8: Final Testing Checklist](#phase-8-final-testing-checklist)
14. [Daily Operation](#daily-operation)
15. [Troubleshooting](#troubleshooting)
16. [Known Risks and Fallback Plans](#known-risks-and-fallback-plans)

---

## System Overview

This setup allows you to control **2 Samsung ultrawide monitors** across **3 computers** using a single **Stream Deck MK.2** button press. One button switches both monitors, keyboard, mouse, and all USB peripherals to the target computer.

### How It Works (High Level)

```
You press a Stream Deck button ("ALL → Work Mac")
    │
    ├─ Step 1: DDC/CI command sent to Left Monitor  → switch to DP input
    ├─ Step 2: DDC/CI command sent to Right Monitor → switch to DP input
    ├─ Step 3: Keyboard shortcut simulated → eKL USB switch moves to Input 2
    │
    └─ Result: Both monitors show Work Mac
              Keyboard/mouse/webcam/Stream Deck all on Work Mac
              Input Leap still running for cross-computer mouse movement
```

### Split Mode

You can also switch monitors independently:
- Left monitor → Personal Mac, Right monitor → Work Mac
- Input Leap provides seamless mouse cursor movement between the two computers
- USB peripherals stay on whichever computer was last selected via the "ALL" buttons

---

## Hardware Inventory

### Computers

| ID | Name | OS | Key Ports |
|----|------|-----|-----------|
| C1 | Personal Mac | macOS (M3 Max) | 3× Thunderbolt 4 (USB-C), 1× HDMI, 1× SD |
| C2 | Work Mac | macOS (M1 Max) | 3× Thunderbolt 4 (USB-C), 1× HDMI, 1× SD |
| C3 | HP EliteBook | Windows 10/11 | Via dock: 2× DP, 1× HDMI, USB-A ports |

### Monitors

| ID | Model | Size | Resolution | Refresh |
|----|-------|------|------------|---------|
| M1 | Samsung ViewFinity S65UC (LS34C650UANXGO) | 34" ultrawide curved | 3440×1440 (UWQHD) | 100Hz |
| M2 | Samsung ViewFinity S65UC (LS34C650UANXGO) | 34" ultrawide curved | 3440×1440 (UWQHD) | 100Hz |

### Samsung S65UC Port Inventory (Per Monitor)

| Port | Count | Version | Notes |
|------|-------|---------|-------|
| USB-C | 1 | DP Alt Mode, 3.2 Gen 1 | Video + data + 90W charging |
| DisplayPort | 1 | 1.2 | HDCP 2.2 |
| HDMI | 2 | 2.0 | HDCP 2.2 |
| USB-B upstream | 1 | 3.0 | For built-in USB hub (non-USB-C connections) |
| USB-A downstream | 3 | 3.2 Gen 1 | Built-in hub for peripherals |
| RJ45 Ethernet | 1 | Gigabit | Wired network pass-through |
| Audio out | 1 | 3.5mm | Headphone jack |

### Peripherals

| Device | Model | Connection |
|--------|-------|------------|
| Stream Deck | Elgato MK.2 (15 keys) | USB-A (through eKL switch) |
| USB Switch | eKL (3-input, 1-output) | USB-A to each computer |
| EDID Emulators | Generic HDMI/DP | On inactive video cables (4 needed) |

---

## Physical Connection Map

```
                    ┌──────────────────────────────────────┐
                    │         LEFT Samsung S65UC (M1)       │
                    │                                      │
                    │  USB-C  ◄── Personal Mac (C1)        │
                    │  DP 1.2 ◄── Work Mac (C2)            │
                    │  HDMI 1 ◄── HP Dock (C3)             │
                    │  HDMI 2     (unused)                  │
                    └──────────────────────────────────────┘

                    ┌──────────────────────────────────────┐
                    │        RIGHT Samsung S65UC (M2)       │
                    │                                      │
                    │  USB-C  ◄── Personal Mac (C1)        │
                    │  DP 1.2 ◄── Work Mac (C2)            │
                    │  HDMI 1 ◄── HP Dock (C3)             │
                    │  HDMI 2     (unused)                  │
                    └──────────────────────────────────────┘

┌────────────────────────────────────────────────────────────────────┐
│                      eKL USB 3.0 Switch                            │
│                                                                    │
│  OUTPUT ──► USB Hub ──► Keyboard, Mouse, Webcam, Stream Deck,     │
│                         External drives, other peripherals         │
│                                                                    │
│  INPUT 1 ◄── Personal Mac (C1)  [Hotkey: ScrollLock×2 + 1]       │
│  INPUT 2 ◄── Work Mac (C2)     [Hotkey: ScrollLock×2 + 2]       │
│  INPUT 3 ◄── HP Dock (C3)      [Hotkey: ScrollLock×2 + 3]       │
└────────────────────────────────────────────────────────────────────┘

┌────────────────────────────────────────────────────────────────────┐
│                   Input Leap (Network KVM)                         │
│                                                                    │
│  Server: Personal Mac (C1) ── static IP on local network          │
│     │                                                              │
│     ├── Client: Work Mac (C2)                                     │
│     └── Client: HP EliteBook (C3)                                 │
│                                                                    │
│  Enables seamless mouse movement across computers (split mode)    │
└────────────────────────────────────────────────────────────────────┘
```

---

## Cable Shopping List

### Video Cables (6 total)

| Qty | Cable | From | To | Notes |
|-----|-------|------|----|-------|
| 2 | USB-C to USB-C (Thunderbolt 4 / DP Alt Mode) | Personal Mac | Each monitor's USB-C port | Must support video; 6ft recommended |
| 2 | USB-C to DisplayPort 1.2 | Work Mac | Each monitor's DP port | 6ft recommended |
| 2 | DisplayPort to HDMI (or HDMI to HDMI if dock has HDMI) | HP Dock DP output | Each monitor's HDMI 1 port | Check dock output type |

### USB Cables (3 total for eKL switch)

| Qty | Cable | From | To |
|-----|-------|------|----|
| 1 | USB-C to USB-A (or USB-A to USB-A) | Personal Mac | eKL Input 1 |
| 1 | USB-C to USB-A (or USB-A to USB-A) | Work Mac | eKL Input 2 |
| 1 | USB-A to USB-A | HP Dock | eKL Input 3 |

### EDID Emulators (4 total)

| Qty | Type | Purpose |
|-----|------|---------|
| 2 | DisplayPort EDID emulator | On Work Mac's DP cables (inactive when Personal Mac or HP is active) |
| 2 | HDMI EDID emulator | On HP Dock's HDMI cables (inactive when Personal Mac or Work Mac is active) |

> **Note:** The Personal Mac's USB-C connections may not need EDID emulators because macOS + Thunderbolt handles display disconnection better. Test first — add emulators only if windows rearrange when switching away.

---

## Software Installation Guide

### Personal Mac (C1 — M3 Max) — INPUT LEAP SERVER

```bash
# 1. Lunar (DDC/CI monitor control — GUI + scripting)
brew install --cask lunar

# 2. m1ddc (command-line DDC/CI tool for automation scripts)
brew install waydabber/m1ddc/m1ddc

# 3. Input Leap (keyboard/mouse sharing — SERVER mode)
brew install --cask input-leap

# 4. Elgato Stream Deck
# Download from: https://www.elgato.com/downloads
# Or: brew install --cask elgato-stream-deck

# 5. Verify installations
m1ddc --help
```

### Work Mac (C2 — M1 Max) — INPUT LEAP CLIENT

```bash
# 1. Lunar (DDC/CI monitor control)
brew install --cask lunar

# 2. m1ddc (command-line DDC/CI tool)
brew install waydabber/m1ddc/m1ddc

# 3. Input Leap (keyboard/mouse sharing — CLIENT mode)
brew install --cask input-leap

# 4. Elgato Stream Deck
# Download from: https://www.elgato.com/downloads
# Or: brew install --cask elgato-stream-deck
```

### HP EliteBook (C3 — Windows 10/11) — INPUT LEAP CLIENT

```
1. ControlMyMonitor (NirSoft — DDC/CI monitor control)
   Download from: https://www.nirsoft.net/utils/control_my_monitor.html
   No installation needed — portable executable

2. Input Leap (keyboard/mouse sharing — CLIENT mode)
   Download from: https://github.com/input-leap/input-leap/releases
   Install the Windows .exe

3. Elgato Stream Deck
   Download from: https://www.elgato.com/downloads
   Install the Windows version
```

### Software Summary Table

| Software | Personal Mac | Work Mac | HP EliteBook | Purpose |
|----------|:---:|:---:|:---:|---------|
| Lunar | YES | YES | — | DDC/CI GUI + hotkeys (macOS) |
| m1ddc | YES | YES | — | DDC/CI CLI for scripts (macOS) |
| ControlMyMonitor | — | — | YES | DDC/CI CLI for scripts (Windows) |
| Input Leap (server) | YES | — | — | KVM server |
| Input Leap (client) | — | YES | YES | KVM client |
| Elgato Stream Deck | YES | YES | YES | Button control |

---

## Phase 1: DDC/CI Testing (DO THIS FIRST)

> **This is the single most critical step.** Samsung monitors have inconsistent DDC/CI support. If input switching doesn't work via DDC/CI, we need a fallback plan before proceeding with the rest of the setup.

### Step 1.1: Enable DDC/CI on Both Samsung Monitors

1. Press the monitor's menu/joystick button to open OSD
2. Navigate to **System** → **DDC/CI**
3. Set to **On**
4. Also check: **System** → **Auto Source Switch+** → set to **Off** (prevents the monitor from auto-switching and fighting your DDC commands)
5. Repeat for both monitors

### Step 1.2: Test from Personal Mac (m1ddc)

Connect Personal Mac to one Samsung monitor via USB-C, then:

```bash
# Install m1ddc
brew install waydabber/m1ddc/m1ddc

# List connected displays (note the display IDs)
m1ddc display list

# Read current input source value
m1ddc get input

# Test: Switch to DisplayPort (try value 15)
m1ddc set input 15

# Test: Switch to HDMI 1 (try value 17)
m1ddc set input 17

# Test: Switch to HDMI 2 (try value 18)
m1ddc set input 18

# Test: Switch back to USB-C (try value 16)
m1ddc set input 16
```

> **Important:** DDC/CI input source values vary by manufacturer. Common values:
> - 1 = VGA
> - 3 = DVI
> - 15 = DisplayPort
> - 16 = USB-C (sometimes)
> - 17 = HDMI 1
> - 18 = HDMI 2
>
> If these don't work, try values 1–20 systematically with `m1ddc set input N`

### Step 1.3: Record Results

Document what works for each monitor:

```
Left Samsung (M1):
  - Current input value when on USB-C: ___
  - Current input value when on DP: ___
  - Current input value when on HDMI 1: ___
  - Switch to USB-C command works: YES / NO
  - Switch to DP command works: YES / NO
  - Switch to HDMI 1 command works: YES / NO
  - Display ID from m1ddc: ___

Right Samsung (M2):
  - Current input value when on USB-C: ___
  - Current input value when on DP: ___
  - Current input value when on HDMI 1: ___
  - Switch to USB-C command works: YES / NO
  - Switch to DP command works: YES / NO
  - Switch to HDMI 1 command works: YES / NO
  - Display ID from m1ddc: ___
```

### Step 1.4: If DDC/CI Input Switching FAILS

See [Known Risks and Fallback Plans](#known-risks-and-fallback-plans) section.

---

## Phase 2: Physical Cabling

### Step 2.1: Personal Mac Connections (2 cables)

1. Connect USB-C cable from **Personal Mac Thunderbolt port 1** → **Left Samsung USB-C port**
2. Connect USB-C cable from **Personal Mac Thunderbolt port 2** → **Right Samsung USB-C port**
3. Verify: Both monitors light up and show Personal Mac desktop
4. In macOS System Settings → Displays, arrange Left and Right to match physical positions

### Step 2.2: Work Mac Connections (2 cables)

1. Connect USB-C to DP cable from **Work Mac Thunderbolt port 1** → **Left Samsung DP port**
2. Connect USB-C to DP cable from **Work Mac Thunderbolt port 2** → **Right Samsung DP port**
3. Manually switch both monitors to DP input via OSD
4. Verify: Both monitors show Work Mac desktop

### Step 2.3: HP EliteBook Connections (2 cables)

1. Connect cable from **HP Dock DP output 1** → **Left Samsung HDMI 1** (using DP-to-HDMI cable or adapter)
2. Connect cable from **HP Dock DP output 2** → **Right Samsung HDMI 1** (using DP-to-HDMI cable or adapter)
3. Manually switch both monitors to HDMI 1 input via OSD
4. Verify: Both monitors show HP EliteBook desktop

### Step 2.4: eKL USB Switch

1. Connect **eKL OUTPUT** → USB Hub → Keyboard, Mouse, Webcam, Stream Deck, other peripherals
2. Connect **eKL INPUT 1** → Personal Mac USB-A (or USB-C with adapter)
3. Connect **eKL INPUT 2** → Work Mac USB-A (or USB-C with adapter)
4. Connect **eKL INPUT 3** → HP Dock USB-A
5. Test: Press eKL physical button to cycle between inputs
6. Verify: Keyboard/mouse work on each computer when selected

---

## Phase 3: EDID Emulators

EDID emulators plug into the video cables that become "inactive" when you switch monitors to a different input. They trick the computer into thinking a display is still connected, preventing:
- Window rearrangement on macOS/Windows
- Resolution resets
- Display profile loss

### Where to Install EDID Emulators

| Cable | EDID Needed? | Reason |
|-------|:---:|--------|
| Personal Mac → Left Samsung (USB-C) | Test first | macOS + Thunderbolt may handle disconnection gracefully |
| Personal Mac → Right Samsung (USB-C) | Test first | Same as above |
| Work Mac → Left Samsung (DP) | YES | DP disconnect causes window rearrangement |
| Work Mac → Right Samsung (DP) | YES | Same as above |
| HP Dock → Left Samsung (HDMI) | YES | Windows will rearrange windows |
| HP Dock → Right Samsung (HDMI) | YES | Same as above |

> **Purchase:** At minimum 4× EDID emulators (2× DP, 2× HDMI). If testing reveals Personal Mac also needs them, buy 2 more USB-C EDID emulators (these are rare — you may need USB-C to HDMI + HDMI EDID emulator inline).

### How EDID Emulators Work

1. Connect your regular video cable to the computer
2. Plug the EDID emulator inline on the cable (between the cable and the monitor)
3. The emulator stores the monitor's EDID profile
4. When the monitor switches away, the emulator continues responding as if the monitor is still there

---

## Phase 4: Software Installation

Follow the [Software Installation Guide](#software-installation-guide) section above for each computer.

### Post-Installation Configuration

#### Lunar (Both Macs)

1. Open Lunar
2. Grant Accessibility permissions when prompted
3. Verify both monitors appear in Lunar's menu bar dropdown
4. Test DDC control: adjust brightness on each monitor via Lunar slider
5. Go to Lunar Preferences → Hotkeys and configure:
   - **Switch to USB-C input:** ⌘⌥⌃1 (all monitors)
   - **Switch to DP input:** ⌘⌥⌃2 (all monitors)
   - **Switch to HDMI 1 input:** ⌘⌥⌃3 (all monitors)

#### ControlMyMonitor (HP EliteBook)

1. Extract ControlMyMonitor.exe to a folder (e.g., `C:\Tools\ControlMyMonitor`)
2. Run it — it will list all connected monitors and their DDC/CI capabilities
3. Find VCP Code **0x60** (Input Source) in the list
4. Note the current value and test setting it to different values
5. Create shortcut scripts (see Phase 7)

---

## Phase 5: Input Leap

### Server Setup (Personal Mac)

1. Open Input Leap
2. Select **Server** mode
3. Go to **Server Configuration** → **Screens and Links**
4. Create three screens:
   - `personal-mac` (center)
   - `work-mac` (linked to the right of personal-mac)
   - `hp-elitebook` (linked to the right of work-mac)
5. Set a static IP for Personal Mac on your router (or note the current IP)
6. Start the server

> **Screen layout should match your physical monitor arrangement.** Since you have 2 monitors side by side, and sometimes split between computers, configure Input Leap screen edges to match where you want the cursor to cross over.

### Client Setup (Work Mac)

1. Open Input Leap
2. Select **Client** mode
3. Enter the Personal Mac's IP address as the server
4. Set screen name to `work-mac`
5. Start the client
6. Test: Move mouse from Personal Mac to the right — it should appear on Work Mac

### Client Setup (HP EliteBook)

1. Open Input Leap
2. Select **Client** mode
3. Enter the Personal Mac's IP address
4. Set screen name to `hp-elitebook`
5. Start the client
6. Test: Move mouse to HP EliteBook's screen position

### Input Leap Notes

- Input Leap is the actively maintained fork of Barrier (which is unmaintained since 2021)
- It's compatible with existing Barrier configurations
- Server must be running for keyboard/mouse sharing to work
- All computers must be on the same network
- Input Leap handles keyboard AND mouse — it complements (doesn't replace) the eKL USB switch
- The eKL switch routes physical USB devices (webcam, Stream Deck, external drives); Input Leap routes keyboard/mouse input over the network

---

## Phase 6: Stream Deck Configuration

### Connection

The Stream Deck MK.2 connects through the **eKL USB switch** so it follows the active computer. The Elgato Stream Deck software must be installed on **all 3 computers** with **identical button profiles**.

### Button Layout (15 Keys)

```
┌───────────┬───────────┬───────────┬───────────┬───────────┐
│  ALL →    │  ALL →    │  ALL →    │           │           │
│ Personal  │   Work    │    HP     │  (spare)  │  (spare)  │
│   Mac     │   Mac     │ EliteBook │           │           │
├───────────┼───────────┼───────────┼───────────┼───────────┤
│  LEFT →   │  LEFT →   │  LEFT →   │           │           │
│ Personal  │   Work    │    HP     │  (spare)  │  (spare)  │
│   Mac     │   Mac     │ EliteBook │           │           │
├───────────┼───────────┼───────────┼───────────┼───────────┤
│ RIGHT →   │ RIGHT →   │ RIGHT →   │  USB →    │  USB →    │
│ Personal  │   Work    │    HP     │   Next    │   Prev    │
│   Mac     │   Mac     │ EliteBook │           │           │
└───────────┴───────────┴───────────┴───────────┴───────────┘
```

### Button Types

Each button uses the **Multi-Action** type in Stream Deck software:

#### "ALL → Personal Mac" Multi-Action (Mac version):

```
Action 1: System → Open (run script: ~/scripts/kvm/switch-all-personal.sh)
Action 2: Delay 1000ms
```

#### "ALL → Personal Mac" Multi-Action (Windows version):

```
Action 1: System → Open (run script: C:\Scripts\kvm\switch-all-personal.bat)
Action 2: Delay 1000ms
```

#### Individual monitor buttons ("LEFT → Work Mac"):

```
Action 1: System → Open (run script: switch-left-work.sh or .bat)
```

> **Note:** The scripts are defined in Phase 7 below.

### Profile Sync

To keep all 3 computers in sync:
1. Configure the profile on one computer first
2. Export the profile from Elgato Stream Deck software
3. Copy the profile to the other two computers
4. Import on each

---

## Phase 7: Automation Scripts

### macOS Scripts (Personal Mac and Work Mac)

Create a directory for KVM scripts:

```bash
mkdir -p ~/scripts/kvm
```

#### ~/scripts/kvm/switch-all-personal.sh

```bash
#!/bin/bash
# Switch ALL monitors + USB to Personal Mac

# DDC/CI input values (REPLACE WITH YOUR TESTED VALUES from Phase 1)
USB_C_INPUT=16    # USB-C input value for Samsung S65UC
LEFT_DISPLAY=1    # m1ddc display ID for Left Samsung
RIGHT_DISPLAY=2   # m1ddc display ID for Right Samsung

# Switch both monitors to USB-C (Personal Mac)
m1ddc set input $USB_C_INPUT -d $LEFT_DISPLAY &
m1ddc set input $USB_C_INPUT -d $RIGHT_DISPLAY &
wait

# Wait for monitors to switch
sleep 0.5

# Trigger eKL USB switch to Input 1 (Personal Mac)
# Simulates: Scroll Lock, Scroll Lock, 1
osascript -e '
tell application "System Events"
    key code 107
    delay 0.1
    key code 107
    delay 0.1
    key code 18
end tell
'
```

#### ~/scripts/kvm/switch-all-work.sh

```bash
#!/bin/bash
# Switch ALL monitors + USB to Work Mac

DP_INPUT=15       # DisplayPort input value for Samsung S65UC
LEFT_DISPLAY=1
RIGHT_DISPLAY=2

m1ddc set input $DP_INPUT -d $LEFT_DISPLAY &
m1ddc set input $DP_INPUT -d $RIGHT_DISPLAY &
wait

sleep 0.5

# Trigger eKL USB switch to Input 2 (Work Mac)
osascript -e '
tell application "System Events"
    key code 107
    delay 0.1
    key code 107
    delay 0.1
    key code 19
end tell
'
```

#### ~/scripts/kvm/switch-all-hp.sh

```bash
#!/bin/bash
# Switch ALL monitors + USB to HP EliteBook

HDMI1_INPUT=17    # HDMI 1 input value for Samsung S65UC
LEFT_DISPLAY=1
RIGHT_DISPLAY=2

m1ddc set input $HDMI1_INPUT -d $LEFT_DISPLAY &
m1ddc set input $HDMI1_INPUT -d $RIGHT_DISPLAY &
wait

sleep 0.5

# Trigger eKL USB switch to Input 3 (HP)
osascript -e '
tell application "System Events"
    key code 107
    delay 0.1
    key code 107
    delay 0.1
    key code 20
end tell
'
```

#### ~/scripts/kvm/switch-left-personal.sh

```bash
#!/bin/bash
# Switch LEFT monitor only to Personal Mac (split mode)
USB_C_INPUT=16
LEFT_DISPLAY=1
m1ddc set input $USB_C_INPUT -d $LEFT_DISPLAY
```

#### ~/scripts/kvm/switch-left-work.sh

```bash
#!/bin/bash
# Switch LEFT monitor only to Work Mac (split mode)
DP_INPUT=15
LEFT_DISPLAY=1
m1ddc set input $DP_INPUT -d $LEFT_DISPLAY
```

#### ~/scripts/kvm/switch-left-hp.sh

```bash
#!/bin/bash
# Switch LEFT monitor only to HP EliteBook (split mode)
HDMI1_INPUT=17
LEFT_DISPLAY=1
m1ddc set input $HDMI1_INPUT -d $LEFT_DISPLAY
```

#### ~/scripts/kvm/switch-right-personal.sh

```bash
#!/bin/bash
# Switch RIGHT monitor only to Personal Mac (split mode)
USB_C_INPUT=16
RIGHT_DISPLAY=2
m1ddc set input $USB_C_INPUT -d $RIGHT_DISPLAY
```

#### ~/scripts/kvm/switch-right-work.sh

```bash
#!/bin/bash
# Switch RIGHT monitor only to Work Mac (split mode)
DP_INPUT=15
RIGHT_DISPLAY=2
m1ddc set input $DP_INPUT -d $RIGHT_DISPLAY
```

#### ~/scripts/kvm/switch-right-hp.sh

```bash
#!/bin/bash
# Switch RIGHT monitor only to HP EliteBook (split mode)
HDMI1_INPUT=17
RIGHT_DISPLAY=2
m1ddc set input $HDMI1_INPUT -d $RIGHT_DISPLAY
```

Make all scripts executable:

```bash
chmod +x ~/scripts/kvm/*.sh
```

### Windows Scripts (HP EliteBook)

Create a directory: `C:\Scripts\kvm\`

#### C:\Scripts\kvm\switch-all-personal.bat

```batch
@echo off
REM Switch ALL monitors + USB to Personal Mac

REM DDC/CI: Switch both monitors to USB-C input
REM REPLACE paths and monitor IDs with your actual values
start "" "C:\Tools\ControlMyMonitor\ControlMyMonitor.exe" /SetValue "\\.\DISPLAY1\Monitor0" 60 16
start "" "C:\Tools\ControlMyMonitor\ControlMyMonitor.exe" /SetValue "\\.\DISPLAY2\Monitor0" 60 16

REM Wait for DDC commands to process
timeout /t 1 /nobreak >nul

REM Trigger eKL USB switch to Input 1
REM Uses PowerShell to simulate Scroll Lock × 2 + 1
powershell -Command "$wsh = New-Object -ComObject WScript.Shell; $wsh.SendKeys('{SCROLLLOCK}'); Start-Sleep -Milliseconds 100; $wsh.SendKeys('{SCROLLLOCK}'); Start-Sleep -Milliseconds 100; $wsh.SendKeys('1')"
```

#### C:\Scripts\kvm\switch-all-work.bat

```batch
@echo off
REM Switch ALL monitors + USB to Work Mac

start "" "C:\Tools\ControlMyMonitor\ControlMyMonitor.exe" /SetValue "\\.\DISPLAY1\Monitor0" 60 15
start "" "C:\Tools\ControlMyMonitor\ControlMyMonitor.exe" /SetValue "\\.\DISPLAY2\Monitor0" 60 15

timeout /t 1 /nobreak >nul

powershell -Command "$wsh = New-Object -ComObject WScript.Shell; $wsh.SendKeys('{SCROLLLOCK}'); Start-Sleep -Milliseconds 100; $wsh.SendKeys('{SCROLLLOCK}'); Start-Sleep -Milliseconds 100; $wsh.SendKeys('2')"
```

#### C:\Scripts\kvm\switch-all-hp.bat

```batch
@echo off
REM Switch ALL monitors + USB to HP EliteBook

start "" "C:\Tools\ControlMyMonitor\ControlMyMonitor.exe" /SetValue "\\.\DISPLAY1\Monitor0" 60 17
start "" "C:\Tools\ControlMyMonitor\ControlMyMonitor.exe" /SetValue "\\.\DISPLAY2\Monitor0" 60 17

timeout /t 1 /nobreak >nul

powershell -Command "$wsh = New-Object -ComObject WScript.Shell; $wsh.SendKeys('{SCROLLLOCK}'); Start-Sleep -Milliseconds 100; $wsh.SendKeys('{SCROLLLOCK}'); Start-Sleep -Milliseconds 100; $wsh.SendKeys('3')"
```

> **Create similar individual monitor scripts** (`switch-left-*.bat`, `switch-right-*.bat`) following the same pattern but only targeting one monitor and omitting the USB switch command.

---

## Phase 8: Final Testing Checklist

### Monitor Switching Tests

- [ ] From Personal Mac: Press "ALL → Work Mac" → Both monitors switch to Work Mac
- [ ] From Personal Mac: Press "ALL → HP" → Both monitors switch to HP EliteBook
- [ ] From Work Mac: Press "ALL → Personal Mac" → Both monitors switch to Personal Mac
- [ ] From Work Mac: Press "ALL → HP" → Both monitors switch to HP EliteBook
- [ ] From HP: Press "ALL → Personal Mac" → Both monitors switch to Personal Mac
- [ ] From HP: Press "ALL → Work Mac" → Both monitors switch to Work Mac

### Split Mode Tests

- [ ] Press "LEFT → Personal Mac" then "RIGHT → Work Mac" → Split view works
- [ ] Input Leap mouse movement works between split-view computers
- [ ] Keyboard follows Input Leap focus (types on whichever screen has cursor)

### USB Switching Tests

- [ ] After "ALL → Personal Mac": Keyboard, mouse, webcam, Stream Deck all on Personal Mac
- [ ] After "ALL → Work Mac": All peripherals switch to Work Mac
- [ ] After "ALL → HP": All peripherals switch to HP EliteBook
- [ ] Stream Deck buttons work correctly on each computer after switching

### Edge Case Tests

- [ ] Switch rapidly between computers (no crashes/hangs)
- [ ] Put Personal Mac to sleep, switch to Work Mac, wake Personal Mac, switch back
- [ ] Close laptop lid (Work Mac), switch to Personal Mac, open lid, switch back
- [ ] Disconnect and reconnect a USB peripheral during use

### EDID Tests

- [ ] Switch away from Personal Mac → windows stay in place when switching back
- [ ] Switch away from Work Mac → windows stay in place when switching back
- [ ] Switch away from HP → windows stay in place when switching back

---

## Daily Operation

### Morning Startup

1. Turn on both Samsung monitors
2. Power on/wake all three computers
3. Input Leap should auto-start on all machines (configure to launch at login)
4. Stream Deck loads your profile automatically via Elgato software
5. Press the Stream Deck button for whichever computer you want to start on

### Switching During the Day

**Full switch (both monitors + all peripherals):**
- Press one of the three "ALL →" buttons on Stream Deck
- Everything switches in ~1-2 seconds

**Split mode (different computer on each monitor):**
- Press individual "LEFT →" and "RIGHT →" buttons
- Move mouse between computers seamlessly via Input Leap
- USB peripherals stay on last "ALL" selected computer

### End of Day

- No special shutdown needed
- Put computers to sleep normally
- Monitors will auto-sleep when all inputs are inactive

---

## Troubleshooting

### Monitor won't switch via DDC/CI

1. Verify DDC/CI is enabled in monitor OSD → System → DDC/CI → On
2. Verify Auto Source Switch+ is Off in monitor OSD
3. Run `m1ddc display list` to confirm the monitor is detected
4. Try different input values (1-20) with `m1ddc set input N`
5. Unplug and replug the video cable
6. Restart Lunar

### Stream Deck buttons don't work after switching

1. Verify Elgato Stream Deck software is installed and running on the target computer
2. Check that the profile is loaded (may need to re-import)
3. Ensure the eKL USB switch actually completed the switch (check eKL LED indicator)

### Input Leap mouse doesn't cross screens

1. Verify server is running on Personal Mac
2. Check IP address hasn't changed (use static IP)
3. Verify screen names match in server and client configurations
4. Check firewall isn't blocking Input Leap (port 24800 by default)
5. Restart Input Leap on both server and affected client

### Windows rearrange after switching monitors

1. EDID emulators may not be installed or may be faulty
2. On macOS: try enabling "Displays have separate Spaces" in System Settings → Desktop & Dock
3. On Windows: check that EDID emulator LED is lit when cable is "inactive"

### eKL USB switch doesn't respond to keyboard shortcut

1. Verify the exact hotkey sequence for your eKL model (check manual)
2. Common sequences: ScrollLock×2+N, or Ctrl×2+N
3. Try the physical button on the eKL device to confirm it works at all
4. Some eKL models require the hotkey feature to be enabled via a DIP switch

---

## Known Risks and Fallback Plans

### Risk 1: Samsung DDC/CI Input Switching Doesn't Work (HIGH RISK)

**Impact:** Cannot switch monitor inputs via software — the entire one-button switching concept breaks.

**Fallback options (in order of preference):**

1. **Use Samsung's built-in KVM for 2 of 3 computers** — Connect Personal Mac via USB-C and Work Mac via DP+USB-B upstream cable. Samsung KVM auto-switches between them via monitor OSD hotkey. For HP, switch manually via monitor OSD button.

2. **Use a programmable microcontroller (Raspberry Pi Pico)** — Wire a Pico to the monitor's physical button contacts. Send serial commands from any computer to trigger the Pico to "press" the monitor's input button. Complex but proven by the DIY KVM community.

3. **Replace monitors with DDC/CI-reliable models** — Dell UltraSharp, LG UltraFine, and BenQ monitors are widely reported to have excellent DDC/CI support. This is the nuclear option.

4. **Use the Samsung Easy Setting Box software** — Samsung's own monitor management tool may offer input switching (available for both Windows and macOS). Worth testing even if m1ddc fails.

### Risk 2: EDID Emulators Don't Prevent Window Rearrangement

**Impact:** Every time you switch monitors away from a computer, its windows shuffle around.

**Fallback:** Use a window manager (Rectangle on macOS, PowerToys FancyZones on Windows) to snap windows back to position. Can be scripted and triggered after switching.

### Risk 3: eKL USB Switch Hotkey Incompatibility

**Impact:** Stream Deck can't trigger the USB switch programmatically.

**Fallback options:**
1. Replace the eKL with a model that explicitly supports keyboard hotkeys (many Amazon USB 3.0 switches do)
2. Use a USB-controlled relay board to physically press the eKL button
3. Skip the eKL entirely and rely on Input Leap for keyboard/mouse + Samsung USB hub for peripherals

### Risk 4: Stream Deck Profile Mismatch Across Computers

**Impact:** Buttons do different things depending on which computer is active.

**Mitigation:** Export profile from one computer, import to all. Use identical button positions and icons. Test all 9 switching buttons from each computer.

### Risk 5: Sleep/Wake DDC/CI Disconnection

**Impact:** After a computer sleeps and wakes, DDC/CI connection may be lost.

**Mitigation:** Add a `m1ddc display list` check at the beginning of each script. If the display isn't found, wait and retry. Lunar also has a "reconnect on wake" feature.

---

## Architecture Decision Record

### Why Input Leap over Barrier?

Barrier has been unmaintained since 2021. Input Leap is the actively maintained fork created by Barrier's original developers. It includes ~800 fixes and improvements over the last Barrier release. Input Leap is available in most Linux distribution repos and has binary releases for macOS and Windows.

### Why Stream Deck through USB switch (not dedicated to one computer)?

Connecting through the USB switch means:
- No dependency on one computer being awake
- Works from any computer (Stream Deck follows the active computer)
- Simpler — just press the button for where you want to go

The tradeoff is that Stream Deck software must be installed on all 3 computers with identical profiles.

### Why m1ddc + ControlMyMonitor (not just Lunar)?

Lunar provides a great GUI but its scripting capabilities are limited for Stream Deck integration. m1ddc is a purpose-built command-line tool that's easy to call from shell scripts, which Stream Deck's "Open" action can execute. ControlMyMonitor serves the same purpose on Windows.

### Why EDID emulators?

Without them, when Monitor A switches from Computer 1 to Computer 2, Computer 1 thinks the monitor disconnected. macOS and Windows both rearrange windows when a display disconnects. EDID emulators maintain the "phantom display" so the OS never knows the monitor switched away.
