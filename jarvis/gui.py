# -*- coding: utf-8 -*-
"""
gui.py - Futuristic dark-themed GUI for the Jarvis AI Assistant.

Built with customtkinter.  Provides:
  • Animated pulsing orb that changes colour based on state.
  • Scrollable conversation log (chat-style).
  • Text input for typing commands manually.
  • Mic toggle button for voice activation.
  • Full integration with speech_engine and commands modules.

Usage:
    python gui.py
"""

from __future__ import annotations

import sys
import os
import math
import threading
import datetime
import queue

# Ensure sibling modules can be imported
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import customtkinter as ctk
import speech_recognition as sr

from config import ASSISTANT_NAME, WAKE_WORD, SCHEDULED_REMINDERS
from speech_engine import speak as _tts_speak
from commands import handle_command

# ──────────────────────────────────────────────
#  Theme & colour constants
# ──────────────────────────────────────────────
BG_DARK       = "#0a0a0f"      # Window background
BG_PANEL      = "#12121a"      # Side panels / cards
BG_INPUT      = "#1a1a2e"      # Text entry background
ACCENT_BLUE   = "#00d4ff"      # Primary accent (idle orb)
ACCENT_GREEN  = "#00ff88"      # Listening state
ACCENT_ORANGE = "#ff9500"      # Processing / speaking
ACCENT_RED    = "#ff3b5c"      # Error
TEXT_PRIMARY  = "#e0e0e0"
TEXT_DIM      = "#6a6a80"
FONT_FAMILY   = "Segoe UI"

# ──────────────────────────────────────────────
#  State enum
# ──────────────────────────────────────────────
STATE_IDLE       = "idle"
STATE_WAITING    = "waiting"     # Waiting for wake word
STATE_LISTENING  = "listening"
STATE_PROCESSING = "processing"
STATE_SPEAKING   = "speaking"
STATE_ERROR      = "error"

STATE_COLOURS = {
    STATE_IDLE:       ACCENT_BLUE,
    STATE_WAITING:    ACCENT_BLUE,
    STATE_LISTENING:  ACCENT_GREEN,
    STATE_PROCESSING: ACCENT_ORANGE,
    STATE_SPEAKING:   ACCENT_ORANGE,
    STATE_ERROR:      ACCENT_RED,
}

STATE_LABELS = {
    STATE_IDLE:       "Ready",
    STATE_WAITING:    'Say "Hey Jarvis" …',
    STATE_LISTENING:  "Listening …",
    STATE_PROCESSING: "Processing …",
    STATE_SPEAKING:   "Speaking …",
    STATE_ERROR:      "Error — retrying …",
}


# ══════════════════════════════════════════════
#  Main application window
# ══════════════════════════════════════════════

