# 原 fch：在群聊内管理员撤回群成员消息时发送日志的组件
import asyncio
from typing import Tuple, Optional
from Hyper import Configurator, Events,Segments,Manager
from Tools.websocket_message import ws_custom_api
Configurator.cm = Configurator.ConfigManager(Configurator.Config(file="config.json").load_from_file())
from datetime import datetime
TRIGGHT_KEYWORD = "Any"
async def on_message(event, actions,ROOT_User):
    if isinstance(event, Events.GroupRecallEvent):
        if not str(event.user_id) == str(event.operator_id):
            print(f"检测到群{event.group_id}内用户{event.user_id}的消息{event.message_id}被{event.operator_id}撤回")
            try:
                msg_info = await ws_custom_api("get_msg",{"message_id":f"{event.message_id}"})
                nickname_origin = await ws_custom_api("get_stranger_info",{"user_id":f"{event.operator_id}","no_cache":True})
                nickname = nickname_origin.get('data', {}).get("nickname", "未知用户")
                nicknameshz_origin = await ws_custom_api("get_stranger_info",{"user_id":f"{event.user_id}","no_cache":True})
                nicknameshz = nicknameshz_origin.get('data', {}).get("nickname", "未知用户")
                group_info = await ws_custom_api("get_group_info",{"group_id":f"{event.group_id}","no_cache":True})
                group_name = group_info.get('data', {}).get('group_name', '未知群组')
                chehuitime = datetime.fromtimestamp(int(event.time))
                notice_message = Manager.Message(
                    Segments.Image(f"https://p.qlogo.cn/gh/{event.group_id}/{event.group_id}/100/"),
                    Segments.Text(f"通知({event.message_id}) - 群聊撤回\n"),
                    Segments.Text(f"撤回群名: {group_name}\n"),
                    Segments.Text(f"撤回群号: {event.group_id}\n"),
                    Segments.Text(f"撤回人员: {event.operator_id}({nickname})\n"),
                    Segments.Text(f"被撤回人员: {event.user_id}({nicknameshz})\n"),
                    Segments.Text(f"撤回时间: {chehuitime.strftime('%Y.%m.%d %H:%M:%S')}")
                )
                await actions.send(user_id=ROOT_User[0], message=notice_message)
            except Exception as e:
                import traceback
                traceback.print_exc()
                print(f"处理撤回消息时出错: {str(e)}")
