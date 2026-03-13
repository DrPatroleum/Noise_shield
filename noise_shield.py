#!/usr/bin/env python3
"""
NoiseShield - Generator szumu maskujacego rozmowy
Generuje wielowarstwowy szum akustyczny, ktory uniemozliwia nagrywanie i rozumienie rozmow.
"""

import subprocess, sys, os, threading, time, math, random, struct

# ── Auto-instalacja zaleznosci ───────────────────────────────────────────────
def install(pkg):
    subprocess.check_call(
        [sys.executable, "-m", "pip", "install", pkg, "-q", "--break-system-packages"],
        stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL
    )

try:
    import numpy as np
except ImportError:
    print("Instaluje numpy..."); install("numpy"); import numpy as np

try:
    import sounddevice as sd
except ImportError:
    print("Instaluje sounddevice..."); install("sounddevice")
    try:
        import sounddevice as sd
    except OSError:
        print("\n  PortAudio nie jest zainstalowane.")
        print("  Linux: sudo apt install portaudio19-dev")
        print("  macOS: brew install portaudio")
        sys.exit(1)

try:
    import tkinter as tk
    from tkinter import ttk
    HAS_TK = True
except ImportError:
    HAS_TK = False

# ── Parametry audio ──────────────────────────────────────────────────────────
SAMPLE_RATE = 44100
BLOCK_SIZE  = 1024
CHANNELS    = 2

state = {
    "running":    False,
    "volume":     0.7,
    "mode":       "ultra",
    "mod_speed":  0.5,
}

_t_offset = 0.0

# ── Generatory szumu ─────────────────────────────────────────────────────────

def white_noise(n):
    return np.random.uniform(-1, 1, n).astype(np.float32)

def pink_noise(n):
    b = np.zeros(7)
    out = np.zeros(n, dtype=np.float32)
    for i in range(n):
        w = np.random.uniform(-1, 1)
        b[0] = 0.99886*b[0] + w*0.0555179
        b[1] = 0.99332*b[1] + w*0.0750759
        b[2] = 0.96900*b[2] + w*0.1538520
        b[3] = 0.86650*b[3] + w*0.3104856
        b[4] = 0.55000*b[4] + w*0.5329522
        b[5] = -0.7616*b[5] - w*0.0168980
        out[i] = (b[0]+b[1]+b[2]+b[3]+b[4]+b[5]+b[6]+w*0.5362) * 0.11
        b[6] = w * 0.115926
    return out

def brown_noise(n):
    w = np.random.uniform(-1, 1, n)
    out = np.cumsum(w * 0.02).astype(np.float32)
    out -= out.mean()
    peak = np.max(np.abs(out)) + 1e-9
    return (out / peak).astype(np.float32)

_BABBLE = [
    (200,0.08),(320,0.06),(440,0.07),(560,0.05),
    (680,0.04),(820,0.06),(980,0.05),(1200,0.04),
    (1500,0.03),(1800,0.03),(2200,0.02),(2800,0.02),
]

def babble_noise(n, t0=0.0):
    out = np.zeros(n, dtype=np.float32)
    t = np.linspace(t0, t0 + n/SAMPLE_RATE, n, endpoint=False)
    for freq, amp in _BABBLE:
        mod = 0.5 + 0.5*np.sin(2*np.pi*random.uniform(0.3,2.0)*t + random.random()*6.28)
        out += amp * mod * np.sin(2*np.pi*freq*t).astype(np.float32)
    out += white_noise(n) * 0.15
    peak = np.max(np.abs(out)) + 1e-9
    return (out / peak).astype(np.float32)

def ultra_noise(n, t0=0.0):
    base = (white_noise(n)*0.3 + pink_noise(n)*0.4
            + brown_noise(n)*0.2 + babble_noise(n, t0)*0.3)
    t = np.linspace(t0, t0 + n/SAMPLE_RATE, n, endpoint=False)
    for _ in range(8):
        f  = random.uniform(250, 3800)
        a  = random.uniform(0.02, 0.08)
        ph = random.random() * 2 * math.pi
        base += a * np.sin(2*np.pi*f*t + ph).astype(np.float32)
    mod = (0.55 + 0.2*np.sin(2*np.pi*1.3*t)
                + 0.12*np.sin(2*np.pi*3.7*t)
                + 0.08*np.sin(2*np.pi*7.1*t)
                + 0.05*np.sin(2*np.pi*13.3*t))
    base *= mod.astype(np.float32)
    peak = np.max(np.abs(base)) + 1e-9
    return (base / peak).astype(np.float32)

# ── Audio callback ───────────────────────────────────────────────────────────

