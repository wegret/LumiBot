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

current_dir = os.path.dirname(os.path.abspath(__file__))
config_path = os.path.join(current_dir, 'chat_config.yaml')
with open(config_path, 'r', encoding='utf-8') as file:
    config = yaml.safe_load(file)
API_TYPE = config['chat']['api_type']
ACCESS_TOKEN = config['chat']['access_token']

erniebot.api_type = API_TYPE
erniebot.access_token = ACCESS_TOKEN

def contains_keyword(keyword: str):
    async def _contains_keyword(bot: Bot, event: Event, state: T_State) -> bool:
        text = str(event.get_message())
        logger.info(f"消息：{text} 结果：{keyword in text}")
        return keyword in text
    return Rule(_contains_keyword)

chat = on_message(rule=to_me() & contains_keyword("你好"))

chating_dict = {}   # 存储qq号是否已经开始聊天
def is_chating(user_id):
    if user_id in chating_dict and chating_dict[user_id] == 1:
        return True
    else:
        chating_dict[user_id] = 0
        return False

from collections import defaultdict
user_sessions = defaultdict(list)

base_role = "猫娘"
base_prompt = f"请你扮演一个{base_role}，根据下面的聊天记录进行回复。"

async def get_model_response(text, user_id):
    global base_prompt
    global user_sessions

    session_text = "".join([f"{entry['role']}: {entry['content']}\n" for entry in user_sessions[user_id]])
    prompt = base_prompt + session_text + f"用户: {text}\n猫娘:"

    response = erniebot.ChatCompletion.create(
        model='ernie-3.5',
        messages=[{'role': 'user', 'content': prompt}]
    )
    model_reply = response.get_result()

    # 更新会话历史
    user_sessions[user_id].append({"role": "user", "content": text})
    user_sessions[user_id].append({"role": "catgirl", "content": model_reply})

    return model_reply


@chat.handle()
async def handle_chat(bot: Bot, matcher: Matcher, event: MessageEvent):
    text = str(event.get_message().extract_plain_text().strip())
    user_id = event.get_user_id()

    logger.info(f"输入艾特文字{text}")

    if is_chating(user_id):
        reply = await get_model_response(text, user_id)
        await bot.send(event=event, message=Message(f"[CQ:at,qq={user_id}] {reply}"), auto_escape=True)
    elif "开始聊天" in text:
        chating_dict[user_id] = 1
        await bot.send(event=event, message=Message(f"[CQ:at,qq={user_id}] 好的，我们开始聊天吧！"), auto_escape=True)
    elif "结束聊天" in text:
        chating_dict[user_id] = 0
        await bot.send(event=event, message=Message(f"[CQ:at,qq={user_id}] 聊天结束啦！"), auto_escape=True)
