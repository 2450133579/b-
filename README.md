Markdown# 🌌 多模态加工厂 2.0 (Multimodal Factory)

本项目是一个全自动的多模态视频分析与对话处理流水线。只需输入一个 Bilibili 或 YouTube 视频链接，系统将自动进行视频下载、关键帧抽取、语音识别、声纹分离、图文对齐，并构建本地 Chroma 向量数据库进行 RAG（检索增强生成）记忆。结合 Vue3 前端，用户可以与视频内容进行深入的 AI 多模态对话。

## 📂 项目结构

```plaintext
multimodal_factory/
├── backend/
│   ├── main.py              # FastAPI 后端引擎，接口路由与流水线调度
│   ├── llm_engine.py        # RAG 检索、向量切片与大模型对话逻辑
│   ├── config.py            # 路径、端口及模型参数配置 (核心配置文件)
│   ├── media_engine.py      # yt-dlp 下载与 FFmpeg 视频抽帧逻辑
│   ├── speech_engine.py     # Faster-Whisper 语音识别与 Pyannote 声纹分离
│   └── cookies.txt          # (可选) B站或网页的 Cookie 缓存
└── frontend/
    └── src/App.vue          # Vue3 交互主界面
🧠 用到的核心模型与技术本流水线集成了多项最前沿的 AI 模型：语音识别 (ASR)：large-v3-turbo (基于 Faster-Whisper，支持 GPU 加速)。声纹分离 (Diarization)：pyannote/speaker-diarization-3.1 (精准识别不同的说话人)。向量记忆库 (Embedding)：qwen3-embed (将视频文案切片并存入本地 ChromaDB 向量数据库)。对话大模型 (LLM)：默认配置为本地 gemma-4，前端支持一键切换配置调用 阿里通义 (Qwen)、DeepSeek、月之暗面 (Kimi) 等 OpenAI 格式的兼容 API。视频/音频处理工具：外部调用 FFmpeg 与 yt-dlp。⚙️ 环境依赖与配置说明1. 核心外部工具：FFmpeg (必须配置！)本项目依赖 ffmpeg 进行视频流的合并与抽帧操作。你必须在本地电脑安装 FFmpeg，并在项目中配置其绝对路径。配置方法：打开 backend/config.py，找到 FFMPEG_PATH 变量，将其修改为你本地的 ffmpeg 可执行文件路径。例如：Python# ⚠️ 本地环境配置 (将下方路径替换为你电脑中的 ffmpeg.exe 真实路径)
FFMPEG_PATH = r"C:\Your\Path\To\ffmpeg\bin\ffmpeg.exe"
2. 声纹模型授权 (HuggingFace Token)声纹分离使用的是 Pyannote 3.1 模型，需要在 HuggingFace 获取授权。配置方法：访问 pyannote/speaker-diarization-3.1 并接受用户协议。在 HuggingFace 设置中生成一个 Access Token。打开 backend/speech_engine.py，找到第 17 行，将 Token 替换：PythonHF_TOKEN = "hf_这里替换成你的真实Token"
3. 本地模型 API 配置打开 backend/config.py，按需修改本地 LLM 引擎和向量引擎的地址（例如使用 llama-cpp-python 或 vLLM 部署的本地接口）：LOCAL_LLM_URL：本地对话大模型 API 地址 (默认 8080 端口)。LOCAL_EMBEDDING_URL：本地向量模型 API 地址 (默认 8081 端口)。🚀 快速启动 (一键部署代码)如果你想一键同时安装依赖并启动前后端，可以在项目根目录使用以下脚本。Windows 用户 (start.bat)在项目根目录新建一个文件命名为 start.bat，粘贴以下内容并保存。双击运行即可自动弹出两个窗口分别运行前后端：DOS@echo off
echo ========================================
echo 正在启动 🌌 多模态加工厂 2.0
echo ========================================

echo [1/2] 正在启动后端服务...
cd backend
start cmd /k "pip install -r requirements.txt && uvicorn main:app --host 0.0.0.0 --port 8000"

echo [2/2] 正在启动前端服务...
cd ../frontend
start cmd /k "npm install && npm run dev"
Linux / macOS 用户 (start.sh)你可以直接在项目根目录的终端中，完整复制并运行以下命令（它将在后台启动后端，前台启动前端）：Bash#!/bin/bash
echo "正在启动多模态加工厂..."
cd backend && pip install -r requirements.txt && uvicorn main:app --host 0.0.0.0 --port 8000 &
cd frontend && npm install && npm run dev
(注：对于 torch 和 torchaudio，为了获得最佳的 GPU 加速体验，建议前往 PyTorch 官网复制对应你电脑 CUDA 版本的安装命令。)🎮 使用方法打开前端页面后，在顶部输入框填入你需要分析的 Bilibili 或 YouTube 视频链接。点击 "🚀 开始解析"。此时后端会自动完成：下载 -> 抽帧 -> 语音识别 -> 图文对齐 -> 向量切片记忆。如果想使用云端大模型（如 DeepSeek），可以点击顶部右侧的 "⚙️ 设置" 按钮，一键切换并填入你的 API Key。解析完成后，切换到 "💬 AI 对话" 标签页。在聊天框中提出问题，AI 将利用 RAG 技术，在 ChromaDB 向量库中瞬间检索相关的视频底稿片段，并结合最新的抽帧图片为你提供精准解答！支持在此页面上传附加图片或 TXT 文本进行多模态联合分析。⚠️ 端口占用说明为确保项目正常运行，请确保以下端口未被其他程序占用：端口用途8000FastAPI 后端服务5173Vue3 前端 UI 界面 (Vite 默认)8080对话大模型 API (本地)8081Qwen3 向量模型 API (本地)🤝 鸣谢与声明本项目基于开源社区多个优秀项目构建，仅供学习交流使用。使用 Pyannote 声纹分离需在 HuggingFace 接受协议并在 speech_engine.py 中填入你的 HF_TOKEN。
