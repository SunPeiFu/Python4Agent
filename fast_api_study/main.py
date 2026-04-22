from typing import Optional, List
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from enum import Enum

# 启动命令 uvicorn main:app --reload
    # 启动main.py中的app程序 
    # --reload 使用热加载的方式

# 1 初始化应用
app = FastAPI(title="first_fast_api")

# 2 定义出入参
    #  Optioanl代表一个可选的参数 不传的话默认值是0.7 其他参数不传则直接报错422
class AgentRequest(BaseModel):
    task_id : str
    promt : str
    temperature : Optional[float] = 0.7 # Optioanl代表一个可选的参数 不传的话默认值是0.7 其他参数不传则直接报错422
    tools : List[str] = []

class AgentResposne(BaseModel): # BaseModel所用 校验参数 类型转换 自动生成文档
    task_id : str
    status : str
    output : str

# 测试定义个枚举 枚举场景不需要使用baseModel localhost:8000/doc中输入的modelName就变成了可选的字符串
class ModelRequest(str, Enum):
    qWen = "Qwen"
    glm = "Glm"
    tongyi ="Tongyi"


# post请求
@app.post(path="/v1/agent/run", response_model= AgentResposne)
async def run_agent(request : AgentRequest):

    if not request.promt:
        raise HTTPException(status_code=503, detail= "prompt can not be null")
    
    # 模拟成功
    result = f"Agent已经根据提示词 {request.promt} 调用了工具 {request.tools}"
    
    return AgentResposne(
        task_id = request.task_id,
        status="completed",
        output=result
    )
@app.post(path="/testEnum")
async def testEnum(model_name : ModelRequest):
    if model_name is ModelRequest.qWen:
        return "modelName is Qwen"
    elif model_name is ModelRequest.glm:
        return "modelName is glm"
    elif model_name is ModelRequest.tongyi:
        return "modelName is tongyi"
    
    return "unknow"
    


# 健康检查
@app.get(path="/health")
def health_check():
    return {"status": "healthy"}