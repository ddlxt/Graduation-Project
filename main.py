import os
import base64
import gradio as gr

import vector_store
from vector_store import query_vector_store
from llm_client import call_llm

# -----------------------------
# 读取图片
# -----------------------------
with open("background.jpg", "rb") as f:
    b64_bg = base64.b64encode(f.read()).decode()

with open("icon.png", "rb") as f:
    b64_icon = base64.b64encode(f.read()).decode()

# -----------------------------
# CSS 样式（保持你的原样式）
# -----------------------------
custom_css = f"""
body, .gradio-container {{
    height: 100vh;
    margin: 0;
    padding: 0;
    background-image: url("data:image/jpeg;base64,{b64_bg}");
    background-size: cover;
    background-repeat: no-repeat;
    background-position: center;
    display: flex;
    flex-direction: column;
}}
#header {{
    flex: 0 0 auto;
    display: flex;
    align-items: center;
    padding: 10px;
    background-color: rgba(0, 0, 0, 0.5);
    color: white;
    font-size: 20px;
    font-weight: bold;
    border-bottom: 1px solid rgba(255,255,255,0.2);
}}
#header img {{
    height: 30px;
    width: 30px;
    margin-right: 10px;
    border-radius: 5px;
}}
#default_buttons {{
    flex: 0 0 auto;
    display: flex;
    justify-content: space-around;
    margin: 5px 10px;
}}
.default-btn button {{
    flex: 1;
    margin: 0 5px;
    padding: 8px 10px;
    border-radius: 10px;
    background-color: #2196F3;
    color: white;
    font-size: 16px;
}}
#chatbot {{
    flex: 1 1 auto;
    overflow-y: auto;
    margin: 5px 10px;
    background-color: rgba(255,255,255,0.2);
    border-radius: 10px;
    padding: 10px;
    display: flex;
    flex-direction: column;
    gap: 10px;
}}
.user-msg {{
    align-self: flex-end;
    background-color: #4CAF50;
    color: white;
    padding: 8px 12px;
    border-radius: 15px 15px 0 15px;
    max-width: 70%;
    word-wrap: break-word;
}}
.ai-msg {{
    align-self: flex-start;
    background-color: rgba(255,255,255,0.8);
    color: black;
    padding: 8px 12px;
    border-radius: 15px 15px 15px 0;
    max-width: 70%;
    word-wrap: break-word;
}}
#input_row {{
    flex: 0 0 auto;
    display: flex;
    margin: 5px 10px;
}}
#user_input textarea {{
    flex: 1;
    border-radius: 10px;
    padding: 10px;
    font-size: 16px;
    background-color: rgba(255,255,255,0.8);
    resize: none;
}}
#send_btn button {{
    margin-left: 5px;
    border-radius: 10px;
    padding: 10px 15px;
    background-color: #4CAF50;
    color: white;
    font-size: 16px;
}}
"""

# -----------------------------
# 模式切换映射
# -----------------------------
MODE_DISPLAY = {
    "normal": "自由问答",
    "scenic": "景点介绍",
    "service": "基础服务问答",
    "route": "路线规划"
}


# -----------------------------
# 设置模式，按钮点击不回答
# -----------------------------
def set_mode(mode_name, chat_history):
    if chat_history is None:
        chat_history = []
    mode_text = MODE_DISPLAY.get(mode_name, mode_name)
    chat_history.append(("【系统】", f"当前模式：{mode_text}（请在下方输入你的问题）"))
    return mode_name, chat_history, ""

def parse_routes(raw_text: str):
    routes = []
    lines = [l.strip() for l in raw_text.splitlines() if l.strip()]

    for line in lines:
        if "：" not in line:
            continue

        name, path = line.split("：", 1)
        nodes = [p.strip() for p in path.split("—") if p.strip()]

        routes.append({
            "name": name,
            "nodes": nodes
        })

    return routes
from docx import Document

