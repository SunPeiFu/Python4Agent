from langchain_community.document_loaders import WebBaseLoader # pip install langchain-community
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_core.vectorstores import InMemoryVectorStore
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.runnables import RunnablePassthrough
from langchain_core.output_parsers import StrOutputParser
from langchain_community.chat_models import ChatTongyi



# 1 加载web资源 形成文档
print("=========开始加载网页=========")
#loader = WebBaseLoader(web_path = "https://zh.wikipedia.org/wiki/%E9%BB%91%E7%A5%9E%E8%AF%9D%EF%BC%9A%E6%82%9F%E7%A9%BA")
loader = WebBaseLoader(web_path = "https://www.google.com/search?q=%E5%87%A0%E7%82%B9%E4%BA%86&oq=%E5%87%A0%E7%82%B9%E4%BA%86&gs_lcrp=EgZjaHJvbWUyBggAEEUYOTIHCAEQABiABDIHCAIQABiABDIHCAMQABiABDIHCAQQABiABDIHCAUQABiABDIHCAYQABiABDIHCAcQABiABDIHCAgQABiABDIHCAkQABiABNIBCTE3NjBqMGoxNagCCLACAfEFoOrhLVQxVaLxBaDq4S1UMVWi&sourceid=chrome&ie=UTF-8")

document = loader.load()
print("=========加载网页完成=========")

# 打印输出看下document具体结构
print("webBaseLoader加载的document类型是:", type(document))
print("每一个d中的meta信息:",document[0].metadata)
print("每一个d中的page_content信息:",document[0].page_content)
    

# 2 chunk 文档拆分
text_spliter = RecursiveCharacterTextSplitter(chunk_size = 300, chunk_overlap = 100)
all_documents = text_spliter.split_documents(document)

# 3 设置embedding模型
embeddings = HuggingFaceEmbeddings(
    model_name = "BAAI/bge-small-zh-v1.5", 
    model_kwargs={'device': 'cpu'}, # qa ->  model_kwargs此处指代什么 一个可变参数的字典 注意它会转成字典
    encode_kwargs={'normalize_embeddings': True}
    )

# 4 文档进行embedding 写入向量库
vector_store = InMemoryVectorStore(embeddings)
vector_store.add_documents(all_documents)

# 5 创建检索器 qa 此处as_retriever作用&意义是什么
# 返回一个检索器接口VectorStoreRetriever
retriever = vector_store.as_retriever(search_kwargs = {"k":6})

question = "黑神话悟空有哪些章节"

# 打印看下检索的内容
docs = retriever.invoke(question)
# for d in docs :
#     print("retriever invoke返回的内容是 -> ",d.page_content[:200])
# 6 创建提示词模板
templte ="""
    基于以下上下文，回答问题。如果上下文中没有相关信息，
请说"我无法从提供的上下文中找到相关信息"。
上下文: {context}
问题: {question}
回答:
    """


# 设置语言模型


# 5 构建quesiton 执行查询召回

# 6 构建question查询限量数据库
templte  = """
基于上下文,回答提问信息 如果上下文中没有信息 请明确说: "未检索到相关信息"
按照如下格式输出
上下文:{context}
问题:{question}
回答:
"""
prompt = ChatPromptTemplate.from_template(templte)


# 7 设置语言模型
api_key = "sk-ceadca0a001f40c6bc1fc0d5f388366e"
model = "qwen-turbo"
llm = ChatTongyi(
    model=model,
    dashscope_api_key = api_key
)

# 单独定义封装一个方法
def format_docs(docs):
    return "\n\n".join(doc.page_content for doc in docs)

# 链式调用执行
chain = (
    {
        "context": retriever | format_docs,    
        "question":RunnablePassthrough() # 把question保留原样不动的传递下去
    }
        | prompt
        | llm
        | StrOutputParser() 
    
)

response = chain.invoke(question) # 同步，可以换成异步执行
print("最终执行的结果:", response)
