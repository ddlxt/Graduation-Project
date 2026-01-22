# llm_client.py
import os
import openai

# ---------------------------- # 1. 配置 OpenAI API（可改成本地 LLM 方案） ----------------------------

os.environ["OPENAI_API_KEY"] = "sk-90a23bc3f3084156ae41da88bffd3578"
os.environ["OPENAI_BASE_URL"] = "https://dashscope.aliyuncs.com/compatible-mode/v1"
openai.api_request_timeout = 60

# ---------------------------- # 2. 生成回答函数 # ----------------------------

def call_llm( user_question, context_texts=None, use_knowledge_only=False, system_prompt=None, temperature=0.2, max_tokens=500 ):
    messages = []
    # 1. 系统角色提示：提供一个行为指导，不能包含资料内容
    if system_prompt:
        messages.append({ "role": "system", "content": system_prompt })

    # 2. 用户问题 + 参考资料，用户问题会结合相关知识文本
    user_content = user_question # 默认用户问题为内容
    if context_texts:
        context_str = "\n".join(context_texts)
        user_content = f"以下是与问题最相关的资料内容，请根据资料回答：\n{context_str}\n\n{user_question}"

    # 3. 用户问题内容
    messages.append({ "role": "user", "content": user_content })
    try:
        resp = openai.chat.completions.create( model="deepseek-v3.2",
                                               messages=messages,
                                               temperature=temperature,
                                               max_tokens=max_tokens )
        return resp.choices[0].message.content.strip()
    except Exception as e:
        print("[LLM 调用错误]", e)
        return "抱歉，生成回答失败。"