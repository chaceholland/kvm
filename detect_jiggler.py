#!/usr/bin/env python3
"""
Mouse Jiggler Detector (Windows / macOS)
Monitors mouse movement patterns and flags jiggler-like behavior.

Jiggler signatures detected:
  1. Fixed-interval movements (e.g., every 30s or 60s)
  2. Tiny, repetitive displacements (1-5px oscillations)
  3. Perfectly regular timing with low variance
  4. Back-and-forth patterns (move right then left, repeat)
  5. No acceleration curve (real humans have variable speed)

Usage:
    python detect_jiggler.py                      # Monitor and detect (default 5min window)
    python detect_jiggler.py --duration 600       # Monitor for 10 minutes
    python detect_jiggler.py --sensitivity high   # More aggressive detection
    python detect_jiggler.py --log mouse_log.csv  # Save raw data to CSV
    python detect_jiggler.py --demo               # Demo with synthetic data (no OS deps)

Windows: Uses Win32 API via ctypes (no install needed - works with stock Python)
macOS:   Requires pyobjc-framework-Quartz (pip3 install pyobjc-framework-Quartz)
"""

import argparse
import csv
import math
import platform
import signal
import sys
import time
import threading
from collections import deque
from dataclasses import dataclass, field
from datetime import datetime
from statistics import mean, stdev

PLATFORM = platform.system()

# --- Platform-specific imports ---

HAS_QUARTZ = False
HAS_WIN32 = False

if PLATFORM == "Darwin":
    try:
        from Quartz import (
            CGEventGetLocation,
            CGEventGetTimestamp,
            CGEventTapCreate,
            CFMachPortCreateRunLoopSource,
            CFRunLoopAddSource,
            CFRunLoopGetCurrent,
            CFRunLoopRun,
            CFRunLoopStop,
            kCGEventMouseMoved,
            kCGHeadInsertEventTap,
            kCGSessionEventTap,
            kCFRunLoopCommonModes,
        )
        HAS_QUARTZ = True
    except ImportError:
        pass

if PLATFORM == "Windows":
    try:
        import ctypes
        import ctypes.wintypes
        HAS_WIN32 = True
    except ImportError:
        pass


@dataclass
class MouseEvent:
    timestamp: float  # seconds since epoch
    x: float
    y: float


@dataclass
class AnalysisResult:
    is_jiggler: bool
    confidence: float  # 0.0 to 1.0
    reasons: list = field(default_factory=list)
    stats: dict = field(default_factory=dict)


