from nonebot import on_message
from nonebot.adapters.onebot.v11 import Bot, MessageEvent, Message
from nonebot.typing import T_State
from nonebot.rule import Rule
from nonebot import logger

last_message = ""
message_cnt = 0

def repeater_check() -> Rule:
    async def _repeater_check(bot: Bot, event: MessageEvent, state: T_State) -> bool:
        global last_message, message_cnt
        
        message = str(event.get_message())
        
        logger.trace(f"REPEATER: message: {message}")

        if message == last_message:
            message_cnt += 1
        else:
            last_message = message
            message_cnt = 1
        
        logger.trace(f"REPEATER: message_cnt: {message_cnt}")
        
        if message_cnt == 3:
            # message_cnt = 0  # 不重置计数
            return True
        return False
    return Rule(_repeater_check)

repeater = on_message(repeater_check())

@repeater.handle()
async def handle(bot: Bot, event: MessageEvent):
    await repeater.send(event.get_message())
