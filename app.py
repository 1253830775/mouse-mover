#!/usr/bin/env python3
import customtkinter as ctk
import threading
import time
from datetime import datetime, timedelta
import pyautogui

pyautogui.FAILSAFE = False

ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("blue")


class MouseMoverApp(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("Mouse Mover")
        self.geometry("360x440")
        self.resizable(False, False)

        self._running = False
        self._target_time = None
        self._thread = None

        self._build_ui()
        self._center()

    def _center(self):
        self.update_idletasks()
        x = (self.winfo_screenwidth() - 360) // 2
        y = (self.winfo_screenheight() - 440) // 2
        self.geometry(f"360x440+{x}+{y}")

    def _build_ui(self):
        self.grid_columnconfigure(0, weight=1)

        # 标题
        ctk.CTkLabel(self, text="🖱  Mouse Mover",
                     font=ctk.CTkFont(size=22, weight="bold")).pack(pady=(28, 4))
        ctk.CTkLabel(self, text="防止屏幕锁定，自动移动鼠标",
                     font=ctk.CTkFont(size=12),
                     text_color="gray").pack(pady=(0, 20))

        # 模式切换
        self.mode = ctk.StringVar(value="指定时间")
        seg = ctk.CTkSegmentedButton(self, values=["指定时间", "运行分钟"],
                                     variable=self.mode,
                                     command=self._on_mode_change)
        seg.pack(padx=24, fill="x")

        # 卡片容器
        self.card = ctk.CTkFrame(self, corner_radius=12)
        self.card.pack(padx=24, pady=16, fill="x")
        self.card.grid_columnconfigure(1, weight=1)

        # 结束时间行
        self.time_label = ctk.CTkLabel(self.card, text="结束时间")
        self.time_label.grid(row=0, column=0, padx=16, pady=14, sticky="w")

        self.time_row = ctk.CTkFrame(self.card, fg_color="transparent")
        self.time_row.grid(row=0, column=1, padx=(0, 16), pady=14, sticky="e")

        self.hour_var = ctk.StringVar(value="18")
        self.min_var = ctk.StringVar(value="00")
        self.hour_entry = ctk.CTkEntry(self.time_row, width=52, textvariable=self.hour_var,
                                       justify="center")
        self.hour_entry.pack(side="left")
        ctk.CTkLabel(self.time_row, text=":", font=ctk.CTkFont(size=16)).pack(side="left", padx=4)
        self.min_entry = ctk.CTkEntry(self.time_row, width=52, textvariable=self.min_var,
                                      justify="center")
        self.min_entry.pack(side="left")

        # 分隔线（时间/分钟之间）
        self.sep1 = ctk.CTkFrame(self.card, height=1, fg_color=("gray80", "gray25"))
        self.sep1.grid(row=1, column=0, columnspan=2, sticky="ew", padx=12)

        # 运行分钟行
        self.dur_label = ctk.CTkLabel(self.card, text="运行分钟")
        self.dur_label.grid(row=2, column=0, padx=16, pady=14, sticky="w")
        self.dur_var = ctk.StringVar(value="120")
        self.dur_entry = ctk.CTkEntry(self.card, width=80, textvariable=self.dur_var,
                                      justify="center")
        self.dur_entry.grid(row=2, column=1, padx=(0, 16), pady=14, sticky="e")

        # 分隔线（分钟/间隔之间）
        self.sep2 = ctk.CTkFrame(self.card, height=1, fg_color=("gray80", "gray25"))
        self.sep2.grid(row=3, column=0, columnspan=2, sticky="ew", padx=12)

        # 间隔行
        ctk.CTkLabel(self.card, text="移动间隔").grid(
            row=4, column=0, padx=16, pady=14, sticky="w")
        interval_row = ctk.CTkFrame(self.card, fg_color="transparent")
        interval_row.grid(row=4, column=1, padx=(0, 16), pady=14, sticky="e")
        self.interval_var = ctk.StringVar(value="60")
        ctk.CTkEntry(interval_row, width=60, textvariable=self.interval_var,
                     justify="center").pack(side="left")
        ctk.CTkLabel(interval_row, text=" 秒", text_color="gray").pack(side="left")

        self._on_mode_change()

        # 状态区
        self.status_label = ctk.CTkLabel(self, text="未运行",
                                         font=ctk.CTkFont(size=13),
                                         text_color="gray")
        self.status_label.pack(pady=(0, 4))

        self.remain_label = ctk.CTkLabel(self, text="",
                                         font=ctk.CTkFont(size=11),
                                         text_color="gray")
        self.remain_label.pack(pady=(0, 12))

        # 日志（默认隐藏）
        self._log_visible = False
        log_header = ctk.CTkFrame(self, fg_color="transparent")
        log_header.pack(padx=24, fill="x")
        ctk.CTkLabel(log_header, text="日志", font=ctk.CTkFont(size=12),
                     text_color="gray").pack(side="left")
        self.log_toggle_btn = ctk.CTkButton(
            log_header, text="展开 ▾", width=60, height=24,
            fg_color="transparent", hover_color=("gray85", "gray25"),
            text_color="gray", font=ctk.CTkFont(size=12),
            command=self._toggle_log)
        self.log_toggle_btn.pack(side="right")

        self.log_box = ctk.CTkTextbox(self, height=90, font=ctk.CTkFont(
            family="Courier", size=11), state="disabled")
        # 不 pack，默认隐藏

        # 按钮
        self.btn_row = ctk.CTkFrame(self, fg_color="transparent")
        self.btn_row.pack(pady=20)

        self.start_btn = self._make_btn(self.btn_row, "开始", "#1f538d", "#1a4a7a", self._start)
        self.start_btn.pack(side="left", padx=8)
        self.stop_btn = self._make_btn(self.btn_row, "停止", "#3a3a3a", "#2a2a2a", self._stop)
        self.stop_btn.pack(side="left", padx=8)
        self._set_stop_enabled(False)

    def _make_btn(self, parent, text, bg, hover_bg, command):
        """用 CTkFrame+CTkLabel 自制按钮，彻底解决 macOS 文字不居中问题"""
        import tkinter as tk
        frame = ctk.CTkFrame(parent, width=120, height=54,
                             corner_radius=8, fg_color=bg, cursor="pointinghand")
        frame.pack_propagate(False)
        label = ctk.CTkLabel(frame, text=text, font=ctk.CTkFont(size=14),
                             text_color="white", fg_color="transparent",
                             cursor="pointinghand")
        label.place(relx=0.5, rely=0.5, anchor="center")

        def on_enter(_):
            frame.configure(fg_color=hover_bg)
        def on_leave(_):
            if frame._fg_color != "#555555":  # disabled color
                frame.configure(fg_color=frame._normal_bg)
        def on_click(_):
            if frame._enabled:
                command()

        frame._normal_bg = bg
        frame._hover_bg = hover_bg
        frame._enabled = True

        for w in (frame, label):
            w.bind("<Enter>", on_enter)
            w.bind("<Leave>", on_leave)
            w.bind("<Button-1>", on_click)

        frame._label = label
        return frame

    def _set_stop_enabled(self, enabled):
        if enabled:
            self.stop_btn._enabled = True
            self.stop_btn._normal_bg = "#3a3a3a"
            self.stop_btn.configure(fg_color="#3a3a3a")
            self.stop_btn._label.configure(text_color="white")
        else:
            self.stop_btn._enabled = False
            self.stop_btn._normal_bg = "#2a2a2a"
            self.stop_btn.configure(fg_color="#2a2a2a")
            self.stop_btn._label.configure(text_color="gray50")

    def _set_start_enabled(self, enabled):
        if enabled:
            self.start_btn._enabled = True
            self.start_btn._normal_bg = "#1f538d"
            self.start_btn.configure(fg_color="#1f538d")
            self.start_btn._label.configure(text_color="white")
        else:
            self.start_btn._enabled = False
            self.start_btn._normal_bg = "#163d6b"
            self.start_btn.configure(fg_color="#163d6b")
            self.start_btn._label.configure(text_color="gray60")

    def _toggle_log(self):
        if self._log_visible:
            self.log_box.pack_forget()
            self.log_toggle_btn.configure(text="展开 ▾")
            self.geometry("360x440")
        else:
            self.log_box.pack(padx=24, fill="x", before=self.btn_row)
            self.log_toggle_btn.configure(text="收起 ▴")
            self.geometry("360x540")
        self._log_visible = not self._log_visible

    def _on_mode_change(self, val=None):
        is_time = self.mode.get() == "指定时间"
        if is_time:
            self.time_label.grid()
            self.time_row.grid()
            self.sep1.grid()
            self.dur_label.grid_remove()
            self.dur_entry.grid_remove()
            self.sep2.grid_remove()
        else:
            self.time_label.grid_remove()
            self.time_row.grid_remove()
            self.sep1.grid_remove()
            self.dur_label.grid()
            self.dur_entry.grid()
            self.sep2.grid()

    def _log(self, msg):
        ts = datetime.now().strftime("%H:%M:%S")
        self.log_box.configure(state="normal")
        self.log_box.insert("end", f"[{ts}] {msg}\n")
        self.log_box.see("end")
        self.log_box.configure(state="disabled")

    def _start(self):
        try:
            interval = int(self.interval_var.get())
        except ValueError:
            self._log("❌ 间隔必须是整数")
            return

        if self.mode.get() == "指定时间":
            try:
                h, m = int(self.hour_var.get()), int(self.min_var.get())
                assert 0 <= h <= 23 and 0 <= m <= 59
            except Exception:
                self._log("❌ 请输入有效时间")
                return
            now = datetime.now()
            target = now.replace(hour=h, minute=m, second=0, microsecond=0)
            if target <= now:
                target += timedelta(days=1)
        else:
            try:
                target = datetime.now() + timedelta(minutes=int(self.dur_var.get()))
            except ValueError:
                self._log("❌ 请输入有效分钟数")
                return

        self._target_time = target
        self._running = True
        self._set_start_enabled(False)
        self._set_stop_enabled(True)
        self.status_label.configure(text="● 运行中", text_color="#1f9e4a")
        self._log(f"启动，运行至 {target.strftime('%H:%M:%S')}")

        self._thread = threading.Thread(target=self._worker,
                                        args=(target, interval), daemon=True)
        self._thread.start()
        self._tick()

    def _stop(self):
        self._running = False
        self.status_label.configure(text="已停止", text_color="gray")
        self.remain_label.configure(text="")
        self._set_start_enabled(True)
        self._set_stop_enabled(False)
        self._log("手动停止")

    def _worker(self, target, interval):
        while self._running and datetime.now() < target:
            x, y = pyautogui.position()
            pyautogui.moveTo(x + 10, y + 10, duration=0.2)
            pyautogui.moveTo(x, y, duration=0.2)
            self.after(0, self._log, "鼠标已移动 ✓")
            for _ in range(interval * 2):
                if not self._running:
                    return
                time.sleep(0.5)
        if self._running:
            self._running = False
            self.after(0, self._on_done)

    def _on_done(self):
        self.status_label.configure(text="✅ 已完成", text_color="#1f9e4a")
        self.remain_label.configure(text="")
        self._set_start_enabled(True)
        self._set_stop_enabled(False)
        self._log("已到达目标时间，自动停止")

    def _tick(self):
        if not self._running:
            return
        secs = int((self._target_time - datetime.now()).total_seconds())
        if secs > 0:
            h, r = divmod(secs, 3600)
            m, s = divmod(r, 60)
            self.remain_label.configure(text=f"剩余  {h:02d}:{m:02d}:{s:02d}")
        self.after(1000, self._tick)


if __name__ == "__main__":
    app = MouseMoverApp()
    app.mainloop()
