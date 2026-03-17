from ast import List
from langchain_core.documents import Document

# 构建两个Document

document1 = Document(
    page_content="Hello, world!",
    metadata={"source":"this is source"}
)
document2 = Document(
    page_content="Hello, world!",
    metadata={"source": "https://example.com"}
)

documents = [document1, document2]
for doc in documents:
    print("doc的内容是:", doc.page_content)
    print("doc的metadata是:", doc.metadata)
    
print("documents的内容是:", documents)