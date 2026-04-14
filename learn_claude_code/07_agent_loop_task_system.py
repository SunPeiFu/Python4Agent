
import os
import subprocess
from openai import OpenAI
import json
import re
import time
from pathlib import Path


WORKDIR = Path.cwd()
print("当前的工作目录是:", WORKDIR)

# task文件存放路径
TASK_DIR = WORKDIR /"learn_claude_code"/"task"

api_key = "sk-qFvDkFk22zpWFpVWLGjHtBXwIH1wekq11pZNzLz0e582pl0v"
base_url = "https://api.lotte-library.top/v1"
model_id = "glm-4.7"
           
SYSTEM = f"""You are a coding agent at {WORKDIR}.
Use task tools to plan and track work
"Note: The bash environment is already pre-configured. Do not use 'conda activate'. Run commands directly."
Use load_skill to access specialized knowledge before tackling unfamiliar topics.
"""

client = OpenAI(
        api_key=api_key, 
        base_url=base_url,
        timeout=180)

# 定义TaskManager
    # init -> task_dir&创建文件夹&next_id ✅
    # maxId -> 遍历当前文件下 找出最大的文件id ✅
    # load -> 入参task_id 文件文件路径 读取文件路径 转成字典 ✅
    # save -> 入参task_id 拼接文件路径 写入文件
    # create -> 入参 主题/描述
        # 创建task字典 属性 id/desc/subject/status/blockedBy(前置依赖)/blocks(后置依赖)
        # 调用save
        # nextId + 1 
    # get -> 入参task_id 读取文件 返回字典
    # update -> 
        # 入参:
            # task_id
            # status [pending, in_progress, complted]
            # add_blocked_by (列表)
            # add_blocks(列表)
        # 逻辑: 
            # 加载load当前task
            # 判断status 非法提示异常
            # 设置status
            # 如果传入status是已完成 调用clear_dependency 清除依赖当前taskId任务
            # if 添加前置依赖任务 则追加
            # if 添加后置依赖add_blocks 则追加
                # 遍历 add_blocks -> block_id
                # self.load加载block_id -> 获取属性blockedBy依赖前置任务列表 
                # 如果当前task_id 不在这个列表中 则添加进去
                # 保存
            
            # 最后save
class TaskManager:
    
    # init -> task_dir&创建文件夹&next_id
    def __init__(self, path_dir: Path):
        self.path_dir = path_dir
        self.path_dir.mkdir(exist_ok = True)
        self.next_id = self.max_id + 1
        
    # maxId -> 遍历当前文件下 找出最大的文件id
    def max_id(self):
        task_ids = []
        for f in self.path_dir.glob("**/*.task_*.json"):
            # 按照_切割 取第二个即taskId
            task_id = int(f.stem.split("_")[1])
            task_ids.append(task_id)
        return max(task_ids) if task_ids else 0
    
    # load -> 入参task_id 文件文件路径 读取文件路径 转成字典
    def load(self, task_id: int) -> dict :  
        path = self.path_dir/f"task_{task_id}.json"
        if not path:
            raise f"当前文件不存在 -> {path}"
        return json.load(path.read_text())
    
 # 定义ToolHandler和Tool
 



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
    
    all_tool_outputs = []
    while True:
        
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
        for tool_call in tool_calls:
            
            # 解析工具调用参数
            arguments = json.loads(tool_call.arguments)
            # 如果类型是functionCall(需要调用工具)
            if "function_call" == tool_call.type:
                print("进入function_call逻辑模型调用的工具是: ", tool_call.name)
                handler = TOOL_HANDLERS.get(tool_call.name)
                print("当前的handler是: ", handler)
                
                if handler:
                    output = handler(**arguments)
                    print("模型调用工具的结果是: ", output)
                else:
                    output = f"unknown tool:{tool_call.name}"
            
                result = {
                    "role": "user", # 工具的调用结果 role一定是user而不是assistant
                    "type": "function_call_output", # type[function_call_output]工具的执行结果
                    "call_id": tool_call.call_id,# 模型输出的调用工具id 
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


