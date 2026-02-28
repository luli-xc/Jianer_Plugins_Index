import os
import glob
import json
import math
from collections import Counter
from Hyper import Configurator
from Tools.deepseek import dsr114
Configurator.cm = Configurator.ConfigManager(Configurator.Config(file="config.json").load_from_file())

# 加载配置
def load_config():
    config_path = os.path.join(os.path.dirname(__file__), 'knowledge_config.json')
    with open(config_path, 'r', encoding='utf-8') as f:
        return json.load(f)

CONFIG = load_config()

TRIGGHT_KEYWORD = "Any"
# HELP_MESSAGE = f"""

# 用于存储用户上下文
user_lists = {}

async def on_message(event, actions, Manager, Segments):
    if not hasattr(event, 'message'):
        return False
        
    user_input = str(event.message).strip() # 用户输入的消息
    
    # 检查用户是否在询问与本应用相关的问题
    if not is_asking_about_app(user_input):
        return False
    
    # 检查并创建知识库文件夹
    knowledge_dir = "data/knowledge"
    if not os.path.exists(knowledge_dir):
        os.makedirs(knowledge_dir)
    
    # 检查知识库文件夹是否为空
    if not os.listdir(knowledge_dir):
        print("提醒：知识库文件夹为空，请在 data/knowledge 文件夹下放置 markdown 格式的 .md 文档当作知识库")
        return False
    
    # 检索知识库中的相关信息
    relevant_info = search_knowledge_base(knowledge_dir, user_input)
    
    # 如果没有检索到相关知识，则不回复
    if not relevant_info:
        print(f"未检索到与用户输入相关的知识：{user_input}")
        return False
    
    # 结合DeepSeek生成回复
    reply = await generate_reply_with_deepseek(user_input, relevant_info, event.user_id)
    
    # 发送回复给用户
    await actions.send(group_id=event.group_id, message=Manager.Message(Segments.Reply(event.message_id), 
                                                                        Segments.At(event.user_id), 
                                                                        Segments.Text(f" {reply.strip()}")))

    return True

def is_asking_about_app(user_input):
    """判断用户输入是否与本应用相关的问题"""
    # 从配置中获取关键词
    app_keywords = CONFIG['keywords']['main']
    
    # 从配置中获取疑问词
    question_words = CONFIG['question_words']
    
    # 检查是否包含应用相关关键词
    contains_app = any(keyword in user_input for keyword in app_keywords)
    
    # 检查是否包含疑问词
    contains_question = any(qw in user_input for qw in question_words)
    
    # 检查是否以疑问词开头
    starts_with_question = user_input.startswith(tuple(question_words))
    
    # 检查是否以问号结尾
    ends_with_question_mark = user_input.strip().endswith(('?', '？'))
    
    # 检查是否包含助动词（表明可能在询问能力、可能性）
    modal_verbs = CONFIG['modal_verbs']
    contains_modal = any(modal in user_input for modal in modal_verbs)
    
    # 检查是否包含动作词
    action_verbs = CONFIG['action_verbs']
    contains_action = any(action in user_input for action in action_verbs)
    
    # 检查是否包含特定问题模式
    question_patterns = CONFIG['question_patterns']
    contains_pattern = any(pattern in user_input for pattern in question_patterns)
    
    # 判断是否为疑问句（综合考虑多种因素）
    is_question = contains_question or starts_with_question or ends_with_question_mark or contains_modal
    
    # 提高判断准确性：确保用户确实是在问问题而不是简单提及
    # 检查文本长度
    text_length = len(user_input.strip())
    
    # 检查是否只是简单称呼或感叹
    simple_expressions = CONFIG['simple_expressions']
    is_simple_expression = user_input in simple_expressions
    
    # 检查是否包含否定词（可能是负面评价而非询问）
    negation_words = CONFIG['negation_words']
    contains_negation = any(neg in user_input for neg in negation_words)
    
    # 综合判断：必须包含应用关键词，是疑问句或包含动词，且不是简单称呼
    return (
        contains_app 
        and (is_question or contains_action or contains_pattern) 
        and not is_simple_expression 
        and text_length > CONFIG['min_text_length']  # 从配置中获取最小长度要求
    )

def chinese_tokenize(text):
    """中文分词函数（简单实现）"""
    # 转换为小写
    text = text.lower()
    
    # 从配置中获取标点符号
    punctuation = CONFIG['punctuation']
    for p in punctuation:
        text = text.replace(p, " ")
    
    # 简单分词
    words = []
    current_word = ""
    
    for char in text:
        if char.isalnum() or char == '_':
            current_word += char
        else:
            if current_word:
                words.append(current_word)
                current_word = ""
            if char.strip():
                words.append(char)
    
    if current_word:
        words.append(current_word)
    
    return words