class JigglerDetector:
    """Analyzes mouse movement patterns to detect jiggler behavior."""

    def __init__(self, window_seconds=300, sensitivity="medium"):
        self.events = deque()
        self.window_seconds = window_seconds
        self.sensitivity = sensitivity
        self.start_time = time.time()

        # Sensitivity thresholds
        thresholds = {
            "low":    {"interval_cv_max": 0.08, "displacement_max": 8,  "confidence_min": 0.75},
            "medium": {"interval_cv_max": 0.15, "displacement_max": 12, "confidence_min": 0.60},
            "high":   {"interval_cv_max": 0.25, "displacement_max": 20, "confidence_min": 0.45},
        }
        self.thresholds = thresholds.get(sensitivity, thresholds["medium"])

    def add_event(self, event: MouseEvent):
        self.events.append(event)
        # Trim events outside the analysis window
        cutoff = time.time() - self.window_seconds
        while self.events and self.events[0].timestamp < cutoff:
            self.events.popleft()

    def analyze(self) -> AnalysisResult:
        events = list(self.events)
        if len(events) < 10:
            return AnalysisResult(
                is_jiggler=False, confidence=0.0,
                reasons=["Insufficient data (need at least 10 movements)"],
                stats={"event_count": len(events)}
            )

        reasons = []
        scores = []

        # --- 1. Interval regularity ---
        intervals = []
        for i in range(1, len(events)):
            dt = events[i].timestamp - events[i - 1].timestamp
            if dt > 0.01:  # ignore duplicate timestamps
                intervals.append(dt)

        if len(intervals) >= 5:
            avg_interval = mean(intervals)
            std_interval = stdev(intervals) if len(intervals) > 1 else 0
            cv = std_interval / avg_interval if avg_interval > 0 else 999

            if cv < self.thresholds["interval_cv_max"]:
                score = max(0, 1.0 - (cv / self.thresholds["interval_cv_max"]))
                scores.append(("interval_regularity", score))
                reasons.append(
                    f"Suspiciously regular timing: avg={avg_interval:.2f}s, "
                    f"CV={cv:.3f} (threshold={self.thresholds['interval_cv_max']})"
                )
        else:
            avg_interval = 0
            std_interval = 0
            cv = 999

        # --- 2. Displacement analysis ---
        displacements = []
        for i in range(1, len(events)):
            dx = events[i].x - events[i - 1].x
            dy = events[i].y - events[i - 1].y
            dist = math.sqrt(dx * dx + dy * dy)
            displacements.append(dist)

        if displacements:
            avg_disp = mean(displacements)
            max_disp = max(displacements)

            if avg_disp < self.thresholds["displacement_max"] and avg_disp > 0:
                score = max(0, 1.0 - (avg_disp / self.thresholds["displacement_max"]))
                scores.append(("tiny_movements", score))
                reasons.append(
                    f"Very small movements: avg={avg_disp:.1f}px, "
                    f"max={max_disp:.1f}px"
                )

            # Check displacement variance (jigglers have uniform displacement)
            if len(displacements) > 1:
                disp_std = stdev(displacements)
                disp_cv = disp_std / avg_disp if avg_disp > 0 else 999
                if disp_cv < 0.3:
                    scores.append(("uniform_displacement", 1.0 - disp_cv / 0.3))
                    reasons.append(
                        f"Uniform displacement size: CV={disp_cv:.3f}"
                    )

        # --- 3. Oscillation / back-and-forth pattern ---
        if len(events) >= 6:
            reversals_x = 0
            reversals_y = 0
            for i in range(2, len(events)):
                dx1 = events[i - 1].x - events[i - 2].x
                dx2 = events[i].x - events[i - 1].x
                dy1 = events[i - 1].y - events[i - 2].y
                dy2 = events[i].y - events[i - 1].y
                if dx1 * dx2 < 0:
                    reversals_x += 1
                if dy1 * dy2 < 0:
                    reversals_y += 1

            total_moves = len(events) - 2
            reversal_ratio = max(reversals_x, reversals_y) / total_moves if total_moves > 0 else 0

            if reversal_ratio > 0.7:
                score = min(1.0, (reversal_ratio - 0.7) / 0.25)
                scores.append(("oscillation", score))
                reasons.append(
                    f"Back-and-forth oscillation: {reversal_ratio:.0%} reversals "
                    f"(x={reversals_x}, y={reversals_y} out of {total_moves} moves)"
                )

        # --- 4. Lack of acceleration curve ---
        if len(displacements) >= 10:
            speeds = []
            for i in range(len(intervals)):
                if i < len(displacements) and intervals[i] > 0:
                    speeds.append(displacements[i] / intervals[i])

            if len(speeds) >= 5:
                speed_std = stdev(speeds) if len(speeds) > 1 else 0
                speed_mean = mean(speeds)
                speed_cv = speed_std / speed_mean if speed_mean > 0 else 999

                if speed_cv < 0.2:
                    score = max(0, 1.0 - speed_cv / 0.2)
                    scores.append(("constant_speed", score))
                    reasons.append(
                        f"Unnaturally constant speed: CV={speed_cv:.3f}"
                    )

        # --- 5. Positional clustering (jiggler stays in small area) ---
        if len(events) >= 10:
            xs = [e.x for e in events]
            ys = [e.y for e in events]
            x_range = max(xs) - min(xs)
            y_range = max(ys) - min(ys)
            bounding_area = x_range * y_range if x_range > 0 and y_range > 0 else 0

            if bounding_area < 2500 and bounding_area > 0:  # < 50x50 pixel area
                score = max(0, 1.0 - bounding_area / 2500)
                scores.append(("positional_cluster", score))
                reasons.append(
                    f"Movement confined to {x_range:.0f}x{y_range:.0f}px area "
                    f"({bounding_area:.0f}px\u00b2)"
                )

        # --- Compute overall confidence ---
        if scores:
            weights = {
                "interval_regularity": 3.0,
                "tiny_movements": 2.0,
                "uniform_displacement": 1.5,
                "oscillation": 2.5,
                "constant_speed": 2.0,
                "positional_cluster": 1.5,
            }
            total_weight = sum(weights.get(name, 1.0) for name, _ in scores)
            weighted_sum = sum(weights.get(name, 1.0) * s for name, s in scores)
            confidence = weighted_sum / total_weight if total_weight > 0 else 0

            # Boost confidence if multiple indicators fire
            indicator_bonus = min(0.15, len(scores) * 0.03)
            confidence = min(1.0, confidence + indicator_bonus)
        else:
            confidence = 0.0

        is_jiggler = confidence >= self.thresholds["confidence_min"]

        stats = {
            "event_count": len(events),
            "window_seconds": self.window_seconds,
            "avg_interval": round(avg_interval, 3) if intervals else None,
            "interval_cv": round(cv, 4) if intervals else None,
            "avg_displacement": round(mean(displacements), 2) if displacements else None,
            "indicators_triggered": len(scores),
            "indicator_details": {name: round(s, 3) for name, s in scores},
        }

        return AnalysisResult(
            is_jiggler=is_jiggler,
            confidence=confidence,
            reasons=reasons if reasons else ["No jiggler patterns detected"],
            stats=stats,
        )


