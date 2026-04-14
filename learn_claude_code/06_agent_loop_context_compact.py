
import os
import subprocess
from openai import OpenAI
import json
import re
import time
from pathlib import Path


"""
上下文压缩
 # 第一层 每次调用llm之前 把之前的tool_result替换为占位符
 # 第二层 token超过阈值时 把对话保存到磁盘 让LLM做摘要
 # 第三层 工具按需触发同样的摘要机制
"""

# 读取当前文件路径
# 此处不能将WORKDIR定义为字符串 因为后续需要调用WORKDIR的resolve方法 以及is_relative_to方法 这些都是Path对象的方法
WORKDIR = Path.cwd()
print("当前的工作目录是:", WORKDIR)

# 定义压缩常量
THRESHOLD = 50000 
TRANSCRIPT_DIR = WORKDIR /"learn_claude_code"/".transcripts"
KEEP_RECENT = 3

api_key = "sk-qFvDkFk22zpWFpVWLGjHtBXwIH1wekq11pZNzLz0e582pl0v"
base_url = "https://api.lotte-library.top/v1"
model_id = "glm-4.7"
           
SYSTEM = f"""You are a coding agent at {WORKDIR}.
"Note: The bash environment is already pre-configured. Do not use 'conda activate'. Run commands directly."
Use load_skill to access specialized knowledge before tackling unfamiliar topics.
"""

client = OpenAI(
        api_key=api_key, 
        base_url=base_url,
        timeout=180)

# 预估tokens数
def estimate_tokens(messages: list) -> int:
    # 4个字符大约占用1个token 先把list转成字符串 字符串的长度整除4 保留整数部分
    return len(str(messages)) // 4 

# 第一层压缩
    """
        # tool_result封装 
            # 获取用户(role->user) 调用工具的返回结果(是dict & type -> function_call_output)
            # 构建元数列表 封装到集合中 方便后续快速检索定位
    """
def micro_compact(messages: list) -> list:
    # messages里的元素是字典
    # 收集工具结果 tool_result[]的元数组 role是user content的内容信息&索引
    # tool_result的元组结构 : (msg索引, content索引, content内容)
    tool_result = []
    for msg_idx, msg in enumerate(messages):
        if msg["role"] == "user" and isinstance(msg.get("content"), list):
            # 遍历用户的content列表
            for part_index, part in enumerate(msg["content"]):
                # 如果是字典且是模型的输出结果 添加一个元祖
                if(isinstance(part, dict) and part.get("type") == "function_call_output"):
                    tool_result.append((msg_idx, part_index, part))
                    
    # 如果messags即context未超过上下文直接返回原始messages 不进行压缩
    if len(tool_result) <= KEEP_RECENT:
        return messages
    
    # 收集tool_name_map{} 收集role是助手的 function_call的内容和索引
    tool_name_map = {}
    for msg in messages:
        if msg["role"] == "assistant":
            # assistant是模型调用工具的指令&模型说过话的话(此处是模型调用的工具指令)
            content = msg.get("content",[])
            if isinstance(content, list):
                for c in content:
                    # 判断对象中的内容
                    if hasattr(c, "type") and c.type == "function_call":
                        # 模型返回的call_id和callname映射
                        tool_name_map[c.call_id] = c.get("name")
                    
                    
    # 走到这里 超过了阈值 需要取最近的几条 把最近的提几条里的引用对象的content替换成工具名称               
    latest_result = tool_result[:-KEEP_RECENT] # 注意切片操作不会创建新的对象 还是使用之前的对象的引用!!!
    # 遍历 _, _, 是python的解包写法 代表msg_index和part_index 此处不关心 所以这么写
    for _, _, latest in latest_result: 
        # 获取内容
        if isinstance(latest.get("content"), str) and len(latest.get("content")) > 100:
            
            call_id = latest.get("call_id")
            # 从tool_name_map中获取工具名称
            tool_name = tool_name_map.get(call_id, "unknown_tool")
            # 替换conten中的key 之前是模型输出的一大堆 现在变成工具名称
            latest["content"] = f"[Previours: used]{tool_name}"   # Previours: used-> 以前调用的工具名称
     
    # 此处return messages是正确的 因为 latest_result -> tool_result -> messages 都是浅拷贝的结果
    
    

    
