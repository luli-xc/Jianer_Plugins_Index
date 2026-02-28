# -*- coding: utf-8 -*-

import requests
import random
import json
from hashlib import md5
import re
import asyncio
import os

TRIGGHT_KEYWORD = "摩斯电码"
HELP_MESSAGE = "/摩斯电码 加密/解密 [内容] —> 摩斯电码加解密功能，支持中英文自动翻译\n      /摩斯电码 设置翻译 [appid] [appkey] —> 配置百度翻译API (仅Root用户)\n      /摩斯电码 查看配置 —> 查看当前翻译配置 (仅Root用户)"

# 配置文件路径
TRANSLATE_CONFIG_FILE = "baidu_translate_config.json"

# 摩斯电码字典
MORSE_CODE_DICT = {
    'A': '.-', 'B': '-...', 'C': '-.-.', 'D': '-..', 'E': '.', 'F': '..-.',
    'G': '--.', 'H': '....', 'I': '..', 'J': '.---', 'K': '-.-', 'L': '.-..',
    'M': '--', 'N': '-.', 'O': '---', 'P': '.--.', 'Q': '--.-', 'R': '.-.',
    'S': '...', 'T': '-', 'U': '..-', 'V': '...-', 'W': '.--', 'X': '-..-',
    'Y': '-.--', 'Z': '--..', '0': '-----', '1': '.----', '2': '..---',
    '3': '...--', '4': '....-', '5': '.....', '6': '-....', '7': '--...',
    '8': '---..', '9': '----.', '.': '.-.-.-', ',': '--..--', '?': '..--..',
    "'": '.----.', '!': '-.-.--', '/': '-..-.', '(': '-.--.', ')': '-.--.-',
    '&': '.-...', ':': '---...', ';': '-.-.-.', '=': '-...-', '+': '.-.-.',
    '-': '-....-', '_': '..--.-', '"': '.-..-.', '$': '...-..-', '@': '.--.-.',
    ' ': '/'
}

# 反向摩斯电码字典
REVERSE_MORSE_DICT = {v: k for k, v in MORSE_CODE_DICT.items()}

# 错误码映射表
BAIDU_ERROR_CODES = {
    '52000': '成功',
    '52001': '请求超时，请检查参数是否正确',
    '52002': '系统错误，请重试',
    '52003': '未授权用户，请检查appid是否正确或服务是否开通',
    '54000': '必填参数为空，请检查是否漏传参数',
    '54001': '签名错误，请检查签名生成方法',
    '54003': '访问频率受限，请降低调用频率',
    '54004': '账户余额不足，请前往管理控制台充值',
    '54005': '长query请求频繁，请降低发送频率',
    '58000': '客户端IP非法，请检查服务器IP设置',
    '58001': '译文语言方向不支持',
    '58002': '服务当前已关闭，请前往管理控制台开启',
    '58003': '此IP已被封禁，请勿将APPID填写到第三方软件中',
    '90107': '认证未通过或未生效',
    '20003': '请求内容存在安全风险'
}

