
import os
import subprocess
from openai import OpenAI
import json
import re
import time
import uuid
from pathlib import Path
import threading

# 核心主旨
    # 后台任务管理维护
        # 根据指令创建任务 thread执行 task中包含command status和任务执行结果 加到queue中
        # 每次while循环全量拉出任务 重置模型心智 提醒模型注意这些后台任务 阅后即焚queue.clear
        


WORKDIR = Path.cwd()
print("当前的工作目录是:", WORKDIR)

# task文件存放路径
TASK_DIR = WORKDIR/"task"
TEAM_DIR = WORKDIR / ".team"
INBOX_DIR = TEAM_DIR / "inbox"

api_key = "sk-qFvDkFk22zpWFpVWLGjHtBXwIH1wekq11pZNzLz0e582pl0v"
base_url = "https://api.lotte-library.top/v1"
model_id = "glm-4.7"
           
SYSTEM = f"""You are a coding agent at {WORKDIR}.
Use task tools to plan and track work
"Note: The bash environment is already pre-configured. Do not use 'conda activate'. Run commands directly."
Use load_skill to access specialized knowledge before tackling unfamiliar topics.
"""

VALID_MSG_TYPES = {
    "message",
    "broadcast",
    "shutdown_request",
    "shutdown_response",
    "plan_approval_response",
}



client = OpenAI(
        api_key=api_key, 
        base_url=base_url,
        timeout=180)

# MessageBus消息总线
    # int方法 ✅
    # send方法 返回str ✅
        # 参数
            # from 
            # to
            # msg_type
            # content
            # extra
        # 逻辑
            # 校验msg_type是否合法
            # 定义msg结构类型 type, from, content, time
            # 如果有extra扩展信息 则msg.update
            # 维护self.dir/{to}.json文件 写入msg(json.dumps形式)
            # return "sent {msg_type} to {to}"    
    # read方法 返回list ✅ 
        # 参数
            # name
        # 逻辑
            # self.dir/{name}.json
            # 校验文件是否存在 空返回[]
            # 遍历读取文件每一行 if line , json.loads() append到messages中
            # 遍历结束 清空当前文件文本(保持干净)
            # return messages
    # broadcast 返回str (广播了几个人) ✅
        # 参数
            # sender
            # content
            # teammates (list)
        # 逻辑
            # 定义count
            # 遍历teammates if name不是send
            # 调用self.send方法 msg_type传入(broadcast)
            # 计数器+1
            # 返回广播了几个人
class MessageBus:

    def __init__(self,inbox_dir : Path):
        self.dir = inbox_dir
        # parents -> 如果a/b/inbox_dir, ab不存在 则自动创建 不报错
        # exist -> 目录存在继续
        self.dir.mkdir(exist_ok = True, parents=True)

    def send(self,
             sender : str,
             to : str,
             msg_type : str,
             content : str,
             extra : dict | None) -> str:
        
        if msg_type not in VALID_MSG_TYPES :
                return f"Error: Invalid type '{msg_type}'. Valid: {VALID_MSG_TYPES}"
        
        msg = {
                "type" : msg_type,
                "from" : sender,
                "content" : content,
                "time" : time.time()
            }
        
        # 根据key merge
        if extra:
            msg.update(extra)

        inbox_path = self.dir/f"{to}.json"
        # 此处a 代表apend mode模式 即追加模式
        with open(inbox_path, "a") as f:
            # 每次写入换行 保证行清晰
            f.write(json.dumps(msg) + "\n")

        return f"sent {msg_type} to {to}"    
    
    def read(self, name : str) -> list:

        inbox_path = self.dir/f"{name}.json"

        messages = []
        if not inbox_path.exists():
            return f"read file path is not exist {inbox_path}"
        for line in inbox_path.read_text().strip().splitlines:
            if line:
                messages.append(json.loads(line))
        # 清空  
        inbox_path.write_text("")
        return messages
    
    def broadcast(self,
                  sender : str,
                  content : str,
                  teammates: list) -> str:
        
        if not teammates:
            return "broadcast is empty "
        
        count = 0
        for team_name in teammates:
            if sender != team_name:
                self.send(
                    sender = sender,
                    to = team_name,
                    msg_type = "broadcast",
                    content = content,
                )
                count += 1
                return f"Broadcast to {count} teammates"
  
