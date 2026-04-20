from openai import OpenAI

client = OpenAI(
    base_url="http://localhost:1234/v1",
    api_key="lm-studio"  # 这里随便填，LM Studio 不校验
)

response = client.chat.completions.create(
    model="zai-org/glm-4.7-flash",
    messages=[{"role": "user", "content": "vscode中如何设置自动保存文件 不用每次手动按control + s"}]
)
print(response.choices[0].message.content)