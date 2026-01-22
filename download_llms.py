##1、到阿里modelscope https://modelscope.cn/ 查找到对应的模型
##2、使用下面的SDK方式下载，速度快
from modelscope import snapshot_download
print("===========download start==========")
model_dir = snapshot_download('Qwen/Qwen3-8B',cache_dir='./model')
print("===========download finished==========")

# python -m fastchat.serve.controller --host=0.0.0.0 --port=20000
# python -m fastchat.serve.model_worker  --controller-address http://localhost:20000 --model-path E:/Production-internship/ModelCode/ModelCode/models/ZhipuAI/chatglm3-6b --worker-address http://localhost:40000 --port 40000  --device cuda
# python -m fastchat.serve.openai_api_server  --controller-address http://localhost:20000  --host 0.0.0.0  --port 8000
# {
#     "model": "chatglm3-6b",
#     "messages": [
#         {
#             "role": "user",
#             "content": "翻译成中文: How are you"
#         }
#     ]
# }