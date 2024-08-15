from nonebot import on_regex
from nonebot.typing import T_State
from nonebot.adapters.onebot.v11 import GroupMessageEvent, Bot, Message

Test = on_regex(pattern=r'^测试$',priority=1)

@Test.handle()
async def Test_send(bot: Bot, event: GroupMessageEvent, state: T_State):
    msg = "Bot启动正常"
    await Test.finish(message=Message(msg))