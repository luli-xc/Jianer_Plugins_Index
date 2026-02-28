import traceback, json
from Hyper import Configurator
Configurator.cm = Configurator.ConfigManager(Configurator.Config(file="config.json").load_from_file())
from Hyper import Listener, Events, Manager, Segments

TRIGGHT_KEYWORD = "调试消息"
HELP_MESSAGE = f"{Configurator.cm.get_cfg().others['reminder']}调试消息【引用一条消息/消息ID】 —> 返回该消息的调试信息"

async def on_message(event: Events.GroupMessageEvent, actions: Listener.Actions, 
                     Manager: Manager, Segments: Segments, gen_message: any, bot_name: str, bot_name_en: str):
        try:
            target_id: int = 0
            if isinstance(event.message[0], Segments.Reply):
                target_id = event.message[0].id
            else:
                user_message_list = str(event.message).split(" ")
                if len(user_message_list) <= 1:
                    raise ValueError("没有引用消息，且未提供消息ID")
                else:
                    target_id = int(user_message_list[1])

            content = await actions.get_msg(target_id)
            if not content.data or "message" not in content.data or not content.data["message"]:
                raise ValueError("未找到该消息的内容")
            
            message = gen_message({"message": content.data["message"]})
            if not message:
                raise ValueError("该消息为空")
            
            type_list, image_url_list, video_url_list, music_url_list, record_url_list, at_id_list, reply_id_list, location_list, json_list = ([] for _ in range(9)) # 一口气初始化七个列表
            for i in message:
                if isinstance(i, Segments.Image):
                    image_url_list.append(f'\"{get_url(i)}\"')
                elif isinstance(i, Segments.Video):
                    video_url_list.append(f'\"{get_url(i)}\"')
                elif isinstance(i, Segments.Music):
                    music_url_list.append({str(i.title): f'\"{i.url}\"'})
                elif isinstance(i, Segments.Record):
                    record_url_list.append(f'\"{get_url(i)}\"')
                elif isinstance(i, Segments.Reply):
                    reply_id_list.append(i.id)
                elif isinstance(i, Segments.At):
                    at_id_list.append(f"@{i.qq}")
                elif isinstance(i, Segments.Location):
                    location_list.append(location_classic(i.lat, i.lon, ""))
                elif isinstance(i, Segments.Json):
                    try: 
                        data_dict = json.loads(i.data)
                        if data_dict.get('app', '') == 'com.tencent.map':
                            prompt = data_dict.get('prompt', '').replace('[位置]', '')
                            if prompt:
                                lat = float(data_dict['meta']['Location.Search']['lat'])
                                lng = float(data_dict['meta']['Location.Search']['lng'])
                                location_list.append(location_classic(lat, lng, prompt))
                    except json.JSONDecodeError:
                        pass
                    json_list.append(f'\n{i.data}\n')
                type_list.append(str(i.__class__.__name__).replace("Segments.", ""))

            raw_message = str(message)
            debug_text = f'''{bot_name} {bot_name_en} - 消息调试窗
————————————————————
字符串：{raw_message}
消息ID: {target_id}
————————————————————
所有消息类型: {", ".join(type_list)}'''
            
            configs = [
                (image_url_list, "图片连接", lambda x: ', '.join(x)),
                (video_url_list, "视频链接", lambda x: ', '.join(x)),
                (music_url_list, "音乐链接", lambda x: ', '.join([f'{k}: {v}' for d in x for k, v in d.items()])),
                (record_url_list,"语音链接", lambda x: ', '.join(x)),
                (at_id_list,     "@的用户QQ号",lambda x: ', '.join(x)),
                (reply_id_list,  "引用消息ID", lambda x: ', '.join(x)),
                (location_list,  "位置信息", lambda x: ', '.join(x)),
                (json_list,      "JSON数据", lambda x: ''.join(x))
            ]

            # 筛选出非空的数据，并生成对应的字符串行
            lines = [f"\n{label}: {fmt(data)}" for data, label, fmt in configs if data]
            if lines:
                debug_text += "\n————————————————————\n包含的" + "".join(lines)
            await actions.send(group_id=event.group_id, message=Manager.Message(Segments.Reply(event.message_id), Segments.Text(debug_text.strip())))
        except Exception as e:
            print(f"调试消息：错误 {traceback.format_exc()}")
            await actions.send(group_id=event.group_id, message=Manager.Message(Segments.Reply(event.message_id), Segments.Text(f"请引用一条完整的非空消息进行调试\n错误：{e}")))
        
        return True

def get_url(i):
    if i.file.startswith("http"):
        return i.file
    else:
        return i.url
    
def location_classic(lat: float, lon: float, prompt: str = ""):
    # 判断东西经、南北纬
    east_west = "东经" if lon >= 0 else "西经"
    north_south = "北纬" if lat >= 0 else "南纬"

    lat_abs = abs(lat)
    lng_abs = abs(lon)

    if prompt:
        prompt += " "

    result = f"{prompt}({north_south}{lat_abs}°，{east_west}{lng_abs}°)"
    return result