# langchaindemo
# langchain中的提示词有两种
# PromptTemplate 普通文本式
# ChatPromptTemplate 对话文本 式
from os import name

from langchain_core.prompts import PromptTemplate, ChatPromptTemplate

prompt = PromptTemplate.from_template("你是一个起名大师 帮我起一个{county}特色的男孩名字")
text = prompt.format(county="中国")
print(text)

chatprompt = ChatPromptTemplate.from_messages(
    [
        ("system", "你是一个股神 名字叫{name}"),
        ("human", "你好{name} 请问你对黄金的价格最近怎么看"),
        ("ai", "非常好 {desc}")
    ]
)
chatPrompt = chatprompt.format(name="陈百万", desc="你必定是大富翁")
print(chatPrompt)
