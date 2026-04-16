
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
TASK_DIR = WORKDIR/"task"

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
    # save -> 入参task的字典 save是保存方法 完整的字典信息是create创建的 ✅
    # create -> 入参 主题/描述 ✅
        # 创建task字典 属性 id/desc/subject/status/blockedBy(前置依赖)/blocks(后置依赖)
        # 调用save
        # nextId + 1 
    # get -> 入参task_id 读取文件 返回字典 ✅
    # clear_dependency -> 入参task_id ✅
        # 遍历当前文件夹下的所有文件
        # 查看当前task中blocked是否包含传入task_id(即完成的completed_id) 如果包含remove
        # 重新保存
    # update ->  ✅
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
        self.next_id = self.max_id() + 1
        
    def get_path(self, task_id: int) -> Path:
        path = self.path_dir/f"task_{task_id}.json"
        if not path:
            raise f"当前文件不存在 -> {path}"
        return path    
        
    # maxId -> 遍历当前文件下 找出最大的文件id
    def max_id(self) -> int:
        task_ids = []
        for f in self.path_dir.glob("**/*.task_*.json"):
            # 按照_切割 取第二个即taskId
            task_id = int(f.stem.split("_")[1])
            task_ids.append(task_id)
        return max(task_ids) if task_ids else 0
    # load -> 入参task_id 文件文件路径 读取文件路径 转成字典
    def load(self, task_id: int) -> dict :  
        path = self.get_path(task_id)
        return json.loads(path.read_text())
    
    # save -> 入参task的字典 save是保存方法 完整的字典信息是create创建的
    def save(self, task: dict):
        task_id = task.get("id", None)
        if not task_id:
            raise f"保存task失败 未获取到taskId 原始信息:{task}"
        # 拼接文件路径
        path = self.path_dir/f"task_{task_id}.json"
        path.write_text(json.dumps(task, indent=2))

    def create (self, 
                subject: str,
                description: str,
                blockedBy: list, # 前置依赖
                blocks: list) -> str: # 后置依赖
        
        # 定义task结构
        task = {
            "id" : self.next_id,
            "subject" : subject,
            "status":"pending",
            "description" : description,
            "blockedBy" : blockedBy,
            "blocks" : blocks
        }
        
        # 保存
        self.save(task)
        
        # nextId更新+1
        self.next_id += 1
        
        # 返回字符串
        return json.dumps(task, indent=2)
    
    def get(self, task_id : int) -> str:
        task_dict = self.load(task_id)
        return json.dumps(task_dict, indent=2)
    
    def clear_dependency(self, completed_id: int):
        # 遍历当前所有文件夹
        for f in self.path_dir.glob("task_*.json"):
            # 此处直接转换成json即可
            task = json.loads(f.read_text())
            blockedBy = task.get("blockedBy", [])
            
            if not blockedBy:
                continue
            
            if completed_id in blockedBy:
                blockedBy.remove(completed_id)
                self.save(task)

    def update(self,
               task_id:int,
               status:str,
               blockedBy: list,
               blocks:list) -> str:
        
        task = self.load(task_id)
        if not task:
            raise f"未加载到指定task taskId: {task_id}"
        
        
    
        # 处理状态
        if status:
            
            if status not in ["pending", "in_progess", "completed"]:
                raise f"状态非法"
            
            task["status"] = status
        
            # 如果当前任务已完成 把其他前置依赖中包含这个任务id的清除
            if "completed" == status:
                self.clear_dependency(task_id)
            
            
        if blockedBy:
            # 第一种 
            task["blockedBy"] = list(set(task.get("blockedBy",[]) + blockedBy))
            
            # 第二种不能用
            #blockedBy = list(task.get("blockedBy",[]))
            # 不能使用append, extend, remove, sort等的原因 
                # 不能使用append方法会返回None 导致set直接报错
                # append是将整体作为一个元素拼接进入 假设之前[1,2] 要拼接的是[3,4] 直接调用append 会得到[1,2,[3,4]]
            #task["blockedBy"] = list(set(blockedBy.append(add_blocked_by)))
            
        if blocks:
            
            # 追加后置任务             
            task["blocks"] = list(set(task.get("blocks",[]) + blocks))   
            
            # 遍历添加进来的后置任务 如果后置任务中的前置任务不包含当前task_id 则追加到前置任务重
            for block_id in blocks:
                block_task = self.load(block_id)
                if not block_task:
                     continue
                 # 如果添加进来的所有后置任务的前置任务不包含当前task_id 则添加进去
                blockedBy = list(block_task.get("blockedBy",[]))
                if task_id not in blockedBy:
                     blockedBy.append(task_id)
                     self.save(block_task)

        self.save(task)
        
        return json.dumps(task, indent=2)
    
    def list_all(self):
        
        tasks = []
        # 加载当前文件夹下的所有文件
        for f in self.path_dir.glob("task_*.json"):
            # 转成字典
            task = json.loads(f.read_text())
            tasks.append(task)
        if not tasks:
            return "no tasks"
        
        lines = []
        for f in tasks:
            
            # maker -> 状态标识位 状态标识符可视化 方便模型快速理解 # 这块的写法没理解
            marker = {"pending":"[ ]", "in_progress":"[>]", "completed":"[x]"}.get(f["status"], "[?]")
            # blocked
            blockedBy = f.get("blockedBy", "")
            status = f.get("status", "")
            subject = f.get("subject", "")

            blocked = f"(blocked by {blockedBy})"
            lines.append(f"{marker} #{status} : {subject} {blocked} ")
        
        return "\n".join(lines)
    

            
 # 定义ToolHandler和Tool
 

