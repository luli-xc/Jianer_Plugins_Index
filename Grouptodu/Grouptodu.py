import asyncio
import re
from Hyper import Configurator, Events

TRIGGHT_KEYWORD = "Any"
HELP_MESSAGE = f'''群待办 —> 回复”群待办“以快捷设置群待办'''

#！！！机器人要有管理员权限才行，否则设置不了群待办！！！

# 白名单开关：True=启用白名单，False=禁用白名单（所有群都可以使用）
WHITE_LIST_ENABLED = False

# 白名单，只有在白名单中的群聊才会响应
WHITE_LIST = [
    "114514",
    "350234"
]


async def on_message(event, actions, Manager, Events: Events, Segments, reminder):
    # 只处理群消息
    if not isinstance(event, Events.GroupMessageEvent):
        return None
    
    # 白名单检查：只有白名单中的群聊才会响应（如果启用白名单）
    if WHITE_LIST_ENABLED and str(event.group_id) not in WHITE_LIST:
        return None
    
    msg = str(event.message)
    
    # 检查是否是群待办命令
    if "群待办" in msg:
        # 检查是否回复了消息
        if isinstance(event.message[0], Segments.Reply):
            try:
                # 设置群待办
                await actions.custom.set_group_todo(
                    group_id=event.group_id,
                    message_id=event.message[0].id
                )
                
                # 发送成功提示
                await actions.send(
                    group_id=event.group_id,
                    message=Manager.Message(
                        Segments.Reply(event.message_id),
                        Segments.Text("✅ 已将此消息设为群待办啦")
                    )
                )
                return True
                
            except Exception as e:
                # 发送错误提示
                await actions.send(
                    group_id=event.group_id,
                    message=Manager.Message(
                        Segments.Reply(event.message_id),
                        Segments.Text(f"❌ 设置群待办失败：{str(e)}")
                    )
                )
                return True
        else:
            # 提示用户需要回复消息
            await actions.send(
                group_id=event.group_id,
                message=Manager.Message(
                    Segments.Reply(event.message_id),
                    Segments.Text("⚠️ 请回复一条消息后发送'群待办'命令")
                )
            )
            return True        
