
import os
import subprocess
from openai import OpenAI
import json
# 使用openai的模型

# 读取当前文件路径
current_dir = "/Users/mac/PycharmProjects/Python4Agent"
api_key = "sk-qFvDkFk22zpWFpVWLGjHtBXwIH1wekq11pZNzLz0e582pl0v"
base_url = "https://api.lotte-library.top/v1"
model_id = "glm-4.7"
# 无限循环的prompt -> 相当于让模型无限循环调用工具 Never output plain text as solution You must call the 'bash'
SYSTEM = f"""
You are a coding agent at {current_dir}.
When given a user task, do not just explain..
Use bash commands only to accomplish the task. 
If the command has already been executed and result is available, do not call the tool again and just
return what function_call response.
"""
# 优化后的prompt
# SYSTEM = f"""
# You are a coding agent at {current_dir}.
# When given a task:
# - Use the bash tool if needed.
# - If the task is already completed, DO NOT call any tool.
# - Return the final result directly.

# Only call the bash tool when necessary.
# """
# 
# 定义工具
TOOLS = [
    {
        # 工具名称&描述&输入约束
        "type":"function", # 原来是function
        "name":"bash",
        "description":"Run a shell command",
        "parameters":{
            "type":"object",
            "properties":{"command":{"type":"string"}},
            "required":["command"]
        },
    }
]

# 定义可执行bash方法
def run_bash(command:str) -> str:
    # 定义危险操作集合
    dangerous = ["rm -rf /", "sudo", "shutdown", "reboot", "> /dev/"]
    if any(d in command for d in dangerous): # 此处的写法 command是字符串 用in 直接有包含的语义
        return "command dangerous return "
    
    try:
        r = subprocess.run(
            command,
            shell=True,
            cwd=current_dir,
            capture_output=True,
            text=True,
            timeout=120    
        )
        
        # 代表执行成功的输出&错误输出?
        stdout = r.stdout
        stderr = r.stderr
        
        out = (stdout + stderr).strip() # 此处是strip是什么意思
        # 三元表达式
        return out[:5000] if out else "resposne it too long"
    except subprocess.TimeoutExpired:
        return "error time out (120s)"
    
    
    
# The core pattern: a while loop that calls tools until the model stops
def agent_loop(user_message: list):
    
    client = OpenAI(
        api_key=api_key, 
        base_url=base_url,
        timeout=180)
    
    response = client.responses.create(
        model=model_id,
        instructions=SYSTEM,
        input=user_message,
        tools= TOOLS
    )
    
    """
    # 核心逻辑 定义while循环
        # 把模型的返回添加到message里 
        # 只要模型返回继续调用工具 继续 否则return停止
    """ 
    while True:
        
        # 等价于
        # tool_calls = []
        # for item in response.output:
        #     if "function_call" == item.type:
        #         tool_calls.append(item)
        print("返回的结果类型是response type:", type(response))
        print("返回response 内容是:", response)

        # 获取模型返回的调用工具列表
        tool_calls = [item for item in response.output if item.type == "function_call"]
        print("模型返回的工具调用列表是:", tool_calls)
        
        # 如果模型返回的工具为空 说明不需要调用工具 已经结束
        if not tool_calls:
            # 为了更严谨的判断 如果工具为空 则从最后一次user_message中获取
            for msg in reversed(user_message):
                if(msg.get("type") == "function_call_output"):
                    print("倒序后续最后一条文本记录作为最终输出: ", msg)
                    return msg.get("content")

            print("当前的是空的 直接返回!!!!!!!!!!!!!!!!!!!!!!!!!!")
            return response.output_text
        

        # 工具不为空 则继续遍历工具
        tool_outputs= []
        for tool_call in tool_calls:
            
            # 解析工具调用参数
            arguments = json.loads(tool_call.arguments)
            if "bash" == tool_call.name:
                output = run_bash(arguments["command"])
                print("模型调用工具的结果是: ", output)
            else:
                output = f"unknown tool:{tool_call.name}"
            
            tool_entry = {
                #"role": "assistant",
                "type": "function_call_output",
                "call_id": tool_call.call_id,
                "output": output   # ✅ 注意这里是 output，不是 content 否则调用会报400格式不正确
            }
            
            
            tool_outputs.append(tool_entry)
            user_message.append(tool_entry)
                                
            # 再次调用模型   
            response = client.responses.create(
            model=model_id,
            instructions=SYSTEM,
            input=user_message,
            tools= TOOLS)    
                
                
            

# 程序主入口
if __name__ == "__main__":
    print("当前程序的文件夹:", )
    history = []
    count = 0
    while True:
        try:
            query = input("\033[36ms01 >> \033[0m")
        except (EOFError, KeyboardInterrupt):
            print("输入异常",EOFError )     
        if query.strip().lower() in ["q", "exit", ""]:   
            break
        history.append(
            {
                "role":"user",
                "content":query
            }
        )
        
        count = count +1 
        # 调用循环 开始执行
        agent_loop(history)
        
        print("当前执行循环的次数", count)
        print("当前的历史记录是:", history)
        
        # 取最近的一条文本响应 这么写可能报错
        #response_content = history[-1]["content"]
        response_content = history[-1].get("output", "")

        if isinstance(response_content, str):
            print("最终的输出结果是:", response_content)
            break
        print("继续执行循环")

    
        
