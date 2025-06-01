import tkinter as tk
from ttkbootstrap import Frame, Label, Combobox
from ttkbootstrap.dialogs import Messagebox

from utils.file_utils import load_json, list_config_ids
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.colors import LinearSegmentedColormap

import matplotlib.pyplot as plt
from datetime import datetime, timedelta

# ---------- Matplotlib 字体配置 ----------
plt.rcParams['font.family'] = 'SimHei'  # 黑体适配中文
plt.rcParams['axes.unicode_minus'] = False  # 正确显示负号


class StatsPage(Frame):
    """
    @class StatsPage
    @brief 统计页面：展示过去30天完成率图表（柱状图）和平均值。
    
    @details
    - 支持计划切换
    - 自动加载计划对应的 summary 数据
    - 图表颜色随完成率渐变
    """

    def __init__(self, master, current_plan_id, on_close=None):
        """
        @brief 构造统计页面。
        @param master 父窗口（通常为 Toplevel）
        @param current_plan_id 当前计划 ID
        @param on_close 关闭页面的回调函数
        """
        super().__init__(master)
        self.pack(fill=tk.BOTH, expand=True)

        self.master = master
        self.current_plan_id = current_plan_id
        self.on_close = on_close

        self._build_ui()
        self.master.protocol("WM_DELETE_WINDOW", self.handle_close)
        self.after_idle(self.refresh_stats)

    def _build_ui(self):
        """
        @brief 构建 UI 元素：计划选择器、图表区域、平均完成率标签。
        """
        Label(self, text="计划选择：").pack(anchor="w", padx=10, pady=5)

        self.plan_selector = Combobox(self, values=list_config_ids(), width=20)
        self.plan_selector.set(self.current_plan_id)
        self.plan_selector.pack(anchor="w", padx=10)
        self.plan_selector.bind("<<ComboboxSelected>>", self.refresh_stats)

        self.figure = plt.Figure(figsize=(12, 5.5), dpi=100)
        self.canvas = FigureCanvasTkAgg(self.figure, master=self)
        self.canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)

        self.avg_label = Label(self, text="平均完成率：0%", font=("Helvetica", 12))
        self.avg_label.pack(pady=5)

    def refresh_stats(self, event=None):
        """
        @brief 刷新图表数据。
        @param event ComboBox 事件（可忽略）
        """
        plan_id = self.plan_selector.get()
        today = datetime.now()
        last_30_days = [(today - timedelta(days=i)).strftime("%Y-%m-%d") for i in range(29, -1, -1)]

        summary_path = f"data/summary_{plan_id}.json"
        summary_data = load_json(summary_path, default={})

        daily_data = [{"date": d, "ratio": summary_data.get(d, 0)} for d in last_30_days]

        if daily_data:
            avg_ratio = sum(d["ratio"] for d in daily_data) / len(daily_data)
            self.avg_label.config(text=f"过去30天平均完成率：{int(avg_ratio * 100)}%")
        else:
            self.avg_label.config(text="过去30天平均完成率：无数据")

        self.after(20, lambda: self.plot_daily_bar(daily_data))

    def plot_daily_bar(self, daily_data):
        """
        @brief 绘制30天完成率柱状图。

        @param daily_data 结构为 [{'date': str, 'ratio': float}, ...]
        """
        self.figure.clear()
        ax = self.figure.add_subplot(111)

        dates = [d["date"] for d in daily_data]
        ratios = [d["ratio"] * 100 for d in daily_data]

        # 渐变绿色 colormap（0% -> 浅绿, 100% -> 深绿）
        cmap = LinearSegmentedColormap.from_list("green_shades", ["#ccffcc", "#006600"], N=100)
        colors = [cmap(min(int(r), 99)) for r in ratios]

        bars = ax.bar(dates, ratios, color=colors)

        for bar, value in zip(bars, ratios):
            ax.text(
                bar.get_x() + bar.get_width() / 2,
                bar.get_height() + 1,
                f"{int(value)}%",
                ha='center',
                va='bottom',
                fontsize=8
            )

        ax.set_ylim(0, 110)
        ax.set_ylabel("完成率 (%)")
        ax.set_xticks(dates)
        ax.set_xticklabels(dates, rotation=45, ha='right')

        if ratios:
            avg_value = int(sum(ratios) / len(ratios))
            ax.set_title(f"过去30天完成率（平均 {avg_value}%）")
        else:
            ax.set_title("过去30天完成率")

        self.figure.subplots_adjust(bottom=0.25, top=0.88)
        self.canvas.draw()

    def handle_close(self):
        """
        @brief 窗口关闭事件，触发 on_close 回调并销毁窗口。
        """
        if self.on_close:
            self.on_close()
        self.master.destroy()