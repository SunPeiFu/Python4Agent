from pymilvus import MilvusClient
from pymilvus import model

# 连接milivus
client = MilvusClient("http://localhost:19530")

collection_name = "milvus_demo"
# 创建集合
if client.has_collection(collection_name = collection_name):
    client.drop_collection(collection_name = collection_name)
client.create_collection(collection_name = collection_name, dimension= 768)

# 使用默认模型
default_embedding = model.DefaultEmbeddingFunction()

# 定义向量化原始信息
docs = [
    "Artificial intelligence was founded as an academic discipline in 1956.",
    "Alan Turing was the first person to conduct substantial research in AI.",
    "Born in Maida Vale, London, Turing was raised in southern England.",
]

# 文本进行embedding
vectors = default_embedding.encode_documents(docs)
print("encode_documents vectors:", vectors)
# TODO SPF 此处还没解决 default_embedding.不出来东西, 为什么可以.dim  dim是什么
#print("dimission", default_embedding.dim) 

# 定义入库数据
# QA此处为什么for循环在代码下面 可以给字典赋值 ->  此处是列表推导公式 {} for i in range(len(vercors))
data = [
    {"id": i, "vector": vectors[i], "text": docs[i], "subject": "history"}
    for i in range(len(vectors))
]

# QA 此处len(data)的长度是3 ,因为docs的数组长度就是3
print("Data has", len(data), "entities, each with fields: ", data[0].keys())
#print("Vector dim:", len(data[0]["vector"]))
# python中获取元素index的语法 enumreate
for i, element in enumerate(data):
    # element 是一个 dict: {"id": ..., "vector": ..., "text": ..., "subject": ...}
    # 为了更快：只输出 text 前 30 个字符和向量前 5 个维度
    print(
        f"[{i}] id={element['id']} text={element['text'][:30]} vec[:5]={element['vector'][:5]}"
    )


# 写入数据
write_result = client.insert(collection_name=collection_name , data = data, timeout=60000)
print("write_result:", write_result) #write_result: {'insert_count': 3, 'ids': [0, 1, 2]}

# search查询
    # 基础向量查询
question = "Who is Alan Turing?"
query_data = default_embedding.encode_queries([question])

# search(向量检索) query(标量检索)
result = client.search(
    collection_name= collection_name,
    data = query_data,
    output_fields=["text","subject"],
    limit = 2,
)
print("search的结果:", result)
"""
[
[{'id': 2, 'distance': 0.5859946012496948, 'entity': {'text': 'Born in Maida Vale, London, Turing was raised in southern England.', 'subject': 'history'}},
 {'id': 1, 'distance': 0.5118255615234375, 'entity': {'text': 'Alan Turing was the first person to conduct substantial research in AI.', 'subject': 'history'}}
 ]
 ]
"""
    # 向量查询&条件过滤


filter_result = client.search(
    collection_name= collection_name,
    data = query_data,
    output_fields=["text","subject"],
    # 增加标量过滤
    filter=["subject == history"], # 注意此处需要增加引号 不加引号会被当做变量or标识符
    limit = 2,
)
print("标量过滤结果 :", filter_result)