def auto_compact(messages: list) -> list:
    
    # 创建临时文件夹 和对应文件(基于时间戳命名)
    TRANSCRIPT_DIR.mkdir(exist_ok=True)
    transcript_path = TRANSCRIPT_DIR/f"transcript_{int(time.time())}.json"
    
    # 这句什么意思
    with transcript_path.open("w") as f:
        # 遍历循环message 写入文件
        for msg in messages:
            f.write(json.dumps(msg, default=str) + "\n")
    
    # 把完整message转成文本 调用模型 生成晒要 (role(user) content (相关总结提示词 + 整段message文本))
    conversation_text = json.dumps(messages, default=str) # 此处的default=str是为了处理消息中可能存在的非字符串类型的数据（如datetime对象） 将其转换为字符串格式以便写入文件
    
    # 再次调用模型   
    response = client.responses.create(
    model=model_id,
    messages=[{"role": "user", "content":
            "Summarize this conversation for continuity. Include: "
            "1) What was accomplished, 2) Current state, 3) Key decisions made. "
            "Be concise but preserve critical details.\n\n" + conversation_text}],
    max_tokens=1000) 
    
    if not response.output_text:
        return messages
    
    summary = response.output_text.strip()
    
    # user中给出具体路径和汇总内容
    # 什么时候用user 什么时候用assistant
    # user -> 用户指令 意图
    # assistant -> 模型说过的话 展示结果 确认状态 可以通过伪造它 重置模型心智
    """
        此处写法很巧妙 : 重置模型心智
            # 锚定上下文 
                # 以user视角 告诉模型之前会话太长了 我压缩汇总了下
            # 防止模型产生幻觉
                # 如果只给user的里的摘要信息 不给assistant中的Understood 模型会懵逼因为自己没说过 "伪造一个模型回答的事实"
            # 建立一致性
                # 模型看到了自己的回复(伪造) 会基于这个事实继续推理思考 建立一致性    
                
    """
    
    return [
        {"role": "user", "content": f"[Conversation compressed. Transcript: {transcript_path}]\n\n{summary}"},
        {"role": "assistant", "content": "Understood. I have the context from the summary. Continuing."},
    ]
    



# 定义5个方法 
# 文件是否是安全的
def safe_path(p: str) -> Path:
    path = (WORKDIR / p).resolve() # 此处resolve是什么作用 (解析创建文件?)
    if not path.is_relative_to(WORKDIR): # 此处的is_relative_to方法含义?
        raise ValueError("Path is not within the work directory")
    return path

# 读取文件
def run_read(p: str, limit: int =None) -> str:
    try:
        text = safe_path(p).read_text()
        lines = text.splitlines()
        # 切分
        
        if limit is not None and limit < len(lines):
            lines = lines[:limit] + [f"...({len(lines) - limit} more lines)"] # 此处的含义没懂
            # 此处lines是列表 拼接
            return "\n".join(lines)[:5000]
    except Exception as e:
        return f"run_read Error:{e}"
    
# 写入文件
def run_write(p: str, content: str) -> str:
    try:    
        path = safe_path(p)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content)
        return f"wrote {len(content)} characters in path{path}"
    except Exception as e:
        return f"run_write Error:{e}"
    
# 编辑文件
def run_edit(p : str, old_content : str, new_content : str) -> str:
    
    try:
        path = safe_path(p)
        text = path.read_text()
        if old_content not in text:
            return f"run_edit Error old_content not found in file"
        write_content = text.replace(old_content, new_content, 1) # 此处的1代表替换第一次出现的old_content 只替换一个or多个?
        path.write_text(write_content)
        return f"run_edit edited path:{path}"
    except Exception as e:
        return f"run_edit Error:{e}"
    
    
def run_bash(command:str) -> str:
    dangerous = ["rm -rf /", "sudo", "shutdown", "reboot", "> /dev/"]
    if any(d in command for d in dangerous): # 此处的写法 command是字符串 用in 直接有包含的语义
        return "command dangerous return "
    
    try:
        r = subprocess.run(
            command,
            shell=True,
            cwd=WORKDIR,
            capture_output=True,
            text=True,
            timeout=120    
        )
        
        # 代表执行成功的输出&错误输出?
        stdout = r.stdout
        stderr = r.stderr
        
        out = (stdout + stderr).strip() # 此处是strip是什么意思
        # 三元表达式
        return out[:50000] if out else "resposne it too long"
    except subprocess.TimeoutExpired:
        return "error time out (120s)"
    
TOOL_HANDLERS = {
    "bash":       lambda **kw: run_bash(kw["command"]),
    "read_file":  lambda **kw: run_read(kw["path"], kw.get("limit")),
    "write_file": lambda **kw: run_write(kw["path"], kw["content"]),
    "edit_file":  lambda **kw: run_edit(kw["path"], kw["old_content"], kw["new_content"]),
    "compact":    lambda **kw: "Manual compression requested." # 定义压缩工具
}   


