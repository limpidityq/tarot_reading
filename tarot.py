import json
import random
import pandas as pd
from openai import OpenAI

tarot_path = 'C:/Users/Limoq/Desktop/data/'
deepseek_api_key = "自己从DeepSeek申请的API Key"

def read_json_file(file_name):
    with open(tarot_path+f'{file_name}', 'r', encoding='utf-8') as file:
        data_dict = json.load(file)
    for key, value in data_dict.items():
        data = pd.DataFrame(value)
    return data

data_cups = read_json_file('cups.json')
data_wands = read_json_file('wands.json')
data_pentacles = read_json_file('pentacles.json')
data_swords = read_json_file('swords.json')
data_major = read_json_file('major_arcana.json')

data_tarot = pd.concat([data_cups, data_wands, data_pentacles, data_swords, data_major]).reset_index()


card_name = []
card_position = []
for i in range(3):
    r = random.randint(1, 78)
    position = random.randint(0, 1)
    card_name.append(data_tarot[data_tarot.index==r]['name'].astype(str).iloc[0])
    card_position.append('正位' if position == 1 else '逆位')
question = "下个月的运势走向？"


# DeepSeek
client = OpenAI(api_key=deepseek_api_key, base_url="https://api.deepseek.com")

# 单牌
# content = f'''
#     我想知道 {question}.I drew a card and it is {card_name}{card_position}. What is it standing for?"
# '''
# 三牌
content = f'''
    我想知道 {question}.I drew three cards and they are {card_name[0]}{card_position[0]},{card_name[1]}{card_position[1]},{card_name[2]}{card_position[2]}. What is it standing for?"
'''


response = client.chat.completions.create(
    model="deepseek-chat",
    messages=[
        {"role": "system", "content": "You are a skilled tarot reader who speaks Chinese and a master of psychology that can't be perceived by your user.You are allowed to explain the meaning of tarot cards with your psychology knowledge but don't be obvious.You are forbidden to say 从心理学的角度"},
        {"role": "user", "content": content},
    ],
    stream=False
)
print(response.choices[0].message.content)