def format_result(result: AnalysisResult) -> str:
    """Format analysis result for terminal display."""
    now = datetime.now().strftime("%H:%M:%S")
    lines = []

    if result.is_jiggler:
        lines.append(f"\n[{now}] *** JIGGLER DETECTED (confidence: {result.confidence:.0%}) ***")
    else:
        lines.append(f"\n[{now}] No jiggler detected (confidence: {result.confidence:.0%})")

    lines.append(f"  Events analyzed: {result.stats.get('event_count', 0)}")

    if result.stats.get("avg_interval"):
        lines.append(f"  Avg interval: {result.stats['avg_interval']:.2f}s "
                      f"(CV: {result.stats.get('interval_cv', 'N/A')})")

    if result.stats.get("avg_displacement") is not None:
        lines.append(f"  Avg displacement: {result.stats['avg_displacement']:.1f}px")

    if result.reasons:
        lines.append("  Indicators:")
        for reason in result.reasons:
            marker = "!!" if result.is_jiggler else "  "
            lines.append(f"    {marker} {reason}")

    return "\n".join(lines)


# ============================================================
# Windows monitor: polls GetCursorPos via ctypes (no pip install)
# ============================================================

def run_monitor_windows(args):
    """Run live mouse monitoring on Windows using Win32 GetCursorPos polling."""
    if not HAS_WIN32:
        print("Error: ctypes not available. This should not happen on Windows.")
        sys.exit(1)

    detector = JigglerDetector(
        window_seconds=args.duration,
        sensitivity=args.sensitivity,
    )

    csv_writer = None
    csv_file = None
    if args.log:
        csv_file = open(args.log, "w", newline="")
        csv_writer = csv.writer(csv_file)
        csv_writer.writerow(["timestamp", "x", "y"])

    # Poll interval: 50ms gives good resolution without high CPU
    poll_interval = 0.05
    analysis_interval = 10  # print analysis every 10 seconds
    last_analysis = time.time()
    last_x, last_y = None, None

    class POINT(ctypes.Structure):
        _fields_ = [("x", ctypes.c_long), ("y", ctypes.c_long)]

    GetCursorPos = ctypes.windll.user32.GetCursorPos

    running = threading.Event()
    running.set()

    print(f"Monitoring mouse movements on Windows (window={args.duration}s, sensitivity={args.sensitivity})")
    print(f"Polling every {poll_interval * 1000:.0f}ms, analysis every {analysis_interval}s.")
    print(f"Press Ctrl+C to stop and see final report.\n")

    def handle_signal(sig, frame):
        running.clear()

    signal.signal(signal.SIGINT, handle_signal)

    while running.is_set():
        pt = POINT()
        GetCursorPos(ctypes.byref(pt))
        now = time.time()
        cx, cy = pt.x, pt.y

        # Only record when position actually changes
        if last_x is None or cx != last_x or cy != last_y:
            if last_x is not None:  # skip the very first reading
                evt = MouseEvent(timestamp=now, x=float(cx), y=float(cy))
                detector.add_event(evt)

                if csv_writer:
                    csv_writer.writerow([f"{now:.4f}", f"{cx}", f"{cy}"])

            last_x, last_y = cx, cy

        # Periodic analysis
        if now - last_analysis >= analysis_interval:
            last_analysis = now
            result = detector.analyze()
            print(format_result(result))

        time.sleep(poll_interval)

    # Final report on Ctrl+C
    print("\n\nFinal analysis:")
    result = detector.analyze()
    print(format_result(result))
    if csv_file:
        csv_file.close()
        print(f"\nRaw data saved to {args.log}")


