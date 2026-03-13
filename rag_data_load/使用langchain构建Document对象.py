from ast import List
from langchain_core.documents import Document

# 构建两个Document

document1 = Document(
    page_content="Hello, world!",
    metadata={"source":"this is source"}
),
document2 = Document(
    page_content="Hello, world!",
    metadata={"source": "https://example.com"}
)

documents = [document1, document2]
print("documents的内容是:", documents)