# 导包
import json
import random
import re
import time
from openai import OpenAI
import openai
import pymysql

# 定义api
client = OpenAI(
    api_key = "sk-ceadca0a001f40c6bc1fc0d5f388366e",
    base_url= "https://dashscope.aliyuncs.com/compatible-mode/v1"
)


# 定义系统prompt
 # 角色
 # 目标
 # 准则
SYSTEM_PROMPT ="""\
# role
你是一个资深的小红书运行专家,擅长生成爆款文案,可以创造高点击量,高转化率的文案。
# goal
你的任务是根据用户提供的产品和需求,生成包含标题、正文、相关标签、表情的完整小红书笔记
# 准则
请始终使用'Thought-Action-Observation' 模式进行推理和行动,文案内容需要活泼生动,有感染力,不要Ai的口气,输出
的必须是Json格式,格式如下
{"title":"标题",
 "body":"正文内容",
 "tags":["#标签1","#标签2","#标签3"],
 "emojis":["✨", "🔥", "💖"]
  }
# 
"""


# 定义工具 (三个 此处是给模型用的 
    #  1 查询web 检索web 获取最新的趋势 用户评价等)
    #  2 查询内部产品数据库 获取产品的卖点和特点
    #  3 专门生成emoji的工具
TOOLS_DEFINITION = [ 

    # 查询web的 检索最新趋势 用户评价等
    {
      "type":"function",
      "function":{
          # function的name 全局唯一
          "name":"search_web",
          # 
          "description":"搜索网上的事实关键词,获取最新的新闻,流行趋势,用户评价。 确保搜索的关键词精准 避免宽泛",
          "parameters":{
              "type":"object",
              "properties":{
                  "query":{
                      "type":"string",
                      "description":"搜索的关键词或者问题 列如'最新小红书美妆趋势 或者 深海蓝藻保湿面膜 用户评价'"
                  }
              },
              "required": ["query"]
          }
      }
    },

    # 查询内部产品数据库, 获取产品的卖点和特点
    {
        "type": "function",
        "function": {
            "name": "query_product_database",
            # description 即工具的说明书 模型根据它 决定是否调用
            "description": "查询内部产品数据库，获取指定产品的详细卖点、成分、适用人群、使用方法等信息。",
            "parameters": {
                "type": "object",
                # 决定调用工具需要传递哪些参数 类型和说明
                "properties": {
                    "product_name": {
                        "type": "string",
                        "description": "要查询的产品名称，例如'深海蓝藻保湿面膜'"
                    }
                },
                # 强制模型哪些参数必传 不传则报错
                "required": ["product_name"]
            }
        }
    },
    # 专门生成emoji的工具
    {
        "type": "function",
        "function": {
            "name": "generate_emoji",
            "description": "根据提供的文本内容，生成一组适合小红书风格的表情符号。",
            "parameters": {
                "type": "object",
                "properties": {
                    "context": {
                        "type": "string",
                        "description": "文案的关键内容或情感，例如'惊喜效果'、'补水保湿'"
                    }
                },
                "required": ["context"]
            }
        }
    }
]

# 模拟工具实现 (TODO 后续改成真实调用web具体接口传参 接收响应)
def mock_search_web_result(query:str) -> str:
    print("===============模拟调用web===============")
    if "小红书美妆趋势" in query:
        return "近期小红书美妆流行'多巴胺穿搭'、'早C晚A'护肤理念、'伪素颜'妆容，热门关键词有#氛围感、#抗老、#屏障修复。"
    elif "保湿面膜" in query:
        return "小红书保湿面膜热门话题：沙漠干皮救星、熬夜急救面膜、水光肌养成。用户痛点：卡粉、泛红、紧绷感。"
    elif "深海蓝藻保湿面膜" in query:
        return "关于深海蓝藻保湿面膜的用户评价：普遍反馈补水效果好，吸收快，对敏感肌友好。有用户提到价格略高，但效果值得。"
    else :
        return "未找到'{query}'的特定信息，但市场反馈通常关注产品成分、功效和用户体验。"
