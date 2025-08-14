import os
import tkinter as tk
from datetime import datetime, timedelta
from tkinter import messagebox
from ttkbootstrap import Frame, Label, Checkbutton, BooleanVar, Button, Combobox
from ttkbootstrap.dialogs import Messagebox

from utils.file_utils import list_config_ids, load_json, save_json, get_today
from utils.time_utils import time_to_minutes, str_to_datetime

# ---------- 颜色定义 ----------
LIGHT_GRAY  = "#e0e0e0"
LIGHT_RED   = "#ffcccc"
LIGHT_GREEN = "#ccffcc"
GRAY_BORDER = "#999999"

RIGHT_GAP = 0
BAR_W = 36
TEXT_W = 160

class ProgressPage(Frame):
    """
    @class ProgressPage
    @brief 任务进度可视化页面，支持横向和竖向布局。

    @details
    显示基于任务配置的进度条，允许打勾任务完成状态，
    同时支持当前任务高亮，方向切换，自适应布局。
    """

    def __init__(self, master: tk.Tk, plan_id: str, *, vertical: bool = False):
        """
        @brief 构造函数。
        @param master 主窗口对象
        @param plan_id 当前使用的计划 ID
        @param vertical 是否为竖向布局
        """
        super().__init__(master)
        self.pack(fill=tk.BOTH, expand=True)

        self.master = master
        self.plan_id = plan_id
        self.vertical = vertical
        self.min_segment = 90
        self.date = get_today()

        self.plan_data = load_json(f"config/{plan_id}.json", {})
        self.tasks = sorted(
            self.plan_data.get("tasks", []),
            key=lambda t: time_to_minutes(t["time"].split("-")[0])
        )

        self.status_file = f"data/status_{self.plan_id}.json"
        self.status = load_json(self.status_file, {})

        # 检查日期是否为今天
        status_date = self.status.get("_date")
        today = get_today()

        if status_date != today:
            self.status = {task["time"]: False for task in self.tasks}
            self.status["_date"] = today
            save_json(self.status_file, self.status)

        self.check_vars: list[tuple[dict, BooleanVar]] = []

        self.sidebar = None
        self.orientation_btn = None
        self.build_ui()
        self.after(1000, self.update_ui_periodically)
        self.after_idle(self.adjust_layout)
        self._layout_locked = False
        
        # 初始化当天已提醒集合
        self._notified_starts: set[str] = set()

        # 可选：启动时对“当前正在进行的段”的开始做忽略，避免启动即提醒
        now = datetime.now()
        today = now.date()
        for task in self.tasks:
            s_str, e_str = task["time"].split("-")
            s_dt = str_to_datetime(today, s_str)
            e_dt = str_to_datetime(today, e_str)
            if s_dt <= now < e_dt:
                self._notified_starts.add(f"{self.date}::{task['time']}")
                break

    # ------------------------------ UI 构建 ------------------------------ #
    def build_ui(self) -> None:
       """
       @brief 构建进度页面的完整 UI 布局。

       @details
       根据当前方向（横向或竖向）创建顶部/侧边栏、计划选择器、时间标签、
       进度条区域（Canvas）、右侧整体完成度区域等主要组件。
       并在首次显示后调用 draw_progress_bar() 进行首绘。

       @note 此方法应在窗口初始化或切换计划/方向时被调用。
       """
       if self.vertical:
           self.top_row_frame = Frame(self)
           self.top_row_frame.pack(side=tk.TOP, fill=tk.X, anchor="nw")

           self.create_sidebar(parent=self.top_row_frame)
           self.sidebar.pack(side=tk.LEFT, padx=(8, 10), pady=(11, 0))

           self.left_frame = Frame(self.top_row_frame, width=200)
           self.left_frame.pack(side=tk.LEFT, anchor="nw", padx=(0, 0))
       else:
           self.create_sidebar(parent=self)
           self.sidebar.pack(side=tk.LEFT, padx=(8, 10), pady=(0, 0))
           self.left_frame = Frame(self, width=200)
           self.left_frame.pack(side=tk.LEFT, fill=tk.Y, anchor="nw")

       anchor_style = "center"

       self.date_label = Label(self.left_frame, text=self.date, font=("Helvetica", 14))
       self.date_label.pack(pady=(20, 0), anchor=anchor_style)

       self.time_label = Label(self.left_frame, text="", font=("Helvetica", 14))
       self.time_label.pack(anchor=anchor_style)
       self.time_label.config(text=datetime.now().strftime("%H:%M"))

       self.plan_var = tk.StringVar(value=self.plan_id)
       plan_ids = list_config_ids()

       self.plan_selector = Combobox(self.left_frame, textvariable=self.plan_var, values=plan_ids, width=8)
       self.plan_selector.config(state="readonly")
       self.plan_selector.pack(pady=(12, 5), anchor="center")
       self.plan_selector.set(self.plan_id)
       self.plan_selector.bind("<<ComboboxSelected>>", lambda e: self.switch_plan(self.plan_var.get()))

       self.center_frame = Frame(self)
       if self.vertical:
           self.center_frame.pack(side=tk.TOP, anchor="n", pady=(20, 0))
       else:
           self.center_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, anchor="n", padx=(0, 0))

       if self.vertical:
           self.canvas = tk.Canvas(self.center_frame,
                                   width=BAR_W + TEXT_W,
                                   highlightthickness=0,
                                   bd=0)
           self.canvas.pack(side=tk.LEFT, anchor="n", padx=0)
       else:
           self.canvas = tk.Canvas(self.center_frame, height=130)
           self.canvas.pack(fill=tk.BOTH, expand=True, padx=10)

       self.right_frame = Frame(self, width=200)
       if self.vertical:
           self.right_frame.pack(side=tk.TOP, fill=tk.X, anchor="n", padx=(0, 0))
       else:
           self.right_frame.pack(side=tk.RIGHT, fill=tk.Y, anchor="n", padx=(0, 30))

       self.progress_label = Label(self.right_frame, text="进度：  0%",
                                   font=("Helvetica", 14),
                                   anchor="e", width=10)
       pad_top = 20 if self.vertical else 48
       self.progress_label.pack(pady=(pad_top, 5), anchor="center")

       self.after_idle(self.draw_progress_bar)

    # ------------------------------ 绘制进度 ------------------------------ #
    def draw_progress_bar(self) -> None:
        """
        @brief 绘制所有任务的进度条、勾选框、时间和任务名。

        @details
        清除旧内容后，根据当前时间、任务配置与完成状态绘制不同颜色的进度段：
        - 浅灰：已过去未完成
        - 浅绿：已完成
        - 浅红：当前任务进行中
        - 白色：未来任务
        每个任务段附带文字与勾选按钮，支持横向与竖向两种布局方式。

        @note 若 Canvas 初次布局尚未就绪，将延迟重新执行此函数。
        """
        for child in self.canvas.winfo_children():
            child.destroy()
        self.canvas.delete("all")
        self.check_vars.clear()

        total = len(self.tasks)
        if total == 0:
            return

        now_dt = datetime.now()
        today = now_dt.date()

        first_start = str_to_datetime(today, self.tasks[0]["time"].split("-")[0])
        last_end = str_to_datetime(today, self.tasks[-1]["time"].split("-")[1])
        total_span_seconds = max(1, (last_end - first_start).total_seconds())
        passed_seconds = min(max(0, (now_dt - first_start).total_seconds()), total_span_seconds)
        gray_ratio = passed_seconds / total_span_seconds

        if not self.vertical:
            canvas_w = self.canvas.winfo_width()
            if canvas_w < 100:
                self.after(100, self.draw_progress_bar)
                return

            bar_top, bar_bottom = 20, 50
            seg_w = canvas_w / total

            self.canvas.create_rectangle(0, bar_top,
                                         int(canvas_w * gray_ratio), bar_bottom,
                                         fill=LIGHT_GRAY, outline="")

            for i, task in enumerate(self.tasks):
                start_str, end_str = task["time"].split("-")
                s_dt = str_to_datetime(today, start_str)
                e_dt = str_to_datetime(today, end_str)

                x0, x1 = int(i * seg_w), int((i + 1) * seg_w)
                mid_x = (x0 + x1) // 2

                is_now = s_dt <= now_dt < e_dt
                is_past = e_dt <= now_dt
                is_future = s_dt > now_dt
                is_done = bool(self.status.get(task["time"], False))

                if is_done:
                    outline = "green"
                elif is_now:
                    outline = "red"
                elif is_future:
                    outline = "black"
                else:
                    outline = GRAY_BORDER

                if is_done:
                    self.canvas.create_rectangle(x0, bar_top, x1, bar_bottom,
                                                 fill=LIGHT_GREEN, outline=outline, width=2)
                elif is_now:
                    seg_total = max(1, (e_dt - s_dt).total_seconds())
                    seg_passed = (now_dt - s_dt).total_seconds()
                    ratio = seg_passed / seg_total
                    fill_x = x0 + int((x1 - x0) * ratio)

                    self.canvas.create_rectangle(x0, bar_top, x1, bar_bottom, fill="white", outline="")
                    self.canvas.create_rectangle(x0, bar_top, fill_x, bar_bottom, fill=LIGHT_RED, outline="")
                    self.canvas.create_rectangle(x0, bar_top, x1, bar_bottom, outline=outline, width=2)
                else:
                    base = LIGHT_GRAY if is_past else "white"
                    self.canvas.create_rectangle(x0, bar_top, x1, bar_bottom,
                                                 fill=base, outline=outline, width=2)

                label_color = "green" if is_done else "red" if is_now else "black"
                self.canvas.create_text(mid_x, bar_bottom + 15, text=task["time"], font=("Arial", 9),
                                        anchor="center", fill=label_color)

                var = BooleanVar(value=is_done)
                cb = Checkbutton(self.canvas, variable=var,
                                 command=lambda t=task, v=var: self.toggle_task(t, v))
                cb.state(["!alternate"])
                if is_future:
                    cb.state(["disabled"])
                self.check_vars.append((task, var))
                self.canvas.create_window(mid_x, bar_bottom + 35, window=cb, anchor="center")

                self.canvas.create_text(mid_x, bar_bottom + 55, text=task["task"],
                                        font=("Arial", 10), anchor="center")
        else:
            canvas_h = self.canvas.winfo_height()
            if canvas_h < 100:
                self.after(100, self.draw_progress_bar)
                return

            bar_left, bar_right = 16, 50
            seg_h = canvas_h / total

            self.canvas.create_rectangle(bar_left, 0,
                                         bar_right, int(canvas_h * gray_ratio),
                                         fill=LIGHT_GRAY, outline="")

            for i, task in enumerate(self.tasks):
                start_str, end_str = task["time"].split("-")
                s_dt = str_to_datetime(today, start_str)
                e_dt = str_to_datetime(today, end_str)

                y0, y1 = int(i * seg_h), int((i + 1) * seg_h)
                mid_y = (y0 + y1) // 2

                is_now = s_dt <= now_dt < e_dt
                is_past = e_dt <= now_dt
                is_future = s_dt > now_dt
                is_done = bool(self.status.get(task["time"], False))

                if is_done:
                    outline = "green"
                elif is_now:
                    outline = "red"
                elif is_future:
                    outline = "black"
                else:
                    outline = GRAY_BORDER

                if is_done:
                    self.canvas.create_rectangle(bar_left, y0, bar_right, y1,
                                                 fill=LIGHT_GREEN, outline=outline, width=2)
                elif is_now:
                    seg_total = max(1, (e_dt - s_dt).total_seconds())
                    seg_passed = (now_dt - s_dt).total_seconds()
                    ratio = seg_passed / seg_total
                    fill_y = y0 + int((y1 - y0) * ratio)

                    self.canvas.create_rectangle(bar_left, y0, bar_right, y1, fill="white", outline="")
                    self.canvas.create_rectangle(bar_left, y0, bar_right, fill_y, fill=LIGHT_RED, outline="")
                    self.canvas.create_rectangle(bar_left, y0, bar_right, y1, outline=outline, width=2)
                else:
                    base = LIGHT_GRAY if is_past else "white"
                    self.canvas.create_rectangle(bar_left, y0, bar_right, y1,
                                                 fill=base, outline=outline, width=2)

                label_color = "green" if is_done else "red" if is_now else "black"
                label_x = bar_right + 20
                self.canvas.create_text(label_x, mid_y - 8, text=task["time"],
                                        font=("Arial", 9), anchor="w", fill=label_color)

                var = BooleanVar(value=is_done)
                cb = Checkbutton(self.canvas, variable=var,
                                 command=lambda t=task, v=var: self.toggle_task(t, v))
                cb.state(["!alternate"])
                if is_future:
                    cb.state(["disabled"])
                self.check_vars.append((task, var))
                self.canvas.create_window(label_x + 80, mid_y - 8, window=cb, anchor="w")

                self.canvas.create_text(label_x, mid_y + 8, text=task["task"],
                                        font=("Arial", 10), anchor="w")

        self.update_progress()

    # -------------------------- 状态切换 / 保存 -------------------------- #
    def toggle_task(self, task: dict, var: BooleanVar) -> None:
        """
        @brief 任务勾选框切换时的回调函数。

        @param task 当前任务的字典信息（含时间段与任务名）
        @param var 对应的 BooleanVar 绑定变量，表示是否勾选

        @details
        检查是否尝试勾选未来时间段，如果非法则禁止。
        否则保存状态，并刷新进度条以更新显示。
        """
        now_dt = datetime.now()
        start_dt = str_to_datetime(now_dt.date(), task["time"].split("-")[0])
        if start_dt > now_dt and var.get():
            messagebox.showwarning("提示", "不能勾选未来时间段！")
            var.set(False)
            return
        self.save_status()
        self.save_daily_completion_summary()
        self.draw_progress_bar()


    def save_status(self) -> None:
        """
        @brief 将当前界面的勾选状态保存到本地状态文件中。

        @details
        遍历所有任务与对应变量，将其值写入状态字典并保存为 JSON 文件。
        同时刷新右上角整体完成度显示。
        """
        for task, var in self.check_vars:
            self.status[task["time"]] = var.get()
        self.status["_date"] = get_today()
        save_json(self.status_file, self.status)
        self.update_progress()
    
    # -------------------------- 进度 & 定时刷新 -------------------------- #
    def update_progress(self) -> None:
        """
        @brief 统计并更新右上角显示的整体任务完成百分比。

        @details
        根据当前任务复选框的勾选状态，计算已完成任务数量并更新 UI。
        """
        done = sum(var.get() for _, var in self.check_vars)
        total = len(self.check_vars)
        percent = int((done / total) * 100) if total else 0
        self.progress_label.config(text=f"进度：{percent:3d}%")

    def update_ui_periodically(self) -> None:
        """
        @brief 每秒刷新一次界面状态，包括当前时间与进度条。

        @details
        自动检测日期变更，若跨天则重新加载任务状态并重绘。
        更新时间标签、重绘进度条并调用布局调整。
        并设定下一次 1000ms 后继续调用自身。
        """
        now_str = get_today()
        if now_str != self.date:
            self.save_daily_completion_summary()

            self.date = now_str
            self.status = {task["time"]: False for task in self.tasks}
            self.status["_date"] = now_str
            save_json(self.status_file, self.status)

            self._notified_starts.clear()   # ← 跨天重置提醒
            self.draw_progress_bar()

        self.time_label.config(text=datetime.now().strftime("%H:%M"))

        # 检查是否到达某个时间段的开始
        self._check_and_notify_task_start()

        self.draw_progress_bar()
        self.adjust_layout()
        self._ui_update_job = self.after(1000, self.update_ui_periodically)

    # ------------------------------ 请假 ------------------------------ #
    def set_leave(self) -> None:
        """
        @brief 将当前日期标记为请假日。

        @details
        用户点击“请假”后提示确认，确认后将日期写入 leave_days.json。
        该日期将不纳入后续统计分析。
        """
        if messagebox.askyesno("请假确认", f"确认将 {self.date} 标记为请假吗？该日将不会纳入统计。"):
            leave_data = load_json("data/leave_days.json", [])
            if self.date not in leave_data:
                leave_data.append(self.date)
                save_json("data/leave_days.json", leave_data)
                messagebox.showinfo("已请假", f"{self.date} 已标记为请假日")

    # -------------------------- 自适应布局 -------------------------- #
    def adjust_layout(self) -> None:
        """
        @brief 根据任务数量与布局方向动态调整窗口尺寸。

        @details
        计算左右中三栏的高度需求，根据横/竖向分别设置窗口宽高与最小尺寸。
        若是竖向布局，同时设置画布高度以适配任务条数。
        @note 若用户正展开下拉框，则跳过本次调整以防 UI 闪烁。
        """
        self.master.update_idletasks()

        if self.plan_selector.tk.call(self.plan_selector._w, "state") == "pressed":
            return

        h_left = self.left_frame.winfo_reqheight()
        h_center = self.center_frame.winfo_reqheight()
        h_right = self.right_frame.winfo_reqheight()

        if not self.vertical:
            total_h = max(h_left, h_center, h_right)
            total_w = max(800, len(self.tasks) * self.min_segment + 200)
        else:
            canvas_h = max(len(self.tasks) * BAR_W, 120)
            total_h = max(300, canvas_h + 200)
            total_w = 260
            self.canvas.config(height=canvas_h)

        self.master.geometry(f"{total_w}x{total_h}")
        self.master.minsize(total_w, total_h)
        self.master.maxsize(total_w, total_h)

    def create_sidebar(self, parent: tk.Widget):
        """
        @brief 创建侧边栏按钮区域。

        @param parent 要放置侧边栏的父容器 Frame。

        @details
        根据当前布局方向设置边距与排列方式。按钮以 2 列网格方式排列，包含：
        - 新建：打开空白设置页面
        - 删除：删除当前计划
        - 设置：编辑当前计划
        - 统计：查看进度统计
        - 横向/竖向：切换页面布局方向
        """
        if self.sidebar and self.sidebar.winfo_exists():
            self.sidebar.destroy()

        TOP_MARGIN = 10
        LEFT_MARGIN = 12
        RIGHT_GAP = 12

        if self.vertical:
            pack_side = tk.LEFT
            pad_x = (LEFT_MARGIN, 0)
            pad_y = (TOP_MARGIN, 0)
        else:
            pack_side = tk.LEFT
            pad_x = (LEFT_MARGIN, RIGHT_GAP)
            pad_y = (TOP_MARGIN, 0)

        self.sidebar = tk.Frame(parent)
        self.sidebar.pack(side=tk.LEFT, padx=(12, 10), pady=(14, 0))

        btn_cfg = dict(width=6)

        buttons = [
            ("新建", lambda: self.open_setting_page(new=True), 1, 1),
            ("删除", self.delete_plan_confirm, 2, 1 ),
            ("设置", self.open_setting_page, 0, 1),
            ("统计", self.open_stats_page, 1, 0),
            ("竖向" if not self.vertical else "横向", self.toggle_orientation, 0, 0),
        ]

        for text, command, row, col in buttons:
            btn = tk.Button(self.sidebar, text=text, command=command, **btn_cfg)
            btn.grid(row=row, column=col, padx=8, pady=4, sticky="nsew")

        self.sidebar.grid_columnconfigure(0, weight=1)
        self.sidebar.grid_columnconfigure(1, weight=1)


    def toggle_orientation(self):
        """
        @brief 切换进度界面的显示方向（横向 <-> 竖向）。

        @details
        更新 vertical 状态，重新构建界面 UI，并恢复自动刷新与窗口居中。
        """
        self.vertical = not self.vertical
        self.master.vertical = self.vertical

        if hasattr(self, "_ui_update_job"):
            self.after_cancel(self._ui_update_job)
            self._ui_update_job = None

        for widget in self.winfo_children():
            widget.destroy()

        self.build_ui()
        self.update_ui_periodically()
        self.master._center_window()


    def open_setting_page(self, new=False):
        """
        @brief 打开设置页面窗口，用于新建或编辑计划。

        @param new 如果为 True 则新建计划；否则编辑当前计划。

        @details
        隐藏主窗口，居中弹出设置页，传入关闭回调以更新主界面。
        """
        from gui.setting_page import SettingPage

        self.master.withdraw()
        win = tk.Toplevel(self)
        win.withdraw()

        plan_id = None if new else self.plan_id
        SettingPage(win, plan_id, on_close=self.on_setting_closed)

        win.update_idletasks()
        self.center_window(win, offset_x=-160)
        win.deiconify()

    def open_stats_page(self):
        """
        @brief 打开统计页面窗口，查看当前计划的历史完成度等信息。
        """
        from gui.stats_page import StatsPage
        self.master.withdraw()  # 隐藏主窗口

        win = tk.Toplevel(self)
        win.title("统计页面")
        win.geometry("1200x500")
        win.attributes("-topmost", False)

        StatsPage(win, self.plan_id, on_close=self.master.deiconify)

        win.after(10, lambda: self.center_window(win))

    def center_window(self, win: tk.Toplevel, offset_x=0, offset_y=0):
        """
        @brief 将给定窗口居中显示。

        @param win 要居中的 Toplevel 窗口
        @param offset_x 水平偏移量（默认 0）
        @param offset_y 垂直偏移量（默认 0）
        """
        win.update_idletasks()
        w = win.winfo_width()
        h = win.winfo_height()
        sw = win.winfo_screenwidth()
        sh = win.winfo_screenheight()
        x = (sw - w) // 2 + offset_x
        y = (sh - h) // 2 + offset_y
        win.geometry(f"{w}x{h}+{x}+{y}")


    def switch_plan(self, selected_plan_id: str):
        """
        @brief 切换到新的计划 ID，并重新加载任务与状态。

        @param selected_plan_id 用户从下拉菜单中选择的新计划 ID。

        @details
        取消定时刷新任务，加载新计划配置，重建界面并居中。
        """
        if selected_plan_id == self.plan_id:
            return

        self.save_daily_completion_summary()  # 保存当前状态

        self.plan_id = selected_plan_id

        if hasattr(self, "_ui_update_job"):
            self.after_cancel(self._ui_update_job)
            self._ui_update_job = None

        self.date = get_today()
        self.status_file = f"data/status_{self.plan_id}.json"
        self.status = load_json(self.status_file, {}) if os.path.exists(self.status_file) else {}

        self.plan_data = load_json(f"config/{self.plan_id}.json", {})
        self.tasks = sorted(
            self.plan_data.get("tasks", []),
            key=lambda t: time_to_minutes(t["time"].split("-")[0])
        )
        self._notified_starts.clear()  # 切换计划后重置提醒
        self.check_vars.clear()

        for widget in self.winfo_children():
            widget.destroy()

        self.build_ui()
        self.update_ui_periodically()
        self.master._center_window()
    
    def delete_plan_confirm(self):
        """
        @brief 用户点击“删除”按钮后的处理逻辑，确认后删除当前计划。

        @details
        弹出确认框，删除本地配置文件。如果删除后无可用配置，打开设置页；
        否则刷新主页面至第一个有效计划。
        """
        self.save_daily_completion_summary()
        
        response = Messagebox.yesno("确认删除", f"是否删除计划：{self.plan_id}？")
        if response != "确认":
            return

        cfg_path = f"config/{self.plan_id}.json"
        if os.path.exists(cfg_path):
            os.remove(cfg_path)

        Messagebox.ok("已删除")
        configs = list_config_ids()
        if not configs:
            self.master.withdraw()
            self.open_setting_page(new=True)
        else:
            self.master.check_and_load_config()
            self.master.show_progress_page()


    def on_setting_closed(self, updated_plan_id=None):
        """
        @brief 设置窗口关闭后的回调函数。
    
        @param updated_plan_id 新设置后的计划 ID，可为 None。
    
        @details
        更新主窗口当前计划，并根据需要切换 UI。
        """
        self.save_daily_completion_summary()

        if updated_plan_id:
            self.master.current_plan_id = updated_plan_id
        else:
            self.master.check_and_load_config()
    
        self.master.show_progress_page()
        self.master.deiconify()
    
        if updated_plan_id:
            self.switch_plan(updated_plan_id)
    
    def save_daily_completion_summary(self):
        """
        @brief 保存当前计划的每日完成率到统一 summary 文件。

        @details
        每个计划仅维护一个汇总文件，如 data/summary_default.json，
        结构为 { "YYYY-MM-DD": ratio }，用于展示统计图。
        """
        date = get_today()
        total = len(self.check_vars)
        done = sum(var.get() for _, var in self.check_vars)
        ratio = round(done / total, 4) if total > 0 else 0
    
        summary_path = f"data/summary_{self.plan_id}.json"
        summary_data = load_json(summary_path, default={})
    
        if summary_data.get(date) == ratio:
            return  # 防止重复写入
    
        summary_data[date] = ratio
        save_json(summary_path, summary_data)

    def _check_and_notify_task_start(self) -> None:
        """
        若当前时间位于任一任务开始时刻的“提醒窗口”内（默认60秒），
        且当天尚未提醒过该时间段，则弹窗提示开始该任务。
        """
        now = datetime.now()
        today = now.date()
    
        # 提醒窗口：开始时刻 ~ 开始时刻 + 60s
        window_seconds = 60
    
        for task in self.tasks:
            start_str = task["time"].split("-")[0]
            s_dt = str_to_datetime(today, start_str)
            key = f"{self.date}::{task['time']}"   # 当天 + 时间段 唯一键
    
            if key in self._notified_starts:
                continue
            
            # 命中提醒窗口
            if s_dt <= now < (s_dt + timedelta(seconds=window_seconds)):
                self._notified_starts.add(key)
    
                # 保证窗口浮到最前
                try:
                    self.master.lift()
                    self.master.attributes("-topmost", True)
                    # 稍后取消顶置交给现有逻辑（或保留顶置也可）
                except Exception:
                    pass
                
                # 弹窗提示（使用 tkinter 的 messagebox，避免 ttkbootstrap 兼容性差异）
                messagebox.showinfo("开始新任务", f"现在 {start_str}，请开始：{task['task']}")
                break  # 本轮只弹一次，避免同秒多任务时多次弹窗
            


