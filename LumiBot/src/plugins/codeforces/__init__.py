from nonebot import get_plugin_config
from nonebot.plugin import PluginMetadata

from .config import Config

__plugin_meta__ = PluginMetadata(
    name="codeforces",
    description="",
    usage="",
    config=Config,
)

config = get_plugin_config(Config)

'''
Codeforces API 配置
'''

import os
import yaml
import requests
import hashlib
import time

current_dir = os.path.dirname(os.path.abspath(__file__))
config_path = os.path.join(current_dir, 'cf_config.yaml')
with open(config_path, 'r', encoding='utf-8') as file:
    config = yaml.safe_load(file)
api_key = config['codeforces']['api_key']
secret = config['codeforces']['secret']

def generate_api_signature(rand, method_name, params, secret):
    param_str = '&'.join(f"{k}={v}" for k, v in sorted(params.items()))
    sig_str = f"{rand}/{method_name}?{param_str}#{secret}"
    return hashlib.sha512(sig_str.encode()).hexdigest()

def get_online_friends(api_key, secret):
    method_name = "user.friends"
    rand = "123abc"
    current_time = int(time.time())
    params = {
        "apiKey": api_key,
        "onlyOnline": "true",
        "time": str(current_time)
    }
    api_sig = generate_api_signature(rand, method_name, params, secret)
    api_sig_full = rand + api_sig
    params["apiSig"] = api_sig_full

    url = f"https://codeforces.com/api/{method_name}"
    response = requests.get(url, params=params)

    if response.status_code == 200:
        data = response.json()
        if data['status'] == 'OK':
            return data['result']  # 返回在线好友列表
        else:
            return data['comment']  # 返回失败原因
    else:
        return f"HTTP Error {response.status_code}"

'''
查询在线好友
'''
from nonebot.plugin.on import on_command
from nonebot.adapters import Bot, Event
from nonebot.adapters.onebot.v11 import Message, MessageEvent, PrivateMessageEvent, MessageSegment, GroupMessageEvent
from nonebot.permission import SUPERUSER

ask_online = on_command("cf在线好友", block=True)
@ask_online.handle()
async def handle_ask_online(bot: Bot, event: MessageEvent):
    online_friends = get_online_friends(api_key, secret)
    reply = "查询在线好友：\n"
    for friend in online_friends:
        reply = reply + f"  {friend}\n"
    await bot.send(event=event, message=Message(reply), auto_escape=True)
    