def load_translate_config():
    """加载翻译配置"""
    if os.path.exists(TRANSLATE_CONFIG_FILE):
        try:
            with open(TRANSLATE_CONFIG_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
        except:
            return {"appid": "", "appkey": ""}
    return {"appid": "", "appkey": ""}

def save_translate_config(appid, appkey):
    """保存翻译配置"""
    config = {"appid": appid, "appkey": appkey}
    with open(TRANSLATE_CONFIG_FILE, 'w', encoding='utf-8') as f:
        json.dump(config, f, ensure_ascii=False, indent=2)
    return config

def is_root_user(user_id, ROOT_User):
    """检查用户是否为Root用户"""
    return str(user_id) in ROOT_User

async def on_message(event, actions, Manager, Segments, ROOT_User):
    message = str(event.message).strip()
    parts = message.split()
    
    # 检查是否包含触发关键词
    if len(parts) < 2:
        await actions.send(
            group_id=event.group_id,
            message=Manager.Message(Segments.Text("格式错误！请使用：/摩斯电码 加密/解密 [内容] 或 /摩斯电码 设置翻译 [appid] [appkey] (Root用户)"))
        )
        return True
    
    operation = parts[1].lower()
    user_id = event.user_id
    
    # 处理设置翻译配置 (仅Root用户)
    if operation == "设置翻译":
        if not is_root_user(user_id, ROOT_User):
            await actions.send(
                group_id=event.group_id,
                message=Manager.Message(Segments.Text("❌ 权限不足！只有Root用户可以设置翻译配置"))
            )
            return True
            
        if len(parts) < 4:
            await actions.send(
                group_id=event.group_id,
                message=Manager.Message(Segments.Text("格式错误！请使用：/摩斯电码 设置翻译 [appid] [appkey]"))
            )
            return True
        
        appid = parts[2]
        appkey = parts[3]
        
        # 验证appid和appkey格式
        if not appid.isdigit() or len(appid) < 5:
            await actions.send(
                group_id=event.group_id,
                message=Manager.Message(Segments.Text("❌ AppID格式错误，应为数字且长度合理"))
            )
            return True
        
        if len(appkey) < 10:
            await actions.send(
                group_id=event.group_id,
                message=Manager.Message(Segments.Text("❌ AppKey格式错误，长度过短"))
            )
            return True
        
        # 保存配置
        config = save_translate_config(appid, appkey)
        
        # 测试配置是否有效
        try:
            test_result = await baidu_translate("test", 'en', 'zh', config)
            await actions.send(
                group_id=event.group_id,
                message=Manager.Message(
                    Segments.Text("✅ 翻译配置设置成功！\n"),
                    Segments.Text(f"AppID: {appid}\n"),
                    Segments.Text(f"测试结果: {test_result}")
                )
            )
        except Exception as e:
            await actions.send(
                group_id=event.group_id,
                message=Manager.Message(
                    Segments.Text("⚠️ 配置已保存但测试失败\n"),
                    Segments.Text(f"AppID: {appid}\n"),
                    Segments.Text(f"错误: {str(e)}")
                )
            )
        return True
    
    # 查看当前配置 (仅Root用户)
    elif operation == "查看配置":
        if not is_root_user(user_id, ROOT_User):
            await actions.send(
                group_id=event.group_id,
                message=Manager.Message(Segments.Text("❌ 权限不足！只有Root用户可以查看翻译配置"))
            )
            return True
            
        config = load_translate_config()
        status = "✅ 已配置" if config["appid"] and config["appkey"] else "❌ 未配置"
        
        await actions.send(
            group_id=event.group_id,
            message=Manager.Message(
                Segments.Text("📋 当前翻译配置 \n"),
                Segments.Text(f"状态: {status}\n"),
                Segments.Text(f"AppID: {config['appid'] or '未设置'}\n"),
                Segments.Text(f"AppKey: {'*' * len(config['appkey']) if config['appkey'] else '未设置'}")
            )
        )
        return True
    
    # 处理加密解密操作 (所有用户可用)
    elif operation in ["加密", "解密"]:
        if len(parts) < 3:
            await actions.send(
                group_id=event.group_id,
                message=Manager.Message(Segments.Text("格式错误！请使用：/摩斯电码 加密/解密 [内容]"))
            )
            return True
        
        content = ' '.join(parts[2:])
        config = load_translate_config()
        
        if operation == "加密":
            await handle_encrypt(event, actions, Manager, Segments, content, config)
        else:
            await handle_decrypt(event, actions, Manager, Segments, content, config)
    
    else:
        await actions.send(
            group_id=event.group_id,
            message=Manager.Message(Segments.Text("操作错误！请使用：/摩斯电码 加密/解密 [内容] 或 /摩斯电码 设置翻译 [appid] [appkey] (Root用户)"))
        )
    
    return True

async def handle_encrypt(event, actions, Manager, Segments, content, config):
    """处理加密操作"""
    # 判断是否为中文
    if is_chinese(content):
        # 检查翻译配置
        if not config["appid"] or not config["appkey"]:
            await actions.send(
                group_id=event.group_id,
                message=Manager.Message(
                    Segments.Text("❌ 翻译功能未配置\n"),
                    Segments.Text("中文加密需要翻译功能支持\n"),
                    Segments.Text("请联系Root用户使用: /摩斯电码 设置翻译 [appid] [appkey]\n"),
                    Segments.Text("或直接输入英文进行加密")
                )
            )
            return
        
        # 使用百度翻译API将中文翻译成英文
        try:
            translated = await baidu_translate(content, 'zh', 'en', config)
            morse_result = text_to_morse(translated.upper())
            await actions.send(
                group_id=event.group_id,
                message=Manager.Message(
                    Segments.Text(f"🔒 加密结果\n"),
                    Segments.Text(f"原文: {content}\n"),
                    Segments.Text(f"翻译: {translated}\n"),
                    Segments.Text(f"摩斯电码: {morse_result}")
                )
            )
        except Exception as e:
            await actions.send(
                group_id=event.group_id,
                message=Manager.Message(
                    Segments.Text(f"❌ 加密失败\n"),
                    Segments.Text(f"错误: {str(e)}")
                )
            )
    else:
        # 直接加密英文
        morse_result = text_to_morse(content.upper())
        await actions.send(
            group_id=event.group_id,
            message=Manager.Message(
                Segments.Text(f"🔒 加密结果\n"),
                Segments.Text(f"原文: {content}\n"),
                Segments.Text(f"摩斯电码: {morse_result}")
            )
        )

async def handle_decrypt(event, actions, Manager, Segments, content, config):
    """处理解密操作"""
    morse_text = content
    try:
        text_result = morse_to_text(morse_text)
        
        # 检查解密结果是否为英文
        if is_english(text_result):
            # 检查翻译配置
            if not config["appid"] or not config["appkey"]:
                await actions.send(
                    group_id=event.group_id,
                    message=Manager.Message(
                        Segments.Text(f"🔓 解密结果 (翻译未配置)\n"),
                        Segments.Text(f"摩斯电码: {morse_text}\n"),
                        Segments.Text(f"解密: {text_result}\n"),
                        Segments.Text("英文解密需要翻译功能支持，请联系Root用户配置")
                    )
                )
                return
            
            # 使用百度翻译API将英文翻译成中文
            try:
                translated = await baidu_translate(text_result, 'en', 'zh', config)
                await actions.send(
                    group_id=event.group_id,
                    message=Manager.Message(
                        Segments.Text(f"🔓 解密结果\n"),
                        Segments.Text(f"摩斯电码: {morse_text}\n"),
                        Segments.Text(f"解密: {text_result}\n"),
                        Segments.Text(f"翻译: {translated}")
                    )
                )
            except Exception as e:
                await actions.send(
                    group_id=event.group_id,
                    message=Manager.Message(
                        Segments.Text(f"🔓 解密结果 (翻译失败)\n"),
                        Segments.Text(f"摩斯电码: {morse_text}\n"),
                        Segments.Text(f"解密: {text_result}\n"),
                        Segments.Text(f"翻译错误: {str(e)}")
                    )
                )
        else:
            await actions.send(
                group_id=event.group_id,
                message=Manager.Message(
                    Segments.Text(f"🔓 解密结果\n"),
                    Segments.Text(f"摩斯电码: {morse_text}\n"),
                    Segments.Text(f"解密: {text_result}")
                )
            )
    except ValueError as e:
        await actions.send(
            group_id=event.group_id,
            message=Manager.Message(
                Segments.Text(f"❌ 解密失败\n"),
                Segments.Text(f"错误: {str(e)}")
            )
        )

def text_to_morse(text):
    """将文本转换为摩斯电码"""
    morse = []
    for char in text.upper():
        if char in MORSE_CODE_DICT:
            morse.append(MORSE_CODE_DICT[char])
        else:
            morse.append('?')  # 未知字符用问号表示
    return ' '.join(morse)

def morse_to_text(morse_code):
    """将摩斯电码转换为文本"""
    # 清理输入，去除多余的空格
    morse_code = re.sub(r'\s+', ' ', morse_code.strip())
    
    words = morse_code.split(' / ')  # 分割单词
    text = []
    for word in words:
        chars = word.split()
        for char in chars:
            if char in REVERSE_MORSE_DICT:
                text.append(REVERSE_MORSE_DICT[char])
            else:
                raise ValueError(f"无效的摩斯电码: {char}")
        text.append(' ')  # 单词间添加空格
    result = ''.join(text).strip()
    
    if not result or result.isspace():
        raise ValueError("解密结果为空，请检查摩斯电码格式")
    
    return result

def is_chinese(text):
    """检查文本是否包含中文字符"""
    return any('\u4e00' <= char <= '\u9fff' for char in text)

def is_english(text):
    """检查文本是否为英文"""
    # 简单检查：如果文本主要由字母和空格组成，则认为是英文
    english_chars = sum(1 for c in text if c.isalpha() or c.isspace() or c in ".,!?;:'\"-")
    return english_chars / max(len(text), 1) > 0.7  # 70%以上是英文字符

def make_md5(s, encoding='utf-8'):
    """生成MD5哈希值"""
    return md5(s.encode(encoding)).hexdigest()

async def baidu_translate(query, from_lang, to_lang, config=None):
    """使用百度翻译API进行翻译"""
    if config is None:
        config = load_translate_config()
    
    if not config["appid"] or not config["appkey"]:
        raise Exception("百度翻译API未配置，请联系Root用户使用 /摩斯电码 设置翻译 [appid] [appkey]")
    
    if not query or query.isspace():
        raise Exception("翻译内容不能为空")
    
    # 限制翻译文本长度
    if len(query) > 700:
        raise Exception("翻译文本过长，请控制在700字符以内")
    
    # 生成salt和sign
    salt = random.randint(32768, 65536)
    sign = make_md5(config["appid"] + query + str(salt) + config["appkey"])
    
    # 构建请求
    headers = {'Content-Type': 'application/x-www-form-urlencoded'}
    payload = {
        'appid': config["appid"], 
        'q': query, 
        'from': from_lang, 
        'to': to_lang, 
        'salt': salt, 
        'sign': sign
    }
    
    try:
        # 发送请求，设置超时时间
        response = await asyncio.get_event_loop().run_in_executor(
            None, 
            lambda: requests.post('http://api.fanyi.baidu.com/api/trans/vip/translate', 
                                params=payload, headers=headers, timeout=10)
        )
        
        result = response.json()
        
        # 检查是否有错误
        if 'error_code' in result:
            error_code = str(result['error_code'])
            error_msg = BAIDU_ERROR_CODES.get(error_code, f"未知错误: {error_code}")
            raise Exception(f"翻译API错误 ({error_code}): {error_msg}")
        
        # 提取翻译结果
        if 'trans_result' not in result or not result['trans_result']:
            raise Exception("翻译API返回结果异常")
        
        translated_text = ' '.join([item['dst'] for item in result['trans_result']])
        return translated_text
        
    except requests.exceptions.Timeout:
        raise Exception("翻译请求超时，请稍后重试")
    except requests.exceptions.ConnectionError:
        raise Exception("网络连接错误，请检查网络连接")
    except requests.exceptions.RequestException as e:
        raise Exception(f"网络请求异常: {str(e)}")
    except json.JSONDecodeError:
        raise Exception("翻译API返回数据格式错误")
    except Exception as e:
        raise Exception(f"翻译过程中发生未知错误: {str(e)}")