def audio_callback(outdata, frames, time_info, status):
    global _t_offset
    if not state["running"]:
        outdata[:] = 0
        return
    m = state["mode"]
    if   m == "white":  mono = white_noise(frames)
    elif m == "pink":   mono = pink_noise(frames)
    elif m == "brown":  mono = brown_noise(frames)
    elif m == "babble": mono = babble_noise(frames, _t_offset)
    else:               mono = ultra_noise(frames, _t_offset)
    _t_offset += frames / SAMPLE_RATE
    vol = state["volume"]
    lfo = 1.0 + 0.12 * math.sin(2*math.pi * state["mod_speed"] * _t_offset)
    mono = np.clip(mono * vol * lfo, -1.0, 1.0)
    outdata[:, 0] = mono
    outdata[:, 1] = mono

# ── GUI (tkinter) ────────────────────────────────────────────────────────────

def gui_mode():
    root = tk.Tk()
    root.title("NoiseShield")
    root.resizable(False, False)
    root.configure(bg="#0f0f1a")

    DARK   = "#0f0f1a"
    CARD   = "#1a1a2e"
    ACCENT = "#e94560"
    GREEN  = "#00e676"
    LIGHT  = "#a8dadc"
    TEXT   = "#eaeaea"
    MUTED  = "#666688"

    # ── Header ──────────────────────────────────────────────────────────────
    hdr = tk.Frame(root, bg=ACCENT, pady=10)
    hdr.pack(fill="x")
    tk.Label(hdr, text="  NoiseShield", bg=ACCENT, fg="white",
             font=("Helvetica",17,"bold")).pack(side="left", padx=14)
    tk.Label(hdr, text="Maskowanie rozmów przed podsłuchem",
             bg=ACCENT, fg="#ffe0e0", font=("Helvetica",9)).pack(side="left")

    # ── Body ─────────────────────────────────────────────────────────────────
    body = tk.Frame(root, bg=DARK, padx=22, pady=16)
    body.pack(fill="both")

    # Status
    status_var = tk.StringVar(value="  Zatrzymany")
    status_lbl = tk.Label(body, textvariable=status_var, bg=CARD, fg=ACCENT,
                          font=("Helvetica",13,"bold"), padx=10, pady=7, width=34)
    status_lbl.pack(pady=(0,14))

    # Tryb
    tk.Label(body, text="Tryb szumu", bg=DARK, fg=LIGHT,
             font=("Helvetica",10,"bold")).pack(anchor="w")

    mode_var = tk.StringVar(value="ultra")
    modes = [
        ("Ultra – wielowarstwowy (zalecany)", "ultra"),
        ("Babble – symulacja gwaru ludzi",    "babble"),
        ("Różowy – pasmo mowy 300-3400 Hz",   "pink"),
        ("Biały – pełne spektrum",            "white"),
        ("Brązowy – niskie częstotliwości",   "brown"),
    ]
    mode_frame = tk.Frame(body, bg=CARD, padx=8, pady=6)
    mode_frame.pack(fill="x", pady=(4,12))
    for label, val in modes:
        tk.Radiobutton(mode_frame, text=label, variable=mode_var, value=val,
                       bg=CARD, fg=TEXT, selectcolor=DARK,
                       activebackground=CARD, activeforeground=TEXT,
                       font=("Helvetica",10),
                       command=lambda v=val: state.update({"mode":v})
                       ).pack(anchor="w", pady=2)

    # Glosnosc
    tk.Label(body, text="GŁOŚNOŚĆ", bg=DARK, fg=LIGHT,
             font=("Helvetica",10,"bold")).pack(anchor="w")
    vol_row = tk.Frame(body, bg=DARK); vol_row.pack(fill="x", pady=(2,10))
    vol_lbl = tk.Label(vol_row, text=f"{int(state['volume']*100)}%",
                       bg=DARK, fg=ACCENT, font=("Helvetica",10,"bold"), width=5)
    vol_lbl.pack(side="right")
    vol_var = tk.DoubleVar(value=state["volume"])
    def on_vol(v):
        val = float(v); state["volume"] = val
        vol_lbl.config(text=f"{int(val*100)}%")
    ttk.Scale(vol_row, from_=0.0, to=1.0, orient="horizontal",
              variable=vol_var, command=on_vol).pack(side="left", fill="x", expand=True)

    # Modulacja
    tk.Label(body, text="MODULACJA", bg=DARK, fg=LIGHT,
             font=("Helvetica",10,"bold")).pack(anchor="w")
    mod_row = tk.Frame(body, bg=DARK); mod_row.pack(fill="x", pady=(2,14))
    mod_lbl = tk.Label(mod_row, text=f"{state['mod_speed']:.1f} Hz",
                       bg=DARK, fg=ACCENT, font=("Helvetica",10,"bold"), width=7)
    mod_lbl.pack(side="right")
    mod_var = tk.DoubleVar(value=state["mod_speed"])
    def on_mod(v):
        val = float(v); state["mod_speed"] = val
        mod_lbl.config(text=f"{val:.1f} Hz")
    ttk.Scale(mod_row, from_=0.1, to=5.0, orient="horizontal",
              variable=mod_var, command=on_mod).pack(side="left", fill="x", expand=True)

    # Przycisk START / STOP
    btn_var = tk.StringVar(value="   START")
    btn_bg  = [ACCENT]

    def toggle():
        state["mode"] = mode_var.get()
        state["running"] = not state["running"]
        if state["running"]:
            btn_var.set("   STOP")
            btn.config(bg="#333", fg=GREEN)
            status_var.set("  AKTYWNY – maskowanie włączone")
            status_lbl.config(fg=GREEN)
        else:
            btn_var.set("   START")
            btn.config(bg=ACCENT, fg="white")
            status_var.set("  Zatrzymany")
            status_lbl.config(fg=ACCENT)

    btn = tk.Button(body, textvariable=btn_var, command=toggle,
                    bg=ACCENT, fg="white", font=("Helvetica",14,"bold"),
                    relief="flat", padx=24, pady=12, cursor="hand2",
                    activebackground="#c73652", activeforeground="white",
                    width=26)
    btn.pack(pady=6)

    # Info
    tk.Label(body,
             text="Ustaw głośnik możliwie blisko mikrofonu nagrywającej osoby.\n"
                  "Tryb Ultra łączy kilka rodzajów szumu i jest najtrudniejszy do odfiltrowania.",
             bg=DARK, fg=MUTED, font=("Helvetica",8), justify="center", wraplength=360
             ).pack(pady=(10,0))

    # ── Audio stream ─────────────────────────────────────────────────────────
    try:
        stream = sd.OutputStream(
            samplerate=SAMPLE_RATE, blocksize=BLOCK_SIZE,
            channels=CHANNELS, dtype="float32", callback=audio_callback)
        stream.start()
    except Exception as e:
        tk.messagebox.showerror("Błąd audio", str(e)); root.destroy(); return

    def on_close():
        stream.stop(); stream.close(); root.destroy()

    root.protocol("WM_DELETE_WINDOW", on_close)
    root.mainloop()