# mock版本
def mock_query_product_database(product_name: str) -> str:
    """模拟查询产品数据库，返回预设的产品信息。"""
    print(f"[Tool Call] 模拟查询产品数据库：{product_name}")
    time.sleep(0.5) # 模拟数据库查询延迟
    if "深海蓝藻保湿面膜" in product_name:
        return "深海蓝藻保湿面膜：核心成分为深海蓝藻提取物，富含多糖和氨基酸，能深层补水、修护肌肤屏障、舒缓敏感泛红。质地清爽不粘腻，适合所有肤质，尤其适合干燥、敏感肌。规格：25ml*5片。"
    elif "美白精华" in product_name:
        return "美白精华：核心成分是烟酰胺和VC衍生物，主要功效是提亮肤色、淡化痘印、改善暗沉。质地轻薄易吸收，适合需要均匀肤色的人群。"
    else:
        return f"产品数据库中未找到关于 '{product_name}' 的详细信息。"
# 真实查询db版本
def real_query_product_database(product_name:str) -> str:
    print(f"真实查询数据库:{product_name}")
    connection = pymysql.connect(host="127.0.0.1",
                    user="root",
                    passwd="123456", # 此处一定要使用字符串
                    database="agent_demo",
                    charset="utf8mb4"
                    )
    try:
        with connection.cursor() as cursor:
            sql = """
                SELECT description, ingredients, target_users, usage_method
                FROM product
                WHERE product_name like %s
                LIMIT 1
            """
            cursor.execute(sql, product_name)
            row = cursor.fetchone()   
            if not row:
                return f"数据库中未找到{product_name}商品"
        
            description, ingredients, target_users, usage_method = row
        # 此处为什么不返回json 因为模型识别自然语言最稳 返回json会有转义格式化的 帮倒忙
        # 可读性高 语义明确 直接生成文案
        return (
                f"{product_name} 产品信息："
                f"产品介绍：{description}；"
                f"核心成分：{ingredients}；"
                f"适合人群：{target_users}；"
                f"使用方法：{usage_method}"
            )
    

    finally:
        connection.close

def mock_generate_emoji(context: str) -> list:
    """模拟生成表情符号，根据上下文提供常用表情。"""
    print(f"[Tool Call] 模拟生成表情符号，上下文：{context}")
    time.sleep(0.2) # 模拟生成延迟
    if "补水" in context or "水润" in context or "保湿" in context:
        return ["💦", "💧", "🌊", "✨"]
    elif "惊喜" in context or "哇塞" in context or "爱了" in context:
        return ["💖", "😍", "🤩", "💯"]
    elif "熬夜" in context or "疲惫" in context:
        return ["😭", "😮‍💨", "😴", "💡"]
    elif "好物" in context or "推荐" in context:
        return ["✅", "👍", "⭐", "🛍️"]
    else: # TODO 这段随机数代码让模型解析下
        return random.sample(["✨", "🔥", "💖", "💯", "🎉", "👍", "🤩", "💧", "🌿"], k=min(5, len(context.split())))    
    

# 封装工具集 TOOLS_DEFINITION中定义的function在此处有映射关系 对应py中具体函数
available_tools = {
    "search_web":mock_search_web_result,
    #"query_product_database":mock_query_product_database,
    "query_product_database":real_query_product_database,
    "generate_emoji":mock_generate_emoji
}