def extract_phrases(text):
    """提取文本中的短语和专有名词"""
    # 转换为小写
    text = text.lower()
    
    # 从配置中获取标点符号
    punctuation = CONFIG['punctuation']
    for p in punctuation:
        text = text.replace(p, " ")
    
    # 提取可能的短语（连续的汉字或字母数字组合）
    phrases = []
    current_phrase = ""
    
    for char in text:
        if char.isalnum() or char == '_':
            current_phrase += char
        else:
            if current_phrase and len(current_phrase) > 1:
                phrases.append(current_phrase)
                current_phrase = ""
    
    if current_phrase and len(current_phrase) > 1:
        phrases.append(current_phrase)
    
    # 从配置中获取常见的专有名词
    common_phrases = CONFIG['proper_nouns']
    for phrase in common_phrases:
        if phrase.lower() in text:
            phrases.append(phrase.lower())
    
    return set(phrases)

def extract_keywords(text):
    """提取文本关键词"""
    # 分词
    words = chinese_tokenize(text)
    
    # 提取短语和专有名词
    phrases = extract_phrases(text)
    
    # 从配置中获取停用词
    stop_words = set(CONFIG['stop_words'])
    
    # 过滤停用词和短词
    keywords = [word for word in words if word not in stop_words and len(word) > 1]
    
    # 从配置中获取同义词扩展
    synonyms = {}
    for key, value in CONFIG['keywords'].items():
        if key != 'main':  # main 是主要关键词，不需要作为同义词处理
            # 使用第一个词作为基础词，其余作为同义词
            if len(value) > 1:
                synonyms[value[0]] = value[1:]
    
    # 扩展关键词
    extended_keywords = set(keywords)
    # 添加短语和专有名词
    extended_keywords.update(phrases)
    
    # 同义词扩展
    for keyword in list(extended_keywords):
        for base_word, syns in synonyms.items():
            if keyword == base_word or keyword in syns:
                extended_keywords.update([base_word] + syns)
    
    return extended_keywords

def calculate_similarity(text1, text2, keywords1=None, keywords2=None, filename=""):
    """计算两个文本的相似度（改进版）"""
    # 如果没有提供关键词，提取关键词
    if keywords1 is None:
        keywords1 = extract_keywords(text1)
    if keywords2 is None:
        keywords2 = extract_keywords(text2)
    
    # 确保keywords1和keywords2是集合
    keywords1 = set(keywords1) if keywords1 else set()
    keywords2 = set(keywords2) if keywords2 else set()
    
    # 计算共同关键词数
    common_keywords = keywords1.intersection(keywords2)
    
    # 计算关键词相似度
    if len(keywords1) == 0 or len(keywords2) == 0:
        keyword_similarity = 0.0
    else:
        keyword_similarity = len(common_keywords) / math.sqrt(len(keywords1) * len(keywords2))
    
    # 计算文本长度相似度（惩罚过长或过短的文本）
    len1 = len(text1)
    len2 = len(text2)
    if len1 + len2 == 0:
        length_similarity = 1.0
    else:
        length_similarity = 1.0 - abs(len1 - len2) / (len1 + len2 + 1)
    
    # 计算语义相似度（基于关键词覆盖率）
    coverage1 = len(common_keywords) / (len(keywords1) + 1)
    coverage2 = len(common_keywords) / (len(keywords2) + 1)
    coverage_similarity = (coverage1 + coverage2) / 2
    
    # 综合相似度
    similarity = 0.4 * keyword_similarity + 0.1 * length_similarity + 0.3 * coverage_similarity
    
    # 额外加分：如果文本2包含文本1的主要词汇
    text1_lower = text1.lower()
    text2_lower = text2.lower()
    main_words = [word for word in chinese_tokenize(text1) if len(word) > 2]
    if main_words:
        main_word_matches = sum(1 for word in main_words if word in text2_lower)
        if main_word_matches > 0:
            similarity += 0.1 * (main_word_matches / len(main_words))
    
    # 额外加分：如果是文件名匹配
    filename_lower = filename.lower()
    if filename:
        # 检查文件名是否包含文本1的关键词
        text1_words = chinese_tokenize(text1)
        filename_matches = sum(1 for word in text1_words if len(word) > 1 and word.lower() in filename_lower)
        if filename_matches > 0:
            similarity += 0.2 * (filename_matches / len([w for w in text1_words if len(w) > 1]))
    
    # 额外加分：如果文本包含相关的语义词汇
    semantic_boost = 0.0
    semantic_groups = CONFIG['semantic_groups']
    
    for group in semantic_groups:
        if any(word in text1_lower for word in group) and any(word in text2_lower for word in group):
            semantic_boost += 0.15
            break
    
    similarity += semantic_boost
    
    # 额外加分：基于语义距离
    semantic_distance_boost = 0.0
    # 计算语义距离（简单实现）
    if len(common_keywords) > 0:
        semantic_distance_boost = 0.05
    
    similarity += semantic_distance_boost
    
    # 额外加分：对于特定关键词的匹配
    # 从配置中获取特定关键词匹配规则
    specific_keywords = {}
    for key, value in CONFIG['keywords'].items():
        if key in ['deploy', 'usage', 'permanent_plugin', 'trigger_plugin', 'bot', 'napcat', 'qq_bot']:
            specific_keywords[value[0]] = value
    
    for base_word, variants in specific_keywords.items():
        if any(variant in text1_lower for variant in variants) and any(variant in text2_lower for variant in variants):
            similarity += 0.2  # 提高特定关键词的匹配权重
            break
    
    # 额外加分：专有名词匹配
    proper_nouns = CONFIG['proper_nouns']
    proper_noun_matches = sum(1 for noun in proper_nouns if noun.lower() in text1_lower and noun.lower() in text2_lower)
    if proper_noun_matches > 0:
        similarity += 0.3 * proper_noun_matches  # 大幅提高专有名词的匹配权重
    
    return min(similarity, 1.0)