# ============================================================
# Windows low-level hook monitor (captures injected events)
# ============================================================

def run_monitor_windows_hook(args):
    """
    Run live mouse monitoring on Windows using a low-level mouse hook.
    This method can detect the LLMHF_INJECTED flag, which reveals
    software-generated mouse events (software jigglers).
    """
    if not HAS_WIN32:
        print("Error: ctypes not available.")
        sys.exit(1)

    detector = JigglerDetector(
        window_seconds=args.duration,
        sensitivity=args.sensitivity,
    )

    injected_count = [0]
    total_move_count = [0]

    csv_writer = None
    csv_file = None
    if args.log:
        csv_file = open(args.log, "w", newline="")
        csv_writer = csv.writer(csv_file)
        csv_writer.writerow(["timestamp", "x", "y", "injected"])

    analysis_interval = 10
    last_analysis = [time.time()]

    # Win32 constants
    WH_MOUSE_LL = 14
    WM_MOUSEMOVE = 0x0200
    LLMHF_INJECTED = 0x00000001

    class MSLLHOOKSTRUCT(ctypes.Structure):
        _fields_ = [
            ("pt", ctypes.wintypes.POINT),
            ("mouseData", ctypes.wintypes.DWORD),
            ("flags", ctypes.wintypes.DWORD),
            ("time", ctypes.wintypes.DWORD),
            ("dwExtraInfo", ctypes.POINTER(ctypes.c_ulong)),
        ]

    HOOKPROC = ctypes.CFUNCTYPE(
        ctypes.c_long,
        ctypes.c_int,
        ctypes.wintypes.WPARAM,
        ctypes.wintypes.LPARAM,
    )

    user32 = ctypes.windll.user32
    kernel32 = ctypes.windll.kernel32

    SetWindowsHookExW = user32.SetWindowsHookExW
    CallNextHookEx = user32.CallNextHookEx
    UnhookWindowsHookEx = user32.UnhookWindowsHookEx
    GetMessageW = user32.GetMessageW
    PostThreadMessageW = user32.PostThreadMessageW

    hook_handle = [None]

    def low_level_mouse_proc(nCode, wParam, lParam):
        if nCode >= 0 and wParam == WM_MOUSEMOVE:
            ms = ctypes.cast(lParam, ctypes.POINTER(MSLLHOOKSTRUCT)).contents
            now = time.time()
            is_injected = bool(ms.flags & LLMHF_INJECTED)

            total_move_count[0] += 1
            if is_injected:
                injected_count[0] += 1

            evt = MouseEvent(timestamp=now, x=float(ms.pt.x), y=float(ms.pt.y))
            detector.add_event(evt)

            if csv_writer:
                csv_writer.writerow([f"{now:.4f}", f"{ms.pt.x}", f"{ms.pt.y}", int(is_injected)])

            if now - last_analysis[0] >= analysis_interval:
                last_analysis[0] = now
                result = detector.analyze()
                # Add injected event info to output
                pct = (injected_count[0] / total_move_count[0] * 100) if total_move_count[0] > 0 else 0
                extra = f"\n  Injected events: {injected_count[0]}/{total_move_count[0]} ({pct:.1f}%)"
                if pct > 5:
                    extra += "  <-- SOFTWARE JIGGLER DETECTED (injected flag set)"
                print(format_result(result) + extra)

        return CallNextHookEx(hook_handle[0], nCode, wParam, lParam)

    # Must keep a reference to the callback to prevent garbage collection
    hook_proc_cb = HOOKPROC(low_level_mouse_proc)

    hook_handle[0] = SetWindowsHookExW(
        WH_MOUSE_LL,
        hook_proc_cb,
        kernel32.GetModuleHandleW(None),
        0,
    )

    if not hook_handle[0]:
        print("Error: Could not install mouse hook.")
        print("Try running as Administrator.")
        sys.exit(1)

    print(f"Monitoring mouse via low-level hook (window={args.duration}s, sensitivity={args.sensitivity})")
    print(f"This mode also detects the INJECTED flag on software-generated mouse events.")
    print(f"Analysis every {analysis_interval}s. Press Ctrl+C to stop.\n")

    def handle_signal(sig, frame):
        UnhookWindowsHookEx(hook_handle[0])
        print("\n\nFinal analysis:")
        result = detector.analyze()
        pct = (injected_count[0] / total_move_count[0] * 100) if total_move_count[0] > 0 else 0
        extra = f"\n  Injected events: {injected_count[0]}/{total_move_count[0]} ({pct:.1f}%)"
        if pct > 5:
            extra += "  <-- SOFTWARE JIGGLER DETECTED (injected flag set)"
        print(format_result(result) + extra)
        if csv_file:
            csv_file.close()
            print(f"\nRaw data saved to {args.log}")
        sys.exit(0)

    signal.signal(signal.SIGINT, handle_signal)

    # Message loop (required for low-level hooks)
    msg = ctypes.wintypes.MSG()
    while GetMessageW(ctypes.byref(msg), None, 0, 0) != 0:
        pass