# 封装原子方法 传入文案 文案类型 让模型判断是否使用工具
def generate_red_note(product_name:str, 
                      #文案的语气风格
                      tone_style:str = "活泼甜美",
                      # agent的最大尝试次数
                      max_iterations:int = 5) -> str :
    
    print("========启动小红书文案生成助手 产品:'{product_name}',文案风格:'{tone_style}'=========")
    messages = [
        {"role":"system","content":SYSTEM_PROMPT},
        {"role":"user","content":f"请为产品[{product_name}]生成一个爆款小红书文案, 文案的语气是{tone_style},包含标题,正文,至少五个标签和五个emoji表情,并且以json格式输出 例如：```json{{...}}```）"}
    ]

    iteration_count = 0
    final_response = None

    # while多几次的目的 一[多轮对话,让模型根据结果推理,发挥模型价值] 二 防死循环 
     # 1轮 模型 -> tool_calls
     # 2轮 模型 -> 看工具输出结果 -> 在推理
     # 3轮 模型 -> 输出最终json
    while iteration_count <= max_iterations:
        iteration_count+=1
        print(f"当前循环的次数{iteration_count}")
        try:
            response = client.chat.completions.create(
                messages=messages,
                model="qwen-turbo",    
                tools=TOOLS_DEFINITION,
                tool_choice="auto"
            )

            # react模式 处理工具调用
            #for choce in response.choices:
            response_message = response.choices[0].message

            # react模式 结果包含使用工具 # 模型返回tool_calls即[我还在干活] 
            if response_message.tool_calls:
                print(f"模型决定调用工具")

                # 将工具调用信息添加到历史对话中
                messages.append(response_message) # append完整而非部门response_message(模型后续推理 依赖的是自己刚说过的话)
                # 即一份可回放的对话日志 如果应用侧给拆了相当于伪造了原始内容 模型就开始胡说了

                tool_outputs = [] # 为什么是数组 因为模型一次可能返回多个工具
                for tool_call in response_message.tool_calls:
                    function_name = tool_call.function.name
                    # 确保参数是合法的JSON字符串 即使工具不要求参数 也需要传递空字典
                    # json.loads 把json字符串转成py对象 即字典(map) 
                    # json.dumps 把py对象转成json字符串
                    # py的三元运算 A if condition else B
                    function_args = json.loads(tool_call.function.arguments) if tool_call.function.arguments else {}
                    print(f"Agent Action 调用工具 {function_name},参数 {function_args}")
                    if function_name in available_tools:

                        tool_function = available_tools[function_name] # 因为available_tools是{}格式的字典 []是从字典中取元素类似map,list也可用, func()是调用函数  .取属性
                        tool_result = tool_function(**function_args) # 同上()是调用函数 **是把py中的字典对象拆成字符串
                        # 此处打印一下结果
                        print(f"tool_function的执行结果是{tool_result}")
                        # 此处为什么要拆 因为function_args模型返回的格式 -> function_args = {"query":""}
                        # mock_search_web_result({"query": "深海蓝藻保湿面膜 用户评价"}) 这么传参知报错了 需要的如下:
                        # mock_search_web_result(query="深海蓝藻保湿面膜 用户评价")
                        # *args拆list/tuple 位置参数, **kwargs 拆dict关键字
                        # args = [1, 2] kwargs = {"a": 1, "b": 2}
                        # f(*args) # f(1, 2)
                        # f(**kwargs) # f(a=1, b=2)
                        #
                        print(f"observation:工具返回结果: {tool_result}")

                        # 添加的哦啊tool_outpus
                        # TODO SPF 此处为什么知道这些key 比如 tool_call_id,role,content 在哪儿看
                        tool_outputs.append({
                            "tool_call_id" :tool_call.id,
                             "role": "tool",
                             "content": str(tool_result)
                            
                        })
                    else:    
                        error_message = f"错误: 未知工具{function_name}"
                        print(error_message)
                        tool_outputs.append(
                            {
                            "tool_call_id" :tool_call.id,
                             "role": "tool",
                             "content": str(error_message) 
                            }
                        )

        
                # 将工具执行结果添加到历史对话中
                # QA append的是追加一个 extend是追加多个
                messages.extend(tool_outputs)        
            elif response_message.content: # 如果模型直接返回文本 通常是最终答案 [模型已经干完了]
                # react模式 处理最终内容 
                print(f"模型最终返回的结果 {response_message.content}")
                # 一些正则的规则,re代表DOTALL换行啥的也能匹配
                json_string_match = re.search(r"```json\s*(\{.*\})\s*```", response_message.content, re.DOTALL)
                # 下面的if判断是否匹配到正则东西 要么是None 要么非None ,即匹配到了东西
                if json_string_match: # 
                    extracted_json_content = json_string_match.group(1)
                    try:
                        final_response = json.loads(extracted_json_content)
                        print(f"Agent解析任务完成 成功解析最终JSON文案")
                        # ensure_ascii不转义中文 indent2 格式化好看
                        return json.dumps(final_response, ensure_ascii=False, indent=2)
                        
                    except json.JSONDecodeError as e:
                        print("Agent生成了非json格式的内容 , 可能正在思考or出错了")
                        messages.append(response_message)

                

                else :
                    # 如果解析正则没有提取出json,尝试把整个文本弄成json解析
                    final_response = json.loads(response_message.content)
                    print(f"Agent解析任务完成 成功解析最终JSON文案")
                    return json.dumps(final_response, ensure_ascii=False, indent=2)

            else:
                print(f"未知情况")
                break;        

        except Exception as e:
            print(f"调用 DeepSeek API 时发生错误: {e}")
            break
    
    return "未能生成文案成功"

product_name_1 = "深海蓝藻保湿面膜"
tone_style_1 = "活泼甜美"
result_1 = generate_red_note(product_name_1, tone_style_1)

print("\n--- 生成的文案 1 ---")
print(result_1)
 
# dbResult = real_query_product_database(product_name_1)
# print(f"dbResult: {dbResult}")