def search_knowledge_base(knowledge_dir, user_input):
    """在知识库中检索相关信息"""
    relevant_info = []
    
    # 查找所有markdown文件
    md_files = glob.glob(os.path.join(knowledge_dir, "*.md"))
    
    # 提取用户问题的关键词
    user_keywords = extract_keywords(user_input)
    
    # 对每个文件进行处理
    for md_file in md_files:
        try:
            with open(md_file, 'r', encoding='utf-8') as f:
                content = f.read()
                
                # 提取文件名
                file_name = os.path.basename(md_file)
                
                # 提取文件关键词
                file_keywords = extract_keywords(content)
                
                # 计算文本相似度（使用改进的算法，传递文件名）
                similarity = calculate_similarity(user_input, content, user_keywords, file_keywords, file_name)
                
                # 打印调试信息
                print(f"文件: {file_name}, 相似度: {similarity}")
                
                # 从配置中获取相似度阈值
                threshold = CONFIG['similarity_threshold']
                if similarity > threshold:
                    # 直接使用整个文件内容，确保不丢失任何信息
                    relevant_info.append({
                        'file': file_name,
                        'content': content,
                        'similarity': similarity
                    })
        except Exception as e:
            print(f"处理文件 {os.path.basename(md_file)} 时出错: {e}")
    
    # 按相似度排序
    relevant_info.sort(key=lambda x: x['similarity'], reverse=True)
    
    # 从配置中获取最大结果数
    max_results = CONFIG['max_results']
    # 从配置中获取相似度阈值
    threshold = CONFIG['similarity_threshold']
    
    # 只返回超过阈值且在最大数量范围内的最相关结果
    filtered_results = [item for item in relevant_info if item['similarity'] > threshold]
    return filtered_results[:max_results]

async def generate_reply_with_deepseek(user_input, relevant_info, user_id):
    """使用DeepSeek生成回复"""
    # 构建知识库信息
    knowledge_info = "\n".join([f"文件: {info['file']}\n内容: {info['content']}\n" for info in relevant_info])
    
    # 从配置中获取应用名称
    app_name = CONFIG['app_name']
    
    # 从配置中获取prompt模板并格式化
    prompt_template = CONFIG['ai_prompt_template']
    prompt = prompt_template.format(app_name=app_name, knowledge_info=knowledge_info)
    
    # 从配置中获取消息模板并格式化
    message_template = CONFIG['ai_message_template']
    message = message_template.format(user_input=user_input)
    
    # 获取DeepSeek API密钥
    deepseek_key = Configurator.cm.get_cfg().others.get("deepseek_key", None)
    if not deepseek_key:
        # 如果没有配置API密钥，使用默认回复
        return generate_default_reply(user_input, relevant_info)
    
    # 调用DeepSeek（关闭流式响应）
    try:
        ds = dsr114(prompt, message, user_lists, user_id, "deepseek-chat", app_name, deepseek_key, stream=False)
        response = ""
        for chunk, chunk_type in ds.Response():
            if isinstance(chunk, str) and chunk_type == 'message':
                response = chunk
                break
        
        # 构建信息来源
        sources = "\n".join([f"- {info['file']}" for info in relevant_info])
        # 从配置中获取来源模板并格式化
        source_template = CONFIG['source_template']
        response += source_template.format(sources=sources)
        
        return response
    except Exception as e:
        print(f"调用DeepSeek时出错: {e}")
        # 出错时使用默认回复
        return generate_default_reply(user_input, relevant_info)

def generate_default_reply(user_input, relevant_info):
    """生成默认回复"""
    # 从配置中获取应用名称
    app_name = CONFIG['app_name']
    
    # 构建知识信息
    knowledge_info = ""
    for info in relevant_info:
        knowledge_info += f"📄 **{info['file']}**\n"
        knowledge_info += f"{info['content']}\n\n"
    
    # 从配置中获取默认回复模板并格式化
    template = CONFIG['default_reply_template']
    reply = template.format(knowledge_info=knowledge_info, app_name=app_name)
    
    return reply