from os import sync
from pymilvus import MilvusClient, DataType
import random

# 普通的索引(全表扫描)

# 1. 设置 Milvus 客户端
client = MilvusClient(uri="http://localhost:19530")
COLLECTION_NAME = "flat_index_demo"

# 如果集合已存在，则删除
if client.has_collection(COLLECTION_NAME):
    client.drop_collection(COLLECTION_NAME)

# 2. 创建 schema
schema = MilvusClient.create_schema(auto_id=False, enable_dynamic_field=True)
schema.add_field(field_name="id", datatype=DataType.INT64, is_primary=True)
schema.add_field(field_name="vector", datatype=DataType.FLOAT_VECTOR, dim=128)

# 3 创建集合
client.create_collection(collection_name=COLLECTION_NAME, schema= schema)

# 4 插入随机向量
num_vectors = 1000
vectors = [[random.random() for _ in range(128)] for _ in range (num_vectors)]
ids = list(range(num_vectors))
entites = [{"id":ids[i], "vector":vectors[i]} for i in range(num_vectors)]

# 5 插入实体
client.insert(collection_name=COLLECTION_NAME, data = entites)

# 6 刷新
client.flush(collection_name = COLLECTION_NAME)

# 7 创建索引
INDEX_NAME = "vector_index"
index = client.prepare_index_params()
index.add_index(
    index_name = INDEX_NAME,
    field_name= "vector",
    index_type="FLAT",
    metric_type = "L2",
    params = {}
)
client.create_index(
    collection_name = COLLECTION_NAME,
    index_params = index,
    sync = True
)

# 验证索引
# 索引列表
index_list = client.list_indexes(collection_name= COLLECTION_NAME)
print("当前集合索引列表:", index_list)

index_detail = client.describe_index(collection_name= COLLECTION_NAME, index_name= INDEX_NAME)
print("当前索引详情:", index_detail)

# 加载集合
client.load_collection(collection_name= COLLECTION_NAME)

# 执行检索
search_vectors = [[random.random() for _ in range(128)]]
print("search_vectors:", )
search_result = client.search(
    collection_name=COLLECTION_NAME,
    data = search_vectors,
    # 此处怎么写会报错 源码search_params定义是字典 需要传字典
    #search_params = ["id"],
    limit=5
)
print("search_result:", search_result)
# 结果是
"""
data: [[{'id': 196, 'distance': 14.469127655029297, 'entity': {}}, {'id': 742, 'distance': 14.974742889404297, 'entity': {}}, {'id': 217, 'distance': 15.319454193115234, 'entity': {}}, {'id': 963, 'distance': 15.812398910522461, 'entity': {}}, {'id': 645, 'distance': 15.859505653381348, 'entity': {}}]]
每个result_detail: {'id': 196, 'distance': 14.469127655029297, 'entity': {}}
"""

for search_result_list in search_result:
    # 每个search_result_list里面的元素是字典 还需要遍历
    for result_detail in search_result_list:
        print("每个result_detail:", result_detail)
        # {'id': 963, 'distance': 15.812398910522461, 'entity': {}}
        detail_id = result_detail.get("id", "empty")
        detail_distance = result_detail.get("distance", "empty")
        print(f"每个detail_id:{detail_id}, detail_distance是:{detail_distance}")

        


        
        
        
            

            

