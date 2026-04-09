#!/usr/bin/env python3
"""
鼠标自动移动工具 - GUI 版本
支持 Windows 和 macOS
"""

import tkinter as tk
from tkinter import ttk, messagebox
import threading
import time
from datetime import datetime, timedelta
import pyautogui

# 禁用 pyautogui 的故障保护（移到角落不会停止）
pyautogui.FAILSAFE = False


class MouseMoverApp:
    def __init__(self, root):
        self.root = root
        self.root.title("鼠标自动移动工具")
        self.root.resizable(False, False)

        self._running = False
        self._thread = None
        self._target_time = None

        self._build_ui()
        self._center_window()

    def _center_window(self):
        self.root.update_idletasks()
        w, h = self.root.winfo_width(), self.root.winfo_height()
        sw = self.root.winfo_screenwidth()
        sh = self.root.winfo_screenheight()
        self.root.geometry(f"{w}x{h}+{(sw - w) // 2}+{(sh - h) // 2}")

    def _build_ui(self):
        pad = {"padx": 16}

        # ── 标题 ──────────────────────────────────────────
        title = tk.Label(self.root, text="🖱  鼠标自动移动工具",
                         font=("", 16, "bold"))
        title.pack(**pad, pady=(16, 4))

        # ── 模式选择 ──────────────────────────────────────
        mode_frame = ttk.LabelFrame(self.root, text="停止方式", padding=10)
        mode_frame.pack(fill="x", padx=16, pady=4)

        self.mode = tk.StringVar(value="time")

        r1 = ttk.Radiobutton(mode_frame, text="指定结束时间  (HH:MM)",
                              variable=self.mode, value="time",
                              command=self._on_mode_change)
        r1.grid(row=0, column=0, sticky="w")

        r2 = ttk.Radiobutton(mode_frame, text="运行指定分钟数",
                              variable=self.mode, value="minutes",
                              command=self._on_mode_change)
        r2.grid(row=1, column=0, sticky="w", pady=(4, 0))

        # ── 时间输入 ──────────────────────────────────────
        input_frame = ttk.LabelFrame(self.root, text="参数设置", padding=10)
        input_frame.pack(fill="x", padx=16, pady=4)

        # 结束时间行
        self.time_label = ttk.Label(input_frame, text="结束时间:")
        self.time_label.grid(row=0, column=0, sticky="w")

        time_entry_frame = tk.Frame(input_frame)
        time_entry_frame.grid(row=0, column=1, sticky="w", padx=(8, 0))

        self.hour_var = tk.StringVar(value="18")
        self.minute_var = tk.StringVar(value="00")

        vcmd = (self.root.register(self._validate_num), "%P", "%W")
        self.hour_spin = ttk.Spinbox(time_entry_frame, from_=0, to=23, width=4,
                                     textvariable=self.hour_var,
                                     validate="key", validatecommand=vcmd,
                                     format="%02.0f")
        self.hour_spin.pack(side="left")
        ttk.Label(time_entry_frame, text=" : ").pack(side="left")
        self.min_spin = ttk.Spinbox(time_entry_frame, from_=0, to=59, width=4,
                                    textvariable=self.minute_var,
                                    validate="key", validatecommand=vcmd,
                                    format="%02.0f")
        self.min_spin.pack(side="left")

        # 分钟数行
        self.min_label = ttk.Label(input_frame, text="运行分钟:")
        self.min_label.grid(row=1, column=0, sticky="w", pady=(8, 0))

        self.duration_var = tk.StringVar(value="120")
        self.duration_spin = ttk.Spinbox(input_frame, from_=1, to=1440, width=6,
                                         textvariable=self.duration_var)
        self.duration_spin.grid(row=1, column=1, sticky="w", padx=(8, 0), pady=(8, 0))
        ttk.Label(input_frame, text="分钟").grid(row=1, column=2, sticky="w", pady=(8, 0))

        # 移动间隔
        ttk.Label(input_frame, text="移动间隔:").grid(row=2, column=0, sticky="w", pady=(8, 0))
        self.interval_var = tk.StringVar(value="60")
        self.interval_spin = ttk.Spinbox(input_frame, from_=10, to=600, width=6,
                                         textvariable=self.interval_var)
        self.interval_spin.grid(row=2, column=1, sticky="w", padx=(8, 0), pady=(8, 0))
        ttk.Label(input_frame, text="秒").grid(row=2, column=2, sticky="w", pady=(8, 0))

        self._on_mode_change()

        # ── 状态显示 ──────────────────────────────────────
        status_frame = ttk.LabelFrame(self.root, text="运行状态", padding=10)
        status_frame.pack(fill="x", padx=16, pady=4)

        self.status_var = tk.StringVar(value="⏸  未运行")
        status_lbl = ttk.Label(status_frame, textvariable=self.status_var,
                                font=("", 11))
        status_lbl.pack(anchor="w")

        self.remain_var = tk.StringVar(value="")
        remain_lbl = ttk.Label(status_frame, textvariable=self.remain_var,
                                foreground="gray")
        remain_lbl.pack(anchor="w")

        self.log_text = tk.Text(status_frame, height=6, state="disabled",
                                font=("Courier", 9), bg="#f5f5f5")
        self.log_text.pack(fill="x", pady=(6, 0))

        # ── 按钮 ──────────────────────────────────────────
        btn_frame = tk.Frame(self.root)
        btn_frame.pack(pady=12)

        self.start_btn = ttk.Button(btn_frame, text="▶  开始", width=12,
                                    command=self._start)
        self.start_btn.pack(side="left", padx=6)

        self.stop_btn = ttk.Button(btn_frame, text="⏹  停止", width=12,
                                   command=self._stop, state="disabled")
        self.stop_btn.pack(side="left", padx=6)

    # ── 模式切换 ──────────────────────────────────────────
    def _on_mode_change(self):
        is_time = self.mode.get() == "time"
        state_on = "normal"
        state_off = "disabled"
        for w in (self.hour_spin, self.min_spin):
            w.config(state=state_on if is_time else state_off)
        self.duration_spin.config(state=state_off if is_time else state_on)

    def _validate_num(self, value, widget_name):
        return value.isdigit() or value == ""

    # ── 日志 ──────────────────────────────────────────────
    def _log(self, msg):
        ts = datetime.now().strftime("%H:%M:%S")
        line = f"[{ts}] {msg}\n"
        self.log_text.config(state="normal")
        self.log_text.insert("end", line)
        self.log_text.see("end")
        self.log_text.config(state="disabled")

    # ── 开始 ──────────────────────────────────────────────
    def _start(self):
        if self._running:
            return

        try:
            interval = int(self.interval_var.get())
        except ValueError:
            messagebox.showerror("错误", "移动间隔必须是整数")
            return

        if self.mode.get() == "time":
            try:
                h = int(self.hour_var.get())
                m = int(self.minute_var.get())
            except ValueError:
                messagebox.showerror("错误", "请输入有效的时间")
                return
            now = datetime.now()
            target = now.replace(hour=h, minute=m, second=0, microsecond=0)
            if target <= now:
                target += timedelta(days=1)
        else:
            try:
                minutes = int(self.duration_var.get())
            except ValueError:
                messagebox.showerror("错误", "请输入有效的分钟数")
                return
            target = datetime.now() + timedelta(minutes=minutes)

        self._target_time = target
        self._running = True
        self.start_btn.config(state="disabled")
        self.stop_btn.config(state="normal")
        self.status_var.set("▶  运行中...")
        self._log(f"启动，将运行到 {target.strftime('%Y-%m-%d %H:%M:%S')}")

        self._thread = threading.Thread(target=self._worker,
                                        args=(target, interval), daemon=True)
        self._thread.start()
        self._update_remain()

    # ── 停止 ──────────────────────────────────────────────
    def _stop(self):
        self._running = False
        self.status_var.set("⏸  已停止")
        self.remain_var.set("")
        self.start_btn.config(state="normal")
        self.stop_btn.config(state="disabled")
        self._log("用户手动停止")

    # ── 工作线程 ──────────────────────────────────────────
    def _worker(self, target, interval):
        while self._running and datetime.now() < target:
            x, y = pyautogui.position()
            pyautogui.moveTo(x + 10, y + 10, duration=0.2)
            pyautogui.moveTo(x, y, duration=0.2)
            self.root.after(0, self._log, "鼠标已移动")

            # 分段 sleep，方便响应停止信号
            for _ in range(interval * 2):
                if not self._running:
                    return
                time.sleep(0.5)

        if self._running:
            self._running = False
            self.root.after(0, self._on_finished)

    def _on_finished(self):
        self.status_var.set("✅  已完成")
        self.remain_var.set("")
        self.start_btn.config(state="normal")
        self.stop_btn.config(state="disabled")
        self._log("已到达目标时间，自动停止")
        messagebox.showinfo("完成", "鼠标移动任务已完成！")

    # ── 剩余时间刷新 ──────────────────────────────────────
    def _update_remain(self):
        if not self._running:
            return
        remaining = self._target_time - datetime.now()
        total_sec = int(remaining.total_seconds())
        if total_sec > 0:
            h, r = divmod(total_sec, 3600)
            m, s = divmod(r, 60)
            self.remain_var.set(f"剩余时间：{h:02d}:{m:02d}:{s:02d}")
        self.root.after(1000, self._update_remain)


def main():
    root = tk.Tk()
    app = MouseMoverApp(root)
    root.mainloop()


if __name__ == "__main__":
    main()
