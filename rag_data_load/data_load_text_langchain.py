import os
import json
from langchain_community.document_loaders import TextLoader
current_file_path = os.path.dirname(__file__)
print("当前脚本执行位置:", current_file_path)

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
# source -> 文件来源路径
# page_content -> 文件具体内容
# [Document(metadata={'source': '/Users/mac/PycharmProjects/Python4Agent/90-文档-Data/黑悟空/黑悟空wiki.txt'}, 
# page_content='黑神话：悟空\n\n类型\t动作角色扮演[1]\n平台\}]

