# langchaindemo
# langchain中的提示词有两种
# PromptTemplate 普通文本式
# ChatPromptTemplate 对话文本 式
from os import name

from langchain_core.messages import SystemMessage, HumanMessage, AIMessage
from langchain_core.prompts import PromptTemplate, ChatPromptTemplate
from sqlalchemy.sql.operators import contains

# 基于promptTemplate方式
prompt = PromptTemplate.from_template("你是一个起名大师 帮我起一个{county}特色的男孩名字")
text = prompt.format(county="中国")
print(text)

# 基于chat模式的
chatprompt = ChatPromptTemplate.from_messages(
    # 此处注意 使用的是[] 里面是()括号 而不是{}
    [
        ("system", "你是一个股神 名字叫{name}"),
        ("human", "你好{name} 请问你对黄金的价格最近怎么看"),
        ("ai", "非常好 {desc}")
    ]
)
chatPrompt = chatprompt.format(name="陈百万", desc="你必定是大富翁")
print(chatPrompt)

# 定义几种常见的消息体 系统消息 人类 AI消息 并转成数组的形式

sysMessage = SystemMessage(
    content="你是一个起名大师"
)

humanMessage = HumanMessage(
    content="这是人类的消息"
)

aiMessage = AIMessage(
    content="这是一个ai的消息"
)

# 组合到一起 直接用[]
resultList = [sysMessage, humanMessage, aiMessage]

# 提取对象中的公共属性 输出成数组
contents = [msg.content for msg in resultList]
print(contents)

# 拼接成一个字符串
content_str = ",".join(msg.content for msg in resultList)
print(content_str)

# 稳妥写法 防止有些对象中没有content
containsDefaultValueList = [msg.content for msg in resultList if getattr(msg, "content", None)]
#print("包含default的方式数组:"+ containsDefaultValueList) # 此处怎么写报错 python中只能是 str+str 或者 list+list 不能str+list
print("包含default的方式数组:",containsDefaultValueList) # 此处怎么写报错 python中只能是 str+str 或者 list+list 不能str+list





#print(resultList)


