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
print("search_vectors:", search_vectors)
search_result = client.search(
    collection_name=COLLECTION_NAME,
    data = search_vectors,
    search_params = ["id"],
    limit=5
)
print("search_result:", search_result)


        
        
        
            

            

