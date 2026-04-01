@echo off
:: 强制使用 UTF-8 编码
chcp 65001 >nul
color 0A
title 🌌 BiliBili AI 智能解析舱 - 环境与资产自检

echo ========================================================
echo           🌌 BiliBili AI 智能解析舱 (Bili-AI-Analyzer)
echo           [环境自检] 正在核对核心资产...
echo ========================================================
echo.

:: 1. 检查 Python 运行环境
if not exist "python_env\python.exe" (
    color 0C
    echo [错误] 找不到核心运行环境 python_env
    pause
    exit
)

:: 2. 打印版本信息
set /p="[版本信息] " <nul
.\python_env\python.exe --version
echo.

:: 3. 核心模型资产检查
echo [🧠 模型检测] 正在扫描本地 AI 权重文件...
:: 检查关键文件是否存在，注意这里去掉了所有可能引起歧义的括号
if exist "models\large-v3-turbo\model.bin" (
    echo [ OK ] 检测到本地模型资产: large-v3-turbo
) else (
    color 0E
    echo [警告] 未能在 models 文件夹下发现模型权重文件
    echo [提示] 程序将尝试从云端下载 - 约 1.6GB - 请确保网络畅通
    color 0A
)
echo --------------------------------------------------------

:: 4. 检查主程序
if not exist "main.py" (
    color 0C
    echo [错误] 找不到主程序 main.py
    pause
    exit
)

:: 5. 正式启动
echo.
echo [🚀 启动] 正在唤醒 GPU 并载入模型，请稍候...
echo.

.\python_env\python.exe main.py

echo.
echo ========================================================
echo [状态] 程序运行已结束。
echo ========================================================
pause