from nonebot import get_plugin_config
from nonebot.plugin import PluginMetadata

from .config import Config

__plugin_meta__ = PluginMetadata(
    name="chat_reply",
    description="",
    usage="",
    config=Config,
)

config = get_plugin_config(Config)

from nonebot.permission import SUPERUSER
from nonebot.plugin.on import on_command, on_message, on_notice, on_regex
from nonebot.rule import to_me, Rule
from nonebot.adapters import Bot, Event
from nonebot.adapters.onebot.v11 import Message, MessageEvent, PrivateMessageEvent, MessageSegment, GroupMessageEvent
from nonebot.params import Arg, ArgPlainText, CommandArg, Matcher
from nonebot.log import logger
from nonebot.typing import T_State

import erniebot
import os
import yaml
from collections import defaultdict

chat_priority = 3

'''
erniebot配置文件：chat_config.yaml
'''

current_dir = os.path.dirname(os.path.abspath(__file__))
config_path = os.path.join(current_dir, 'chat_config.yaml')
with open(config_path, 'r', encoding='utf-8') as file:
    config = yaml.safe_load(file)
API_TYPE = config['chat']['api_type']
ACCESS_TOKEN = config['chat']['access_token']

erniebot.api_type = API_TYPE
erniebot.access_token = ACCESS_TOKEN

'''
聊天记录和启动状态
'''
chating_dict = {}   # 存储qq号是否已经开始聊天
user_sessions = defaultdict(list)   # 聊天记录

'''
大模型和prompt
'''
base_role = "猫娘"
base_prompt = f"请你扮演一个{base_role}，根据下面的聊天记录进行回复。"

async def get_model_response(text, user_id):
    global base_prompt
    global base_role
    global user_sessions

    session_text = "".join([f"{entry['role']}: {entry['content']}\n" for entry in user_sessions[user_id]])
    prompt = base_prompt + session_text + f"用户: {text}\n {base_role}:"

    response = erniebot.ChatCompletion.create(
        model='ernie-3.5',
        messages=[{'role': 'user', 'content': prompt}]
    )
    model_reply = response.get_result()

    # 更新会话历史
    user_sessions[user_id].append({"role": "user", "content": text})
    user_sessions[user_id].append({"role": "catgirl", "content": model_reply})

    return model_reply

'''
状态机
'''

# 启动聊天
chat_start = on_command("开始聊天", block=True, priority=chat_priority)
@chat_start.handle()
async def handle_start(bot: Bot, matcher: Matcher, event: MessageEvent):
    user_id = event.get_user_id()
    reply = f"[CQ:at,qq={user_id}]"
    if chating_dict.get(user_id, 0) == 1:
        reply = reply + "我们已经在聊天了呢！"
    else:
        reply = reply + "好的，我们开始聊天吧！"
    chating_dict[user_id] = 1
    await bot.send(event=event, message=Message(reply), auto_escape=True)

# 结束聊天
chat_end = on_command("结束聊天", block=True, priority=chat_priority)
@chat_end.handle()
async def handle_end(bot: Bot, matcher: Matcher, event: MessageEvent):
    global user_sessions

    user_id = event.get_user_id()
    reply = f"[CQ:at,qq={user_id}]"
    if chating_dict.get(user_id, 0) == 0:
        reply = reply + "我们没在聊天呢！"
    else:
        reply = reply + "聊天结束啦！"
        user_sessions[user_id].clear()
    chating_dict[user_id] = 0
    await bot.send(event=event, message=Message(reply), auto_escape=True)

# 聊天中
def chat_rule():
    async def _chat_rule(bot: Bot, event: Event, state: T_State) -> bool:
        user_id = event.get_user_id()
        return chating_dict.get(user_id, 0) == 1
    return Rule(_chat_rule)
chat = on_message(rule=chat_rule(), priority=chat_priority)

@chat.handle()
async def handle_chat(bot: Bot, matcher: Matcher, event: MessageEvent):
    text = str(event.get_message().extract_plain_text().strip())
    user_id = event.get_user_id()

    logger.info(f"输入艾特文字{text}")

    reply = await get_model_response(text, user_id)
    await bot.send(event=event, message=Message(f"[CQ:at,qq={user_id}] {reply}"), auto_escape=True)