BUS = MessageBus(INBOX_DIR)
     

# TeamManager
    # init方法 ✅
        # dir
        # mkdir
        # config_path
        # self.config = self.load_config()
        # threads
    # load_config -> dict ✅
        # 判断config_path是否存在 存在返回json.loads(self.read_text())   
        # 不存在返回默认字典 team_name(default), member=[]
    # save_config ✅
        # self.config_path.wirte_text(json.dumps(self.config())
    # find_members: -> dict 成员字典✅
        # 入参 name
        # 遍历m self.config("members")
        # if m.["name"] == name return else None
    # 创建队友并在线程中启动 -> str
        # 入参
            # name role prompt 
        # member = self.find_members
        # if member
            # 判断状态 如果不是 idle, shuntdown
                # return current member status is 
            # 赋值 member["status"] = 入参状态 角色=入参
        # else 
            # 创建member对象member =  name role status("working")
            # self.config["members"].append(member)
        # self.save_config()
        # 定义线程, 调用agent_loop方法 传入参数 name role prompt
        # 启动线程
    # agent_loop方法
        # 定义system prompt name role 工作空间
        # 定义messages  [] 默认赋值字典 role:user content:content
        # self.teammate_tools()
        # 从0开始循环50次
            # Bus.read_inbox(name) 返回列表
            # for inbox_content in list  , messags append user content 
        # 调用模型 传入sys messages等
        # 之前的逻辑 把模型的结果加入到上下文中
        # self.find_member("name")
        # if member and member status  != shutdown
            # member["status"] = "idle"
            # self.save_config()
    # exe方法
        # 参数 send ,too_name, args(字典)
        # 判断 too_name 不同的工具名称 调用不同方法  
    # teammate_tools(self) - list:
        # 定义数组字典工具 多加了send_message和read_inbox
    # list_all方法
        # lines 拼接 self.config.team_name    
        # self.config.["members"] 遍历字典 lines拼接 name role status
        # return \n.join(lines)
    # member_names方法
        # 遍历self.config[members] 直接使用return [for] 方式初始化    
