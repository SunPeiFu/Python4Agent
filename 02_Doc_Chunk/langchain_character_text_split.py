
from langchain_community.document_loaders import TextLoader
from langchain_text_splitters import CharacterTextSplitter


# 读取文档(TextLoader简单读取模式 不智能 demo用)
loader = TextLoader("90-文档-Data/山西文旅/云冈石窟.txt")
docs = loader.load()

# 切分文档
characterTextSpliter = CharacterTextSplitter(
    chunk_size = 100, # chunk_size 100 是按照多少个字符切分(如果是中文)
    chunk_overlap = 10 # chunk_overlap 10 对应中文是多少
)

# enumerate是for中 同时拿到index和具体element的方法 , 设置start指定index开始位置
split_documents = characterTextSpliter.split_documents(docs)
for i,split_doc in enumerate(split_documents, start=1):
    print("当前的index:",i)
    print("切分后的metadata:", split_doc.metadata)
    print("切分后的pagecontext:", split_doc.page_content)


# 