def show_routes(chat_history):
    if chat_history is None:
        chat_history = []

    route_file = "knowledge/预设路线.docx"
    if not os.path.exists(route_file):
        chat_history.append(("【系统】", "路线文件不存在。"))
        return chat_history

    # 读取 docx 全部文本
    from docx import Document
    doc = Document(route_file)
    raw_lines = [p.text.strip() for p in doc.paragraphs if p.text.strip()]
    if not raw_lines:
        chat_history.append(("【系统】", "路线文件为空。"))
        return chat_history

    # 解析路线
    routes = []
    for line in raw_lines:
        if "：" not in line:
            continue
        name, path = line.split("：", 1)
        nodes = [p.strip() for p in path.split("—") if p.strip()]
        if nodes:
            routes.append((name, nodes))

    # 渲染为 HTML
    reply_text = "【推荐参观路线】\n\n"
    for idx, (name, nodes) in enumerate(routes, 1):
        reply_text += f"路线 {idx}：{name}\n"
        reply_text += " → ".join(nodes) + "\n\n"

    chat_history.append(("【系统】", reply_text))
    return chat_history

# -----------------------------
# 聊天函数：向量检索 + LLM 回答
# -----------------------------
# -----------------------------
# 聊天函数：根据模式区分处理
# -----------------------------
def chat_ai(user_input, chat_history, mode):
    if chat_history is None:
        chat_history = []
    if not user_input.strip():
        return chat_history, ""

    if mode in ["scenic", "service"]:
        context_text = query_vector_store(user_input, mode)

        if not context_text:
            ai_reply = "知识库中未检索到相关内容。"
        else:
            ai_reply = call_llm(
                user_question=user_input,
                context_texts=context_text,
                system_prompt=(
                    "你是景区智能讲解员。"
                    "回答时只能使用【资料内容】中明确出现的信息。"
                    "不要将用户输入中的陈述句当作事实来源。"
                    "如果某个事实仅出现在用户输入而未出现在资料中，请忽略它。"
                ),
                temperature=0.1
            )
    else:
        # 自由问答模式
        ai_reply = call_llm(user_input, context_texts="", use_knowledge_only=False)

    chat_history.append((user_input, ai_reply))
    return chat_history, ""

# -----------------------------
# Gradio UI
# -----------------------------
with gr.Blocks(css=custom_css) as demo:
    mode_state = gr.State("normal")
    chat = gr.Chatbot()

    # 顶部标题 + 图标
    with gr.Row(elem_id="header"):
        gr.HTML(f'<img src="data:image/png;base64,{b64_icon}">')
        gr.HTML("故宫问答助手")

    # 默认交互按钮
    with gr.Row(elem_id="default_buttons"):
        btn1 = gr.Button("景点介绍", elem_classes="default-btn")
        btn2 = gr.Button("基础服务", elem_classes="default-btn")
        btn3 = gr.Button("路线规划", elem_classes="default-btn")

    # 聊天区
    chat = gr.Chatbot(elem_id="chatbot")

    # 输入区
    with gr.Row(elem_id="input_row"):
        user_input = gr.Textbox(placeholder="请输入你的问题...", show_label=False, lines=1, elem_id="user_input")
        send_btn = gr.Button("发送", elem_id="send_btn")

    # 按钮绑定
    btn1.click(set_mode, inputs=[gr.State("scenic"), chat], outputs=[mode_state, chat, user_input])
    btn2.click(set_mode, inputs=[gr.State("service"), chat], outputs=[mode_state, chat, user_input])
    btn3.click(fn=show_routes,inputs=[chat],outputs=[chat])

    # 输入框绑定
    send_btn.click(chat_ai, inputs=[user_input, chat, mode_state], outputs=[chat, user_input])
    user_input.submit(chat_ai, inputs=[user_input, chat, mode_state], outputs=[chat, user_input])

    # 自动滚动 + 聚焦输入框
    demo.load(lambda: None, [], [], _js="""
        const chatContainer = document.getElementById('chatbot');
        const inputBox = document.querySelector('#user_input textarea');
        if (chatContainer && inputBox) {
            const observer = new MutationObserver(() => {
                const children = chatContainer.children;
                for (let i=0; i<children.length; i++) {
                    let child = children[i];
                    if (!child.classList.contains('user-msg') && !child.classList.contains('ai-msg')) {
                        if (i % 2 === 0) child.classList.add('user-msg');
                        else child.classList.add('ai-msg');
                    }
                }
                chatContainer.scrollTop = chatContainer.scrollHeight;
                inputBox.focus();
            });
            observer.observe(chatContainer, { childList: true, subtree: true });
            inputBox.focus();
        }
    """)

demo.launch(server_name="127.0.0.1", server_port=7860)
