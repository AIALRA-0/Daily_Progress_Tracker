import os
import tkinter as tk
from ttkbootstrap import Style
from ttkbootstrap.dialogs import Messagebox

from utils.file_utils import *
from gui.setting_page import SettingPage
from gui.progress_page import ProgressPage
from gui.stats_page import StatsPage


class DailyProgressApp(tk.Tk):
    """
    @class DailyProgressApp
    @brief 日常进度追踪应用主窗口类。

    提供自动贴顶隐藏、鼠标悬停展开、页面切换、计划配置等功能。
    """

    def __init__(self):
        """
        @brief 初始化主窗口，加载配置，并设置自动隐藏逻辑。
        """
        super().__init__()
        self.title("Daily Progress Tracker")
        self.geometry("900x500")
        self.resizable(False, False)
        self.style = Style("cosmo")
        ensure_dirs()

        self._auto_hide_threshold = 100000
        self._visible_edge_height = -20
        self._edge_margin = 50
        self._slide_step = 10
        self._slide_interval = 1
        self._hide_delay = 200

        self._is_hidden = False
        self._animating = False
        self._hide_job = None

        self.vertical = False
        self.current_plan_id = None

        configs = list_config_ids()
        if configs:
            self.current_plan_id = configs[0]
            self.show_progress_page()
        else:
            self.withdraw()
            self.show_setting_page()

        self.bind("<Configure>", self._on_configure)
        self.bind("<Enter>", self._on_pointer_enter)
        self.bind("<Leave>", self._on_pointer_leave)
        self.protocol("WM_DELETE_WINDOW", self._on_close)

    def _on_configure(self, _):
        """
        @brief 窗口位置变化回调，判断是否准备隐藏。
        @param _ 未使用的事件参数。
        """
        if not self._is_hidden and not self._animating and self.winfo_y() <= self._auto_hide_threshold:
            if self._hide_job is None:
                self._hide_job = self.after(300, self._try_hide)

    def _on_pointer_enter(self, _):
        """
        @brief 鼠标进入窗口区域，取消隐藏并立即展开。
        @param _ 未使用的事件参数。
        """
        self._cancel_hide_job()
        self._animate_show()

    def _on_pointer_leave(self, _):
        """
        @brief 鼠标离开窗口，若贴顶则准备隐藏。
        @param _ 未使用的事件参数。
        """
        if self.winfo_y() <= self._auto_hide_threshold and not self._is_hidden:
            if self._hide_job is None:
                self._hide_job = self.after(self._hide_delay, self._try_hide)

    def _try_hide(self):
        """
        @brief 判断是否应执行隐藏，若鼠标已移出缓冲区则触发隐藏动画。
        """
        self._hide_job = None
        if not self._pointer_in_widget():
            self._animate_hide()

    def _animate_hide(self):
        """
        @brief 执行隐藏动画，窗口向上滑动。
        """
        if self._is_hidden or self._animating:
            return
        self._animating = True
        self.update_idletasks()
        target_y = -(self.winfo_height() - self._visible_edge_height)
        self._slide(to_y=target_y, on_complete=lambda: setattr(self, "_is_hidden", True))

    def _animate_show(self):
        """
        @brief 执行展开动画，窗口滑回顶部。
        """
        if not self._is_hidden or self._animating:
            return
        self._animating = True
        self._slide(to_y=0, on_complete=lambda: setattr(self, "_is_hidden", False))

    def _slide(self, to_y: int, on_complete):
        """
        @brief 执行窗口平滑滑动动画。
        @param to_y 滑动目标 y 坐标。
        @param on_complete 动画完成后的回调函数。
        """
        cur_x, cur_y = self.winfo_x(), self.winfo_y()
        step = self._slide_step if to_y > cur_y else -self._slide_step
        next_y = cur_y + step

        if (step > 0 and next_y >= to_y) or (step < 0 and next_y <= to_y):
            self.geometry(f"+{cur_x}+{to_y}")
            self._animating = False
            on_complete()
            if self._pointer_in_widget():
                self._cancel_hide_job()
            return

        self.geometry(f"+{cur_x}+{next_y}")
        self.after(self._slide_interval, lambda: self._slide(to_y, on_complete))

    def _pointer_in_widget(self) -> bool:
        """
        @brief 判断鼠标是否仍在窗口及其上方缓冲区内。
        @return True 若在有效区域内，否则 False。
        """
        x, y = self.winfo_pointerx(), self.winfo_pointery()
        left, top = self.winfo_rootx(), self.winfo_rooty() - self._edge_margin
        right = left + self.winfo_width()
        bottom = self.winfo_rooty() + self.winfo_height()
        return left <= x <= right and top <= y <= bottom

    def _cancel_hide_job(self):
        """
        @brief 取消延迟隐藏任务（若存在）。
        """
        if self._hide_job:
            self.after_cancel(self._hide_job)
            self._hide_job = None

    def show_setting_page(self):
        """
        @brief 显示设置页面窗口。
        """
        win = tk.Toplevel(self)
        win.title("设置页面")
        win.geometry("800x400")
        SettingPage(win, self.current_plan_id, on_close=self.handle_setting_close)

    def handle_setting_close(self, updated_plan_id=None):
        """
        @brief 设置页面关闭后的回调。
        @param updated_plan_id 设置页返回的新计划 ID（可选）。
        """
        self.current_plan_id = updated_plan_id or (list_config_ids() or [None])[0]
        self.deiconify()
        self.after(10, self.show_progress_page)

    def show_progress_page(self):
        """
        @brief 显示进度页面。
        """
        self.clear_center_frames()
        self.attributes("-topmost", True)
        ProgressPage(self, self.current_plan_id, vertical=self.vertical)
        self.after(10, self._center_window)

    def show_stats_page(self):
        """
        @brief 显示统计页面。
        """
        self.clear_center_frames()
        self.attributes("-topmost", False)
        StatsPage(self, self.current_plan_id)
        self.after(10, self._center_window)

    def delete_current_plan(self):
        """
        @brief 删除当前计划并重新加载配置。
        """
        if Messagebox.yesno("确认删除", f"是否删除计划：{self.current_plan_id}？"):
            cfg_path = f"config/{self.current_plan_id}.json"
            if os.path.exists(cfg_path):
                os.remove(cfg_path)
            self.current_plan_id = None
            self.check_and_load_config()
            self.show_progress_page()

    def check_and_load_config(self):
        """
        @brief 检查并加载计划配置，如果为空则显示设置页面。
        """
        configs = list_config_ids()
        if not configs:
            self.current_plan_id = None
            self.show_setting_page()
        elif self.current_plan_id not in configs:
            self.current_plan_id = configs[0]

    def clear_center_frames(self):
        """
        @brief 清除窗口中所有控件。
        """
        [w.destroy() for w in self.winfo_children()]

    def _center_window(self):
        """
        @brief 将窗口水平居中并贴近屏幕顶部。
        """
        self.update_idletasks()
        w, h = self.winfo_width(), self.winfo_height()
        sw = self.winfo_screenwidth()
        x = (sw - w) // 2
        self.geometry(f"{w}x{h}+{x}+0")

    def _on_close(self):
        """
        @brief 在关闭主窗口时保存统计
        """
        for w in self.winfo_children():
            if isinstance(w, ProgressPage):
                w.save_daily_completion_summary()
        self.destroy()



if __name__ == "__main__":
    """
    @brief 启动 DailyProgress 应用。
    """
    app = DailyProgressApp()
    app.mainloop()
