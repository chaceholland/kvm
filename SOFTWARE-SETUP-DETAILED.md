# Detailed Software Setup Guide

> This document is the step-by-step, click-by-click companion to `KVM-SETUP-GUIDE.md`.
> Follow it in exact order — each section builds on the previous one.

---

## Table of Contents

1. [Prerequisites](#prerequisites)
2. [Computer 1 — Personal Mac (M3 Max): Homebrew](#computer-1--personal-mac-m3-max-homebrew)
3. [Computer 1 — Personal Mac: m1ddc](#computer-1--personal-mac-m1ddc)
4. [Computer 1 — Personal Mac: Lunar](#computer-1--personal-mac-lunar)
5. [Computer 1 — Personal Mac: Input Leap (Server)](#computer-1--personal-mac-input-leap-server)
6. [Computer 1 — Personal Mac: Elgato Stream Deck](#computer-1--personal-mac-elgato-stream-deck)
7. [Computer 2 — Work Mac (M1 Max): Homebrew](#computer-2--work-mac-m1-max-homebrew)
8. [Computer 2 — Work Mac: m1ddc](#computer-2--work-mac-m1ddc)
9. [Computer 2 — Work Mac: Lunar](#computer-2--work-mac-lunar)
10. [Computer 2 — Work Mac: Input Leap (Client)](#computer-2--work-mac-input-leap-client)
11. [Computer 2 — Work Mac: Elgato Stream Deck](#computer-2--work-mac-elgato-stream-deck)
12. [Computer 3 — HP EliteBook (Windows): ControlMyMonitor](#computer-3--hp-elitebook-windows-controlmymonitor)
13. [Computer 3 — HP EliteBook: Input Leap (Client)](#computer-3--hp-elitebook-input-leap-client)
14. [Computer 3 — HP EliteBook: Elgato Stream Deck](#computer-3--hp-elitebook-elgato-stream-deck)
15. [DDC/CI Testing (Critical — Do Before Anything Else)](#ddcci-testing)
16. [Creating the Automation Scripts (All Computers)](#creating-the-automation-scripts)
17. [Stream Deck Profile Configuration](#stream-deck-profile-configuration)
18. [Auto-Start Configuration](#auto-start-configuration)
19. [Verification Walkthrough](#verification-walkthrough)

---

## Prerequisites

Before starting, confirm the following:

- [ ] Both Samsung S65UC monitors are physically connected to your desk
- [ ] All 3 computers are powered on and connected to the same local network (Wi-Fi or Ethernet)
- [ ] You have admin/sudo access on all 3 computers
- [ ] You know your Personal Mac's IP address on your local network (we'll set a static IP later)
- [ ] The eKL USB switch is connected with cables to all 3 computers
- [ ] The Stream Deck MK.2 is plugged into the eKL USB switch's OUTPUT (via USB hub)

### How to Find Your Personal Mac's IP Address

1. Open **System Settings** (click Apple menu → System Settings)
2. Click **Wi-Fi** (or **Network** if using Ethernet)
3. Click **Details** next to your connected network
4. Look for **IP Address** (e.g., `192.168.1.100`)
5. **Write this down** — you'll need it for Input Leap client setup

### How to Set a Static IP (Recommended)

A static IP prevents Input Leap clients from losing connection if the server's IP changes.

1. Open **System Settings** → **Wi-Fi** (or **Network**)
2. Click **Details** next to your connected network
3. Click **TCP/IP** tab
4. Change **Configure IPv4** from "Using DHCP" to **"Using DHCP with manual address"**
5. Enter your desired IP (e.g., `192.168.1.100`) — use the current IP if it's not already taken
6. Click **OK**

Alternatively, set a DHCP reservation on your router (consult your router's admin page).

---

## Computer 1 — Personal Mac (M3 Max): Homebrew

Homebrew is the package manager we'll use to install m1ddc, Lunar, and Input Leap.

### Check if Homebrew is Already Installed

1. Open **Terminal** (Applications → Utilities → Terminal, or press `⌘+Space`, type "Terminal", press Enter)
2. Type the following and press Enter:

```bash
brew --version
```

3. If you see a version number (e.g., `Homebrew 4.x.x`), Homebrew is installed — **skip to the next section**.
4. If you see `command not found: brew`, continue below.

### Install Homebrew

1. In Terminal, paste this entire command and press Enter:

```bash
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
```

2. You'll be prompted for your Mac password — type it (nothing will appear on screen, that's normal) and press Enter
3. Follow any on-screen instructions. On Apple Silicon Macs, Homebrew may ask you to run two additional commands to add it to your PATH. They will look like:

```bash
echo 'eval "$(/opt/homebrew/bin/brew shellenv)"' >> ~/.zprofile
eval "$(/opt/homebrew/bin/brew shellenv)"
```

4. **Run those commands if prompted.**

### Verify Homebrew

```bash
brew --version
```

You should see `Homebrew 4.x.x` or similar.

---

## Computer 1 — Personal Mac: m1ddc

m1ddc is a command-line tool that sends DDC/CI commands to external monitors from Apple Silicon Macs. This is what your automation scripts will use to switch monitor inputs.

### Install m1ddc

1. In Terminal on your Personal Mac:

```bash
brew install waydabber/m1ddc/m1ddc
```

2. Wait for installation to complete (usually under 30 seconds).

### Verify m1ddc is Installed

```bash
m1ddc display list
```

**Expected output:** A list of your connected external monitors with display numbers and identifiers. Example:

```
1 - 381C72C8-0CDA-4B71-A1CD-F8AFE90AB0ED
    Samsung Electric Company - S34C650 - HCXXXXXXXX
2 - 9A2B3C4D-5E6F-7A8B-9C0D-E1F2A3B4C5D6
    Samsung Electric Company - S34C650 - HCYYYYYYYY
```

**Write down:**
- Display 1's number and which physical monitor it is (Left or Right)
- Display 2's number and which physical monitor it is (Left or Right)

> **Tip:** To figure out which is which, run `m1ddc display 1 set luminance 10` — whichever monitor dims is Display 1. Then restore it with `m1ddc display 1 set luminance 70`.

### m1ddc Command Reference

Here are all the commands you'll use in this project:

```bash
# List all connected displays
m1ddc display list

# List displays with extended details (vendor, model, serial, UUID)
m1ddc display list detailed

# Get current input source value for Display 1
m1ddc display 1 get input

# Set input source for Display 1 (replace N with the value)
m1ddc display 1 set input N

# Set input source for Display 2
m1ddc display 2 set input N

# Get current brightness
m1ddc display 1 get luminance

# Set brightness (0-100)
m1ddc display 1 set luminance 70

# Get current volume
m1ddc display 1 get volume

# Set volume (0-100)
m1ddc display 1 set volume 30

# Mute/unmute
m1ddc display 1 set mute on
m1ddc display 1 set mute off
```

### Input Source Values to Try

These are the standard DDC/CI input source values. **Your Samsung monitors may use different values** — that's what the DDC/CI testing phase will determine.

| Value | Typically Mapped To |
|-------|-------------------|
| 15 | DisplayPort 1 |
| 16 | DisplayPort 2 |
| 17 | HDMI 1 |
| 18 | HDMI 2 |
| 27 | USB-C (on some monitors) |

> Samsung sometimes uses non-standard values. If 15-18 and 27 don't work, try every value from 1 to 30: `for i in $(seq 1 30); do echo "Trying $i"; m1ddc display 1 set input $i; sleep 2; done`

---

## Computer 1 — Personal Mac: Lunar

Lunar provides a GUI for DDC/CI control, menu bar access to monitor settings, and the ability to assign hotkeys for input switching. It's your day-to-day visual interface for monitor management.

### Install Lunar

**Option A — Via Homebrew (recommended):**

```bash
brew install --cask lunar
```

**Option B — Direct download:**

1. Go to https://lunar.fyi
2. Click the download button
3. Open the downloaded `.dmg` file
4. Drag Lunar to your Applications folder

### First Launch and Permissions

1. Open **Lunar** (from Applications or Spotlight: `⌘+Space`, type "Lunar")
2. Lunar will request **Accessibility permissions**:
   - A dialog will appear: "Lunar would like to control this computer using accessibility features"
   - Click **Open System Settings** (or it may say "Open System Preferences")
   - In **System Settings → Privacy & Security → Accessibility**, find **Lunar** in the list
   - Toggle the switch **ON** next to Lunar
   - You may need to click the lock icon and enter your password first
   - Close System Settings

3. If Lunar asks for **Screen Recording** permission:
   - Go to **System Settings → Privacy & Security → Screen Recording**
   - Toggle **Lunar** ON
   - Close System Settings

4. **Restart Lunar** after granting permissions (Quit from menu bar → reopen)

### Verify DDC/CI Detection

1. After restart, look at your **menu bar** (top of screen) — you should see Lunar's icon (a sun/moon symbol)
2. Click the Lunar menu bar icon
3. You should see both Samsung monitors listed with their names
4. Click on one monitor — you should see sliders for **Brightness**, **Contrast**, and **Volume**
5. **Test:** Drag the Brightness slider on one monitor — the physical monitor's brightness should change
6. If the brightness slider works, DDC/CI communication is functional for that monitor

> **If monitors don't appear or sliders don't work:**
> - Make sure DDC/CI is enabled on the monitor OSD (see DDC/CI Testing section)
> - Try unplugging and replugging the video cable
> - Try a different USB-C/Thunderbolt port on the Mac
> - Check Lunar's menu → Controls → ensure "Hardware DDC" is checked

### Install Lunar CLI (Optional but Recommended)

The Lunar CLI lets you control monitors from Terminal and from scripts:

1. Open Terminal
2. Run:

```bash
/Applications/Lunar.app/Contents/MacOS/Lunar install-cli
```

3. Verify:

```bash
lunar displays
```

This should list your connected monitors. You can then use:

```bash
# Switch Display "left-samsung" to HDMI 1 input
lunar displays left-samsung input hdmi1

# Switch Display "right-samsung" to DisplayPort input
lunar displays right-samsung input displayPort1

# List all available input names for a display
lunar displays left-samsung inputs
```

> **Note:** The display names used by Lunar may differ from m1ddc. Use `lunar displays` to see what Lunar calls each monitor.

### Configure Lunar Hotkeys for Input Switching

Even though Stream Deck will be the primary switching method, having keyboard hotkeys as backup is valuable.

1. Open **Lunar**
2. Click the Lunar menu bar icon → **Preferences** (or press `⌘+,`)
3. Navigate to the **Hotkeys** tab
4. Under **Input Hotkeys**, configure the following for **each monitor**:

**Left Samsung Monitor:**

| Hotkey | Action | Notes |
|--------|--------|-------|
| `⌘⌥⌃1` | Switch to USB-C input | For Personal Mac |
| `⌘⌥⌃2` | Switch to DisplayPort input | For Work Mac |
| `⌘⌥⌃3` | Switch to HDMI 1 input | For HP EliteBook |

**Right Samsung Monitor:**

Configure the same hotkeys — Lunar will attempt to switch all monitors at once if you assign the same hotkey to the same input across monitors.

> **Important:** Lunar can't assign the same hotkey to switch multiple monitors to different inputs simultaneously from its native UI. For that, we use the automation scripts + Stream Deck. The Lunar hotkeys are a backup for individual monitor control.

### Configure Lunar's Startup Behavior

1. In Lunar **Preferences** → **General** tab:
   - Check **"Launch at Login"** — Lunar starts automatically when you log in
   - Check **"Start Minimized"** — Lunar runs in the menu bar without opening a window

---

## Computer 1 — Personal Mac: Input Leap (Server)

Input Leap provides seamless keyboard/mouse sharing between your computers over the network. Your Personal Mac will be the **server** (the computer whose physical keyboard and mouse are shared with the others).

### Install Input Leap

**Option A — Via Homebrew:**

```bash
brew install --cask input-leap
```

**Option B — Direct download:**

1. Go to https://github.com/input-leap/input-leap/releases
2. Download the macOS `.dmg` file (look for `InputLeap-x.x.x-macos.dmg`)
3. Open the `.dmg` and drag Input Leap to Applications

### First Launch and Permissions

1. Open **Input Leap** (from Applications or Spotlight)
2. On first launch, it will ask you to choose a language — select your language and click **Next**
3. Select **"Server (share this computer's mouse and keyboard)"** and click **Finish**

4. Input Leap will request **Accessibility permissions**:
   - Go to **System Settings → Privacy & Security → Accessibility**
   - Find **Input Leap** in the list and toggle it **ON**
   - You may need to click the lock icon first

5. Input Leap may also request **Local Network** permission:
   - A dialog will appear asking to find and connect to devices on your local network
   - Click **Allow**

6. Input Leap may also request **Input Monitoring** permission:
   - Go to **System Settings → Privacy & Security → Input Monitoring**
   - Toggle **Input Leap** ON

7. **Restart Input Leap** after granting all permissions

### Configure the Server Screen Layout

This is where you define the spatial relationship between your computers — how the mouse moves from one to another.

1. In the Input Leap window, click **"Configure Server..."**
2. You'll see a **5×3 grid** with your Personal Mac's screen in the center
3. **Drag a new screen icon** from the top-right corner onto the grid:
   - Place it to the **right** of your Personal Mac (this will be Work Mac)
   - Double-click the new screen icon
   - In the **"Screen name"** field, type: `work-mac` (this MUST match the screen name on the Work Mac client — case-sensitive)
   - Click **OK**

4. **Drag another screen icon** onto the grid:
   - Place it to the **right** of `work-mac` (this will be HP EliteBook)
   - Double-click it
   - In the **"Screen name"** field, type: `hp-elitebook`
   - Click **OK**

5. Your grid should now look like:

```
┌────────────┐  ┌────────────┐  ┌────────────┐
│  personal  │──│  work-mac  │──│hp-elitebook│
│    -mac    │  │            │  │            │
└────────────┘  └────────────┘  └────────────┘
```

> **Adjusting layout for split mode:** Since you have 2 physical monitors and sometimes split between computers, you may want to experiment with placing `work-mac` above or below instead of to the right. The ideal layout depends on your physical desk arrangement. Start with left-to-right and adjust later.

6. Click **OK** to save the server configuration

### Configure Server Options

1. Back in the main Input Leap window:
   - The **IP address** field should show your Personal Mac's IP
   - The **Port** should be `24800` (default — don't change unless you have a conflict)

2. Click **Settings** (or press **F4**):
   - **Screen name:** Verify it says something like `personal-mac` or your Mac's hostname
   - **Port:** `24800`
   - **Interface:** leave blank (listens on all interfaces)
   - If you want to rename the screen, type `personal-mac` in the Screen name field
   - Click **OK**

3. Optionally, under **Advanced** settings:
   - **Switch on double-tap:** If enabled, you need to bump the screen edge twice to switch — prevents accidental switches
   - **Switch delay:** Milliseconds before the switch happens (0 = instant, 250 = slight delay)

### SSL/TLS Configuration

Input Leap uses SSL by default. On first run, it generates certificates automatically.

- If clients can't connect, try **unchecking** "Enable SSL" on both server and clients as a troubleshooting step
- For a home network, SSL is optional but recommended

### Start the Server

1. Click **Start** (bottom of the Input Leap window)
2. The status bar at the bottom should say: **"Input Leap is running."**
3. Leave Input Leap running — clients will connect to it

### Note the Server's IP and Port

Write these down — you'll need them for the client computers:

```
Server IP: _____________ (e.g., 192.168.1.100)
Server Port: 24800
```

---

## Computer 1 — Personal Mac: Elgato Stream Deck

### Install Stream Deck Software

**Option A — Via Homebrew:**

```bash
brew install --cask elgato-stream-deck
```

**Option B — Direct download:**

1. Go to https://www.elgato.com/downloads
2. Find **Stream Deck** under the product list
3. Download the macOS version
4. Open the `.dmg` and drag to Applications

### First Launch

1. Open **Stream Deck** (from Applications or Spotlight)
2. If the Stream Deck MK.2 is currently connected to this computer (via eKL switch), you should see the 15-button grid in the Stream Deck software
3. If the Stream Deck is on a different computer right now, the software will show a "Connect your Stream Deck" message — that's fine, we'll configure the profile first

### Create a New Profile

1. Click the **Preferences** icon (gear icon, top-right of the Stream Deck window)
2. Go to the **Profiles** tab
3. Click the **+** button to create a new profile
4. Name it: **KVM Control**
5. Click **OK** — this creates a blank 15-key layout

### Configure Buttons (Done After Scripts Are Created)

Button configuration requires the automation scripts to exist first. **Skip ahead to the [Creating the Automation Scripts](#creating-the-automation-scripts) section, then return here for the [Stream Deck Profile Configuration](#stream-deck-profile-configuration) section.**

### Enable Auto-Start

1. Open **System Settings → General → Login Items**
2. Under "Open at Login," click **+**
3. Navigate to **Applications** → select **Stream Deck** (Elgato Stream Deck)
4. Click **Open** — Stream Deck will now start automatically on login

---

## Computer 2 — Work Mac (M1 Max): Homebrew

Repeat the exact same Homebrew installation steps as Computer 1.

### Check if Homebrew is Already Installed

1. Open **Terminal** on the Work Mac
2. Run:

```bash
brew --version
```

3. If installed, proceed. If not, install it:

```bash
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
```

4. Follow the PATH instructions if prompted (same as Computer 1).

---

## Computer 2 — Work Mac: m1ddc

### Install m1ddc

```bash
brew install waydabber/m1ddc/m1ddc
```

### Verify

```bash
m1ddc display list
```

You should see both Samsung monitors listed. **Note the display numbers** — they may be different from the Personal Mac's numbering because the Work Mac connects via DisplayPort (not USB-C).

> **Important:** Display numbering is per-computer, not per-monitor. Display 1 on the Work Mac might be the Right Samsung, while Display 1 on the Personal Mac might be the Left Samsung. Use the brightness trick to identify: `m1ddc display 1 set luminance 10`

**Write down the Work Mac's display IDs:**

```
Work Mac — Display 1 is the: LEFT / RIGHT Samsung (circle one)
Work Mac — Display 2 is the: LEFT / RIGHT Samsung (circle one)
```

---

## Computer 2 — Work Mac: Lunar

### Install Lunar

```bash
brew install --cask lunar
```

### Grant Permissions

Follow the exact same permission steps as Computer 1:

1. Open Lunar
2. Grant **Accessibility** permission (System Settings → Privacy & Security → Accessibility → Lunar → ON)
3. Grant **Screen Recording** permission if prompted
4. Restart Lunar

### Verify DDC/CI

1. Click Lunar's menu bar icon
2. Verify both Samsung monitors appear
3. Test brightness slider on each — they should physically change

### Configure Lunar Hotkeys (Same as Computer 1)

1. Lunar menu bar → **Preferences** → **Hotkeys** tab
2. Set up the same input hotkeys:
   - `⌘⌥⌃1` → USB-C input (Personal Mac)
   - `⌘⌥⌃2` → DisplayPort input (Work Mac)
   - `⌘⌥⌃3` → HDMI 1 input (HP EliteBook)

### Enable Launch at Login

1. Lunar **Preferences** → **General** → Check **"Launch at Login"**
2. Check **"Start Minimized"**

### Install Lunar CLI (Optional)

```bash
/Applications/Lunar.app/Contents/MacOS/Lunar install-cli
lunar displays
```

---

## Computer 2 — Work Mac: Input Leap (Client)

### Install Input Leap

```bash
brew install --cask input-leap
```

### First Launch and Permissions

1. Open Input Leap
2. Select language → click **Next**
3. Select **"Client (use another computer's mouse and keyboard)"** → click **Finish**
4. Grant **Accessibility** permission (System Settings → Privacy & Security → Accessibility → Input Leap → ON)
5. Grant **Local Network** permission if prompted → **Allow**
6. Grant **Input Monitoring** permission if prompted
7. Restart Input Leap

### Configure the Client

1. In the Input Leap window, you should see a **"Server IP"** field
2. **Uncheck** "Auto config" (manual is more reliable)
3. Enter the **Personal Mac's IP address**: `____________` (e.g., `192.168.1.100`)

4. Click **Settings** (or press **F4**):
   - **Screen name:** Type `work-mac` (this MUST match what you configured on the server — case-sensitive)
   - Click **OK**

### Start the Client

1. Click **Start**
2. The status bar should say: **"Input Leap is running."**
3. **Test:** On the Personal Mac, move your mouse to the right edge of the screen — it should appear on the Work Mac's display

> **If it doesn't work:**
> - Verify the screen name matches exactly: `work-mac` on both server and client
> - Verify the IP address is correct
> - Check that both machines are on the same network
> - Try disabling SSL on both server and client
> - Check macOS firewall: System Settings → Network → Firewall → allow Input Leap

### Enable Auto-Start

To make Input Leap start automatically on login:

1. Open **System Settings → General → Login Items**
2. Click **+** under "Open at Login"
3. Select **Input Leap** from Applications
4. Click **Open**

---

## Computer 2 — Work Mac: Elgato Stream Deck

### Install Stream Deck Software

```bash
brew install --cask elgato-stream-deck
```

### First Launch

1. Open Stream Deck
2. The Stream Deck MK.2 may or may not be connected to this computer right now (depends on eKL switch position) — that's fine
3. We'll configure the profile later and import it from the Personal Mac

### Enable Auto-Start

1. Open **System Settings → General → Login Items**
2. Add **Stream Deck** to "Open at Login"

---

## Computer 3 — HP EliteBook (Windows): ControlMyMonitor

ControlMyMonitor is a free, portable Windows tool from NirSoft that sends DDC/CI commands to monitors. It's the Windows equivalent of m1ddc.

### Download ControlMyMonitor

1. Open a web browser on the HP EliteBook
2. Go to: **https://www.nirsoft.net/utils/control_my_monitor.html**
3. Scroll to the bottom of the page
4. Click **"Download ControlMyMonitor"** (the first download link — the standard 64-bit version)
5. Your browser may warn you about the download (NirSoft tools trigger false positives in some antivirus software because they're system utilities) — click **"Keep"** or **"Allow"**

### Extract and Set Up

1. Open File Explorer and navigate to your **Downloads** folder
2. Right-click the downloaded `controlmymonitor.zip` file → **Extract All...**
3. Extract to: `C:\Tools\ControlMyMonitor\`
4. Open that folder — you should see `ControlMyMonitor.exe`

### Run ControlMyMonitor for the First Time

1. Double-click **ControlMyMonitor.exe**
2. The main window will open and list all VCP codes for your primary monitor
3. Look for:

| VCP Code | Name | What It Controls |
|----------|------|-----------------|
| 10 (hex 0x0A) | Brightness/Luminance | Monitor brightness |
| 12 (hex 0x0C) | Contrast | Monitor contrast |
| 60 (hex 0x3C) | Input Source | **This is the one we need** |
| 62 (hex 0x3E) | Audio Speaker Volume | Monitor volume |

4. Find **VCP Code 60** (Input Source) — note the **Current Value**. This tells you what input the monitor is currently using.

### Identify Your Monitors

1. Press **Ctrl+M** in ControlMyMonitor — this shows the **monitor identifier strings**
2. Write down the identifiers for each Samsung monitor. Example:

```
Left Samsung:  \\.\DISPLAY1\Monitor0
Right Samsung: \\.\DISPLAY2\Monitor0
```

> **Note:** The DISPLAY number can change between reboots. If this happens, use the monitor's **serial number** instead (also shown in Ctrl+M view).

### Test DDC/CI from Command Line

Open **Command Prompt** (press `Win+R`, type `cmd`, press Enter):

```batch
REM Get current input source value for Left monitor
"C:\Tools\ControlMyMonitor\ControlMyMonitor.exe" /GetValue "\\.\DISPLAY1\Monitor0" 60

REM Get current input source value for Right monitor
"C:\Tools\ControlMyMonitor\ControlMyMonitor.exe" /GetValue "\\.\DISPLAY2\Monitor0" 60
```

### ControlMyMonitor Command Reference

```batch
REM Set a VCP value on a specific monitor
ControlMyMonitor.exe /SetValue "MonitorID" VCPCode Value

REM Examples:
REM Set brightness to 70 on DISPLAY1
ControlMyMonitor.exe /SetValue "\\.\DISPLAY1\Monitor0" 10 70

REM Set input source to DisplayPort (value 15) on DISPLAY1
ControlMyMonitor.exe /SetValue "\\.\DISPLAY1\Monitor0" 60 15

REM Set input source to HDMI 1 (value 17) on DISPLAY2
ControlMyMonitor.exe /SetValue "\\.\DISPLAY2\Monitor0" 60 17

REM Set multiple values at once (two monitors in one command)
ControlMyMonitor.exe /SetValue "\\.\DISPLAY1\Monitor0" 60 15 /SetValue "\\.\DISPLAY2\Monitor0" 60 15

REM List all monitors (outputs to a text file)
ControlMyMonitor.exe /smonitors "C:\Tools\ControlMyMonitor\monitors.txt"
```

---

## Computer 3 — HP EliteBook: Input Leap (Client)

### Download Input Leap for Windows

1. Open a web browser on the HP EliteBook
2. Go to: **https://github.com/input-leap/input-leap/releases**
3. Find the latest release (currently **v3.0.2**)
4. Download: **`InputLeap_3.0.2_windows_qt6.exe`**

**Alternative: Install via winget (if available):**

Open **PowerShell** or **Command Prompt** and run:

```
winget install input-leap.input-leap
```

### Install Input Leap

1. Run the downloaded `.exe` installer
2. Follow the installation wizard:
   - Accept the license agreement
   - Choose the default installation directory (typically `C:\Program Files\Input Leap\`)
   - Click **Install**
3. When finished, click **Finish** to launch Input Leap

### Windows Firewall Configuration

Windows Firewall will likely block Input Leap on first run:

1. A **Windows Security Alert** dialog will appear: "Windows Defender Firewall has blocked some features of this app"
2. Check **both** boxes:
   - [x] Private networks
   - [x] Public networks (optional — only if your home network is set to "Public")
3. Click **Allow access**

**If the dialog doesn't appear or you dismissed it:**

1. Open **Windows Security** (search "Windows Security" in Start menu)
2. Click **Firewall & network protection**
3. Click **Allow an app through firewall**
4. Click **Change settings** (admin permission required)
5. Click **Allow another app...**
6. Browse to `C:\Program Files\Input Leap\input-leap.exe`
7. Click **Add**, then check both **Private** and **Public** boxes
8. Click **OK**

### Configure the Client

1. On first launch, Input Leap will ask for mode:
   - Select **"Client (use another computer's mouse and keyboard)"**
   - Click **Finish**

2. In the main window:
   - **Uncheck** "Auto config"
   - In the **Server IP** field, enter: `____________` (your Personal Mac's IP address, e.g., `192.168.1.100`)

3. Click **Settings** (or press **F4**):
   - **Screen name:** Type `hp-elitebook` (MUST match the server configuration — case-sensitive)
   - Click **OK**

### Start the Client

1. Click **Start**
2. Status should show: **"Input Leap is running."**
3. **Test:** On the Personal Mac, move your mouse past the Work Mac screen to the right — it should appear on the HP EliteBook's display

> **If it doesn't work:**
> - Verify screen name is exactly `hp-elitebook` (case-sensitive)
> - Verify the IP address is correct
> - Check Windows Firewall (see above)
> - Try disabling SSL on both server and client
> - Make sure both machines are on the same network subnet

### Enable Auto-Start on Windows

1. Press `Win+R`, type `shell:startup`, press Enter — this opens the Startup folder
2. Right-click in the folder → **New** → **Shortcut**
3. Browse to `C:\Program Files\Input Leap\input-leap.exe`
4. Click **Next**, name it "Input Leap", click **Finish**
5. Input Leap will now start automatically when you log into Windows

---

## Computer 3 — HP EliteBook: Elgato Stream Deck

### Download and Install

1. Go to: **https://www.elgato.com/downloads**
2. Find **Stream Deck** in the product list
3. Download the **Windows** version
4. Run the installer and follow the prompts
5. Restart the HP EliteBook if prompted

### First Launch

1. Open Stream Deck (it should be in your Start menu)
2. If the Stream Deck MK.2 is currently connected to this computer, you'll see the button grid
3. We'll import the profile from the Personal Mac later

### Enable Auto-Start on Windows

Elgato Stream Deck typically enables auto-start during installation. To verify:

1. Open **Task Manager** (press `Ctrl+Shift+Esc`)
2. Click the **Startup** tab (or **Startup apps** on Windows 11)
3. Find **Elgato Stream Deck** in the list
4. Ensure its Status is **Enabled**
5. If it's Disabled, right-click → **Enable**

---

## DDC/CI Testing

> **STOP. This section is the most important part of the entire setup.** If DDC/CI input switching doesn't work on your Samsung monitors, the one-button switching via Stream Deck won't work and we'll need a fallback plan. Do not skip this.

### Preparation

1. Make sure **both Samsung monitors are connected** to at least your Personal Mac (via USB-C)
2. Make sure **DDC/CI is enabled** on both monitors:
   - Press the **joystick/menu button** on the back of each Samsung monitor
   - Navigate to: **Menu → System → DDC/CI**
   - Set to **ON**
3. **Disable Auto Source Switch+** on both monitors:
   - Navigate to: **Menu → System → Auto Source Switch+**
   - Set to **OFF**
   - This prevents the monitor from auto-switching and fighting your DDC commands

### Test from Personal Mac

Open Terminal and run each command one at a time. **Wait 3-5 seconds between commands** — monitors are slow to respond.

#### Step 1: List Displays

```bash
m1ddc display list
```

Write down the output:

```
Display 1: _____________________________________________
Display 2: _____________________________________________
```

#### Step 2: Read Current Input Values

```bash
m1ddc display 1 get input
m1ddc display 2 get input
```

Write down: `Display 1 current input = ___`, `Display 2 current input = ___`

These values represent the USB-C input (since your Personal Mac is connected via USB-C).

#### Step 3: Test Switching to DisplayPort

```bash
m1ddc display 1 set input 15
```

**Watch the Left monitor.** Did it switch to DisplayPort? (You should see the Work Mac's desktop, or "No Signal" if Work Mac isn't connected yet.)

- If YES → USB-C → DP switching works! Write down: `DP value = 15`
- If NO → Try other values:

```bash
m1ddc display 1 set input 16
# wait 3 seconds
m1ddc display 1 set input 3
# wait 3 seconds
m1ddc display 1 set input 4
```

If none of these work, try a brute-force scan:

```bash
for i in $(seq 1 30); do echo "--- Trying value $i ---"; m1ddc display 1 set input $i; sleep 3; done
```

Watch the monitor during the scan. When it switches, note which value caused it.

#### Step 4: Switch Back to USB-C

```bash
m1ddc display 1 set input 27
```

If that doesn't work:

```bash
m1ddc display 1 set input 16
# or
m1ddc display 1 set input 15
```

If nothing switches back, use the **physical button** on the Samsung monitor to switch back to USB-C via the OSD menu, then note the value:

```bash
m1ddc display 1 get input
```

#### Step 5: Test Switching to HDMI 1

```bash
m1ddc display 1 set input 17
```

Check if it switches to HDMI. If not, try 18, 4, 5, 8, 9, 11.

#### Step 6: Repeat for Display 2

Run all the same tests for Display 2 to confirm both monitors respond.

#### Step 7: Record Your Values

```
┌──────────────────────────────────────────────────────────┐
│               DDC/CI INPUT VALUE MAP                      │
│                                                           │
│  USB-C (Personal Mac) input value:    ___                 │
│  DisplayPort (Work Mac) input value:  ___                 │
│  HDMI 1 (HP EliteBook) input value:   ___                 │
│                                                           │
│  Left Samsung is m1ddc Display:       ___                 │
│  Right Samsung is m1ddc Display:      ___                 │
│                                                           │
│  Left Samsung ControlMyMonitor ID:    ___                 │
│  Right Samsung ControlMyMonitor ID:   ___                 │
│                                                           │
│  DDC/CI INPUT SWITCHING WORKS:        YES / NO            │
└──────────────────────────────────────────────────────────┘
```

**If DDC/CI input switching does NOT work:** Stop here and refer to the "Known Risks and Fallback Plans" section in `KVM-SETUP-GUIDE.md`.

### Test from Work Mac (After Connecting DP Cables)

Once the Work Mac is connected to both monitors via DisplayPort:

```bash
m1ddc display list
m1ddc display 1 get input
m1ddc display 1 set input [USB-C value from above]
m1ddc display 1 set input [HDMI value from above]
```

Verify the Work Mac can also switch inputs on both monitors.

### Test from HP EliteBook (After Connecting HDMI Cables)

Once the HP is connected via HDMI:

```batch
"C:\Tools\ControlMyMonitor\ControlMyMonitor.exe" /GetValue "\\.\DISPLAY1\Monitor0" 60
"C:\Tools\ControlMyMonitor\ControlMyMonitor.exe" /SetValue "\\.\DISPLAY1\Monitor0" 60 [USB-C value]
"C:\Tools\ControlMyMonitor\ControlMyMonitor.exe" /SetValue "\\.\DISPLAY1\Monitor0" 60 [DP value]
```

Verify the HP can switch inputs on both monitors.

---

## Creating the Automation Scripts

These scripts are what the Stream Deck buttons actually execute. You need scripts on all 3 computers.

### macOS Scripts (Personal Mac AND Work Mac)

Run these commands on **BOTH Macs** to create the script directory and files:

#### Step 1: Create the Directory

```bash
mkdir -p ~/scripts/kvm
```

#### Step 2: Create the Scripts

> **BEFORE CREATING THESE SCRIPTS:** Replace the placeholder values below with your actual DDC/CI values from the testing section above.

**Create `switch-all-personal.sh`:**

```bash
cat > ~/scripts/kvm/switch-all-personal.sh << 'SCRIPT'
#!/bin/bash
# ============================================================
# Switch ALL monitors + USB peripherals to PERSONAL MAC
# ============================================================
# CONFIGURATION — Replace these with your actual values:
USB_C_INPUT=27        # DDC/CI value for USB-C input (from testing)
LEFT_DISPLAY=1        # m1ddc display number for Left Samsung
RIGHT_DISPLAY=2       # m1ddc display number for Right Samsung
# ============================================================

echo "Switching both monitors to Personal Mac (USB-C)..."

# Send DDC/CI commands to both monitors in parallel
m1ddc display $LEFT_DISPLAY set input $USB_C_INPUT &
m1ddc display $RIGHT_DISPLAY set input $USB_C_INPUT &
wait

echo "Monitors switching... waiting for DDC to process"
sleep 1

# Trigger eKL USB switch to Input 1 (Personal Mac)
# Simulates: Scroll Lock, Scroll Lock, 1
# NOTE: If your eKL uses a different hotkey, change this
osascript -e '
tell application "System Events"
    key code 107
    delay 0.15
    key code 107
    delay 0.15
    key code 18
end tell
'

echo "Done. Personal Mac should now be active on all monitors."
SCRIPT
```

**Create `switch-all-work.sh`:**

```bash
cat > ~/scripts/kvm/switch-all-work.sh << 'SCRIPT'
#!/bin/bash
# ============================================================
# Switch ALL monitors + USB peripherals to WORK MAC
# ============================================================
DP_INPUT=15           # DDC/CI value for DisplayPort input
LEFT_DISPLAY=1
RIGHT_DISPLAY=2
# ============================================================

echo "Switching both monitors to Work Mac (DisplayPort)..."

m1ddc display $LEFT_DISPLAY set input $DP_INPUT &
m1ddc display $RIGHT_DISPLAY set input $DP_INPUT &
wait

sleep 1

# Trigger eKL USB switch to Input 2 (Work Mac)
osascript -e '
tell application "System Events"
    key code 107
    delay 0.15
    key code 107
    delay 0.15
    key code 19
end tell
'

echo "Done. Work Mac should now be active on all monitors."
SCRIPT
```

**Create `switch-all-hp.sh`:**

```bash
cat > ~/scripts/kvm/switch-all-hp.sh << 'SCRIPT'
#!/bin/bash
# ============================================================
# Switch ALL monitors + USB peripherals to HP ELITEBOOK
# ============================================================
HDMI1_INPUT=17        # DDC/CI value for HDMI 1 input
LEFT_DISPLAY=1
RIGHT_DISPLAY=2
# ============================================================

echo "Switching both monitors to HP EliteBook (HDMI 1)..."

m1ddc display $LEFT_DISPLAY set input $HDMI1_INPUT &
m1ddc display $RIGHT_DISPLAY set input $HDMI1_INPUT &
wait

sleep 1

# Trigger eKL USB switch to Input 3 (HP EliteBook)
osascript -e '
tell application "System Events"
    key code 107
    delay 0.15
    key code 107
    delay 0.15
    key code 20
end tell
'

echo "Done. HP EliteBook should now be active on all monitors."
SCRIPT
```

**Create individual monitor scripts (for split mode):**

```bash
cat > ~/scripts/kvm/switch-left-personal.sh << 'SCRIPT'
#!/bin/bash
USB_C_INPUT=27
LEFT_DISPLAY=1
m1ddc display $LEFT_DISPLAY set input $USB_C_INPUT
echo "Left monitor → Personal Mac"
SCRIPT

cat > ~/scripts/kvm/switch-left-work.sh << 'SCRIPT'
#!/bin/bash
DP_INPUT=15
LEFT_DISPLAY=1
m1ddc display $LEFT_DISPLAY set input $DP_INPUT
echo "Left monitor → Work Mac"
SCRIPT

cat > ~/scripts/kvm/switch-left-hp.sh << 'SCRIPT'
#!/bin/bash
HDMI1_INPUT=17
LEFT_DISPLAY=1
m1ddc display $LEFT_DISPLAY set input $HDMI1_INPUT
echo "Left monitor → HP EliteBook"
SCRIPT

cat > ~/scripts/kvm/switch-right-personal.sh << 'SCRIPT'
#!/bin/bash
USB_C_INPUT=27
RIGHT_DISPLAY=2
m1ddc display $RIGHT_DISPLAY set input $USB_C_INPUT
echo "Right monitor → Personal Mac"
SCRIPT

cat > ~/scripts/kvm/switch-right-work.sh << 'SCRIPT'
#!/bin/bash
DP_INPUT=15
RIGHT_DISPLAY=2
m1ddc display $RIGHT_DISPLAY set input $DP_INPUT
echo "Right monitor → Work Mac"
SCRIPT

cat > ~/scripts/kvm/switch-right-hp.sh << 'SCRIPT'
#!/bin/bash
HDMI1_INPUT=17
RIGHT_DISPLAY=2
m1ddc display $RIGHT_DISPLAY set input $HDMI1_INPUT
echo "Right monitor → HP EliteBook"
SCRIPT
```

#### Step 3: Make All Scripts Executable

```bash
chmod +x ~/scripts/kvm/*.sh
```

#### Step 4: Test Each Script Manually

Before connecting them to Stream Deck, test from Terminal:

```bash
~/scripts/kvm/switch-all-work.sh
# Both monitors should switch to Work Mac
# Wait 3 seconds, then:
~/scripts/kvm/switch-all-personal.sh
# Both monitors should switch back to Personal Mac
```

> **IMPORTANT for Work Mac:** The display numbers may be different on the Work Mac. After running `m1ddc display list` on the Work Mac, edit the scripts to use the correct `LEFT_DISPLAY` and `RIGHT_DISPLAY` values for that computer. If the Work Mac sees them as Display 2 and Display 1 (swapped), update accordingly.

### Windows Scripts (HP EliteBook)

#### Step 1: Create the Script Directory

1. Open **File Explorer**
2. Navigate to `C:\`
3. Create a new folder: `C:\Scripts`
4. Inside it, create: `C:\Scripts\kvm`

#### Step 2: Create the Scripts

Open **Notepad** (or any text editor) and create each file:

**File: `C:\Scripts\kvm\switch-all-personal.bat`**

```batch
@echo off
REM ============================================================
REM Switch ALL monitors + USB peripherals to PERSONAL MAC
REM ============================================================
REM CONFIGURATION — Replace these with your actual values:
SET USB_C_INPUT=27
SET LEFT_MON=\\.\DISPLAY1\Monitor0
SET RIGHT_MON=\\.\DISPLAY2\Monitor0
REM ============================================================

echo Switching both monitors to Personal Mac (USB-C)...

REM Send DDC/CI commands to both monitors
start "" /B "C:\Tools\ControlMyMonitor\ControlMyMonitor.exe" /SetValue "%LEFT_MON%" 60 %USB_C_INPUT%
start "" /B "C:\Tools\ControlMyMonitor\ControlMyMonitor.exe" /SetValue "%RIGHT_MON%" 60 %USB_C_INPUT%

REM Wait for DDC commands to process
timeout /t 2 /nobreak >nul

REM Trigger eKL USB switch to Input 1 (Personal Mac)
REM Simulates: Scroll Lock, Scroll Lock, 1
powershell -Command "$wsh = New-Object -ComObject WScript.Shell; $wsh.SendKeys('{SCROLLLOCK}'); Start-Sleep -Milliseconds 150; $wsh.SendKeys('{SCROLLLOCK}'); Start-Sleep -Milliseconds 150; $wsh.SendKeys('1')"

echo Done. Personal Mac should now be active on all monitors.
```

**File: `C:\Scripts\kvm\switch-all-work.bat`**

```batch
@echo off
REM ============================================================
REM Switch ALL monitors + USB peripherals to WORK MAC
REM ============================================================
SET DP_INPUT=15
SET LEFT_MON=\\.\DISPLAY1\Monitor0
SET RIGHT_MON=\\.\DISPLAY2\Monitor0
REM ============================================================

echo Switching both monitors to Work Mac (DisplayPort)...

start "" /B "C:\Tools\ControlMyMonitor\ControlMyMonitor.exe" /SetValue "%LEFT_MON%" 60 %DP_INPUT%
start "" /B "C:\Tools\ControlMyMonitor\ControlMyMonitor.exe" /SetValue "%RIGHT_MON%" 60 %DP_INPUT%

timeout /t 2 /nobreak >nul

powershell -Command "$wsh = New-Object -ComObject WScript.Shell; $wsh.SendKeys('{SCROLLLOCK}'); Start-Sleep -Milliseconds 150; $wsh.SendKeys('{SCROLLLOCK}'); Start-Sleep -Milliseconds 150; $wsh.SendKeys('2')"

echo Done. Work Mac should now be active on all monitors.
```

**File: `C:\Scripts\kvm\switch-all-hp.bat`**

```batch
@echo off
REM ============================================================
REM Switch ALL monitors + USB peripherals to HP ELITEBOOK
REM ============================================================
SET HDMI1_INPUT=17
SET LEFT_MON=\\.\DISPLAY1\Monitor0
SET RIGHT_MON=\\.\DISPLAY2\Monitor0
REM ============================================================

echo Switching both monitors to HP EliteBook (HDMI 1)...

start "" /B "C:\Tools\ControlMyMonitor\ControlMyMonitor.exe" /SetValue "%LEFT_MON%" 60 %HDMI1_INPUT%
start "" /B "C:\Tools\ControlMyMonitor\ControlMyMonitor.exe" /SetValue "%RIGHT_MON%" 60 %HDMI1_INPUT%

timeout /t 2 /nobreak >nul

powershell -Command "$wsh = New-Object -ComObject WScript.Shell; $wsh.SendKeys('{SCROLLLOCK}'); Start-Sleep -Milliseconds 150; $wsh.SendKeys('{SCROLLLOCK}'); Start-Sleep -Milliseconds 150; $wsh.SendKeys('3')"

echo Done. HP EliteBook should now be active on all monitors.
```

**File: `C:\Scripts\kvm\switch-left-personal.bat`**

```batch
@echo off
SET USB_C_INPUT=27
SET LEFT_MON=\\.\DISPLAY1\Monitor0
"C:\Tools\ControlMyMonitor\ControlMyMonitor.exe" /SetValue "%LEFT_MON%" 60 %USB_C_INPUT%
echo Left monitor switched to Personal Mac.
```

**File: `C:\Scripts\kvm\switch-left-work.bat`**

```batch
@echo off
SET DP_INPUT=15
SET LEFT_MON=\\.\DISPLAY1\Monitor0
"C:\Tools\ControlMyMonitor\ControlMyMonitor.exe" /SetValue "%LEFT_MON%" 60 %DP_INPUT%
echo Left monitor switched to Work Mac.
```

**File: `C:\Scripts\kvm\switch-left-hp.bat`**

```batch
@echo off
SET HDMI1_INPUT=17
SET LEFT_MON=\\.\DISPLAY1\Monitor0
"C:\Tools\ControlMyMonitor\ControlMyMonitor.exe" /SetValue "%LEFT_MON%" 60 %HDMI1_INPUT%
echo Left monitor switched to HP EliteBook.
```

**File: `C:\Scripts\kvm\switch-right-personal.bat`**

```batch
@echo off
SET USB_C_INPUT=27
SET RIGHT_MON=\\.\DISPLAY2\Monitor0
"C:\Tools\ControlMyMonitor\ControlMyMonitor.exe" /SetValue "%RIGHT_MON%" 60 %USB_C_INPUT%
echo Right monitor switched to Personal Mac.
```

**File: `C:\Scripts\kvm\switch-right-work.bat`**

```batch
@echo off
SET DP_INPUT=15
SET RIGHT_MON=\\.\DISPLAY2\Monitor0
"C:\Tools\ControlMyMonitor\ControlMyMonitor.exe" /SetValue "%RIGHT_MON%" 60 %DP_INPUT%
echo Right monitor switched to Work Mac.
```

**File: `C:\Scripts\kvm\switch-right-hp.bat`**

```batch
@echo off
SET HDMI1_INPUT=17
SET RIGHT_MON=\\.\DISPLAY2\Monitor0
"C:\Tools\ControlMyMonitor\ControlMyMonitor.exe" /SetValue "%RIGHT_MON%" 60 %HDMI1_INPUT%
echo Right monitor switched to HP EliteBook.
```

#### Step 3: Test Windows Scripts

Open **Command Prompt** and run:

```batch
C:\Scripts\kvm\switch-all-personal.bat
```

Watch both monitors — they should switch to the Personal Mac's input.

---

## Stream Deck Profile Configuration

Now that all scripts exist on all 3 computers, configure the Stream Deck buttons.

### Step 1: Start on the Personal Mac

1. Make sure the eKL USB switch is set to the **Personal Mac** (so Stream Deck is connected there)
2. Open the **Elgato Stream Deck** software

### Step 2: Create the "KVM Control" Profile

1. Click the **gear icon** (top-right) → **Profiles** tab
2. Click **+** to create a new profile
3. Name it: **KVM Control**
4. Click **OK**

### Step 3: Configure Row 1 — "ALL" Buttons

#### Button 1 (top-left): ALL → Personal Mac

1. In the **Actions** panel on the right, expand **"Stream Deck"** section
2. Drag **"Multi Action"** onto button position **Row 1, Column 1**
3. The Multi Action editor opens. Now add sub-actions:

**Sub-action 1: Run the script**
   - In the actions panel, expand **"System"**
   - Drag **"Open"** into the Multi Action list
   - In the **App/File** field, click the folder icon and browse to:
     - **macOS:** `/Users/[your-username]/scripts/kvm/switch-all-personal.sh`
     - (When configuring on Windows later, use: `C:\Scripts\kvm\switch-all-personal.bat`)

**Sub-action 2: Add a delay**
   - Drag **"Delay"** from the Stream Deck actions into the Multi Action list (below the Open action)
   - Set the delay to **2000** milliseconds (2 seconds) — this gives the script time to execute

4. **Set the button title and icon:**
   - Click the **title area** below the button
   - Type: `ALL` on line 1, `Personal` on line 2
   - Choose a color (e.g., blue for Personal Mac)
   - Optionally: download/create a custom icon (a monitor + computer image)

#### Button 2 (top-center): ALL → Work Mac

1. Drag **"Multi Action"** onto Row 1, Column 2
2. Add **"System → Open"** → path: `~/scripts/kvm/switch-all-work.sh`
3. Add **"Delay"** → 2000ms
4. Title: `ALL` / `Work`
5. Choose a color (e.g., green for Work Mac)

#### Button 3 (top-right-ish): ALL → HP EliteBook

1. Drag **"Multi Action"** onto Row 1, Column 3
2. Add **"System → Open"** → path: `~/scripts/kvm/switch-all-hp.sh`
3. Add **"Delay"** → 2000ms
4. Title: `ALL` / `HP`
5. Choose a color (e.g., orange for HP)

### Step 4: Configure Row 2 — "LEFT" Buttons

#### Button 6 (middle-left): LEFT → Personal Mac

1. Drag **"System → Open"** onto Row 2, Column 1
   - (No need for Multi Action — single monitor scripts don't need delays)
   - Path: `~/scripts/kvm/switch-left-personal.sh`
2. Title: `LEFT` / `Personal`

#### Button 7 (middle-center): LEFT → Work Mac

1. Drag **"System → Open"** onto Row 2, Column 2
   - Path: `~/scripts/kvm/switch-left-work.sh`
2. Title: `LEFT` / `Work`

#### Button 8 (middle-right-ish): LEFT → HP

1. Drag **"System → Open"** onto Row 2, Column 3
   - Path: `~/scripts/kvm/switch-left-hp.sh`
2. Title: `LEFT` / `HP`

### Step 5: Configure Row 3 — "RIGHT" Buttons

#### Button 11 (bottom-left): RIGHT → Personal Mac

1. Path: `~/scripts/kvm/switch-right-personal.sh`
2. Title: `RIGHT` / `Personal`

#### Button 12 (bottom-center): RIGHT → Work Mac

1. Path: `~/scripts/kvm/switch-right-work.sh`
2. Title: `RIGHT` / `Work`

#### Button 13 (bottom-right-ish): RIGHT → HP

1. Path: `~/scripts/kvm/switch-right-hp.sh`
2. Title: `RIGHT` / `HP`

### Step 6: Spare Buttons (Columns 4-5)

Buttons 4, 5, 9, 10, 14, 15 are spare. Ideas for later:
- Toggle mute on monitors
- Adjust brightness up/down
- Launch specific applications
- Open a particular URL

### Step 7: Export the Profile

1. Click **gear icon** → **Profiles** tab
2. Right-click the **KVM Control** profile
3. Click **"Export"**
4. Save the `.streamDeckProfile` file somewhere accessible (e.g., Desktop, or a shared folder/USB drive)

### Step 8: Import on Work Mac

1. Switch the eKL USB switch to the **Work Mac** (the Stream Deck physically moves to Work Mac)
2. Open the **Elgato Stream Deck** software on the Work Mac
3. Click **gear icon** → **Profiles** tab
4. Click the **down arrow** below the profile list → **"Restore"** or simply double-click the exported `.streamDeckProfile` file
5. The profile imports with all button positions

**CRITICAL: Update the script paths for macOS:**
- The exported profile may reference `/Users/[personal-mac-username]/scripts/kvm/...`
- If your Work Mac has a **different username**, you need to update each button's "Open" path
- Click each button → update the path to `/Users/[work-mac-username]/scripts/kvm/...`

> **Tip:** If both Macs use the same username, the paths will be identical and no changes are needed.

### Step 9: Import on HP EliteBook

1. Switch the eKL USB switch to the **HP EliteBook**
2. Open Stream Deck software on Windows
3. Import the profile (double-click the `.streamDeckProfile` file, or use gear → Profiles → Restore)

**CRITICAL: Update ALL script paths for Windows:**
- Every button's "Open" action must point to the Windows `.bat` file instead of the macOS `.sh` file
- Click each button and change the path:
  - `~/scripts/kvm/switch-all-personal.sh` → `C:\Scripts\kvm\switch-all-personal.bat`
  - `~/scripts/kvm/switch-all-work.sh` → `C:\Scripts\kvm\switch-all-work.bat`
  - `~/scripts/kvm/switch-all-hp.sh` → `C:\Scripts\kvm\switch-all-hp.bat`
  - And so on for all 9 buttons

### Step 10: Test from Each Computer

1. **From Personal Mac:** Press "ALL → Work Mac" → verify both monitors switch + USB switches
2. **From Work Mac:** Press "ALL → Personal Mac" → verify everything switches back
3. **From HP:** Press "ALL → Personal Mac" → verify switching works from Windows too
4. Test all 9 buttons from each computer

---

## Auto-Start Configuration

For the one-button switching to work reliably, all background software must start automatically when each computer boots.

### Personal Mac — Auto-Start Checklist

| Software | How to Enable |
|----------|--------------|
| **Lunar** | Lunar Preferences → General → "Launch at Login" ✓ |
| **Input Leap** | System Settings → General → Login Items → add Input Leap |
| **Elgato Stream Deck** | System Settings → General → Login Items → add Stream Deck |

Verify all three appear in **System Settings → General → Login Items** under "Open at Login."

### Work Mac — Auto-Start Checklist

| Software | How to Enable |
|----------|--------------|
| **Lunar** | Lunar Preferences → General → "Launch at Login" ✓ |
| **Input Leap** | System Settings → General → Login Items → add Input Leap |
| **Elgato Stream Deck** | System Settings → General → Login Items → add Stream Deck |

### HP EliteBook — Auto-Start Checklist

| Software | How to Enable |
|----------|--------------|
| **Input Leap** | Shortcut in `shell:startup` folder (see above) |
| **Elgato Stream Deck** | Verify in Task Manager → Startup tab → Enabled |

> **ControlMyMonitor** does NOT need to auto-start — it's a command-line tool called on-demand by the scripts.

### Verify Auto-Start

1. **Restart each computer**
2. After login, verify:
   - Lunar icon appears in the Mac menu bar
   - Input Leap shows "Input Leap is running" (check its window or menu bar icon)
   - Stream Deck software is running (Stream Deck buttons are lit and responsive)
3. Test a Stream Deck switch to make sure everything works after a fresh boot

---

## Verification Walkthrough

Follow this exact sequence to verify the entire system end-to-end. Check off each step.

### Round 1: Full Switch Tests

- [ ] **Currently on Personal Mac.** Press "ALL → Work Mac"
  - [ ] Left monitor switches to Work Mac desktop
  - [ ] Right monitor switches to Work Mac desktop
  - [ ] Keyboard types on Work Mac
  - [ ] Mouse works on Work Mac
  - [ ] Stream Deck buttons are responsive (showing KVM Control profile)
  - [ ] Total switch time: _____ seconds

- [ ] **Currently on Work Mac.** Press "ALL → HP EliteBook"
  - [ ] Left monitor switches to HP desktop
  - [ ] Right monitor switches to HP desktop
  - [ ] Keyboard types on HP
  - [ ] Mouse works on HP
  - [ ] Stream Deck buttons are responsive
  - [ ] Total switch time: _____ seconds

- [ ] **Currently on HP.** Press "ALL → Personal Mac"
  - [ ] Left monitor switches to Personal Mac desktop
  - [ ] Right monitor switches to Personal Mac desktop
  - [ ] Keyboard types on Personal Mac
  - [ ] Mouse works on Personal Mac
  - [ ] Stream Deck buttons are responsive
  - [ ] Total switch time: _____ seconds

### Round 2: Split Mode Tests

- [ ] **Currently on Personal Mac.** Press "LEFT → Work Mac" (only left monitor)
  - [ ] Left monitor switches to Work Mac
  - [ ] Right monitor stays on Personal Mac
  - [ ] Input Leap: move mouse from right monitor to left monitor — cursor should cross to Work Mac

- [ ] **Split mode active.** Press "RIGHT → HP" (now 3-way split)
  - [ ] Left monitor on Work Mac
  - [ ] Right monitor on HP EliteBook
  - [ ] Input Leap: verify cursor moves between all computers

- [ ] **Return to normal.** Press "ALL → Personal Mac"
  - [ ] Both monitors return to Personal Mac
  - [ ] Windows on Personal Mac are in the same positions as before the split

### Round 3: Stress Tests

- [ ] **Rapid switching:** Press "ALL → Work Mac" then immediately "ALL → Personal Mac" (within 2 seconds)
  - [ ] System recovers correctly (may need extra time, but should stabilize)

- [ ] **Sleep/wake:** Put Personal Mac to sleep, switch to Work Mac, wake Personal Mac, switch back
  - [ ] Monitors and DDC/CI still work after wake

- [ ] **Lid close/open:** Close Work Mac's lid, switch to Personal Mac, open lid, switch to Work Mac
  - [ ] Everything still functions

### Round 4: Window Position Tests (EDID)

- [ ] Switch away from Personal Mac and back — are windows in the same positions?
- [ ] Switch away from Work Mac and back — are windows in the same positions?
- [ ] Switch away from HP and back — are windows in the same positions?

> If windows rearrange, you need EDID emulators on the inactive cables. See `KVM-SETUP-GUIDE.md` Phase 3.
