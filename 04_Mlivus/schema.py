from pymilvus import DataType, MilvusClient

# schema相关
client = MilvusClient(uri="http://localhost:19530")

# 创建db
create_scheme_data_base = "create_scheme_data_base"
if create_scheme_data_base not in client.list_databases():
    client.create_database(db_name = create_scheme_data_base)

# 创建空的scheme 往里添加字段
default_scheme = client.create_schema()

# 设置INT主键
default_scheme.add_field(
    field_name = "id", 
    datatype= DataType.INT64,
    is_primary = True, # 设置主键
    auto_id = False # 不自增
    )

# default_scheme.add_field(
#     field_name = "doc_id", 
#     datatype= DataType.VARCHAR,
#     is_primary = True, # 设置主键
#     auto_id = True # 不自增
#     )

# 添加向量字段 - 浮点向量
default_scheme.add_field(
    field_name = "text_vector", 
    datatype= DataType.FLOAT_VECTOR,
    dim = 768 # 此处的dim属性在哪里看到的
    )

# 添加向量字段 - 二进制向量
default_scheme.add_field(
    field_name = "image_vector", 
    datatype= DataType.BINARY_VECTOR,
    dim = 256 # 维度必须是2的倍数 为什么
    )  
print("✓ 已添加向量字段")

# 设置字符串 varchar 
default_scheme.add_field(
    field_name = "title", 
    datatype= DataType.VARCHAR,
    max_length = 100,
    is_nullable = True, #可以为空
    default_value = "untitled"
    ) 

# 设置字符串string
default_scheme.add_field(
    field_name = "title_desc", 
    datatype= DataType.VARCHAR,
    max_length = 100,
    is_nullable = True, #可以为空
    default_value = "untitled"
    ) 

# 设置int
default_scheme.add_field(
    field_name = "num", 
    datatype= DataType.INT64,
    is_primary = False, # 设置主键
    auto_id = False # 不自增
    )

# 设置boolean
default_scheme.add_field(
    field_name = "is_avaliable", 
    datatype= DataType.BOOL,
    default_value = False
    )

# 设置json
default_scheme.add_field(
    field_name = "metadata", 
    datatype= DataType.JSON
    )

# 设置数组 可以限制范围
default_scheme.add_field(
    field_name = "tags", 
    datatype= DataType.ARRAY,
    element_type = DataType.VARCHAR,
    max_capacity = 100, # 数组最大容量
    max_length= 200, # 每个元素最大长度
    )

# 设置动态字段  
# default_scheme.add_field(
#     field_name = "dynamic_filed", 
#     datatype= DataType.VARCHAR,
#     is_dynamic = True, # 动态字段是干啥的
#     max_length=500
#     )  

# 创建collection
create_collection_schema_name = "create_collection_schema_name"
client.create_collection(
    collection_name = create_collection_schema_name,
    schema = default_scheme
)

create_collection_schema_detail = client.describe_collection(collection_name = create_collection_schema_name)
print("schema内容:", create_collection_schema_detail)
# 创建各种schema

# 