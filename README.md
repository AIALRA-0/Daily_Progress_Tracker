
# 日常进度追踪器 Daily Progress Tracker

一个可视化、时间段驱动的每日任务追踪应用，基于 **Tkinter + ttkbootstrap + matplotlib** 开发，支持任务配置、完成状态记录、统计分析图表、自动隐藏等功能。
<div align="center">
  <img src="https://github.com/user-attachments/assets/b439e20f-c8ad-4f98-a1f8-f8dea7eed258" width="700"/>
</div>

---

## ⚠️ 项目说明
本项目为作者自用的日常任务追踪工具，初始开发以个人需求为主，界面行为和逻辑偏定制化，尚未全面测试。
可能存在部分 bug 或异常场景未处理，如需部署到实际环境，请谨慎评估并自行测试。

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
### 横向任务进度界面
<div align="center"> <img src="https://github.com/user-attachments/assets/b439e20f-c8ad-4f98-a1f8-f8dea7eed258" width="700"/> </div>

### 竖向任务进度界面
<div align="center"> <img src="https://github.com/user-attachments/assets/16a811d7-1026-4ebb-8234-fbddc8567c19" width="200"/> </div>

### 统计图表页面（30天完成率）
<div align="center"> <img src="https://github.com/user-attachments/assets/47d0dd9e-5826-495e-a33d-dfeae770ac79" width="700"/> </div>

### 任务时间段配置页面
<div align="center"> <img src="https://github.com/user-attachments/assets/c61b9d04-cbd9-4b19-a4d2-4df3a21d2ab3" width="600"/> </div>

---

## 🗂️ 项目结构

```
项目目录/
├── main.py           # 主程序入口，负责加载计划、启动界面
├── build.bat         # 一键打包脚本：自动生成 requirements.txt 并打包成 .exe
├── config/           # 用户自定义的任务计划配置（每个 JSON 文件对应一个计划）
├── data/             # 自动生成的数据，如打卡状态、完成率统计、请假记录等
├── gui/              # 图形界面模块，包含进度页、统计页、设置页
├── utils/            # 通用工具函数模块，如时间解析、文件读写
└── requirements.txt  # 项目依赖列表，可用于 pip 安装所需库
````

---

## 💻 快速开始

### 1️⃣ 安装依赖

```bash
pip install -r requirements.txt
````

### 2️⃣ 启动项目（开发模式）

```bash
python main.py
```

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



