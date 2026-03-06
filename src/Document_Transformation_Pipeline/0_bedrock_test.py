import openai

client = openai.OpenAI(
    api_key="zhRlfl1!",  # config.yaml에 설정한 master_key
    base_url="http://0.0.0.0:4000"  # litellm 프록시 주소
)

# config.yaml에 정의한 model_name 사용
response = client.chat.completions.create(
    model="bedrock-claude-4-5-sonnet", 
    messages=[
        {"role": "user", "content": "How does litellm work?"}
    ]
)

print(response.choices[0].message.content)