# ── TUI (terminal) ────────────────────────────────────────────────────────────

def tui_mode():
    print("\n" + "="*52)
    print("  NoiseShield – Maskowanie rozmów")
    print("="*52)
    print("  Tryby: [1] Ultra  [2] Babble  [3] Rozowy")
    print("         [4] Biały  [5] Brązowy")
    print("  Głośność: [+] więcej  [-] mniej")
    print("  [ENTER] Start/Stop   [Q] Wyjście")
    print("="*52)

    stream = sd.OutputStream(
        samplerate=SAMPLE_RATE, blocksize=BLOCK_SIZE,
        channels=CHANNELS, dtype="float32", callback=audio_callback)
    stream.start()

    mode_map = {"1":"ultra","2":"babble","3":"pink","4":"white","5":"brown"}

    import tty, termios
    fd = sys.stdin.fileno()
    old = termios.tcgetattr(fd)
    msg = "Naciśnij ENTER aby zacząć..."
    try:
        tty.setraw(fd)
        while True:
            sys.stdout.write(f"\r  [{msg}]  Vol={int(state['volume']*100)}%  Tryb={state['mode'].upper()}    ")
            sys.stdout.flush()
            ch = sys.stdin.read(1)
            if ch in mode_map:
                state["mode"] = mode_map[ch]; msg = f"Tryb: {state['mode'].upper()}"
            elif ch == "+":
                state["volume"] = min(1.0, state["volume"]+0.05)
                msg = f"Głośność: {int(state['volume']*100)}%"
            elif ch == "-":
                state["volume"] = max(0.0, state["volume"]-0.05)
                msg = f"Głośność: {int(state['volume']*100)}%"
            elif ch == "\r":
                state["running"] = not state["running"]
                msg = "AKTYWNY" if state["running"] else "ZATRZYMANY"
            elif ch in ("q","Q"):
                break
    finally:
        termios.tcsetattr(fd, termios.TCSADRAIN, old)
        stream.stop(); stream.close()
        print("\n\nZakończono.\n")

# ── Main ──────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    print("\nNoiseShield – sprawdzam urządzenia audio...")
    try:
        devs = [d for d in sd.query_devices() if d["max_output_channels"] > 0]
        if not devs:
            print("Brak urządzeń wyjściowych!"); sys.exit(1)
        print(f"OK – znaleziono {len(devs)} urządzeń wyjściowych.")
    except Exception as e:
        print(f"Błąd: {e}"); sys.exit(1)

    if HAS_TK:
        gui_mode()
    else:
        tui_mode()
