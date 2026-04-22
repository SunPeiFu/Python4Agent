from typing import Optional, List
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel


# 1 初始化应用
app = FastAPI(title="first_fast_api")

# 2 定义出入参
class AgentRequest(BaseModel):
    task_id : str
    promt : str
    temperature : Optional[float] = 0.7 # 此处Optioanl是什么意思
    tools : List[str] = []

class AgentResposne(BaseModel):
    task_id : str
    status : str
    output : str

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

# 健康检查
@app.get(path="/health")
def health_check():
    return {"status": "healthy"}