from nonebot import get_plugin_config
from nonebot.plugin import PluginMetadata

from .config import Config
from nonebot.plugin.on import on_command, on_message, on_notice, on_regex, on_keyword
from nonebot.rule import to_me, Rule
from nonebot.adapters import Bot, Event
from nonebot.adapters.onebot.v11 import Message, MessageSegment
from nonebot.plugin import on
from nonebot.typing import T_State

import random

__plugin_meta__ = PluginMetadata(
    name="Divination",
    description="",
    usage="",
    config=Config,
)

config = get_plugin_config(Config)

def contains_keyword(keyword: str):
    async def _contains_keyword(bot: Bot, event: Event, state: T_State) -> bool:
        text = str(event.get_message())
        return keyword in text
    return Rule(_contains_keyword)

divine = on_keyword({"求签"}, priority=2, block=True)

import random
import json
from typing import Dict, Optional
import os

class Divine:
    def __init__(self, signs_file: str):
        self.signs = self.load_signs(signs_file)
    def load_signs(self, filepath: str) -> Dict[int, Dict]:
        """从JSON文件加载签文数据"""
        base_dir = os.path.dirname(os.path.abspath(__file__))
        json_path = os.path.join(base_dir, filepath)
        with open(json_path, 'r', encoding='utf-8') as file:
            return {item["num"]: item for item in json.load(file)}
    def get_sign(self) -> Dict:
        """随机选择一个签文返回"""
        sign_number = random.randint(1, len(self.signs))
        return self.signs[sign_number]
    
class GuanyinDivine(Divine):
    def __init__(self, signs_file: str = 'guanyin_signs.json'):
        super().__init__(signs_file)

    def format_sign(self, sign: Dict) -> str:
        detail = sign['detail']
        response = [
            f"您的签文为：第{sign['num']}签，{detail['【吉凶】']}",
            f"【签文】{detail['【灵签诗文】']}",
            f"【宫位】{detail['【宫位】']}",
            f"【诗意】{detail['【诗意】']}",
            f"【解曰】{detail['【解曰】']}",
        ]
        return "\n".join(response)
        

guanyin_divine = GuanyinDivine()

@divine.handle()
async def handle_divine(bot: Bot, event: Event):
    at_ = f'[CQ:at,qq={event.get_user_id()}]  '
    sign = guanyin_divine.get_sign()
    reply = at_ + guanyin_divine.format_sign(sign)

    await bot.send(event=event, message=Message(reply), auto_escape=True)
    