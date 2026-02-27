import os
from openai import OpenAI

# 从环境变量读取配置
deepSeekApiKey = os.getenv("DEEP_SEEK_API_KEY")
deepSeekApiKey = "sk-ceadca0a001f40c6bc1fc0d5f388366e"
if not deepSeekApiKey: 
    raise ValueError("请设置apikey")

# 初始化openAi客户端
client = OpenAI(
    api_key = deepSeekApiKey,
    base_url= "https://dashscope.aliyuncs.com/compatible-mode/v1"
)

tools = [
    {
        "type": "function",
        "function": {
            "name": "get_weather",
            "description": "Get weather of an location, the user should supply a location first",
            "parameters": {
                "type": "object",
                "properties": {
                    "location": {
                        "type": "string",
                        "description": "The city and state, e.g. San Francisco, CA",
                    }
                },
                "required": ["location"]
            },
        }
    },
]

# 定义sendMessage方法
def send_message(messages) :
    
    response = client.chat.completions.create(
        model="qwen-turbo",    
        messages=messages,
        tools=tools
    )
    return response.choices[0].message

# 定义一个message结构体 并且调用send_message方法
messages = [{"role":"user","content":"How is Weather in BeiJing"}]
message = send_message(messages)

# 打印输出结果
print(message)
print(f"user>\t {messages[0]['content']}")

 # messages中已经封装了tools 所以此处返回的是传入的工具
tool = message.tool_calls[0]
messages.append(message)


# 模拟 searchWeb返回
messages.append({"role":"tool","too_call_id":tool.id,"content":"66°"})
message = send_message(messages)
print(message)


# 疑问点梳理总结归纳
# 1 重载方法很多, 如何确认调用的是第几个 -> py中没有重载的这一说
# 2 返回值怎么看 为什么是response -> 直接点进去看方法最终的声明返回
# 3 字符串tools定义的位置 有影响吗 -> 在create之前都可以
# 4 client.chat.completions.create可以自动补全出来response -> 不可以
# 5 tool.id 为啥能.出来id -> 直接点进去看方法最终的声明返回

# 精华汇总 -> 模型只能负责"想", 程序负责最终"执行"  模型永远都是嘴 程序是手
# messages 相当于"记忆" 模型不会记得前文的内容(之前生成输出过什么) 通过自己append把上下文串起来 模型就有所谓的"记忆"了,因为token有效信息多
# tools 相当于 能力声明 告诉模型你有这个能力了 具体用不用 取决于模型自己 并且强制
# tool_call 是请求
# append 是状态推进 