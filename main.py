import yt_dlp
import os
import torch
from faster_whisper import WhisperModel
from typing import Optional
import anthropic
import gradio as gr

import sys
import os
current_dir = os.path.dirname(os.path.abspath(__file__))
model_path = os.path.join(current_dir, "models", "large-v3-turbo")
from openai import OpenAI
# --- 在 main.py 的初始化部分 ---

# --- [修改后的开头逻辑] ---
import os
import sys
from faster_whisper import WhisperModel

base_path = os.path.dirname(os.path.abspath(__file__))
# 优先匹配你截图中的文件夹名 'model'
local_model_folder = os.path.join(base_path, "model", "large-v3-turbo")

# 默认值
model_to_use = "large-v3-turbo"
is_local = False

# 严谨检测 model.bin
if os.path.exists(os.path.join(local_model_folder, "model.bin")):
    model_to_use = os.path.abspath(local_model_folder)
    is_local = True
    print(f"✅ [系统确认] 成功锁定本地模型: {model_to_use}")
else:
    print("🌐 [系统确认] 未发现本地模型，将尝试在线加载...")

# --- 关键修复：去掉 self. ---
try:
    # 如果你是在类里面，就保留 self.model；如果你在外面，就直接写 model
    model = WhisperModel(
        model_to_use,
        device="cuda",          # 强制 GPU
        compute_type="float16",  # 13代 i7 + RTX 显卡标配
        local_files_only=is_local
    )
    print("🚀 AI 引擎已就绪，准备解析视频！")
except Exception as e:
    print(f"❌ 启动失败: {e}")

def get_ffmpeg_path():
    """动态获取 FFmpeg 的路径"""
    # getattr(sys, 'frozen', False) 是 PyInstaller 的专属魔法变量
    # 如果它为 True，说明当前是打包后的 exe 正在运行
    if getattr(sys, 'frozen', False):
        # 获取 exe 所在的当前目录
        application_path = os.path.dirname(sys.executable)
        # 假设我们把 ffmpeg.exe 放在和主程序 exe 同一个目录下
        return os.path.join(application_path, "ffmpeg.exe")
    else:
        # 如果是平时用 PyCharm 或终端敲 python 运行，就用你的本地绝对路径
        return r"C:\Users\Yao\.claude\ffmpeg-master-latest-win64-gpl-shared\bin\ffmpeg.exe"


