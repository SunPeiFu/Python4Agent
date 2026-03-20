from pymilvus import MilvusClient
from pymilvus import model

# 创建一个db
client = MilvusClient("http://localhost:19530")

# 创建一个集合
if client.has_collection(collection_name = "milvus_demo"):
    client.drop_collection(collection_name = "milvus_demo")
client.create_collection(collection_name = "milvus_demo", dimension= 768)

# 创建一个默认模型 写入一段文本用于检索
default_embedding = model.DefaultEmbeddingFunction()

# 检索文本
docs = [
    "Artificial intelligence was founded as an academic discipline in 1956.",
    "Alan Turing was the first person to conduct substantial research in AI.",
    "Born in Maida Vale, London, Turing was raised in southern England.",
]

# 文本进行embedding
vectors = default_embedding.encode_documents(docs)
print("dimission", default_embedding.dim)

# 定义数据

data = [
    {"id": i, "vector": vectors[i], "text": docs[i], "subject": "history"}
    for i in range(len(vectors))
]

print("Data has", len(data), "entities, each with fields: ", data[0].keys())
print("Vector dim:", len(data[0]["vector"]))