class JarvisGUI(ctk.CTk):
    """Top-level Jarvis GUI window."""

    WIDTH  = 1000
    HEIGHT = 720

    def __init__(self) -> None:
        super().__init__()

        # --- window setup ---
        self.title(f"{ASSISTANT_NAME} — AI Assistant")
        self.geometry(f"{self.WIDTH}x{self.HEIGHT}")
        self.minsize(700, 500)
        self.configure(fg_color=BG_DARK)
        ctk.set_appearance_mode("dark")
        ctk.set_default_color_theme("blue")

        # --- internal state ---
        self._state: str = STATE_IDLE
        self._mic_active = False               # Is the voice loop running?
        self._voice_thread: threading.Thread | None = None
        self._msg_queue: queue.Queue = queue.Queue()   # Thread → UI messages
        self._anim_angle = 0.0                 # Rotating halo / elements
        self._breath_phase = 0.0                   # Breathing animation cycle
        self._blink_timer = 0                      # Frames until next blink
        self._is_blinking = False
        self._mouth_open = False                   # Mouth moves when speaking

        # --- build UI ---
        self._build_header()
        self._build_centre()
        self._build_input_bar()

        # --- scheduled reminders ---
        self._fired_reminders: set = set()    # Track which reminders already fired today

        # --- periodic UI updaters ---
        self._poll_queue()
        self._animate_character()
        self._check_reminders()                # Start reminder checker

        # --- greeting ---
        self._post_jarvis("Systems online. Say \"Hey Jarvis\" or type a command below.")

        self.protocol("WM_DELETE_WINDOW", self._on_close)

    # ──────────────────────────────────────────
    #  Layout builders
    # ──────────────────────────────────────────

    def _build_header(self) -> None:
        """Top bar with title and mic toggle."""
        header = ctk.CTkFrame(self, fg_color=BG_PANEL, corner_radius=0, height=56)
        header.pack(fill="x")
        header.pack_propagate(False)

        # Title
        title = ctk.CTkLabel(
            header,
            text=f"  ◆  {ASSISTANT_NAME.upper()}  ",
            font=(FONT_FAMILY, 20, "bold"),
            text_color=ACCENT_BLUE,
        )
        title.pack(side="left", padx=16)

        # Subtitle / clock
        self._clock_label = ctk.CTkLabel(
            header,
            text="",
            font=(FONT_FAMILY, 12),
            text_color=TEXT_DIM,
        )
        self._clock_label.pack(side="left", padx=8)
        self._update_clock()

        # Mic toggle button
        self._mic_btn = ctk.CTkButton(
            header,
            text="🎤  Start Voice",
            width=140,
            height=34,
            corner_radius=17,
            font=(FONT_FAMILY, 13, "bold"),
            fg_color="#1e1e2f",
            hover_color="#2a2a40",
            border_width=1,
            border_color=ACCENT_BLUE,
            text_color=ACCENT_BLUE,
            command=self._toggle_mic,
        )
        self._mic_btn.pack(side="right", padx=16)

    def _build_centre(self) -> None:
        """Centre area: avatar on the left, chat log on the right."""
        centre = ctk.CTkFrame(self, fg_color=BG_DARK)
        centre.pack(fill="both", expand=True, padx=0, pady=0)
        centre.grid_columnconfigure(0, weight=3)
        centre.grid_columnconfigure(1, weight=5)
        centre.grid_rowconfigure(0, weight=1)

        # --- Left panel: Avatar + status ---
        left = ctk.CTkFrame(centre, fg_color=BG_DARK)
        left.grid(row=0, column=0, sticky="nsew", padx=(16, 8), pady=16)

        # Canvas for holographic character
        self._char_canvas = ctk.CTkCanvas(
            left,
            width=300,
            height=440,
            bg=BG_DARK,
            highlightthickness=0,
        )
        self._char_canvas.pack(pady=(10, 8))

        # Name label under avatar
        name_lbl = ctk.CTkLabel(
            left,
            text=ASSISTANT_NAME.upper(),
            font=(FONT_FAMILY, 18, "bold"),
            text_color=ACCENT_BLUE,
        )
        name_lbl.pack(pady=(0, 2))

        # Status label
        self._status_label = ctk.CTkLabel(
            left,
            text=STATE_LABELS[STATE_IDLE],
            font=(FONT_FAMILY, 13),
            text_color=STATE_COLOURS[STATE_IDLE],
        )
        self._status_label.pack(pady=(0, 6))

        # Command count
        self._cmd_count = 0
        self._cmd_label = ctk.CTkLabel(
            left,
            text="Commands: 0",
            font=(FONT_FAMILY, 11),
            text_color=TEXT_DIM,
        )
        self._cmd_label.pack()

        # --- Right panel: Chat log ---
        right = ctk.CTkFrame(centre, fg_color=BG_PANEL, corner_radius=12)
        right.grid(row=0, column=1, sticky="nsew", padx=(8, 16), pady=16)

        log_header = ctk.CTkLabel(
            right,
            text="  Conversation Log",
            font=(FONT_FAMILY, 13, "bold"),
            text_color=TEXT_DIM,
            anchor="w",
        )
        log_header.pack(fill="x", padx=12, pady=(10, 4))

        self._chat_log = ctk.CTkTextbox(
            right,
            font=(FONT_FAMILY, 13),
            fg_color=BG_PANEL,
            text_color=TEXT_PRIMARY,
            wrap="word",
            state="disabled",
            corner_radius=8,
            activate_scrollbars=True,
        )
        self._chat_log.pack(fill="both", expand=True, padx=8, pady=(0, 8))

        # Configure coloured tags
        self._chat_log.tag_config("jarvis", foreground=ACCENT_BLUE)
        self._chat_log.tag_config("user", foreground=ACCENT_GREEN)
        self._chat_log.tag_config("system", foreground=TEXT_DIM)
        self._chat_log.tag_config("error", foreground=ACCENT_RED)

    def _build_input_bar(self) -> None:
        """Bottom bar with text entry and send button."""
        bar = ctk.CTkFrame(self, fg_color=BG_PANEL, corner_radius=0, height=56)
        bar.pack(fill="x", side="bottom")
        bar.pack_propagate(False)

        self._input_entry = ctk.CTkEntry(
            bar,
            placeholder_text="Type a command …",
            font=(FONT_FAMILY, 14),
            fg_color=BG_INPUT,
            text_color=TEXT_PRIMARY,
            border_color="#2a2a3e",
            corner_radius=20,
            height=38,
        )
        self._input_entry.pack(side="left", fill="x", expand=True, padx=(16, 8), pady=9)
        self._input_entry.bind("<Return>", self._on_send)

        send_btn = ctk.CTkButton(
            bar,
            text="Send  ➤",
            width=100,
            height=38,
            corner_radius=20,
            font=(FONT_FAMILY, 13, "bold"),
            fg_color=ACCENT_BLUE,
            hover_color="#00b8d9",
            text_color=BG_DARK,
            command=self._on_send,
        )
        send_btn.pack(side="right", padx=(0, 16), pady=9)

    # ──────────────────────────────────────────
    #  Holographic human-character animation
    # ──────────────────────────────────────────

    @staticmethod
    def _lerp_colour(c1: str, c2: str, t: float) -> str:
        """Linearly interpolate between two hex colours."""
        r1, g1, b1 = int(c1[1:3], 16), int(c1[3:5], 16), int(c1[5:7], 16)
        r2, g2, b2 = int(c2[1:3], 16), int(c2[3:5], 16), int(c2[5:7], 16)
        r = int(r1 + (r2 - r1) * t)
        g = int(g1 + (g2 - g1) * t)
        b = int(b1 + (b2 - b1) * t)
        return f"#{r:02x}{g:02x}{b:02x}"

    @staticmethod
    def _dim_colour(colour: str, factor: float = 0.35) -> str:
        """Return a dimmed version of a hex colour."""
        r, g, b = int(colour[1:3], 16), int(colour[3:5], 16), int(colour[5:7], 16)
        r, g, b = int(r * factor), int(g * factor), int(b * factor)
        return f"#{r:02x}{g:02x}{b:02x}"

    def _animate_character(self) -> None:
        """Draw a full-body holographic human figure (called every 50 ms)."""
        c = self._char_canvas
        c.delete("all")
        W, H = 300, 440
        cx = W // 2

        colour = STATE_COLOURS.get(self._state, ACCENT_BLUE)
        dim = self._dim_colour(colour, 0.30)
        body_fill = self._dim_colour(colour, 0.12)  # Very dark fill for body

        # Advance animation counters
        self._anim_angle += 0.03
        self._breath_phase += 0.045
        breath = math.sin(self._breath_phase) * 2.5

        # Blink logic
        self._blink_timer -= 1
        if self._blink_timer <= 0:
            self._is_blinking = not self._is_blinking
            self._blink_timer = 3 if self._is_blinking else 60 + int(40 * abs(math.sin(self._anim_angle)))

        # Mouth logic
        self._mouth_open = self._state == STATE_SPEAKING and int(self._anim_angle * 10) % 3 != 0

        # ─── Key Y landmarks ───
        head_cy   = 62 + breath * 0.3
        head_rx   = 28                       # horizontal radius
        head_ry   = 32                       # vertical radius (oval head)
        neck_top  = head_cy + head_ry - 2
        neck_bot  = neck_top + 14
        shoulder_y = neck_bot
        shoulder_w = 58
        torso_bot  = shoulder_y + 95
        waist_w    = 42
        hip_y      = torso_bot + 4
        hip_w      = 46
        knee_y     = hip_y + 62
        ankle_y    = knee_y + 58
        foot_y     = ankle_y + 6

        # ─── Rotating halo above head ───
        halo_r = head_rx + 16
        halo_y_pos = head_cy - head_ry - 14 + breath * 0.3
        for i in range(28):
            a = self._anim_angle * 2 + i * (math.pi * 2 / 28)
            dx = cx + math.cos(a) * halo_r
            dy = halo_y_pos + math.sin(a) * 5
            dot_sz = 2.2 + math.sin(a + self._anim_angle) * 0.8
            c.create_oval(dx - dot_sz, dy - dot_sz, dx + dot_sz, dy + dot_sz,
                          fill=colour, outline="")

        # ─── Soft glow behind body ───
        glow_cx, glow_cy = cx, (shoulder_y + torso_bot) / 2 + breath
        for g in range(4, 0, -1):
            gr = 80 + g * 12
            c.create_oval(glow_cx - gr, glow_cy - gr * 1.4,
                          glow_cx + gr, glow_cy + gr * 1.4,
                          outline=self._dim_colour(colour, 0.06 + g * 0.02), width=1)

        # ─── Energy aura lines ───
        for i in range(6):
            a = self._anim_angle * 1.5 + i * (math.pi * 2 / 6)
            r_aura = 95 + 15 * math.sin(self._breath_phase + i)
            ax = cx + math.cos(a) * r_aura
            ay = glow_cy + math.sin(a) * 55
            c.create_line(cx, glow_cy, ax, ay, fill=dim, width=1, dash=(3, 6))

        # ════════════════════════════════════
        #  HEAD — oval with hair, ears, face
        # ════════════════════════════════════

        # Hair (slightly larger oval behind head)
        hair_extra = 5
        c.create_oval(cx - head_rx - hair_extra, head_cy - head_ry - hair_extra - 2,
                      cx + head_rx + hair_extra, head_cy - 2,
                      fill=body_fill, outline=colour, width=2)
        # Head oval (face)
        c.create_oval(cx - head_rx, head_cy - head_ry,
                      cx + head_rx, head_cy + head_ry,
                      fill=body_fill, outline=colour, width=2)

        # Ears
        ear_y = head_cy - 2
        ear_h = 10
        for sign in (-1, 1):
            ex = cx + sign * head_rx
            c.create_oval(ex - 4 * sign, ear_y - ear_h,
                          ex + 6 * sign, ear_y + ear_h,
                          outline=colour, width=1)

        # Eyebrows
        brow_y = head_cy - 14
        for sign in (-1, 1):
            bx = cx + sign * 11
            c.create_line(bx - 7, brow_y, bx + 7, brow_y - 2, fill=colour, width=2)

        # Eyes
        eye_dx = 11
        eye_y = head_cy - 6
        if self._is_blinking:
            c.create_line(cx - eye_dx - 6, eye_y, cx - eye_dx + 6, eye_y, fill=colour, width=2)
            c.create_line(cx + eye_dx - 6, eye_y, cx + eye_dx + 6, eye_y, fill=colour, width=2)
        else:
            for sign in (-1, 1):
                ex_c = cx + sign * eye_dx
                # Almond eye shape
                c.create_polygon(
                    ex_c - 7, eye_y,
                    ex_c - 3, eye_y - 5,
                    ex_c + 3, eye_y - 5,
                    ex_c + 7, eye_y,
                    ex_c + 3, eye_y + 4,
                    ex_c - 3, eye_y + 4,
                    outline=colour, fill="", width=1, smooth=True)
                # Iris
                c.create_oval(ex_c - 3.5, eye_y - 3.5, ex_c + 3.5, eye_y + 3.5,
                              outline=colour, width=1)
                # Pupil
                c.create_oval(ex_c - 1.5, eye_y - 1.5, ex_c + 1.5, eye_y + 1.5,
                              fill=colour, outline="")

        # Nose
        nose_y = head_cy + 4
        c.create_line(cx, nose_y - 6, cx - 3, nose_y + 2, fill=colour, width=1)
        c.create_line(cx - 3, nose_y + 2, cx + 3, nose_y + 2, fill=colour, width=1)

        # Mouth
        mouth_y = head_cy + 14
        if self._mouth_open:
            c.create_oval(cx - 8, mouth_y - 4, cx + 8, mouth_y + 6,
                          outline=colour, fill=body_fill, width=1)
        else:
            # Slight smile curve
            c.create_arc(cx - 10, mouth_y - 6, cx + 10, mouth_y + 6,
                         start=200, extent=140, style="arc", outline=colour, width=1)

        # Chin line (subtle jaw)
        c.create_arc(cx - head_rx + 4, head_cy + 6,
                     cx + head_rx - 4, head_cy + head_ry + 8,
                     start=220, extent=100, style="arc", outline=dim, width=1)

        # ════════════════════════════════════
        #  NECK — thick column
        # ════════════════════════════════════
        neck_w = 12
        c.create_polygon(
            cx - neck_w, neck_top,
            cx + neck_w, neck_top,
            cx + neck_w + 3, neck_bot,
            cx - neck_w - 3, neck_bot,
            fill=body_fill, outline=colour, width=2)

        # ════════════════════════════════════
        #  TORSO — filled trapezoid with details
        # ════════════════════════════════════
        # Shoulder caps (rounded)
        for sign in (-1, 1):
            sx = cx + sign * shoulder_w
            c.create_oval(sx - 10, shoulder_y - 8, sx + 10, shoulder_y + 8,
                          fill=body_fill, outline=colour, width=2)

        # Main torso body
        c.create_polygon(
            cx - shoulder_w,  shoulder_y,
            cx + shoulder_w,  shoulder_y,
            cx + waist_w,     shoulder_y + 55,   # waist
            cx + hip_w,       torso_bot,          # hip
            cx - hip_w,       torso_bot,
            cx - waist_w,     shoulder_y + 55,
            fill=body_fill, outline=colour, width=2, smooth=False)

        # Chest muscle lines
        c.create_arc(cx - 30, shoulder_y + 4, cx, shoulder_y + 36,
                     start=280, extent=160, style="arc", outline=dim, width=1)
        c.create_arc(cx, shoulder_y + 4, cx + 30, shoulder_y + 36,
                     start=300, extent=160, style="arc", outline=dim, width=1)

        # Centre line
        c.create_line(cx, shoulder_y + 8, cx, torso_bot - 4, fill=dim, width=1, dash=(4, 6))

        # Ab lines (subtle horizontal)
        for i in range(3):
            ay = shoulder_y + 48 + i * 16
            half_w = waist_w - 6 - i * 2
            c.create_line(cx - half_w, ay, cx + half_w, ay, fill=dim, width=1, dash=(3, 5))

        # Arc reactor (chest centre)
        reactor_y = shoulder_y + 22 + breath * 0.3
        reactor_r = 10 + 2 * math.sin(self._breath_phase * 2)
        c.create_oval(cx - reactor_r, reactor_y - reactor_r,
                      cx + reactor_r, reactor_y + reactor_r,
                      outline=colour, width=2)
        inner_r = reactor_r * 0.45
        c.create_oval(cx - inner_r, reactor_y - inner_r,
                      cx + inner_r, reactor_y + inner_r,
                      fill=colour, outline="")
        # Reactor spokes
        for i in range(6):
            a = self._anim_angle * 3 + i * (math.pi / 3)
            c.create_line(cx + math.cos(a) * inner_r, reactor_y + math.sin(a) * inner_r,
                          cx + math.cos(a) * reactor_r, reactor_y + math.sin(a) * reactor_r,
                          fill=colour, width=1)

        # Circuit lines from reactor
        for dx_sign in (-1, 1):
            c.create_line(cx + dx_sign * reactor_r, reactor_y,
                          cx + dx_sign * (shoulder_w - 8), reactor_y - 8,
                          fill=dim, width=1, dash=(4, 4))
            c.create_line(cx + dx_sign * reactor_r, reactor_y,
                          cx + dx_sign * (hip_w - 2), torso_bot - 8,
                          fill=dim, width=1, dash=(4, 4))

        # Belt at hip
        belt_h = 5
        c.create_polygon(
            cx - hip_w - 2, torso_bot - belt_h,
            cx + hip_w + 2, torso_bot - belt_h,
            cx + hip_w + 2, torso_bot + belt_h,
            cx - hip_w - 2, torso_bot + belt_h,
            fill=body_fill, outline=colour, width=1)
        # Belt buckle
        c.create_rectangle(cx - 6, torso_bot - 4, cx + 6, torso_bot + 4,
                           outline=colour, width=1)

        # ════════════════════════════════════
        #  ARMS — thick upper + forearm + hand
        # ════════════════════════════════════
        arm_thick_upper = 10
        arm_thick_lower = 8
        for sign in (-1, 1):
            # Shoulder joint
            sj_x = cx + sign * shoulder_w
            sj_y = shoulder_y

            # Elbow position
            elbow_x = cx + sign * (shoulder_w + 18)
            elbow_y_pos = shoulder_y + 52 + breath * 0.3

            # Wrist position
            wrist_x = cx + sign * (shoulder_w + 8)
            wrist_y = torso_bot + 10

            # Upper arm (polygon with thickness)
            perp_ux = -(elbow_y_pos - sj_y)
            perp_uy = (elbow_x - sj_x)
            ul = math.hypot(perp_ux, perp_uy) or 1
            perp_ux, perp_uy = perp_ux / ul * arm_thick_upper, perp_uy / ul * arm_thick_upper
            c.create_polygon(
                sj_x - perp_ux, sj_y - perp_uy,
                sj_x + perp_ux, sj_y + perp_uy,
                elbow_x + perp_ux * 0.8, elbow_y_pos + perp_uy * 0.8,
                elbow_x - perp_ux * 0.8, elbow_y_pos - perp_uy * 0.8,
                fill=body_fill, outline=colour, width=2, smooth=False)

            # Elbow joint circle
            c.create_oval(elbow_x - 6, elbow_y_pos - 6, elbow_x + 6, elbow_y_pos + 6,
                          fill=body_fill, outline=colour, width=2)

            # Forearm (polygon with thickness)
            perp_fx = -(wrist_y - elbow_y_pos)
            perp_fy = (wrist_x - elbow_x)
            fl = math.hypot(perp_fx, perp_fy) or 1
            perp_fx, perp_fy = perp_fx / fl * arm_thick_lower, perp_fy / fl * arm_thick_lower
            c.create_polygon(
                elbow_x - perp_fx, elbow_y_pos - perp_fy,
                elbow_x + perp_fx, elbow_y_pos + perp_fy,
                wrist_x + perp_fx * 0.7, wrist_y + perp_fy * 0.7,
                wrist_x - perp_fx * 0.7, wrist_y - perp_fy * 0.7,
                fill=body_fill, outline=colour, width=2, smooth=False)

            # Hand (pentagon shape)
            hx, hy = wrist_x, wrist_y
            c.create_polygon(
                hx - 6 * sign, hy,
                hx + 2 * sign, hy - 5,
                hx + 8 * sign, hy,
                hx + 8 * sign, hy + 10,
                hx - 6 * sign, hy + 10,
                fill=body_fill, outline=colour, width=1)
            # Finger lines
            for f in range(4):
                fx = hx + (f * 3 - 4) * sign
                c.create_line(fx, hy + 10, fx + sign * 2, hy + 15,
                              fill=colour, width=1)
            # Thumb
            c.create_line(hx - 5 * sign, hy + 3, hx - 10 * sign, hy + 8,
                          fill=colour, width=1)

        # ════════════════════════════════════
        #  LEGS — thick thigh + calf + foot
        # ════════════════════════════════════
        thigh_thick = 14
        calf_thick = 10
        for sign in (-1, 1):
            # Hip joint
            hip_jx = cx + sign * (hip_w - 8)
            hip_jy = hip_y + 4

            # Knee position
            knee_jx = cx + sign * (hip_w - 2)
            knee_jy = knee_y + breath * 0.15

            # Ankle
            ankle_jx = cx + sign * (hip_w - 6)
            ankle_jy = ankle_y

            # Thigh (polygon)
            perp_tx = -(knee_jy - hip_jy)
            perp_ty = (knee_jx - hip_jx)
            tl = math.hypot(perp_tx, perp_ty) or 1
            perp_tx, perp_ty = perp_tx / tl * thigh_thick, perp_ty / tl * thigh_thick
            c.create_polygon(
                hip_jx - perp_tx, hip_jy - perp_ty,
                hip_jx + perp_tx, hip_jy + perp_ty,
                knee_jx + perp_tx * 0.85, knee_jy + perp_ty * 0.85,
                knee_jx - perp_tx * 0.85, knee_jy - perp_ty * 0.85,
                fill=body_fill, outline=colour, width=2, smooth=False)

            # Knee joint
            c.create_oval(knee_jx - 7, knee_jy - 7, knee_jx + 7, knee_jy + 7,
                          fill=body_fill, outline=colour, width=2)

            # Calf (polygon)
            perp_cx = -(ankle_jy - knee_jy)
            perp_cy = (ankle_jx - knee_jx)
            cl = math.hypot(perp_cx, perp_cy) or 1
            perp_cx, perp_cy = perp_cx / cl * calf_thick, perp_cy / cl * calf_thick
            c.create_polygon(
                knee_jx - perp_cx, knee_jy - perp_cy,
                knee_jx + perp_cx, knee_jy + perp_cy,
                ankle_jx + perp_cx * 0.7, ankle_jy + perp_cy * 0.7,
                ankle_jx - perp_cx * 0.7, ankle_jy - perp_cy * 0.7,
                fill=body_fill, outline=colour, width=2, smooth=False)

            # Foot / boot
            c.create_polygon(
                ankle_jx - 8, ankle_jy - 3,
                ankle_jx + 8, ankle_jy - 3,
                ankle_jx + sign * 16 + 4, ankle_jy + 10,
                ankle_jx - 10, ankle_jy + 10,
                fill=body_fill, outline=colour, width=2)

        # ═══ Holographic platform ═══
        plat_y = foot_y + 14
        plat_rx, plat_ry = 70, 12
        # Glow rings under feet
        for i in range(3):
            alpha_dim = self._dim_colour(colour, 0.15 - i * 0.04)
            c.create_oval(cx - plat_rx - i * 6, plat_y - plat_ry - i * 2,
                          cx + plat_rx + i * 6, plat_y + plat_ry + i * 2,
                          outline=alpha_dim, width=1)
        c.create_oval(cx - plat_rx, plat_y - plat_ry,
                      cx + plat_rx, plat_y + plat_ry,
                      outline=colour, width=1, dash=(4, 4))

        # Scanning line
        scan_range = int(ankle_y - head_cy + 40)
        if scan_range > 0:
            scan_y = plat_y - int((self._anim_angle * 40) % scan_range)
            c.create_line(cx - 65, scan_y, cx + 65, scan_y, fill=dim, width=1)

        # ═══ Listening ring ═══
        if self._state == STATE_LISTENING:
            pulse = 0.5 + 0.5 * math.sin(self._breath_phase * 3)
            lr = 105 + pulse * 18
            mid_y = glow_cy
            c.create_oval(cx - lr, mid_y - lr, cx + lr, mid_y + lr,
                          outline=colour, width=2, dash=(6, 4))

        # ═══ Sound wave bars when speaking ═══
        if self._state == STATE_SPEAKING:
            bar_base = plat_y + 18
            for i in range(13):
                bx = cx - 60 + i * 10
                bh = 3 + 10 * abs(math.sin(self._anim_angle * 6 + i * 0.8))
                c.create_rectangle(bx - 2, bar_base - bh, bx + 2, bar_base + bh,
                                   fill=colour, outline="")

        self.after(50, self._animate_character)

    # ──────────────────────────────────────────
    #  Clock
    # ──────────────────────────────────────────

    def _update_clock(self) -> None:
        now = datetime.datetime.now().strftime("%A, %b %d  •  %I:%M %p")
        self._clock_label.configure(text=now)
        self.after(30_000, self._update_clock)

    # ──────────────────────────────────────────
    #  State management helpers
    # ──────────────────────────────────────────

    def _set_state(self, state: str) -> None:
        self._state = state
        colour = STATE_COLOURS.get(state, ACCENT_BLUE)
        self._status_label.configure(
            text=STATE_LABELS.get(state, ""),
            text_color=colour,
        )

    def _post_jarvis(self, text: str) -> None:
        """Append a Jarvis message to the chat log."""
        self._append_chat(f"  ◆ {ASSISTANT_NAME}", text, "jarvis")

    def _post_user(self, text: str) -> None:
        """Append a user message to the chat log."""
        self._append_chat("  You", text, "user")

    def _post_system(self, text: str) -> None:
        self._append_chat("  ⚙ System", text, "system")

    def _post_error(self, text: str) -> None:
        self._append_chat("  ✖ Error", text, "error")

    def _append_chat(self, sender: str, text: str, tag: str) -> None:
        ts = datetime.datetime.now().strftime("%H:%M")
        self._chat_log.configure(state="normal")
        self._chat_log.insert("end", f"\n[{ts}] {sender}\n", tag)
        self._chat_log.insert("end", f"  {text}\n")
        self._chat_log.configure(state="disabled")
        self._chat_log.see("end")

    # ──────────────────────────────────────────
    #  Message queue (thread → main thread)
    # ──────────────────────────────────────────

    def _poll_queue(self) -> None:
        """Drain the message queue and update the UI."""
        while not self._msg_queue.empty():
            msg_type, payload = self._msg_queue.get_nowait()
            if msg_type == "state":
                self._set_state(payload)
            elif msg_type == "jarvis":
                self._post_jarvis(payload)
            elif msg_type == "user":
                self._post_user(payload)
            elif msg_type == "error":
                self._post_error(payload)
            elif msg_type == "cmd_count":
                self._cmd_count = payload
                self._cmd_label.configure(text=f"Commands: {payload}")
        self.after(100, self._poll_queue)

    def _q(self, msg_type: str, payload: str | int) -> None:
        """Enqueue a message for the UI thread."""
        self._msg_queue.put((msg_type, payload))

    # ──────────────────────────────────────────
    #  Text-input handler
    # ──────────────────────────────────────────

    def _on_send(self, event=None) -> None:
        text = self._input_entry.get().strip()
        if not text:
            return
        self._input_entry.delete(0, "end")
        self._post_user(text)
        self._cmd_count += 1
        self._cmd_label.configure(text=f"Commands: {self._cmd_count}")

        # Process in background so UI stays responsive
        threading.Thread(target=self._process_command, args=(text.lower(),), daemon=True).start()

    def _process_command(self, command: str) -> None:
        """Run the command handler + TTS in a background thread."""
        self._q("state", STATE_PROCESSING)
        try:
            response = handle_command(command)
        except SystemExit:
            self._q("jarvis", "Goodbye, sir!")
            self._q("state", STATE_IDLE)
            return
        except Exception as exc:
            self._q("error", str(exc))
            self._q("state", STATE_ERROR)
            return

        if response:
            self._q("jarvis", response)
            self._q("state", STATE_SPEAKING)
            try:
                _tts_speak(response)
            except Exception:
                pass
        self._q("state", STATE_IDLE if not self._mic_active else STATE_WAITING)

    # ──────────────────────────────────────────
    #  Mic toggle & voice loop
    # ──────────────────────────────────────────

    def _toggle_mic(self) -> None:
        if self._mic_active:
            self._mic_active = False
            self._mic_btn.configure(
                text="🎤  Start Voice",
                border_color=ACCENT_BLUE,
                text_color=ACCENT_BLUE,
            )
            self._set_state(STATE_IDLE)
            self._post_system("Voice mode deactivated.")
        else:
            self._mic_active = True
            self._mic_btn.configure(
                text="⏹  Stop Voice",
                border_color=ACCENT_GREEN,
                text_color=ACCENT_GREEN,
            )
            self._post_system("Voice mode activated. Say \"Hey Jarvis\" …")
            self._set_state(STATE_WAITING)
            self._voice_thread = threading.Thread(target=self._voice_loop, daemon=True)
            self._voice_thread.start()

    def _voice_loop(self) -> None:
        """Background thread: wake-word → listen → process → repeat."""
        recognizer = sr.Recognizer()
        recognizer.energy_threshold = 4000
        recognizer.pause_threshold = 1.0

        while self._mic_active:
            # --- wait for wake word ---
            self._q("state", STATE_WAITING)
            woke = False
            while self._mic_active and not woke:
                try:
                    with sr.Microphone() as source:
                        audio = recognizer.listen(source, timeout=3, phrase_time_limit=4)
                        text = recognizer.recognize_google(audio).lower()
                        if WAKE_WORD in text:
                            woke = True
                except (sr.UnknownValueError, sr.WaitTimeoutError):
                    continue
                except sr.RequestError as exc:
                    self._q("error", f"Speech service error: {exc}")
                    continue
                except OSError:
                    # Mic unavailable
                    self._q("error", "Microphone not available.")
                    self._mic_active = False
                    return

            if not self._mic_active:
                break

            # --- acknowledged ---
            self._q("jarvis", "Yes sir, I'm listening.")
            self._q("state", STATE_LISTENING)
            try:
                _tts_speak("Yes sir, I'm listening.")
            except Exception:
                pass

            # --- listen for command ---
            command = ""
            try:
                with sr.Microphone() as source:
                    audio = recognizer.listen(source, timeout=5, phrase_time_limit=10)
                    command = recognizer.recognize_google(audio).lower()
            except (sr.UnknownValueError, sr.WaitTimeoutError):
                self._q("jarvis", "I didn't hear anything. Please try again.")
                try:
                    _tts_speak("I didn't hear anything. Please try again.")
                except Exception:
                    pass
                continue
            except sr.RequestError as exc:
                self._q("error", f"Speech service error: {exc}")
                continue

            if not command:
                continue

            self._q("user", command)
            self._cmd_count += 1
            self._q("cmd_count", self._cmd_count)
            self._process_command(command)

    # ──────────────────────────────────────────
    #  Scheduled reminders
    # ──────────────────────────────────────────

    def _check_reminders(self) -> None:
        """Check every 30 seconds if a scheduled reminder should fire."""
        now = datetime.datetime.now()
        today_key = now.strftime("%Y-%m-%d")

        for hour, minute, message in SCHEDULED_REMINDERS:
            reminder_id = f"{today_key}-{hour:02d}:{minute:02d}"
            if reminder_id in self._fired_reminders:
                continue
            if now.hour == hour and now.minute == minute:
                self._fired_reminders.add(reminder_id)
                self._post_jarvis(message)
                # Speak in background thread so UI doesn't freeze
                threading.Thread(
                    target=_tts_speak, args=(message,), daemon=True
                ).start()

        # Reset fired reminders at midnight
        if now.hour == 0 and now.minute == 0:
            self._fired_reminders.clear()

        self.after(30_000, self._check_reminders)   # Check every 30 seconds

    # ──────────────────────────────────────────
    #  Cleanup
    # ──────────────────────────────────────────

    def _on_close(self) -> None:
        self._mic_active = False
        self.destroy()


# ══════════════════════════════════════════════
#  Entry point
# ══════════════════════════════════════════════

def main() -> None:
    app = JarvisGUI()
    app.mainloop()


if __name__ == "__main__":
    main()