class BiliGPUTranscriber:
    def __init__(self,
                 output_dir: str = "bilibili_works",
                 ffmpeg_path: Optional[str] = None):
        self.output_dir = output_dir
        self.ffmpeg_path = ffmpeg_path

        if not os.path.exists(self.output_dir):
            os.makedirs(self.output_dir)

        # 硬件检测
        self.device = "cuda" if torch.cuda.is_available() else "cpu"
        self.compute_type = "float16" if self.device == "cuda" else "int8"

        print(f"🚀 系统初始化: 使用 {self.device.upper()} 加速引擎")

        # --- 核心修复点：直接使用全局检测好的 model_to_use ---
        self.model = WhisperModel(
            model_to_use,
            device=self.device,
            compute_type=self.compute_type,
            local_files_only=is_local  # 如果是本地，强制不联网
        )

    def download_audio(self, url: str) -> str:
        """从 Bilibili 下载最佳音质的音频"""
        print(f"\n🔄 正在连接 Bilibili，准备扒取音频: {url}")

        def progress_hook(d):
            if d['status'] == 'downloading':
                percent = d.get('_percent_str', '0%')
                speed = d.get('_speed_str', '0KiB/s')
                print(f"\r📥 [下载进度] {percent} | 当前网速: {speed}", end='', flush=True)
            elif d['status'] == 'finished':
                print("\n✅ 音频文件落地成功，准备进入下一环节！")

        ydl_opts = {
            'format': 'bestaudio/best',
            'restrictfilenames': True,
            'outtmpl': os.path.join(self.output_dir, '%(title)s.%(ext)s'),
            'quiet': True,
            'nocheckcertificate': True,  # 绕过 SSL 检查，防止证书报错
            'source_address': '0.0.0.0',  # 强制 IPv4，防止网络断流
            'progress_hooks': [progress_hook],
            'cookiefile': 'cookies.txt' if os.path.exists('cookies.txt') else None,
        }

        if self.ffmpeg_path and os.path.exists(self.ffmpeg_path):
            ydl_opts['ffmpeg_location'] = self.ffmpeg_path

        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
            if 'requested_downloads' in info:
                return info['requested_downloads'][0]['filepath']
            else:
                return ydl.prepare_filename(info)

    def transcribe(self, audio_path: str) -> tuple:
        """使用 GPU 运行 Whisper 模型进行语音转文字"""
        print(f"\n🎧 唤醒 GPU 模型... AI 戴上耳机开始听写...")
        # 初始提示词：引导模型输出正确的中文标点符号
        prompt_text = "这是一段发音清晰、带有标点符号的普通话文本，包含逗号、句号、问号和叹号。"

        # 启用 VAD (人声活动检测) 过滤静音片段，防止模型产生“幻觉”
        segments, info = self.model.transcribe(
            audio_path,
            beam_size=5,
            language="zh",
            vad_filter=True,
            vad_parameters=dict(min_silence_duration_ms=1000),
            initial_prompt=prompt_text
        )

        print(f"🗣️ 识别到语言: {info.language}，音频总时长: {info.duration:.2f}秒")
        print("-" * 50)

        timestamp_text = []
        clean_text = []

        for segment in segments:
            line = f"[{segment.start:>7.2f}s -> {segment.end:>7.2f}s] {segment.text}"
            print(line, flush=True)
            timestamp_text.append(line)
            clean_text.append(segment.text.strip())

        print("-" * 50)
        return "".join(clean_text), "\n".join(timestamp_text)

    def summarize_text_with_api(self, source_text: str, api_key: str, base_url: str, model_name: str) -> str:
        """通用的 AI 总结函数，使用深度提示词模板"""
        if not api_key or not base_url:
            return "⚠️ 未配置 API_KEY，跳过总结。"

        # 1. 准备数据（这里的 source_text 就是你要总结的内容）
        summary_text = source_text[:15000]  # 截取前 1.5 万字

        # 2. 定义【深度内容提炼专家版】提示词模板
        system_prompt = """
        你是一位拥有 10 年经验的资深知识博主与内容架构师，擅长从长篇视频转录稿中提取深层逻辑。
        字数要求：总结内容不得少于 800 字，力求还原视频的 90% 核心信息。
        结构化输出：必须包含“一句话核心摘要”、“详细思维大纲”以及“实操建议”。
        """

        user_prompt = f"""
        请深度解析以下视频转录内容，并按要求输出总结：

        ---
        [转录文本开始]
        {summary_text}
        [转录文本结束]
        ---

        # 输出格式要求：
        ## 📌 一句话省流
        ## 🔍 核心内容深度拆解 (严禁只写标题，每个模块必须详细展开描述)
        ## 💡 关键结论与实操建议
        ## 🌟 视频金句提取 (摘录 3 条原句)
        """

        # 3. 发送请求
        try:
            from openai import OpenAI
            client = OpenAI(api_key=api_key, base_url=base_url)

            response = client.chat.completions.create(
                model=model_name,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                temperature=0.4,  # 降低随机性，保证逻辑严谨
                max_tokens=3000  # 给够输出空间，防止总结被截断
            )
            return response.choices[0].message.content.strip()
        except Exception as e:
            return f"❌ 总结失败: {e}"

    def run_stream(self, url: str, api_key: str, base_url: str,model_name: str):
        """流式生成器：协调下载、识别、总结三个步骤，并向前端推送实时状态"""
        try:
            # ... 前面的代码保持不变 ...


            yield "", "", "⏳ **步骤 1/3:** 正在连接服务器，扒取高清音频中，请稍候..."
            audio_file = self.download_audio(url)
            base_name = os.path.splitext(audio_file)[0]

            yield "", "", f"✅ **音频获取成功！**\n⏳ **步骤 2/3:** 正在唤醒 GPU 开启 Whisper 语音识别引擎..."
            clean_txt, time_txt = self.transcribe(audio_file)

            clean_file = base_name + "_阅读版.txt"
            time_file = base_name + "_字幕版.txt"
            with open(clean_file, "w", encoding="utf-8") as f:
                f.write(clean_txt)
            with open(time_file, "w", encoding="utf-8") as f:
                f.write(time_txt)

            yield clean_txt, "", f"✅ **语音识别完美结束！**\n⏳ **步骤 3/3:** 正在连接云端大模型进行深度内容总结..."

            # --- 核心修改点：把 model_name 传给总结函数 ---
            summary_result = self.summarize_text_with_api(clean_txt, api_key, base_url, model_name)

            if "⚠️" not in summary_result and "❌" not in summary_result:
                summary_file = base_name + "_内容总结.txt"
                with open(summary_file, "w", encoding="utf-8") as f:
                    f.write(summary_result)

            final_status = f"🎉 **大功告成！** 所有流程执行完毕。文件已妥善保存在 `{self.output_dir}` 文件夹中。"
            yield clean_txt, summary_result, final_status

        except Exception as e:
            yield "", "", f"❌ **发生致命错误:** {e}"