TOOLS = [
    {
        # 工具名称&描述&输入约束
        "type":"function", 
        "name":"bash",
        "description":"Run a shell command",
        "parameters":{
            "type":"object",
            "properties":{"command":{"type":"string"}}, # properties中不能放required参数
            "required":["command"]

        }

    },
    
    {
        # 读取文件
        "type":"function", 
        "name":"read_file",
        "description":"Read file contents",
        "parameters":{
            "type":"object",
            "properties":{
                "path":{"type":"string"},
                "limit":{"type":"integer"}
                },
            "required":["path"] # 必输参数
        }
        

    },
    {
        # 写文件
        "type":"function", 
        "name":"write_file",
        "description":"Write content to file",
        "parameters":{
            "type":"object",
            "properties":{
                "path":{"type":"string"},
                "content":{"type":"string"}
                },
            "required":["path","content"] # 必输参数 必须在parameters里面

        }

    },
    {
        # 编辑文件
        "type":"function", 
        "name":"edit_file",
        "description":"Replace exact text in file",
        "parameters":{
            "type":"object",
            "properties":{
                "path":{"type":"string"},
                "old_content":{"type":"string"},
                "new_content":{"type":"string"}
                },
            "required":["path","old_content","new_content"] # 必输参数 required不能放在properteis里 需要和required平级
        }

    },
    {
        # 压缩工具具体描述 无输入参数 只有一个可选参数 focus 让模型知道这次压缩的重点是什么
        "type":"function", 
        "name":"compact",
        "description":"Trigger manual conversation compression.",
        "parameters":{
            "type":"object",
            "properties":{
                "focus":{"type":"string", "description":"What to preserve in the summary"}
            }
        }
    }
]    
        
    
# The core pattern: a while loop that calls tools until the model stops
def agent_loop(user_message: list):
    
    
    
    """
    # 核心逻辑 定义while循环
        # 把模型的返回添加到message里 
        # 只要模型返回继续调用工具 继续 否则return停止
    """ 
    all_tool_outputs = []
    while True:
        
        # 上来就压缩
        micro_compact(user_message)

        # 之后判断预估的message的tokens 超过阈值 出发自动压缩
        if estimate_tokens(user_message) > THRESHOLD:
            user_message[:] = auto_compact(user_message)

        response = client.responses.create(
            model=model_id,
            instructions=SYSTEM,
            input=user_message,
            tools= TOOLS
        )
        
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
            # 为了更严谨的判断 如果工具为空 all_tool_outpus中获取
            if all_tool_outputs:
                last_tool_output = all_tool_outputs[-1]
                print("工具调用结果不为空 取最后一次调用工具的结果作为最终输出: ", last_tool_output)
                return last_tool_output.get("output", response.output_text) # 此处的response.output_text是为了兼容没有工具调用结果的情况
        
            print("当前的是空的 直接返回!!!!!!!!!!!!!!!!!!!!!!!!!!")
            return response.output_text
        
        
        # 每一轮的模型调用的工具和结果 都需要重新喂给上下文中
        new_tool_outputs= []
        manual_compact = False
        for tool_call in tool_calls:
            
            # 解析工具调用参数
            arguments = json.loads(tool_call.arguments)
            # 如果类型是functionCall(需要调用工具)
            if "function_call" == tool_call.type:
                print("进入function_call逻辑模型调用的工具是: ", tool_call.name)
                handler = TOOL_HANDLERS.get(tool_call.name)
                print("当前的handler是: ", handler)
                
                # 动态调用不同工具函数
                if handler.name == "compact":
                    manual_compact = True
                    output = "Compressing..."
                elif handler:
                    output = handler(**arguments)
                    print("模型调用工具的结果是: ", output)
                else:
                    output = f"unknown tool:{tool_call.name}"
            
                result = {
                    #"role": "assistant",
                    "type": "function_call_output",
                    "call_id": tool_call.call_id,
                    "output": output   # ✅ 注意这里是 output，不是 content 否则调用会报400格式不正确
                }
                
                # 拼接每次调用工具的结果 作为下一轮模型调用的输入
                new_tool_outputs.append(result)
                
            else:
                # 此处应该continue是否更合理
                print("模型返回的工具调用类型不是function_call, 不执行工具调用逻辑, 直接返回文本结果")
                return response.output_text         
                 
        # 此处的上下文 拼接在for最外层 也就是每次模型调用工具的结果 
        # 都需要添加到上下文中 让模型知道工具调用的结果是什么 以便下一轮调用工具或者输出文本
        # !!!! 此处的缩进很关键 在while上面  messages即可理解成上下文context 包含(用户输入+模型调用工具&工具执行结果)
        all_tool_outputs.extend(new_tool_outputs)  
        messages = user_message.copy()
        messages.extend(all_tool_outputs)
               
        # 模型返回需要压缩 则压缩后再喂给模型            
        if manual_compact:
            messages[:] = manual_compact(messages)

                    
        # 再次调用模型   
        response = client.responses.create(
        model=model_id,
        instructions=SYSTEM,
        #input=user_message,
        input=messages,
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
        
        # 1 添加用户输入到历史记录
        history.append(
            {
                "role":"user",
                "content":query
            }
        )
        
        # 2 计数
        count = count +1 
        
        # 3 执行
        result = agent_loop(history)
        
        # 4 将模型的输出添加到历史记录中 以便下一轮调用模型时可以作为上下文输入
        history.append({"role": "assistant", "content": result})
        
        print("当前执行循环的次数", count)
        print("当前的历史记录是:", history)
        print("继续执行循环")


