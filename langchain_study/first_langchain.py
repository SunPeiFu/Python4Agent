from langchain.agents import create_agent
from langchain_openai import ChatOpenAI
from langchain.tools import tool
from pydantic import BaseModel, Field, RootModel
import json

model_id = "glm-4.7"

# 定义args_schema 业界标准形式
class WeatherInput(BaseModel):
    city : str = Field(description="城市的名字 e.g : 北京")

@tool(description="Get current weather for a given city." ,args_schema=WeatherInput)
def get_weather(city : str) :
    return f" It's always sunny in {city}"

# 声明模型
llm = ChatOpenAI(
    # LM Studio 里加载的模型名
    model="glm-4.7",  
    base_url="http://localhost:1234/v1",
    # apikey已经是环境变量中 -> export OPENAI_API_KEY=lm-studio
)

agent = create_agent(
    model=llm,
    tools=[get_weather],
    system_prompt="You are a helpful assistant",
)

# 调用模型
result = agent.invoke(
    {"messages":[{"role":"user", "content":"What's the weather in San Francisco?"}]}
)

# 结构话输出
data = result["messages"]
json_str = RootModel(data).model_dump_json(indent=2)
# 两端代码等价
# json_str = json.dumps(
#     # data本质是list 内容是字典
#     [m.model_dump() for m in data],  
#     indent=2, # 生成的字符串会有两个空行的缩进和换行 方便观看
#     ensure_ascii=False # 中文显示正常
# )

print(f"格式化后的json:{json_str}")


api_key = "sk-qFvDkFk22zpWFpVWLGjHtBXwIH1wekq11pZNzLz0e582pl0v"
base_url = "https://api.lotte-library.top/v1"
model_id = "glm-4.7"



"""
完整的响应信息
总结:
type -> hunman
type -> ai  & tool_call非空 模型思考过程 决定调用工具
type -> tool 工具执行结果
type -> ai & tool_call空 agent执行完毕 模型基于工具调用结果 生成最终答案


[
    {
        "content": "What's the weather in San Francisco?",
        "additional_kwargs": {

        },
        "response_metadata": {

        },
        "type": "human",
        "name": null,
        "id": "57365ef2-f8ce-4d9c-8520-d66881501956"
    },
    {
        "content": "I'll get the current weather in San Francisco for you.",
        "additional_kwargs": {
            "refusal": null
        },
        "response_metadata": {
            "token_usage": {
                "completion_tokens": 83,
                "prompt_tokens": 184,
                "total_tokens": 267,
                "completion_tokens_details": {
                    "accepted_prediction_tokens": null,
                    "audio_tokens": null,
                    "reasoning_tokens": 58,
                    "rejected_prediction_tokens": null
                },
                "prompt_tokens_details": null
            },
            "model_provider": "openai",
            "model_name": "zai-org/glm-4.7-flash",
            "system_fingerprint": "zai-org/glm-4.7-flash",
            "id": "chatcmpl-ik9dddcc63i1y3j3ak3ojf",
            "finish_reason": "tool_calls",
            "logprobs": null
        },
        "type": "ai",
        "name": null,
        "id": "lc_run--019dbd7c-7e81-7913-b5f8-b3714a6fa6a1-0",
        "tool_calls": [
            {
                "name": "get_weather",
                "args": {
                    "city": "San Francisco"
                },
                "id": "281892473",
                "type": "tool_call"
            }
        ],
        "invalid_tool_calls": [

        ],
        "usage_metadata": {
            "input_tokens": 184,
            "output_tokens": 83,
            "total_tokens": 267,
            "input_token_details": {

            },
            "output_token_details": {
                "reasoning": 58
            }
        }
    },
    {
        "content": " It's always sunny in San Francisco",
        "additional_kwargs": {

        },
        "response_metadata": {

        },
        "type": "tool",
        "name": "get_weather",
        "id": "aec2bae9-5e17-4bfb-bd9d-5e29b2a4dcea",
        "tool_call_id": "281892473",
        "artifact": null,
        "status": "success"
    },
    {
        "content": "According to the weather service, it's always sunny in San Francisco! \n\nHowever, I should note that this appears to be a playful response rather than actual current weather data. For accurate, up-to-date weather information, you might want to check a dedicated weather service or app.",
        "additional_kwargs": {
            "refusal": null
        },
        "response_metadata": {
            "token_usage": {
                "completion_tokens": 120,
                "prompt_tokens": 219,
                "total_tokens": 339,
                "completion_tokens_details": {
                    "accepted_prediction_tokens": null,
                    "audio_tokens": null,
                    "reasoning_tokens": 62,
                    "rejected_prediction_tokens": null
                },
                "prompt_tokens_details": null
            },
            "model_provider": "openai",
            "model_name": "zai-org/glm-4.7-flash",
            "system_fingerprint": "zai-org/glm-4.7-flash",
            "id": "chatcmpl-54egkcvy9elq87ib87qgc",
            "finish_reason": "stop",
            "logprobs": null
        },
        "type": "ai",
        "name": null,
        "id": "lc_run--019dbd7c-85d9-7463-8f61-40eb84feea07-0",
        "tool_calls": [

        ],
        "invalid_tool_calls": [

        ],
        "usage_metadata": {
            "input_tokens": 219,
            "output_tokens": 120,
            "total_tokens": 339,
            "input_token_details": {

            },
            "output_token_details": {
                "reasoning": 62
            }
        }
    }
]
"""