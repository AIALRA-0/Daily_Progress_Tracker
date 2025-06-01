import tkinter as tk
from tkinter import messagebox
from ttkbootstrap import Frame, Button, Entry, Label, Scrollbar
from utils.file_utils import save_json, load_json
from utils.time_utils import auto_pad_time, is_time_format_valid, time_overlap, is_full_day_covered
import os


class SettingPage(Frame):
    """
    @class SettingPage
    @brief 时间段任务配置界面。

    提供任务时间段添加、编辑、验证、保存等交互功能。
    """

    def __init__(self, master, current_plan_id, on_close=None):
        """
        @brief 初始化设置页面。
        @param master 父窗口（通常为 Toplevel）
        @param current_plan_id 当前加载的计划 ID
        @param on_close 设置完成关闭时的回调函数
        """
        super().__init__(master)
        self.pack(fill=tk.BOTH, expand=True)
        self.master = master
        self.entries = []
        self.current_plan_id = current_plan_id
        self.on_close = on_close
        
        Label(self, text="时间段设置（格式：HH:MM-HH:MM）", font=("Arial", 12)).pack(pady=5)

        self.task_frame = Frame(self)
        self.task_frame.pack(pady=10)

        btn_frame = Frame(self)
        btn_frame.pack(side=tk.BOTTOM, pady=10)
        Button(btn_frame, text="添加", command=self.add_entry).pack(side=tk.LEFT, padx=10)
        Button(btn_frame, text="保存", command=self.save_config).pack(side=tk.LEFT, padx=10)
        Button(btn_frame, text="退出", command=self.exit_and_return).pack(side=tk.RIGHT, padx=10)
        self.master.protocol("WM_DELETE_WINDOW", self.exit_and_return)
        
        if current_plan_id:
            self.load_existing()
        else:
            self.add_entry("00:00-24:00", "任务名称")

    def add_entry(self, time_text="", task_text=""):
        """
        @brief 添加一个时间段任务条目。
        @param time_text 初始时间段文本
        @param task_text 初始任务描述文本
        """
        if not time_text and self.entries:
            last_time = self.entries[-1][0].get().strip()
            if "-" in last_time:
                _, end = last_time.split("-")
                time_text = f"{end}-"
    
        row = Frame(self.task_frame)
        row.pack(fill=tk.X, pady=5)
    
        inner = Frame(row)
        inner.pack(anchor="center")
    
        time_entry = Entry(inner, width=15)
        time_entry.insert(0, time_text)
        time_entry.pack(side=tk.LEFT, padx=5)
    
        task_entry = Entry(inner, width=40)
        task_entry.insert(0, task_text)
        task_entry.pack(side=tk.LEFT, padx=5)
    
        del_btn = Button(inner, text="删除", command=lambda: self.delete_entry(row, (time_entry, task_entry)))
        del_btn.pack(side=tk.LEFT, padx=5)
    
        self.entries.append((time_entry, task_entry))
        self.after(50, self.expand_window_height)

    def delete_entry(self, row_frame, entry_pair):
        """
        @brief 删除指定的任务条目。
        @param row_frame 行容器 Frame
        @param entry_pair (time_entry, task_entry) 元组
        """
        row_frame.destroy()
        if entry_pair in self.entries:
            self.entries.remove(entry_pair)
        self.after(50, self.expand_window_height)

    def expand_window_height(self):
        """
        @brief 动态调整窗口高度以适应条目数量。
        """
        header_height = 60
        row_height = 40
        button_bar_height = 80

        total_height = header_height + button_bar_height + row_height * len(self.entries)
        new_height = max(min(total_height, 1500), 150)
        width = max(self.master.winfo_width(), 800)
        self.master.geometry(f"{width}x{new_height}")

    def load_existing(self):
        """
        @brief 加载当前计划 ID 对应的任务配置。
        """
        path = f"config/{self.current_plan_id}.json"
        data = load_json(path, default={})
        for block in data.get("tasks", []):
            self.add_entry(block["time"], block["task"])

    def save_config(self):
        """
        @brief 保存当前输入的任务配置并进行校验。
        """
        from datetime import datetime
        tasks = []

        for idx, (time_entry, task_entry) in enumerate(self.entries):
            time_range = auto_pad_time(time_entry.get().strip())
            task = task_entry.get().strip()

            if not time_range or not task:
                messagebox.showwarning(
                    "输入不完整",
                    f"第 {idx + 1} 项未填写完整，请填写时间段和任务名称。"
                )
                return

            if not is_time_format_valid(time_range):
                messagebox.showerror(
                    "时间格式错误",
                    f"第 {idx + 1} 项时间段格式错误：{time_range}\n必须为 HH:MM-HH:MM，例如 09:00-12:00。"
                )
                return

            try:
                start_str, end_str = time_range.split('-')
                if end_str == "24:00":
                    end_str = "23:59"
                start_time = datetime.strptime(start_str, "%H:%M")
                end_time = datetime.strptime(end_str, "%H:%M")
            except Exception:
                messagebox.showerror(
                    "解析错误",
                    f"第 {idx + 1} 项时间段无法解析：{time_range}"
                )
                return

            if end_time <= start_time:
                messagebox.showerror(
                    "时间顺序错误",
                    f"第 {idx + 1} 项时间段不合理：{time_range}\n结束时间必须晚于开始时间。"
                )
                return

            tasks.append({"time": time_range, "task": task})

        indexed_tasks = [(i, t["time"]) for i, t in enumerate(tasks)]
        sorted_times = sorted(indexed_tasks, key=lambda x: x[1].split('-')[0])
        for i in range(len(sorted_times) - 1):
            idx1, t1 = sorted_times[i]
            idx2, t2 = sorted_times[i + 1]
            if time_overlap(t1, t2):
                messagebox.showerror(
                    "时间段重叠",
                    f"第 {idx1 + 1} 项 [{t1}] 与第 {idx2 + 1} 项 [{t2}] 存在重叠，请检查并修改。"
                )
                return

        if not is_full_day_covered(tasks):
            messagebox.showerror(
                "时间覆盖不完整",
                "所有时间段未能覆盖完整的 00:00 - 24:00。\n请确保无缝衔接，避免有空缺时间。"
            )
            return

        plan_id = self.current_plan_id or self.prompt_plan_id()
        if not plan_id:
            return

        all_ids = os.listdir("config")
        if not self.current_plan_id and f"{plan_id}.json" in all_ids:
            messagebox.showerror("计划ID已存在", f"计划ID“{plan_id}”已存在，请重新输入一个唯一的ID。")
            return

        save_json(f"config/{plan_id}.json", {"id": plan_id, "tasks": tasks})
        messagebox.showinfo("保存成功", f"计划“{plan_id}”已成功保存。")

        if self.on_close:
            self.on_close(plan_id)

    def exit_and_return(self):
        """
        @brief 退出设置页并回到主页面，如未保存配置则阻止退出。
        """

        configs = os.listdir("config")
        if not configs:
            messagebox.showwarning("尚未设置", "请至少保存一个计划配置后再退出。")
            return

        if self.on_close:
            self.on_close(self.current_plan_id)

        if isinstance(self.master, tk.Toplevel):
            self.master.destroy()

    def prompt_plan_id(self):
        """
        @brief 弹出窗口让用户输入新计划 ID。
        @return str 用户输入的计划 ID，如果取消则为 None。
        """
        top = tk.Toplevel(self)
        top.title("输入计划ID")
        Label(top, text="请输入本次计划的唯一ID:").pack(pady=5)
        entry = Entry(top)
        entry.pack(pady=5)

        result = {}

        def confirm():
            plan_id = entry.get().strip()
            if not plan_id:
                messagebox.showwarning("输入为空", "请输入计划ID")
                return
            result["id"] = plan_id
            top.destroy()

        Button(top, text="确认", command=confirm).pack(pady=5)
        self.wait_window(top)
        return result.get("id")
