from nonebot import get_plugin_config
from nonebot.plugin import PluginMetadata

from .config import Config

__plugin_meta__ = PluginMetadata(
    name="checkin_xmu",
    description="",
    usage="",
    config=Config,
)

config = get_plugin_config(Config)

import json
import requests
import sys
import time
import random
import os

current_script_path = os.path.abspath(__file__)
current_dir = os.path.dirname(current_script_path)
json_path = os.path.join(current_dir, "userInfo.json")

try:
    with open(json_path, "r", encoding="utf-8") as file:
        userInfo = json.load(file)
except FileNotFoundError:
    print("未找到文件。请确保文件名正确，并位于正确的目录下。")
except json.JSONDecodeError:
    print("文件不是有效的 JSON 格式。")

http_header = {
    "Host": "tingke.xmu.edu.cn",
    "Content-Type": "application/x-www-form-urlencoded",
    "Accept-Encoding": "gzip, deflate, br",
    "Connection": "keep-alive",
    "Accept": "*/*",
    "User-Agent": "Mozilla/5.0 (iPhone; CPU iPhone OS 11_3 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Mobile/15E217 MicroMessenger/6.8.0(0x16080000) NetType/WIFI Language/en Branch/Br_trunk MiniProgramEnv/Mac",
    "Content-Length": "126",
    "Referer": "https://servicewechat.com/wx4890ebb3c7b628d9/98/page-frame.html",
    "Accept-Language": "zh-CN,zh-Hans;q=0.9"
}
session = requests.Session()
serverUrl = "https://tingke.xmu.edu.cn/app"

def getCheckinInfo(session, http_header, userInfo, lesson):
    try:
        url = serverUrl + "/getXsQdInfo"
        data = {
            'sign': userInfo['sign'],
            'unitCode': userInfo['unitCode'],
            'userCode': userInfo['userCode'],
            'userName': userInfo['userName'],
            'xkKh': lesson['xkKh'],
            'qdRq': lesson['qdRq'],
            'xqj': lesson['xqj'],
            'djj': lesson['djj'],
            'djz': lesson['djz'],
            'qdId': lesson['qdId'],
            'isFz': lesson['isFz'],
            'fzMc': lesson['fzMc']
        }
        res = session.post(url, data=data, headers=http_header)
        if res.status_code != 200:
            raise Exception('get Checkin info failed')
        res = json.loads(res.text)
        return res['Rows']
    except:
        print(json.dumps({
            "status": "failed",
            "reason": "Get checkin info failed"
        }, indent=4))
        raise

def checkin(session, http_header, userInfo, lesson, tips=True):
    checkinInfo = getCheckinInfo(session, http_header, userInfo, lesson)
    return checkinInfo['klHm']

def getCheckinList(session, http_header, userInfo, today=True):
    try:
        url = serverUrl + "/getQdKbList"
        data = {
            'sign': userInfo['sign'],
            'userType': userInfo['userType'],
            'userCode': userInfo['userCode'],
            'unitCode': userInfo['unitCode'],
            'userName': userInfo['userName'],
            'roleCode': userInfo['roleCode'],
            'bm': None,
            'xyMc': userInfo['xy'],
            'zy': userInfo['zy'],
            'bj': userInfo['bj'],
            'xsCc': userInfo['xsCc'],
            'scene': 1,
            'key': 1 if today else 2
        }
        res = session.post(url, data=data, headers=http_header).text
        res = json.loads(res)
        if res['status'] != 1:
            print('get Checkin list failed')
            raise Exception('get Checkin list failed')
        # print(res)
        return res['Rows']

    except:
        print(json.dumps({
            "status": "failed",
            "reason": "Get checkin list failed"
        }, indent=4))
        raise

def searchCheckinList(session, http_header, userInfo, today=True, type="签到"):
    rows = getCheckinList(session, http_header, userInfo, today)
    for id, lesson in enumerate(rows):
        if lesson['qdQkMc'] == "签到中":
            code = checkin(session, http_header, userInfo, rows[id])
            text = [
                f"【{id}】",
                f"课程名称：{lesson['kcMc']}",
                f"上课时间：{lesson['skSj']}",
                f"签到发起情况：{lesson['qdQkMc']}",
                f"签到码：{code}"
            ]
            return "\n".join(text)
    return "没有课程正在签到！"

from nonebot.permission import SUPERUSER
from nonebot.plugin.on import on_command, on_message, on_notice, on_regex
from nonebot.rule import to_me, Rule
from nonebot.adapters import Bot, Event
from nonebot.adapters.onebot.v11 import Message, MessageEvent, PrivateMessageEvent, MessageSegment, GroupMessageEvent
from nonebot.params import Arg, ArgPlainText, CommandArg, Matcher
from nonebot.log import logger
from nonebot.typing import T_State

checkin_code = on_command("签到码", block=True)
@checkin_code.handle()
async def handle_checkin_code(bot: Bot, matcher: Matcher, event: MessageEvent):
    user_id = event.get_user_id()
    reply = f"[CQ:at,qq={user_id}]"
    reply = reply + searchCheckinList(session, http_header, userInfo)
    await bot.send(event=event, message=Message(reply), auto_escape=True)