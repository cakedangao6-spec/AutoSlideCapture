# GitHub 上传整理报告

## 快速状态

- 项目：CMOS 自动截图生成 PPT 工程
- 当前状态：已整理为适合上传 GitHub 的最小项目仓库；保留源码与说明，排除课程资料、运行输出和本机配置
- 入口文件：`capture_slides.py`
- 运行方式：`python capture_slides.py` 或 `python capture_slides.py --chapter 2 --title "Basic MOS Device Physics" --pages 50 --interval 0.5 --select-region`
- 最后修改：2026-06-02

## 已检查内容

- 项目结构：单脚本 Python 工具，依赖记录在 `requirements.txt`。
- 入口文件：`capture_slides.py`。
- 依赖：`pyautogui`、`Pillow`。
- 运行方式：支持交互式运行和命令行参数运行。
- 路径情况：核心脚本使用脚本所在目录作为基础路径，没有发现写死的个人绝对路径。
- 账号信息：未发现账号、密码、Token、API Key 等敏感凭据。

## 已清理内容

- `captures/`：运行生成的截图输出，包含课程页面截图，不适合公开上传。
- `pdf/`：课程讲义 PDF，属于课程资料，不适合公开上传。
- `__pycache__/`：Python 缓存文件。
- `capture_region.json`：本机屏幕区域坐标，与个人显示器和窗口位置相关。

## 已新增或优化

- 新增 `.gitignore`，排除 Python 缓存、虚拟环境、本地配置、截图输出、PPT/PDF 成品和编辑器临时文件。
- 新增 `capture_region.example.json`，保留区域配置格式示例。
- 重写 `README.md`，补充项目简介、功能特点、使用环境、依赖安装、运行方法、输入/输出说明和示例预留说明。
- 新增本报告 `GITHUB_UPLOAD_REPORT.md`。

## 不确定或需后续确认

- 当前仓库只发现自动截图脚本，未发现独立的 PPT 生成脚本。如果需要完整展示“截图并生成 PPT”的闭环，可以后续新增一个将 `captures/` 图片批量插入 PPT 的脚本。
- README 中没有附带真实课程截图示例。建议后续使用脱敏测试页面生成一张示例图，或用自制空白页面生成示例输出。

## 建议上传 GitHub 的文件

- `capture_slides.py`
- `requirements.txt`
- `README.md`
- `.gitignore`
- `capture_region.example.json`
- `GITHUB_UPLOAD_REPORT.md`

## 不建议上传的内容

- 课程讲义 PDF
- 真实课程截图
- 生成的 PPT/PDF 成品
- 本机屏幕坐标配置
- 任何包含学校平台、账号、个人姓名、学号或课程内部资料的信息
