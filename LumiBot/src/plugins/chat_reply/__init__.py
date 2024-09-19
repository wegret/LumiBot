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


API_KEY = config['llm']['API_KEY']
MODEL_NAME = config['llm']['MODEL_NAME']
API_URL = config['llm']['API_URL']
import requests
import json

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
base_modifier = "慈爱的"
base_role = "猫娘"
base_prompt = f"请你扮演一个{base_modifier}{base_role}，根据下面的聊天记录进行回复。"
attach_prompt = f"（每次回复不要超过100字）"

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

from nonebot.log import logger

from uuid import uuid4
stream_flags = {}  # 每个用户的流标志存储

@chat.handle()
async def handle_chat(bot: Bot, matcher: Matcher, event: MessageEvent):
    global base_prompt
    global base_role
    global user_sessions
    global stream_flags

    text = str(event.get_message().extract_plain_text().strip())
    user_id = event.get_user_id()

    stream_flags[user_id] = uuid4().hex
    current_stream_flag = stream_flags[user_id]

    session_text = "".join([f"{entry['role']}: {entry['content']}\n" for entry in user_sessions[user_id]])
    prompt = base_prompt + session_text + f"用户: {text}\n {base_role}:" + attach_prompt

    response = requests.post(
        API_URL,
        headers={
            "Authorization": f"Bearer {API_KEY}",
            "Content-Type": "application/json"
        },
        data=json.dumps({
            "model": MODEL_NAME,
            "stream": True,  # 启用流式传输
            "messages": [
                {
                    "role": "user",
                    "content": prompt
                }
            ]
        }),
        stream=True  # 启用请求的流式传输
    )

    model_reply = ""

    if response.status_code == 200:
        buffer = ""
        for line in response.iter_lines(decode_unicode=True):
            if stream_flags[user_id] != current_stream_flag:
                break
            if line:
                line = line.lstrip("data: ").strip()
                logger.info(line)
                try:
                    data = json.loads(line)
                    if "choices" in data and data["choices"]:
                        delta = data["choices"][0].get("delta", {})
                        content = delta.get("content", "")
                        if content:
                            #    print(content)
                            buffer += content
                            if ("。" in content):
                                buffer = buffer.strip("\n")
                                if buffer:
                                    # print(buffer)
                                    logger.info(buffer)
                                    model_reply += buffer
                                    await bot.send(event=event,
                                                   message=Message(f"[CQ:at,qq={user_id}] {buffer}"),
                                                   auto_escape=True)
                                buffer = ""
                except json.JSONDecodeError:
                    if line.strip() == "[DONE]":
                        break
                    else:
                        print(f"无法解析的JSON数据: {line}")
        if buffer and stream_flags[user_id] == current_stream_flag :
            model_reply += buffer
            await bot.send(event=event,
                           message=Message(f"[CQ:at,qq={user_id}] {buffer}"),
                           auto_escape=True)

    else:
        await bot.send(event=event, message=Message(f"[CQ:at,qq={user_id}] 好像发生了一些错误！"), auto_escape=True)

    if model_reply:
        # 更新会话历史
        user_sessions[user_id].append({"role": "user", "content": text})
        user_sessions[user_id].append({"role": base_role, "content": model_reply})