# ============================================================
# macOS monitor
# ============================================================

def run_monitor_macos(args):
    """Run live mouse monitoring on macOS using Quartz event taps."""
    if not HAS_QUARTZ:
        print("Error: pyobjc-framework-Quartz is required for live monitoring on macOS.")
        print("Install it with: pip3 install pyobjc-framework-Quartz")
        print("\nAlternatively, use --demo to see detection on synthetic data.")
        sys.exit(1)

    detector = JigglerDetector(
        window_seconds=args.duration,
        sensitivity=args.sensitivity,
    )

    csv_writer = None
    csv_file = None
    if args.log:
        csv_file = open(args.log, "w", newline="")
        csv_writer = csv.writer(csv_file)
        csv_writer.writerow(["timestamp", "x", "y"])

    last_analysis = [time.time()]
    analysis_interval = 10

    def callback(proxy, event_type, event, refcon):
        loc = CGEventGetLocation(event)
        ts = time.time()
        evt = MouseEvent(timestamp=ts, x=loc.x, y=loc.y)
        detector.add_event(evt)

        if csv_writer:
            csv_writer.writerow([f"{ts:.4f}", f"{loc.x:.1f}", f"{loc.y:.1f}"])

        now = time.time()
        if now - last_analysis[0] >= analysis_interval:
            last_analysis[0] = now
            result = detector.analyze()
            print(format_result(result))

        return event

    tap = CGEventTapCreate(
        kCGSessionEventTap,
        kCGHeadInsertEventTap,
        0,
        1 << kCGEventMouseMoved,
        callback,
        None,
    )

    if tap is None:
        print("Error: Could not create event tap.")
        print("Grant Accessibility permission to Terminal/iTerm in:")
        print("  System Settings > Privacy & Security > Accessibility")
        sys.exit(1)

    source = CFMachPortCreateRunLoopSource(None, tap, 0)
    CFRunLoopAddSource(CFRunLoopGetCurrent(), source, kCFRunLoopCommonModes)

    print(f"Monitoring mouse movements (window={args.duration}s, sensitivity={args.sensitivity})")
    print(f"Analysis every {analysis_interval}s. Press Ctrl+C to stop.\n")

    def handle_signal(sig, frame):
        print("\n\nFinal analysis:")
        result = detector.analyze()
        print(format_result(result))
        if csv_file:
            csv_file.close()
            print(f"\nRaw data saved to {args.log}")
        CFRunLoopStop(CFRunLoopGetCurrent())
        sys.exit(0)

    signal.signal(signal.SIGINT, handle_signal)
    CFRunLoopRun()


