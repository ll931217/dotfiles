#!/home/ll931217/.local/share/voice-dictate-venv/bin/python
"""Voice dictation for i3wm. Toggle: press once to start, again to stop.

Records audio → streams to faster-whisper in chunks → types text in real-time.
"""

import os
import sys
import shutil
import signal
import subprocess
import tempfile
import threading
import time
from pathlib import Path

import numpy as np
import tkinter as tk
from faster_whisper import WhisperModel

PID_FILE = Path(tempfile.gettempdir()) / "voice-dictate.pid"
MAX_DURATION = 120
WINDOW_SIZE = 160

SAMPLE_RATE = 16000
CHUNK_SECONDS = 3
CHUNK_SAMPLES = SAMPLE_RATE * CHUNK_SECONDS
MIN_SAMPLES = SAMPLE_RATE  # 1 second minimum to transcribe

BG = "#1e1e2e"
ACCENT = "#89b4fa"
MIC_COLOR = "#f38ba8"
TEXT_COLOR = "#cdd6f4"

_model = None


def notify(msg):
    subprocess.Popen(
        ["notify-send", "-u", "low", "Voice Dictation", msg],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )


def require(cmd):
    if not shutil.which(cmd):
        notify(f"'{cmd}' not found")
        sys.exit(1)


def load_model():
    global _model
    if _model is None:
        _model = WhisperModel("small", device="cuda", compute_type="int8_float16")
    return _model


def lerp_color(a, b, t):
    ar, ag, ab = int(a[1:3], 16), int(a[3:5], 16), int(a[5:7], 16)
    br, bg, bb = int(b[1:3], 16), int(b[3:5], 16), int(b[5:7], 16)
    return "#{:02x}{:02x}{:02x}".format(
        int(ar + (br - ar) * t),
        int(ag + (bg - ag) * t),
        int(ab + (bb - ab) * t),
    )


def get_active_window():
    r = subprocess.run(
        ["xdotool", "getactivewindow"],
        capture_output=True,
        text=True,
    )
    return r.stdout.strip() if r.returncode == 0 else None


def type_text(text, window_id):
    if not text:
        return
    if window_id:
        subprocess.run(["xdotool", "windowactivate", "--sync", window_id])
        time.sleep(0.05)
    subprocess.run(["xdotool", "type", "--clearmodifiers", "--delay", "12", text])


# ── Streaming transcription ──────────────────────────────────────────────────


def start_ffmpeg():
    return subprocess.Popen(
        [
            "ffmpeg", "-y", "-loglevel", "quiet",
            "-f", "pulse", "-i", "default",
            "-ac", "1", "-ar", str(SAMPLE_RATE),
            "-acodec", "pcm_s16le", "-f", "s16le", "pipe:1",
        ],
        stdout=subprocess.PIPE,
        stderr=subprocess.DEVNULL,
    )


def stream_transcribe(ffmpeg_proc, window_id, stop_event):
    model = load_model()
    buffer = np.array([], dtype=np.float32)

    while not stop_event.is_set():
        raw = ffmpeg_proc.stdout.read(CHUNK_SAMPLES * 2)
        if not raw:
            break
        samples = np.frombuffer(raw, dtype=np.int16).astype(np.float32) / 32768.0
        buffer = np.concatenate([buffer, samples])

        while len(buffer) >= CHUNK_SAMPLES:
            chunk = buffer[:CHUNK_SAMPLES]
            buffer = buffer[CHUNK_SAMPLES:]
            _transcribe_chunk(model, chunk, window_id)

    # Flush remaining audio
    if len(buffer) >= MIN_SAMPLES:
        _transcribe_chunk(model, buffer, window_id)


def _transcribe_chunk(model, audio, window_id):
    segments, _ = model.transcribe(audio, beam_size=3, vad_filter=True)
    text = "".join(seg.text for seg in segments).strip()
    if text:
        type_text(" " + text, window_id)


# ── UI ───────────────────────────────────────────────────────────────────────


