
# 日常进度追踪器（Daily Progress Tracker）

一个可视化、时间段驱动的每日任务追踪应用，基于 **Tkinter + ttkbootstrap + matplotlib** 开发，支持任务配置、完成状态记录、统计分析图表、自动隐藏等功能。

---

## 🚀 功能特色

- 🕘 **时间段任务配置**：支持 `HH:MM-HH:MM` 格式定义任务，要求 100% 时间覆盖。
- ✅ **任务进度可视化**：横向或竖向进度条，多种颜色标示当前状态。
- 📊 **30天统计图表**：自动保存每日完成率，并以柱状图展示。
- 💤 **贴顶自动隐藏窗口**：窗口置顶贴近屏幕上沿后自动隐藏，鼠标悬停自动展开。
- 🔧 **内置计划编辑器**：新建、编辑计划配置，实时更新界面。
- 📦 **一键打包脚本**：执行 `build.bat` 自动提取依赖并打包为可执行文件（.exe）。

---

## 📷 界面演示

> 👉 可将实际截图保存至 `assets/` 文件夹，并替换下方图片路径。

### 横向任务进度界面
![横向进度示例](assets/horizontal_progress.png)

### 竖向任务进度界面
![竖向进度示例](assets/vertical_progress.png)

### 统计图表页面（30天柱状图）
![统计图示例](assets/statistics_bar_chart.png)

### 配置任务时间段界面
![设置页面示例](assets/setting_page.png)

---

## 🗂️ 项目结构

```

项目目录/
├── main.py
├── build.bat
├── config/
├── data/
├── gui/
├── utils/
└── requirements.txt
````

---

## 💻 快速开始

### 1️⃣ 安装依赖

```bash
pip install -r requirements.txt
````

---

### 2️⃣ 启动项目（开发模式）

```bash
python main.py
```

---

## 🛠️ 打包为可执行文件

```bash
./build.bat
```

将自动生成：

* `requirements.txt`（包含 pipreqs 与 pyinstaller）
* `dist/main.exe` 可执行程序

---

## 📁 数据说明

* `config/*.json`：计划任务配置
* `data/status_*.json`：每日勾选状态记录
* `data/summary_*.json`：完成率汇总
* `data/leave_days.json`：请假记录

---

## 📄 许可证

MIT License

---



