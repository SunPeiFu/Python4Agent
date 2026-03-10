
from langchain_community.document_loaders import WebBaseLoader # pip install langchain-community
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_core.vectorstores import InMemoryVectorStore
from langchain_core.prompts import ChatPromptTemplate
from dashscope import Generation
import dashscope

# 加载web资源 形成文档
loader = WebBaseLoader(web_path = "https://zh.wikipedia.org/wiki/%E9%BB%91%E7%A5%9E%E8%AF%9D%EF%BC%9A%E6%82%9F%E7%A9%BA")
document = loader.load()

# chunk 文档切分
text_spliter = RecursiveCharacterTextSplitter(chunk_size = 1000, chunk_overlap = 200)
all_documents = text_spliter.split_documents(document)

# 设置嵌入模型embedding 
# qa -> HuggingFaceEmbeddings的返回值是什么 此处调用 py中的__init__ 不返回任何实例 不像java return 
# 完整的流程是
 # 创建对象 调用 __new__ 方法 先创建HuggingFaceEmbeddings对象 即执行 __new__ 方法 ()
 # 初始化对象 调用 __int__ 执行HuggingFaceEmbeddings中的__int__方法
 # 把对象实例指向 -> embeddings
#  HuggingFaceEmbeddings(BaseModel, Embeddings)中后面括号两个 代表实现两个接口
embeddings = HuggingFaceEmbeddings(
    model_name = "BAAI/bge-small-zh-v1.5", 
    model_kwargs={'device': 'cpu'}, # qa ->  model_kwargs此处指代什么 一个可变参数的字典
    encode_kwargs={'normalize_embeddings': True}
    )

# 写入向量库 
# qa -> 此处为什么能传入embeddings 因为HuggingFaceEmbeddings实现了Embeddings接口 __init__ 接收Embeddings接口不关心实现
# qa -> ABC又是什么 Abstrac base class 抽象基类 理解成接口
vector_store = InMemoryVectorStore(embeddings)
#vector_store.aadd_documents(all_documents) Q&A a代表async 所以有些方法a开头的 就是异步意思
vector_store.add_documents(all_documents)

# 构建查询
question = "黑神话悟空有哪些章节"
retrireved_docs = vector_store.similarity_search(query = question, k = 10)
# qa ->  此处的retrireved_docs为什么可以doc.出page_context 因为page_context是返回Docment的属性
docs_content = "\n\n".join(doc.page_content for doc in retrireved_docs)

# 构建prompt 
templte  = """
基于上下文,回答提问信息 如果上下文中没有信息 请明确说: "未检索到相关信息"
按照如下格式输出
上下文:{context}
问题:{question}
回答:
"""
#prompt = ChatPromptTemplate.from_template(template = templte, question = question, context = docs_content)
prompt = ChatPromptTemplate.from_template(templte)
# qa ->  format方法中的 **kwargs 代表什么 **kwargs代表各边参数 可以是任意
final_prompt = prompt.format(
    question=question,
    context=docs_content
)

#prompt.format(question = question, context = docs_content)

# 构建llm
api_key = "sk-ceadca0a001f40c6bc1fc0d5f388366e"
model = "qwen-turbo"

dashscope.api_key = api_key



response = Generation.call(
    model=model,
    prompt=final_prompt
)

print("llm的返回结果是:", response.output.text)

# 执行获取结果