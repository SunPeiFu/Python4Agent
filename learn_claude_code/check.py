from openai import OpenAI
import json

api_key = "sk-qFvDkFk22zpWFpVWLGjHtBXwIH1wekq11pZNzLz0e582pl0v"
base_url = "https://api.lotte-library.top/v1"
model_id = "glm-4.7"

client = OpenAI(api_key=api_key, base_url=base_url)

print("🔍 开始协议验证测试...")
print(f"📡 目标地址: {base_url}")
print("-" * 40)

# 1️⃣ 测试 Chat Completions（99% 兼容 API 支持）
try:
    r1 = client.chat.completions.create(
        model=model_id,
        messages=[{"role": "user", "content": "Reply 'OK'"}]
    )
    print("✅ [Chat Completions] 请求成功")
    print(f"   返回对象类型: {type(r1).__name__}")
    print(f"   是否有 .choices 属性: {hasattr(r1, 'choices')}")
    print(f"   原始 JSON 键名示例: {list(r1.model_dump().keys())}")
except Exception as e:
    print(f"❌ [Chat Completions] 失败: {e}")

print("-" * 40)

# 2️⃣ 测试 Responses API（仅 OpenAI 官方/极少数厂商支持）
try:
    r2 = client.responses.create(
        model=model_id,
        input="Reply 'OK'"
    )
    print("✅ [Responses API] 请求成功（罕见）")
    print(f"   返回对象类型: {type(r2).__name__}")
    print(f"   是否有 .output 属性: {hasattr(r2, 'output')}")
except Exception as e:
    print(f"❌ [Responses API] 失败（预期结果）: {e}")

print("-" * 40)
