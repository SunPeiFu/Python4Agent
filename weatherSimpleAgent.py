from langchain_classic.agents import create_react_agent, AgentExecutor
from langchain_core.prompts import PromptTemplate
from langchain_core.tools import tool
from langchain_openai import ChatOpenAI


#定义一个方法
@tool
def get_weather(city: str) -> str:
    """Get Weather for city"""
    return f"获取{city}的天气情况"

#配置模型
# 创建 LLM（这里才是配置 key 的地方）
llm = ChatOpenAI(
    model="qwen-turbo",
    api_key="sk-ceadca0a001f40c6bc1fc0d5f388366e",  # 环境变量
    base_url="https://dashscope.aliyuncs.com/compatible-mode/v1",
)

prompt = PromptTemplate.from_template(
    """You are a helpful assistant.
You have access to the following tools:
{tools}
Use the following format:
Question: the input question
Thought: your reasoning
Action: the action to take, should be one of [{tool_names}]
Action Input: the input to the action
Observation: the result of the action
... (this Thought/Action/Observation can repeat)
Thought: I now know the final answer
Final Answer: the final answer to the user

Question: {input}
Thought:{agent_scratchpad}
"""
)

#创建react agent
agent = create_react_agent(
    llm=llm,
    tools=[get_weather],
    prompt=prompt
)

# 定义执行器
agent_executor = AgentExecutor(
    agent=agent,
    tools=[get_weather],
    verbose=True
)

# run一下
result = agent_executor.invoke(
    {"input": "北京今天的天气如何 多少度 会下雨吗"}
)

print(result)


