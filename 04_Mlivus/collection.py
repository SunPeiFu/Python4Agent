from pymilvus import MilvusClient

# miluvs中collection相关操作

client = MilvusClient(uri="http://localhost:19530")

database_name = "crud_collection_database"

data_base_list = client.list_databases()
for data_base in data_base_list:
    if data_base == database_name:
        # 如database中有集合 不能直接删除 需要先删除集合
        client.use_database(db_name = data_base)
        collection_list = client.list_collections()
        for collection in collection_list:
            client.drop_collection(collection_name=collection)

#client.drop_database(db_name = database_name)


# 更精简的写法是 if xxx in
if database_name in client.list_databases():
    client.drop_database(db_name = database_name)


# 先创建一个db
client.create_database(db_name = database_name)
client.use_database(db_name = database_name)

# 集合的crud操作

# 创建集合
my_first_collection_name = "my_first_collection_name"
client.create_collection(
    collection_name=my_first_collection_name,
    dimension = 6
)

# 集合详情
collection_detail = client.describe_collection(collection_name=my_first_collection_name)
print("集合详情内容是:", collection_detail)

# 修改集合
client.alter_collection_properties(
    collection_name=my_first_collection_name ,
    properties = {"timeout":10}
)
print("修改后集合详情内容是:", collection_detail)

# 列出所有collection
collection_list = client.list_collections()
print("集合列表:", collection_list)

rename_collection_name = "new_rename_my_first_collection_name"
client.rename_collection(
    old_name = my_first_collection_name,
    new_name = rename_collection_name
)
collection_detail = client.describe_collection(collection_name= rename_collection_name)
print("重命名后的集合名称:", collection_detail)

# 集合加载释放相关操作 为什么加载释放 和mysql类比
before_load_status = client.get_load_state(collection_name=rename_collection_name)
print("before_load_status:",before_load_status)

client.load_collection(collection_name=rename_collection_name)

after_load_status =client.get_load_state(collection_name=rename_collection_name)
print("after_load_status:",after_load_status)

# parttion相关操作

# 管理alias

