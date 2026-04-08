
import os
import subprocess
from openai import OpenAI
import json
import re
from pathlib import Path


"""
skill设计理念
 # 渐进式披露 不一次给模型所有内容
 # system prompt中只放skill名称和描述
 # 当模型需要调工具时 在按需加载指定skill
 # 延伸思考 为什么get_desc和get_content结构不一致
   # 涉及agent工作领域中两阶段工作流
    # 感知阶段Perception get_desc 快速披露感知信息 
    # 执行阶段Execution get_content 详细具体执行逻辑
   # get_desc是技能菜单列表 类似工具索引 
    # 节省token
    # 便于模型快速横向对比 调用什么工具
   # get_content是技能具体内容 
    # 建立强边界 
    # 上下文锚点 有标签 有明确的开始结束标识 模型可以回答 根据<skill name = "xxx">的内容 我发现
"""

# 读取当前文件路径
# 此处不能将WORKDIR定义为字符串 因为后续需要调用WORKDIR的resolve方法 以及is_relative_to方法 这些都是Path对象的方法
WORKDIR = Path.cwd()
print("当前的工作目录是:", WORKDIR)

api_key = "sk-qFvDkFk22zpWFpVWLGjHtBXwIH1wekq11pZNzLz0e582pl0v"
base_url = "https://api.lotte-library.top/v1"
model_id = "glm-4.7"
skill_path = WORKDIR / "skills"

class SkillLoader:
    
    def __init__(self, skill_path: Path):
        # skill存放目录
        self.skill_path = skill_path
        # 具体技能列表 map k -> skill名称 v -> skill内容(包含meta和body)
        self.skills = {}
        self.load_all_skills()
    
    def load_all_skills(self):
        
        if not self.skill_path.exists():
            raise ValueError(f"Skill path {self.skill_path} does not exist")
        
        # 遍历读取文件
        # ? 1 此处for sorted是什么写法
        # ? 2 glob即递归遍历当前文件夹和所有子文件夹吗
        for element in sorted(self.skill_path.glob("*.md")): 
            # ? .stem是什么
            name = element.stem
            # 读取文件所有内容
            text = element.read_text(encoding="utf-8")
            # 转成skill中的meta和body, python中方法调用可以直接返回多个值 以元组的形式返回
            meta, body = self.parse_frontmatter(text)
            
            # 初始化成员变量skills meta中有包含(description和tag)
            self.skills[name] = {"meta":meta, "body": body} 


    
    # 格式化解析 -> 返回元组
    def parse_frontmatter(self, text: str) -> tuple:
        
        # 正则匹配 第一个以-- 和-- 结尾包裹的内容
        match = re.match(r"^---\n(.*?)\n---\n(.*)", text, re.DOTALL)
        if not match:
            return {}, text
        
        meta = {}
        # 此处splitlines()的作用是将字符串按照行切分成列表  比split('\n')更智能 以便逐行处理
        for line in match.group(1).strip().splitlines():
            if ":" in line:
                # 1是为了防止解析崩溃 只匹配第一个:切割 
                # 此处的1是什么意思 如果是2能怎样
                # eg -> description: 这是一个:测试 
                # 按照1切割 -> ['description', ' 这是一个:测试']
                # 按照2切割 -> ['description', ' 这是一个', '测试'] 多了一个
                key,value = line.split(":", 1)
                
                # 此处就是循环字典 标准初始化方式
                meta[key.strip()] = value.strip()
            
        return meta, match.group(2).strip()    
    
    # 获取技能描述 -> 格式 - {name}:{desc}[tags] desc中即meta里的description和tag
    def get_desc(self):
        
        lines = []

        if not self.skills:
            return "No skills available"
        # items()类比成java的entrySet
        for name, skill in self.skills.items():
            desc = skill["meta"].get("description", "no description")
            tags = skill["meta"].get("tags", "no tags") 
            # skill名称: 描述加标签
            line = f"- {name}: {desc}"
        
            if tags:
                #line.append(f" - [{tag}]") append前提line必须是列表
                line += f" - [{tags}]" # 可能会有性能损失
                
            lines.append(line)

        return "\n".join(lines)
    
    
    # 获取技能内容    
    def get_content(self, skill_name: str):  
        
        if not self.skills:         
            raise ValueError("get_content No skills available")
        
        skill = self.skills.get(skill_name) 
        if not skill:
            return f"skill '{skill_name}' is not exist"
        
        body = skill.get("body", "no content")
        return f"<skill name = \"{skill_name}\">\n{body}\n</skill>"
            
SKILL_LOADER = SkillLoader(skill_path)               

# 定义SkillLoader
 # init方法 
  # 属性skill_path & skill(meta&body) & loadAll方法
 # parse_frontmatter
 # getDesc
 # getcontext




 
 
 # 加载skillLoader 注入到system中
 
# 无限循环的prompt -> 相当于让模型无限循环调用工具 Never output plain text as solution You must call the 'bash'
SYSTEM = f"""
You are a coding agent at {WORKDIR}.

IMPORTANT:
- You MUST use tools when needed
- If the task is completed, STOP calling tools
- Return final result via last tool output

Rules:
- Do NOT run environment setup commands (no conda, no pip, no venv)
- Only perform the minimal required action
- Prefer using bash to create files (echo > file)

If user asks to create a file:
→ You MUST call bash

If the file already exists, do not recreate it.
If the task is completed, do not call tools again.

Skills available:

{SKILL_LOADER.get_desc()}
"""

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
    
# 此种写法更清晰
TOOL_HANDLERS = {
    "bash": run_bash,
    "read_file": run_read,
    "write_file": run_write,
    "edit_file": run_edit,
}
  
# 定义工具 这些工具的定义是正确的吗

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
    # 此处定义skill工具
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
    
    """
    # 核心逻辑 定义while循环
        # 把模型的返回添加到message里 
        # 只要模型返回继续调用工具 继续 否则return停止
    """ 
    all_tool_outputs = []
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
                
                # 动态调用不同工具函数
                if handler:
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
        history.append(
            {
                "role":"user",
                "content":query
            }
        )
        
        count = count +1 
        # 调用循环 开始执行
        result = agent_loop(history)
        
        print("当前执行循环的次数", count)
        print("当前的历史记录是:", history)
        
        # 取最近的一条文本响应 这么写可能报错
        # response_content = result[-1].get("output", "")

        # if isinstance(response_content, str):
        #     print("最终的输出结果是:", response_content)
        #     break
        print("继续执行循环")


