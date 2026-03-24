from pymilvus import MilvusClient, db
from pymilvus import model


# 此篇幅为database相关操作
client = MilvusClient("http://localhost:19530")

# 先批量删除所有数据库
data_base_list = client.list_databases()
for data_base in data_base_list:
    print("当前的dabase:", data_base)
    if "default" == data_base:
        continue
    client.drop_database(db_name=data_base)



# 数据库的crud操作

data_base_name_first = "first_milvus_data_base"
data_base_name_second = "my_second_milvus_data_base"


# 创建数据库
client.create_database(db_name= data_base_name_first)

# 查看数据库
data_base_list = client.list_databases()
print("当前的数据库列表:", data_base_list)

# 创建第二个数据库
client.create_database(
    db_name = data_base_name_second,
    properties={"database.max.collections":6}
)

data_base_list = client.list_databases()
print("当前的数据库列表:", data_base_list)

# 查看数据库详情
second_detail = client.describe_database(data_base_name_second)
print("当前第二个数据库详情:", second_detail)

# 修改数据库相关内容
client.alter_database_properties(
    db_name=data_base_name_second,
    properties = {"database.max.collections":10}
    )

second_detail = client.describe_database(data_base_name_second)
print("当前第二个数据库详情(修改后的):", second_detail)

# 删除数据库
client.drop_database(db_name= data_base_name_first)

# 再次查看 因为删除了所以报错 data_base_not_found
#first_detail = client.describe_database(db_name= data_base_name_first)

data_base_list = client.list_databases()
print("数据库列表", data_base_list)

# 指定client
client.use_database(data_base_name_second)


