import os
from dotenv import load_dotenv
from openai import OpenAI  

#load_dotenv(dotenv_path=".env", override=False)


client = OpenAI()  

models = client.models.list()

for model in models.data:
    print(model.id)
'''
response = client.responses.create( 
    model="openai.anthropic.claude-sonnet-4-5-20250929-v1:0", 
    input=[ 
        {"role": "user", "content": "Write a one-sentence bedtime story about a unicorn."} 
    ] 
)  
'''
#print(response.output_text)