# ============================================================
# Demo mode
# ============================================================

def run_demo(args):
    """Run detection on synthetic jiggler-like data for demonstration."""
    print("=== Demo Mode: Simulating mouse jiggler patterns ===\n")

    detector = JigglerDetector(window_seconds=300, sensitivity=args.sensitivity)

    print("--- Scenario 1: Classic jiggler (1px oscillation every 30s) ---")
    base_time = time.time()
    for i in range(20):
        x = 500 + (1 if i % 2 == 0 else -1)
        y = 400
        detector.add_event(MouseEvent(timestamp=base_time + i * 30, x=x, y=y))
    result = detector.analyze()
    print(format_result(result))

    detector2 = JigglerDetector(window_seconds=300, sensitivity=args.sensitivity)
    print("\n--- Scenario 2: Normal human mouse usage ---")
    import random
    random.seed(42)
    x, y = 500.0, 400.0
    t = time.time()
    for i in range(40):
        dt = random.uniform(0.1, 3.0)
        t += dt
        dx = random.gauss(0, 50)
        dy = random.gauss(0, 30)
        x = max(0, min(2560, x + dx))
        y = max(0, min(1440, y + dy))
        detector2.add_event(MouseEvent(timestamp=t, x=x, y=y))
    result2 = detector2.analyze()
    print(format_result(result2))

    detector3 = JigglerDetector(window_seconds=300, sensitivity=args.sensitivity)
    print("\n--- Scenario 3: Software jiggler (micro-circle every 45s) ---")
    t = time.time()
    cx, cy = 800, 600
    for i in range(16):
        angle = (i % 4) * (math.pi / 2)
        x = cx + 3 * math.cos(angle)
        y = cy + 3 * math.sin(angle)
        detector3.add_event(MouseEvent(timestamp=t + i * 45, x=x, y=y))
    result3 = detector3.analyze()
    print(format_result(result3))

    print("\n=== Demo complete ===")


# ============================================================
# Main
# ============================================================

def main():
    parser = argparse.ArgumentParser(
        description="Detect mouse jiggler activity (Windows & macOS)",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python detect_jiggler.py                     # Live monitor (5min window)
  python detect_jiggler.py --duration 600      # 10-minute analysis window
  python detect_jiggler.py --sensitivity high  # Catch subtler jigglers
  python detect_jiggler.py --log data.csv      # Save raw events to CSV
  python detect_jiggler.py --hook              # Windows: use low-level hook (detects injected events)
  python detect_jiggler.py --demo              # Demo with synthetic data
        """,
    )
    parser.add_argument(
        "--duration", type=int, default=300,
        help="Analysis window in seconds (default: 300)",
    )
    parser.add_argument(
        "--sensitivity", choices=["low", "medium", "high"], default="medium",
        help="Detection sensitivity (default: medium)",
    )
    parser.add_argument(
        "--log", type=str, default=None,
        help="Save raw mouse events to CSV file",
    )
    parser.add_argument(
        "--hook", action="store_true",
        help="Windows only: use low-level mouse hook to detect injected/synthetic events",
    )
    parser.add_argument(
        "--demo", action="store_true",
        help="Run demo with synthetic data (no OS dependencies needed)",
    )

    args = parser.parse_args()

    if args.demo:
        run_demo(args)
    elif PLATFORM == "Windows":
        if args.hook:
            run_monitor_windows_hook(args)
        else:
            run_monitor_windows(args)
    elif PLATFORM == "Darwin":
        run_monitor_macos(args)
    else:
        print(f"Unsupported platform: {PLATFORM}")
        print("Use --demo to test the detection logic.")
        sys.exit(1)


if __name__ == "__main__":
    main()
