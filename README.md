# 🌟 BlogGenerator AI

一个基于 Streamlit 构建的智能博客生成工具，利用大语言模型（LLM）自动生成高质量的技术博客内容。支持 ZenMux 和 DeepSeek 等多种 API 提供商，提供多智能体工作流和批量处理功能。其支持导出JSON和md格式的博客文件。

---

## ✨ 展示效果
<img width="1919" height="898" alt="image" src="https://github.com/user-attachments/assets/f0b4b0ef-9165-45e7-be65-a5970f66cc54" />
<img width="1911" height="917" alt="image" src="https://github.com/user-attachments/assets/a51e871b-4a89-43a6-98e5-c0ca46500418" />
<img width="1908" height="897" alt="image" src="https://github.com/user-attachments/assets/92501a56-ba24-41de-ba16-97c47ef59636" />



## ✨ 功能特性

### 🔥 核心功能
- **多模型支持**：集成 ZenMux 和 DeepSeek API，自动切换备用服务
- **智能工作流**：支持"调研→大纲→写作"三步工作流，产出更优质内容
- **批量处理**：一键生成多个主题的博客文章
- **多样化风格**：支持标准博客、入门教程、深度解析、实战指南、最佳实践等多种风格

### 🎯 特色功能
- **自动 API 切换**：当主 API 服务不可用时，自动切换到备用服务
- **实时预览**：在生成过程中实时查看各个阶段的输出
- **Token 统计**：详细统计各阶段 Token 使用情况
- **批量导出**：自动组织文件结构，方便管理
- **中文优化**：特别针对 CSDN 等中文技术社区优化内容风格

---

## 📋 环境要求
- Python >= 3.8
- pip >= 20.0

---

## 🚀 安装步骤

### 1. 克隆项目
```bash
git clone https://github.com/yourusername/blog-generator-ai.git
cd blog-generator-ai
```

### 2. 创建虚拟环境
```bash
**Windows：**
python -m venv venv
venv\Scripts\activate
```
```bash
**macOS/Linux：**
python3 -m venv venv
source venv/bin/activate
```
### 3. 安装依赖
```bash
pip install -r requirements.txt
```
### 4. 配置API密钥(.env)
```bash
# ZenMux API 配置
ZENMUX_API_KEY=your_zenmux_api_key_here
ZENMUX_OPENAI=https://zenmux.ai/api/v1  # 可选，使用默认值也可

# DeepSeek API 配置
DEEPSEEK_API_KEY=your_deepseek_api_key_here
```
### 5. 运行应用
```bash
streamlit run Blog_Generator_pro.py
```
---

## 🏗️ 技术架构
```bash
BlogGenerator AI
├── 用户界面层 (Streamlit)
│   ├── 配置面板
│   ├── 实时预览
│   └── 结果展示
├── 业务逻辑层
│   ├── API 客户端管理
│   ├── 多智能体工作流
│   └── 批量处理引擎
├── 模型服务层
│   ├── ZenMux 客户端
│   ├── DeepSeek 客户端
│   └── 模型适配器
└── 数据处理层
    ├── 内容生成
    ├── 文件管理
    └── 缓存管理

---
```

## 🔄 智能工作流
```bash
### 1. 📊 研究员阶段
- 调研主题背景
- 收集技术资料
- 分析应用场景

### 2. 📝 架构师阶段
- 设计文章结构
- 规划内容要点
- 优化阅读体验

### 3. ✍️ 作家阶段
- 撰写完整内容
- 添加示例代码
- 优化表达风格

---
```
## 📁 项目结构
```bash
blog-generator-ai/
├── Blog_Generator_pro.py     # 主程序文件
├── requirements.txt          # Python 依赖
├── .env.example             # 环境变量示例
├── .streamlit/              # Streamlit 配置
│   └── config.toml
├── blogs/                   # 生成的博客文件
│   └── {timestamp}_{topic}/
│       ├── 1_research.md
│       ├── 2_outline.md
│       └── 3_final_blog.md
├── README.md                # 本文档
└── LICENSE                  # 许可协议

---
```
## 📄 许可协议
本项目采用 **MIT 协议** - 查看 [LICENSE](LICENSE) 文件了解详情。

---

## 🙏 致谢
- 感谢所有贡献者和用户的支持
- 感谢 ZenMux 和 DeepSeek 提供的 API 服务
- 感谢 Streamlit 社区提供的优秀框架
