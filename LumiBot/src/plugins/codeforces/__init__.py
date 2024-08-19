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

'''
查询在线好友
'''

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

from nonebot.plugin.on import on_command
from nonebot.adapters import Bot, Event
from nonebot.adapters.onebot.v11 import Message, MessageEvent, PrivateMessageEvent, MessageSegment, GroupMessageEvent
from nonebot.permission import SUPERUSER

ask_online = on_command("cf在线好友", block=True)
@ask_online.handle()
async def handle_ask_online(bot: Bot, event: MessageEvent):
    online_friends = get_online_friends(api_key, secret)
    reply = "【CF在线好友】\n"
    for friend in online_friends:
        reply = reply + f"  {friend}\n"
    await bot.send(event=event, message=Message(reply), auto_escape=True)

'''
查询近期比赛
'''
def get_contests_before(gym=False):
    response = requests.get("https://codeforces.com/api/contest.list", params={"gym": str(gym).lower()})
    if response.status_code == 200:
        data = response.json()
        if data['status'] == 'OK':
            contests_before = [contest for contest in data['result'] if contest['phase'] == 'BEFORE']
            return contests_before
        else:
            return data['comment']
    else:
        return f"HTTP Error {response.status_code}"

from datetime import datetime, timedelta, timezone
def convert_to_beijing_time(unix_timestamp):
    utc_time = datetime.utcfromtimestamp(unix_timestamp)
    beijing_time = utc_time + timedelta(hours=8)
    return beijing_time.strftime('%Y-%m-%d %H:%M:%S')


def display_contests(contests):
    for contest in contests:
        beijing_start_time = convert_to_beijing_time(contest['startTimeSeconds'])
        print(f"比赛ID: {contest['id']}, 名称: {contest['name']}, 开始时间 (北京时间): {beijing_start_time}")

ask_contest = on_command("cf近期比赛", block=True)
@ask_contest.handle()
async def handle_ask_contest(bot: Bot, event: MessageEvent):
    contests = get_contests_before()
    reply = "【CF近期比赛】\n"
    for contest in contests:
        beijing_start_time = convert_to_beijing_time(contest['startTimeSeconds'])
        reply = reply + f"{contest['name']}, {beijing_start_time}\n"
    await bot.send(event=event, message=Message(reply), auto_escape=True)

'''
比赛提醒
'''

from nonebot.log import logger

reminder_group = []     # 订阅提醒的群聊
reminder_user = []      # 订阅提醒的用户

reminder_start = on_command("cf比赛提醒开启", block=True)
@reminder_start.handle()
async def handle_reminder_start(bot: Bot, event: MessageEvent):
    logger.info("提醒！")
    if isinstance(event, GroupMessageEvent):
        if event.group_id not in reminder_group:
            reminder_group.append(event.group_id)
            await bot.send(event=event, message="群聊比赛提醒已开启！")
        else:
            await bot.send(event=event, message="本群已经开启了比赛提醒！")
    elif isinstance(event, PrivateMessageEvent):
        user_id = event.get_user_id()
        if user_id not in reminder_user:
            reminder_user.append(user_id)
            await bot.send(event=event, message="私聊比赛提醒已开启！")
        else:
            await bot.send(event=event, message="你已经开启了比赛提醒！")

reminder_end = on_command("cf比赛提醒关闭", block=True)
@reminder_end.handle()
async def handle_reminder_end(bot: Bot, event: MessageEvent):
    if isinstance(event, GroupMessageEvent):
        if event.group_id in reminder_group:
            reminder_group.remove(event.group_id)
            await bot.send(event=event, message="群聊比赛提醒已关闭！")
        else:
            await bot.send(event=event, message="本群没有开启比赛提醒！")
    elif isinstance(event, PrivateMessageEvent):
        user_id = event.get_user_id()
        if user_id in reminder_user:
            reminder_user.remove(user_id)
            await bot.send(event=event, message="私聊比赛提醒已关闭！")
        else:
            await bot.send(event=event, message="你没有开启比赛提醒！")

'''
数据库
'''

from nonebot import get_bots
from nonebot_plugin_orm import async_scoped_session, get_session
import requests
import sqlalchemy
from datetime import datetime
from sqlalchemy.future import select

from nonebot import require
require("nonebot_plugin_apscheduler")
from nonebot_plugin_apscheduler import scheduler

from nonebot_plugin_orm import Model
from sqlalchemy.orm import Mapped, mapped_column
import sqlalchemy.types as types

from sqlalchemy import Column, Integer, String, DateTime
from nonebot_plugin_orm import Model

class Contest(Model):
    id = Column(Integer, primary_key=True)
    name = Column(String)
    type = Column(String)
    status = Column(String)
    start_time = Column(DateTime)
    end_time = Column(DateTime)


# 获取新比赛
async def get_contests_before_new(gym=False):
    response = requests.get("https://codeforces.com/api/contest.list", params={"gym": str(gym).lower()})
    new_contests = []
    if response.status_code == 200:
        data = response.json()
        if data['status'] == 'OK':
            session = get_session()
            async with session() as s:
                result = await s.execute(select(Contest.id))
                existing_ids = {id[0] for id in result.scalars().all()}
                for contest in data['result']:
                    if contest['phase'] == 'BEFORE' and contest['id'] not in existing_ids:
                        new_contest = Contest(
                            id=contest['id'],
                            name=contest['name'],
                            type='CF',
                            status=contest['phase'],
                            start_time=datetime.fromtimestamp(contest['startTimeSeconds']),
                            end_time=datetime.fromtimestamp(contest['startTimeSeconds'] + contest['durationSeconds'])
                        )
                        s.add(new_contest)
                        new_contests.append(new_contest)
                await s.commit()
        else:
            print("Error fetching contests: ", data['comment'])
    else:
        print("HTTP Error: ", response.status_code)
    return new_contests

# 通知用户新的比赛信息
async def notify_users(contests):
    message = "\n".join(f"新比赛: {contest.name} - 开始时间: {contest.start_time.strftime('%Y-%m-%d %H:%M:%S')}" for contest in contests)
    bots = get_bots()
    if bots:
        for bot in bots.values():
            for group in reminder_group:
                await bot.send_group_msg(group_id=group, message=message)
            for user in reminder_user:
                await bot.send_private_msg(user_id=user, message=message)

# 设置定时任务，每2个小时执行一次检查
@scheduler.scheduled_job("cron", hour="*/2", id="job_0")
async def routine_contest_check():
    logger.info("检查比赛...")
    contests = await get_contests_before_new()
    if contests:
        logger.info("有新的比赛")
        await notify_users(contests)
    else:
        logger.info("没有新的比赛")