class RecordingWindow:
    def __init__(self):
        self.root = tk.Tk()
        self.root.withdraw()
        self.root.overrideredirect(True)
        self.root.attributes("-topmost", True)
        self.root.configure(bg=BG)

        sw = self.root.winfo_screenwidth()
        sh = self.root.winfo_screenheight()
        x = (sw - WINDOW_SIZE) // 2
        y = (sh - WINDOW_SIZE) // 2
        self.root.geometry(f"{WINDOW_SIZE}x{WINDOW_SIZE}+{x}+{y}")

        self.canvas = tk.Canvas(
            self.root,
            width=WINDOW_SIZE,
            height=WINDOW_SIZE,
            bg=BG,
            highlightthickness=0,
        )
        self.canvas.pack()

        self.canvas.bind("<Button-1>", lambda _: self.stop())
        self.root.bind("<Escape>", lambda _: self.stop())

        self._running = True
        self._phase = 0.0
        self._draw()
        self.root.deiconify()

    def _draw(self):
        if not self._running:
            return
        self.canvas.delete("all")
        cx, cy = WINDOW_SIZE // 2, WINDOW_SIZE // 2 - 8

        for i in range(4):
            p = (self._phase + i * 0.25) % 1.0
            r = 22 + 38 * p
            alpha = 1.0 - p
            color = lerp_color(ACCENT, BG, 1 - alpha)
            self.canvas.create_oval(
                cx - r, cy - r, cx + r, cy + r,
                outline=color, width=max(1, int(2.5 * alpha)),
            )

        self.canvas.create_oval(
            cx - 12, cy - 12, cx + 12, cy + 12,
            fill=MIC_COLOR, outline=MIC_COLOR,
        )
        self.canvas.create_rectangle(
            cx - 3, cy - 22, cx + 3, cy - 12,
            fill=MIC_COLOR, outline=MIC_COLOR,
        )
        self.canvas.create_arc(
            cx - 9, cy - 4, cx + 9, cy + 12,
            start=0, extent=-180, style=tk.ARC,
            outline=MIC_COLOR, width=2,
        )
        self.canvas.create_line(cx, cy + 8, cx, cy + 18, fill=MIC_COLOR, width=2)
        self.canvas.create_line(
            cx - 7, cy + 18, cx + 7, cy + 18, fill=MIC_COLOR, width=2
        )

        self.canvas.create_text(
            cx, cy + 35, text="Recording…",
            fill=TEXT_COLOR, font=("sans-serif", 8),
        )

        self._phase = (self._phase + 0.018) % 1.0
        self.root.after(40, self._draw)

    def stop(self):
        self._running = False
        self.root.quit()

    def run(self):
        self.root.mainloop()
        try:
            self.root.destroy()
        except tk.TclError:
            pass


# ── Main ─────────────────────────────────────────────────────────────────────


def main():
    require("ffmpeg")
    require("xdotool")

    # Toggle: signal existing instance to stop
    if PID_FILE.exists():
        try:
            pid = int(PID_FILE.read_text().strip())
            os.kill(pid, signal.SIGUSR1)
        except (ProcessLookupError, ValueError, PermissionError):
            PID_FILE.unlink(missing_ok=True)
        sys.exit(0)

    PID_FILE.write_text(str(os.getpid()))

    active_win = get_active_window()

    # Start ffmpeg piping raw PCM to stdout
    ffmpeg_proc = start_ffmpeg()

    # Stream transcribe in background thread
    stop_event = threading.Event()
    transcriber = threading.Thread(
        target=stream_transcribe,
        args=(ffmpeg_proc, active_win, stop_event),
        daemon=True,
    )
    transcriber.start()

    # Show recording window (main thread, blocks until stopped)
    stop_flag = [False]
    start_time = [time.time()]

    def on_signal(signum, frame):
        stop_flag[0] = True

    signal.signal(signal.SIGUSR1, on_signal)

    win = RecordingWindow()

    def poll():
        if stop_flag[0] or time.time() - start_time[0] > MAX_DURATION:
            win.stop()
            return
        win.root.after(100, poll)

    win.root.after(100, poll)
    win.run()

    # Stop everything
    stop_event.set()
    ffmpeg_proc.terminate()
    try:
        ffmpeg_proc.wait(timeout=3)
    except subprocess.TimeoutExpired:
        ffmpeg_proc.kill()

    transcriber.join(timeout=10)
    PID_FILE.unlink(missing_ok=True)


if __name__ == "__main__":
    main()