class TeammateManager:

    # 初始化
    def __init__(self, team_dir : Path):
        self.dir = team_dir
        self.dir.mkdir(exist_ok= True, parents=True)
        self.config_path = self.dir/"config.json"
        threads = []
        self.config = self.load_config()

    # 加载配置
    def load_config(self) -> dict:  
        if self.dir.exists():  
            return json.loads(self.config_path.read_text())
        return {"team_name":"default", "members" : []}
    
    def save_config(self):
        self.config_path.write_text(json.dumps(self.config))

    def find_members(self, name : str) -> dict:    
        for m in self.config["members"]:
            if m["name"] == name:
                return m
        return None    
    
    def spawn(self,
              name : str,
              role : str,
              prompt : str) -> str:
        
        member = self.find_members(name)
        if member:
            if member["status"] not in ["idle", "shuntdown"]:
                return f"current member status is un support "
            member["status"] = ""
        else :
            member = {"name":name, "role":role, "status":"working"}
            self.config["members"].update(member)
        self.save_config()
        thread = threading.Thread(
            target=self
            args=(name, role, prompt),
            daemon=True
        )
        thread.start()
        return f"Spawned '{name}' (role: {role})"
    
    def _exec(self, sender: str, tool_name: str, args: dict) -> str:
        # these base tools are unchanged from s02
        if tool_name == "bash":
            return run_bash(args["command"])
        if tool_name == "read_file":
            return run_read(args["path"])
        if tool_name == "write_file":
            return run_write(args["path"], args["content"])
        if tool_name == "edit_file":
            return run_edit(args["path"], args["old_text"], args["new_text"])
        if tool_name == "send_message":
            return BUS.send(sender, args["to"], args["content"], args.get("msg_type", "message"))
        if tool_name == "read_inbox":
            return json.dumps(BUS.read_inbox(sender), indent=2)
        return f"Unknown tool: {tool_name}"

    def _teammate_tools(self) -> list:
        # these base tools are unchanged from s02
        return [
            {"name": "bash", "description": "Run a shell command.",
             "input_schema": {"type": "object", "properties": {"command": {"type": "string"}}, "required": ["command"]}},
            {"name": "read_file", "description": "Read file contents.",
             "input_schema": {"type": "object", "properties": {"path": {"type": "string"}}, "required": ["path"]}},
            {"name": "write_file", "description": "Write content to file.",
             "input_schema": {"type": "object", "properties": {"path": {"type": "string"}, "content": {"type": "string"}}, "required": ["path", "content"]}},
            {"name": "edit_file", "description": "Replace exact text in file.",
             "input_schema": {"type": "object", "properties": {"path": {"type": "string"}, "old_text": {"type": "string"}, "new_text": {"type": "string"}}, "required": ["path", "old_text", "new_text"]}},
            {"name": "send_message", "description": "Send message to a teammate.",
             "input_schema": {"type": "object", "properties": {"to": {"type": "string"}, "content": {"type": "string"}, "msg_type": {"type": "string", "enum": list(VALID_MSG_TYPES)}}, "required": ["to", "content"]}},
            {"name": "read_inbox", "description": "Read and drain your inbox.",
             "input_schema": {"type": "object", "properties": {}}},
        ]
    
    def agent_loop(self, name : str, role : str , prompt : str):
    
    # 定义system name role 和工作目录
        sys_prompt = (
                f"You are '{name}', role: {role}, at {WORKDIR}. "
                f"Use send_message to communicate. Complete your task."
            )
        # 初始化上下文 
        messages = [{"role":"user", "content": prompt}]
        tools = self._teammate_tools()

        client = OpenAI(
            api_key=api_key, 
            base_url=base_url,
            timeout=180)
        
        
        
        all_tool_outputs = []
        for _ in range(50):

            inbox = BUS.read(name)
            for m in inbox:

                messages.append({"role":"user", "content":json.dumps(m)})

                response = client.responses.create(
                model=model_id,
                instructions=SYSTEM,
                sys_prompt = sys_prompt,
                input=messages,
                tools=tools
                tools= TOOLS
            )
            
            
            
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
                        "role": "tool", # 工具的调用输出结果 role使用tool
                        "type": "function_call_output", # type[function_call_output]工具的执行结果
                        "call_id": tool_call.call_id,# 模型输出的调用工具id 
                        "output": output   # ✅ 注意这里是 output，output代表工具执行的结果 ? 不是 content 否则调用会报400格式不正确
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
        member = self.find_members(name)    
        if member and member["status"] != "shutdown":
            member["status"] = "idle"
            self._save_config()

TEAM = TeammateManager(TEAM_DIR)
     


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
    "edit_file":  lambda **kw: run_edit(kw["path"], kw["old_content"], kw["new_content"]),
    
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
    # 执行task
    {
        "type":"function", 
        "name":"run_task",
        "description":"Run command in background thread. Returns task_id immediately.",
        "parameters":{
            "type":"object",
            "properties":{
                "command":{"type":"string"}
                },
            "required":["command"] # required不能放在properteis里 需要和required平级
        }

    },
    # 检查task
    {
        "type":"function", 
        "name":"check_task",
        "description":"Check background task status. Omit task_id to list all.",
        "parameters":{
            "type":"object",
            "properties":{
                "task_id":{"type":"string"}
                },
            "required":["task_id"] # 必输参数 required不能放在properteis里 需要和required平级
        }

    }
    
    
    
]    
        
    
# The core pattern: a while loop that calls tools until the model stops

                
                
            

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