task_manager = TaskManager(TASK_DIR)


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
    "task_create": lambda **kw: task_manager.create(kw["subject"], 
                                                   kw.get("description", ""),
                                                   kw.get("blockedBy",[]), # 模型首次调用 可能没有前置依赖 不加默认值真实调用会create会报错
                                                   kw.get("blocks",[]) # 模型首次调用 可能没有前置依赖 不加默认值真实调用会create会报错
                                                   ),
    "task_update": lambda **kw: task_manager.update(kw["task_id"], kw.get("status"), kw.get("blockedBy"), kw.get("blocks")),
    "task_list":   lambda **kw: task_manager.list_all(),
    "task_get":    lambda **kw: task_manager.get(kw["task_id"]),

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
    },
    
    # 四个工具 task_list / task_get / task_create / task_update
    {
        # 压缩工具具体描述 无输入参数 只有一个可选参数 focus 让模型知道这次压缩的重点是什么
        "type":"function", 
        "name":"task_list",
        "description":"List all tasks with status summary.",
        "parameters":{}
        
    },
    
    {
        # 压缩工具具体描述 无输入参数 只有一个可选参数 focus 让模型知道这次压缩的重点是什么
        "type":"function", 
        "name":"task_get",
        "description":"Get full details of a task by ID.",
        "parameters":{
            "type":"object",
            "properties":{
                "task_id":{"type":"integer", "description":"What to preserve in the summary"}
            },
            "required":["task_id"] #required不能放在properteis里 需要和required平级

        }
    },
    
    {
        "type":"function", 
        "name":"task_create",
        "description":"Create a new task.",
        "parameters":{
            "type":"object",
            "properties":{
                "subject":{"type":"string"},
                "description":{"type":"string"},
                "blockedBy":{"type":"array", "items":{"type": "integer"}},
                "blocks":{"type":"array", "items":{"type": "integer"}}   
            },
            "required":["subject"]
        }
    },
    
    {
        "type":"function", 
        "name":"task_update",
        "description":"Update a task's status or dependencies.",
        "parameters":{
            "type":"object",
            "properties":{

                "type":"object", # 数组字段
                "properties":{
                    "task_id":{"type":"integer"},
                    "status":{"type":"string", "enum":["pending","in_progress","completed"]},
                    "blockedBy":{"type":"array", "items":{"type": "integer"}},
                    "blocks":{"type":"array", "items":{"type": "integer"}}
                },
                "required":["task_id","status"]
                
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


