## KnowledgeAnswer - 知识库问答插件
一个基于知识库的智能问答插件，通过关键词匹配判断用户是否询问相关问题，检索知识库并结合AI生成回复。

### 功能特性

- 通过关键词匹配判断用户是否在询问与应用相关的问题
- 自动创建和管理知识库文件夹(data/knowledge)
- 从Markdown文件(.md)中检索相关信息
- 使用DeepSeek模型生成智能回复
- 支持文件名匹配和语义相似度计算
- 包含信息来源标注
- 高度可配置的参数设置

### 先决条件
此插件要求你的机器人为 **简儿 NEXT 3.1** 或更高版本。你可以前往 [简儿 NEXT Release](https://github.com/SRInternet-Studio/Jianer_QQ_bot/releases) 页面下载 **NEXT 3.1 Release** 或更新版本的 Release。

### 安装方法
#### 使用设置向导（插件中心）安装
在设置向导 -> 插件中心页面，切换筛选条件为 ```筛选：全部``` ，然后搜索 ```KnowledgeAnswer``` ，点击安装

#### 手动安装
1. 下载 `setup.py` 文件
2. 将文件放入机器人的 `plugins/KnowledgeAnswer` 目录
3. 将 `knowledge_config.json` 配置文件放入 `plugins/KnowledgeAnswer` 目录
4. 在 `data` 目录下创建 `knowledge` 文件夹，并放入 Markdown 格式的知识库文档
5. 重启机器人或发送 `重载插件` 命令

### 使用方法

在群聊中向机器人提问与应用相关的问题，插件会自动识别并从知识库中检索相关信息，结合AI生成回复。

例如：`简儿怎么用？` 或 `如何部署简儿？`

### 配置说明

插件的所有配置都存储在 `knowledge_config.json` 文件中，以下是详细的配置项说明：

#### 基本配置
- `app_name`: 应用名称，用于动态替换，如"简儿"
- `similarity_threshold`: 相似度阈值，低于此值的结果将被忽略（默认0.08）
- `paragraph_similarity_threshold`: 段落相似度阈值（默认0.15）
- `max_results`: 返回的最大结果数量（默认3）
- `min_text_length`: 最小文本长度要求，用于判断是否为有效问题（默认5）

#### 关键词配置
- `keywords.main`: 主要关键词数组，包含应用的各种称呼和别名
- `keywords.usage`: 使用相关的同义词数组，如["使用", "用", "使用方法", ...]
- `keywords.start`: 开始相关的同义词数组
- `keywords.deploy`: 部署相关的同义词数组
- `keywords.feature`: 功能相关的同义词数组
- `keywords.tutorial`: 教程相关的同义词数组
- `keywords.question`: 问题相关的同义词数组
- `keywords.solution`: 解决相关的同义词数组
- `keywords.config`: 配置相关的同义词数组
- `keywords.launch`: 启动相关的同义词数组
- `keywords.install`: 安装相关的同义词数组
- `keywords.update`: 更新相关的同义词数组
- `keywords.error`: 错误相关的同义词数组
- `keywords.command`: 命令相关的同义词数组
- `keywords.permanent_plugin`: 永久触发插件相关的同义词数组
- `keywords.trigger_plugin`: 触发插件相关的同义词数组
- `keywords.bot`: 机器人相关的同义词数组
- `keywords.napcat`: NapCat相关的同义词数组
- `keywords.qq_bot`: QQ机器人相关的同义词数组

#### 语言处理配置
- `question_words`: 疑问词数组，如["什么", "怎么", "如何", ...]
- `modal_verbs`: 助动词数组，如["能", "可以", "会", ...]
- `action_verbs`: 动作词数组，如["使用", "设置", "配置", ...]
- `question_patterns`: 问题模式数组，如["是什么", "怎么用", ...]
- `simple_expressions`: 简单表达数组，用于过滤简单称呼
- `negation_words`: 否定词数组，如["不", "没", "无", ...]
- `stop_words`: 停用词数组，用于过滤无意义词汇
- `punctuation`: 标点符号字符串，用于文本处理

#### 语义匹配配置
- `semantic_groups`: 语义词组数组，每组包含相关的词汇，如[["使用", "怎么用", "如何使用"], ...]
- `proper_nouns`: 专有名词数组，如["永久触发插件", "触发插件", ...]

#### 模板配置
- `default_reply_template`: 默认回复模板，支持 `{knowledge_info}` 和 `{app_name}` 变量
- `ai_prompt_template`: AI提示词模板，支持 `{app_name}` 和 `{knowledge_info}` 变量
- `ai_message_template`: AI消息模板，支持 `{user_input}` 变量
- `source_template`: 信息来源模板，支持 `{sources}` 变量

### 如何编写配置文件

#### 1. 基本结构
配置文件采用标准JSON格式，所有配置项都应包含在根对象中。

#### 2. 关键词配置详解
关键词配置是插件的核心，决定了插件如何识别用户问题：

```json
"keywords": {
  "main": ["简儿", "jianer", "Jianer", "簡兒", "NapCat", "napcat", "Napcat", "nc"],
  "usage": ["使用", "用", "使用方法", "使用指南", "如何使用", "怎么用", "运用", "应用", "操作"]
}
```

- `main` 键包含应用的所有称呼和别名
- 每个子键对应一类同义词，第一个词是基础词，后续是同义词
- 插件会自动将同义词扩展应用于相似度计算

#### 3. 语言处理配置详解
这些配置影响文本分析和问题识别：

```json
"question_words": ["什么", "怎么", "如何", "为什么", "为何", "怎", "吗", "呢", "啥", "哪个", "哪里", "谁", "多少"],
"stop_words": ["的", "了", "和", "是", "在", "有", "我", "他", "她", "它", "们", "这", "那", "你"]
```

- `question_words` 包含常见的疑问词，影响问题识别
- `stop_words` 包含常见的停用词，这些词会在关键词提取时被过滤

#### 4. 模板配置详解
模板配置允许自定义AI交互和回复格式：

```json
"ai_prompt_template": "你是一个智能助手，名为{app_name}。请严格根据以下知识库中的信息，回答用户的问题。\\n\\n知识库信息：\\n{knowledge_info}\\n\\n重要要求：\\n1. 必须基于知识库中的信息回答，不能编造内容\\n2. 即使知识库中的信息不完整，也要尽可能基于现有信息提供有用的回答\\n3. 回答要详细、准确，并且要明确引用信息来源（文件名）\\n4. 禁止使用'我不知道'、'无法回答'等类似表述\\n5. 请用自然、友好的语言回答用户的问题",
"ai_message_template": "用户问题：{user_input}\\n\\n请严格根据知识库中的信息回答用户的问题，回答要详细、准确，并且要明确包含信息来源（文件名）。即使信息不完整，也要基于现有信息提供最有用的回答。"
```

- 使用 `{variable_name}` 语法插入动态内容
- 支持转义字符如 `\\n` 表示换行

#### 5. 调优建议
- **相似度阈值**: 如果匹配过于严格，降低 `similarity_threshold`；如果匹配过于宽松，提高该值
- **关键词扩展**: 根据用户常见问题不断扩展 `keywords` 中的同义词
- **语义词组**: 将经常一起出现的词语放在同一组，提高匹配准确性
- **模板调整**: 根据AI模型特点调整提示词，获得更好的回复质量

### 注意事项

- 确保 `data/knowledge` 目录下有 Markdown 格式的知识库文档
- 需要配置 DeepSeek API 密钥才能使用AI生成功能
- 配置文件修改后需要重启插件或重新加载配置
- 插件仅在群聊中使用，通过群消息事件触发
- 知识库文档应使用 Markdown 格式，以获得最佳解析效果

## 贡献代码

欢迎提交 Pull Request 来改进这个插件！