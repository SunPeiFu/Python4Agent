from typing import Optional, List
from fastapi import FastAPI, HTTPException, Query, Path, Body
from pydantic import BaseModel, Field
from enum import Enum
from typing import Annotated, Literal


# 启动命令 uvicorn main:app --reload
    # 启动main.py中的app程序 
    # --reload 使用热加载的方式 每次改完代码 自己重启验证 不对会有报错

# 1 初始化应用
app = FastAPI(title="first_fast_api")

# 2 BaseModel -> 校验参数 类型转换 自动生成文档deng gongneng 
    #  Optioanl代表一个可选的参数 不传的话默认值是0.7 其他参数不传则直接报错422
class AgentRequest(BaseModel):
    task_id : str
    promt : str
    temperature : Optional[float] = 0.7 # Optioanl代表一个可选的参数 不传的话默认值是0.7 其他参数不传则直接报错422
    tools : List[str] = []

class AgentResposne(BaseModel): 
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
    # elif model_name is ModelRequest.glm:
    #     return "modelName is glm"
    elif model_name is ModelRequest.tongyi:
        return "modelName is tongyi"
    # 直接使用枚举.value方式 也可以
    elif model_name.value == "Glm":
        return "modelName is glm"
    
    return "unknow"

@app.post(path = "/testDefaultValue")
async def testDefaultValue(item_id: str = None ,
                           shor : bool = False):   

    if shor:
        return f"进入True逻辑 当前输入bool是{bool}" 
    
    return f"进入兜底逻辑 当前输入bool是{bool}"


# 健康检查
@app.get(path="/health")
def health_check():
    return {"status": "healthy"}

# Annotated注解使用 更加结构化
@app.get(path="/annotatedTest")
async def annotatedTest(q: Annotated[str | None, Query(max_length=50)] = None):
    return q
@app.get(path="/annotatedTest2")
async def annotatedTest2(userName: Annotated[str | None, Query(min_length=3, max_length=20)]):
    return userName

# Path和Query和Body的区别
    # Path用来校验Url
    # Query用来校验Url ? 后面的参数kv参数
    # Body用来校验请求体的参数
    # tips 如果是get请求 当传入一个对象时 是用Query校验 如果是Post请求 则使用Body校验(前者当成url?后的kv处理 后者类似requestBody 和SpirngBoot一样)
  

# Field使用方式
    # Field函数中的第一个参数永远代表default 即默认值 可以省略不写
    # Literal 中文翻译成字面量 传参必须严格匹配里面的内容
class FilterParams(BaseModel):
    limit : int = Field(100, gt=10, le=100) 
    offset: int = Field(0, ge=0),
    order_by: Literal["create_tiem", "update_time"] = "create_tiem"
    tags: list[str] = []

@app.post(path="/testFilerParams")
async def testFilerParams(request:Annotated[FilterParams, Query()]):
    return "ok"

# Body方式接受传参
class Item(BaseModel):
    name : str
    desc : str
    price : float
    tax : float = 0.00

class User(BaseModel):
    username: str
    full_name: str | None = None

@app.put(path="/item/detail/{item_id}")
async def updateItemDetail(
    # 此处两个实体对象
    item_id : Annotated[int, Path(title="It's id", ge=0, le=100)],
    q : str | None = None,
    item : Item | None = None,
    user : User | None = None,
    level: Annotated[int, Body()] = 0 # 当声明Body时 level就在请求体中 所有Annotated声明的必须要有默认值
):
    return {"item_id": item_id, "item": item, "user" : user}
"""
fastapi会自动根据key进行映射
curl -X 'PUT' \
  'http://127.0.0.1:8000/item/detail/11' \
  -H 'accept: application/json' \
  -H 'Content-Type: application/json' \
  -d '{
  "item": {
    "name": "商品名字",
    "desc": "string",
    "price": 0,
    "tax": 0
  },
  "user": {
    "username": "用户名",
    "full_name": "string"
  },
  "level": 0
}'
"""
    
    

