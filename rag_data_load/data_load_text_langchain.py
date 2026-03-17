import os
import json
from langchain_community.document_loaders import DirectoryLoader, TextLoader

current_file_path = os.path.dirname(__file__)
print("当前脚本执行位置:", current_file_path)

# 替换空串
current_file_path = current_file_path.replace("rag_data_load","")
data_folder_path = os.path.join(current_file_path, "90-文档-Data")
print("data_folder_path的路径是:",data_folder_path)

text_loader = DirectoryLoader(path = data_folder_path)
documents = text_loader.load()
print(f"当前文件下{data_folder_path} 共有{len(documents)}个文件")

current_file_path = current_file_path.replace("rag_data_load","")
print("替换后的文件路径:", current_file_path)

# 基于相对路径构建完整的文档路径
txt_file_path = os.path.join(current_file_path, "90-文档-Data/黑悟空/黑悟空wiki.txt")

# 使用langchian
text_loader = TextLoader(txt_file_path)
documents = text_loader.load()

if documents:
    first_document = documents[0]
    # 转成json输出
    dict = {
        "page_content":first_document.page_content,
        "metadata":first_document.metadata
    } 
    json_str = json.dumps(dict,ensure_ascii=False, indent =2)
    print("序列化后的结果是:", json_str)
    #print("字典内容:",dict)
    

#print("doc的具体内容:", documents)
# langchain中的Docment结构 :
# page_content -> 文件具体内容
# metadata -> 源数据信息

# 加载某个文件夹下

