from langchain_community.document_loaders import TextLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter

# 加载读取文档
loader = TextLoader("90-文档-Data/山西文旅/云冈石窟.txt")
documents = loader.load()

# 按照换行符 逗号 点句号 空格切分
separators = ["\n\n", ",", "."," "]
# 构造切分器
recursiveCharacterTextSplitter = RecursiveCharacterTextSplitter(
    chunk_size = 100,
    chunk_overlap = 15,
    separators = separators
)

docs = recursiveCharacterTextSplitter.split_documents(documents)

for i, doc in enumerate(docs):
    print("当前index:",i)
    print("当前的pagecontent:",doc.page_content)
    print("-" * 50)