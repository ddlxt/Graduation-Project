##1、到阿里modelscope https://modelscope.cn/ 查找到对应的模型
##2、使用下面的SDK方式下载，速度快
from modelscope import snapshot_download
model_dir = snapshot_download('sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2',cache_dir='./model')

# from modelscope import snapshot_download
# print("===========download start==========")
# model_dir = snapshot_download('Qwen/Qwen3-8B',cache_dir='./model')
# print("===========download finished==========")