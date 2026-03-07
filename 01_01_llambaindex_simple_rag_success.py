import os

from llama_index.core import VectorStoreIndex, SimpleDirectoryReader, Settings
from llama_index.embeddings.huggingface import HuggingFaceEmbedding
from llama_index.llms.dashscope import DashScope

# ======================
# 1 配置 LLM (阿里 qwen)
# ======================

# 这么玩儿不同 存在各种api兼容问题
# Settings.llm = OpenAILike(
#     model="qwen-max",
#     api_key=os.environ["DASHSCOPE_API_KEY"],
#     api_base="https://dashscope.aliyuncs.com/compatible-mode/v1",
# )

# 这个是Qwen的官方Sdk
Settings.llm = DashScope(
    model_name="qwen-turbo",
    api_key=os.environ["DASHSCOPE_API_KEY"],
)

# ======================
# 2 本地 embedding 模型
# ======================

Settings.embed_model = HuggingFaceEmbedding(
    model_name="BAAI/bge-small-zh"
)

print("LLM的配置是----------->:", Settings.llm)

# ======================
# 3 读取文档
# ======================

documents = SimpleDirectoryReader(
    input_files=["90-文档-Data/黑悟空/设定.txt"]
).load_data()

# ======================
# 4 构建向量索引
# ======================

index = VectorStoreIndex.from_documents(documents)

# ======================
# 5 创建查询引擎
# ======================

query_engine = index.as_query_engine()

# ======================
# 6 提问
# ======================

response = query_engine.query("孙悟空使用什么武器")

print("模型返回的最终答案",response)