# ==========================================
# 🌐 现代化网页 UI 构建区 (Gradio)
# ==========================================

# ⚠️ 注意：发布前已将个人绝对路径脱敏。
# 开发者/用户请在此处填写你的本地 FFmpeg bin 目录绝对路径。
# 如果你已经将 FFmpeg 加入了系统环境变量，这里可以保留为空字符串 ""。
CUSTOM_FFMPEG = ""
CUSTOM_FFMPEG = get_ffmpeg_path()
agent = BiliGPUTranscriber(ffmpeg_path=CUSTOM_FFMPEG)


def process_video_ui(url, api_key, base_url, model_name): # 新增 model_name
    if not url.strip():
        yield "等待输入...", "等待输入...", "⚠️ 错误：请输入视频链接！"
        return
    # 记得在 agent.run_stream 里也要对应增加这个参数传递
    for clean_txt, summary, status in agent.run_stream(url, api_key, base_url, model_name):
        yield clean_txt, summary, status


custom_css = """
footer {display: none !important;}
.gradio-container {border-radius: 15px;}
textarea {font-family: 'Microsoft YaHei', sans-serif !important; line-height: 1.6 !important;}
"""

theme = gr.themes.Soft(primary_hue="indigo", neutral_hue="slate", spacing_size="lg", radius_size="lg")

with gr.Blocks(title="BiliBili AI 智能解析舱", theme=theme, css=custom_css) as demo:
    gr.HTML("""
        <div style="text-align: center; max-width: 800px; margin: 0 auto; padding: 20px 0;">
            <h1 style="font-weight: 800; font-size: 2.5rem; color: #4338ca; margin-bottom: 10px;">🌌 BiliBili AI 智能解析舱</h1>
            <p style="color: #64748b; font-size: 1.1rem;">极速提取视频语音 · GPU精准转录 · 大模型智能总结</p>
        </div>
    """)

    with gr.Row():
        with gr.Column(scale=5):
            url_input = gr.Textbox(
                label="📺 视频链接",
                placeholder="在此粘贴 Bilibili 视频链接 (例如: https://www.bilibili.com/video/BV...)",
                show_label=True
            )
        with gr.Column(scale=2):
            # 提供默认的接口格式，隐藏了真实的 API KEY
            base_url_input = gr.Textbox(label="🌐 接口地址", value="https://api.openai.com/v1")
            api_key_input = gr.Textbox(label="🔑 访问密钥", type="password", placeholder="sk-...")
            # 新增模型名称输入框
            model_name_input = gr.Textbox(label="🤖 模型名称", value="gpt-3.5-turbo", placeholder="例如: deepseek-chat")

    submit_btn = gr.Button("✨ 启动智能流水线 ✨", variant="primary", size="lg")
    status_output = gr.Markdown("🟢 **系统空闲中，等待任务指令...**")

    gr.HTML("<hr style='border: 1px solid #e2e8f0; margin: 20px 0;'>")

    with gr.Tabs():
        with gr.TabItem("🧠 AI 核心总结"):
            summary_output = gr.Textbox(label="云端大模型深度提炼", lines=12, interactive=False, show_copy_button=True)
        with gr.TabItem("📝 完整转录文本"):
            transcribe_output = gr.Textbox(label="Whisper 纯净阅读文本", lines=12, interactive=False,
                                           show_copy_button=True)

    submit_btn.click(
        fn=process_video_ui,
        inputs=[url_input, api_key_input, base_url_input, model_name_input],  # 增加输入
        outputs=[transcribe_output, summary_output, status_output]
    )

if __name__ == "__main__":
    print("准备启动现代化本地网页 UI...")
    demo.launch(inbrowser=True)