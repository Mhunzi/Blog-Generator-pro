import os
import sys
import streamlit as st
from dotenv import load_dotenv
import openai
import json
from typing import List, Dict, Any
import time
import requests

# ===========================================
SAMPLE_TOPICS = """人工智能基础：其概念，其实现原理，其适用的场景，常见的应用，以及未来布局的产业和市场，以及涉及的人物，其优缺点有哪些
机器学习算法：其概念，其实现原理，其适用的场景，常见的应用，以及未来布局的产业和市场，以及涉及的人物，其优缺点有哪些
深度学习框架：其概念，其实现原理，其适用的场景，常见的应用，以及未来布局的产业和市场，以及涉及的人物，其优缺点有哪些
自然语言处理：其概念，其实现原理，其适用的场景，常见的应用，以及未来布局的产业和市场，以及涉及的人物，其优缺点有哪些
计算机视觉：其概念，其实现原理，其适用的场景，常见的应用，以及未来布局的产业和市场，以及涉及的人物，其优缺点有哪些
数据分析技术：其概念，其实现原理，其适用的场景，常见的应用，以及未来布局的产业和市场，以及涉及的人物，其优缺点有哪些
云计算服务：其概念，其实现原理，其适用的场景，常见的应用，以及未来布局的产业和市场，以及涉及的人物，其优缺点有哪些
大数据处理：其概念，其实现原理，其适用的场景，常见的应用，以及未来布局的产业和市场，以及涉及的人物，其优缺点有哪些
物联网技术：其概念，其实现原理，其适用的场景，常见的应用，以及未来布局的产业和市场，以及涉及的人物，其优缺点有哪些
区块链应用：其概念，其实现原理，其适用的场景，常见的应用，以及未来布局的产业和市场，以及涉及的人物，其优缺点有哪些
"""

def setup_environment():
    """
    加载环境变量
    """
    load_dotenv()
    zenmux_api_key = os.getenv("ZENMUX_API_KEY")
    zenmux_base_url = os.getenv("ZENMUX_OPENAI", "https://zenmux.ai/api/v1")

    # 新增 DeepSeek API
    deepseek_api_key = os.getenv("DEEPSEEK_API_KEY")

    if not zenmux_api_key or not deepseek_api_key:
        # 尝试从streamlit secrets获取
        try:
            zenmux_api_key = st.secrets.get("ZENMUX_API_KEY", zenmux_api_key)
            zenmux_base_url = st.secrets.get("ZENMUX_OPENAI", zenmux_base_url)
            deepseek_api_key = st.secrets.get("DEEPSEEK_API_KEY", deepseek_api_key)
        except:
            pass

    return zenmux_api_key, zenmux_base_url, deepseek_api_key


class DeepSeekClient:
    """
    DeepSeek API 客户端
    """

    def __init__(self, api_key):
        self.api_key = api_key
        self.base_url = "https://api.deepseek.com/chat/completions"
        self.headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {api_key}"
        }

    def call_llm(self, system_prompt, user_prompt, max_tokens=2000, temperature=0.7, model="deepseek-chat"):
        """
        调用 DeepSeek API
        """
        messages = []

        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})

        messages.append({"role": "user", "content": user_prompt})

        data = {
            "model": model,
            "messages": messages,
            "max_tokens": max_tokens,
            "temperature": temperature,
            "stream": False
        }

        try:
            response = requests.post(self.base_url, headers=self.headers, json=data)
            response.raise_for_status()

            result = response.json()
            content = result["choices"][0]["message"]["content"]
            usage = result.get("usage", {})
            total_tokens = usage.get("total_tokens", 0)

            return content, total_tokens

        except requests.exceptions.RequestException as e:
            raise Exception(f"DeepSeek API调用失败: {e}")
        except KeyError as e:
            raise Exception(f"DeepSeek API响应格式错误: {e}")

    def get_available_models(self):
        """
        获取可用模型列表
        """
        # DeepSeek 目前主要提供以下模型
        return ["deepseek-chat", "deepseek-coder"]


class ZenMuxBlogGenerator:
    """
    ZenMux博客生成器
    """

    def process_topics(self, topics_text: str, generation_mode: str = "多智能体工作流",
                       tokens_config: dict = None, temperature: float = 0.7,
                       output_dir: str = None) -> dict:
        """
        批量处理多个博客主题

        参数:
            topics_text: 包含多个主题的文本，每行一个主题
            generation_mode: 生成模式
            tokens_config: Token配置
            temperature: 温度参数
            output_dir: 输出目录路径

        返回:
            dict: 包含处理结果的字典
        """
        import os
        from datetime import datetime

        # 解析主题
        lines = topics_text.strip().split('\n')
        topics = [line.strip() for line in lines if line.strip()]

        if not topics:
            return {"success": False, "message": "没有找到有效的主题"}

        # 设置输出目录
        if output_dir is None:
            output_dir = r"C:\Users\Administrator\Desktop\csdn封面"

        # 创建目录
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        batch_dir = os.path.join(output_dir, f"batch_{timestamp}")
        os.makedirs(batch_dir, exist_ok=True)

        # 保存主题列表
        topics_file = os.path.join(batch_dir, "topics_list.txt")
        with open(topics_file, "w", encoding="utf-8") as f:
            for i, topic in enumerate(topics, 1):
                f.write(f"{i}. {topic}\n")

        # 批量生成
        results = []
        total_topics = len(topics)

        for i, topic in enumerate(topics, 1):
            result = {
                "index": i,
                "topic": topic,
                "status": "pending",
                "file_path": None,
                "tokens_used": 0
            }

            try:
                # 显示进度
                print(f"正在生成 [{i}/{total_topics}]: {topic}")

                if generation_mode == "多智能体工作流":
                    # 使用多智能体工作流
                    research, research_tokens = self.run_researcher(
                        topic,
                        tokens_config.get('research', 1500) if tokens_config else 1500,
                        temperature
                    )

                    outline, outline_tokens = self.run_outline_planner(
                        research,
                        topic,
                        tokens_config.get('outline', 1000) if tokens_config else 1000,
                        temperature
                    )

                    blog, blog_tokens = self.run_writer(
                        outline,
                        topic,
                        tokens_config.get('blog', 3000) if tokens_config else 3000,
                        temperature
                    )

                    total_tokens = research_tokens + outline_tokens + blog_tokens
                else:
                    # 使用一步生成
                    blog, total_tokens = self.one_step_generation(
                        topic,
                        tokens_config.get('blog', 3500) if tokens_config else 3500,
                        temperature
                    )

                # 保存博客
                safe_filename = f"{i:03d}_{topic.replace(' ', '_').replace('/', '_')[:50]}.md"
                file_path = os.path.join(batch_dir, safe_filename)

                with open(file_path, "w", encoding="utf-8") as f:
                    f.write(f"# {topic}\n\n")
                    f.write(blog)

                result.update({
                    "status": "success",
                    "file_path": file_path,
                    "tokens_used": total_tokens
                })

            except Exception as e:
                result.update({
                    "status": "failed",
                    "error": str(e)
                })

            results.append(result)

        # 生成汇总报告
        success_count = sum(1 for r in results if r["status"] == "success")
        failed_count = sum(1 for r in results if r["status"] == "failed")
        total_tokens_used = sum(r["tokens_used"] for r in results if r["status"] == "success")

        summary = {
            "total_topics": total_topics,
            "success": success_count,
            "failed": failed_count,
            "total_tokens_used": total_tokens_used,
            "batch_dir": batch_dir,
            "results": results
        }

        # 保存汇总
        summary_file = os.path.join(batch_dir, "summary.json")
        with open(summary_file, "w", encoding="utf-8") as f:
            json.dump(summary, f, ensure_ascii=False, indent=2)

        return {
            "success": True,
            "summary": summary
        }

    def __init__(self, api_key, base_url, model="openai/gpt-5.2-pro", api_provider="zenmux"):
        self.api_provider = api_provider

        if api_provider == "zenmux":
            self.client = openai.OpenAI(
                base_url=base_url,
                api_key=api_key,
            )
            self.model = model
        elif api_provider == "deepseek":
            self.client = DeepSeekClient(api_key)
            self.model = "deepseek-chat"  # 默认使用 deepseek-chat
        else:
            raise ValueError(f"不支持的API提供商: {api_provider}")

    def get_available_models(self):
        """
        获取可用模型列表
        """
        if self.api_provider == "zenmux":
            try:
                models = self.client.models.list()
                model_list = [model.id for model in models.data]
                return model_list
            except Exception as e:
                st.error(f"获取模型列表失败: {e}")
                return []
        elif self.api_provider == "deepseek":
            return self.client.get_available_models()
        return []

    def call_llm(self, system_prompt, user_prompt, max_tokens=2000, temperature=0.7):
        """
        调用LLM
        """
        if self.api_provider == "zenmux":
            messages = []

            if system_prompt:
                messages.append({"role": "system", "content": system_prompt})

            messages.append({"role": "user", "content": user_prompt})

            try:
                response = self.client.chat.completions.create(
                    model=self.model,
                    messages=messages,
                    max_tokens=max_tokens,
                    temperature=temperature,
                )

                return response.choices[0].message.content, response.usage.total_tokens

            except Exception as e:
                # 如果 ZenMux 调用失败，抛出异常让外层处理
                raise Exception(f"ZenMux API调用失败: {e}")

        elif self.api_provider == "deepseek":
            return self.client.call_llm(
                system_prompt=system_prompt,
                user_prompt=user_prompt,
                max_tokens=max_tokens,
                temperature=temperature,
                model=self.model
            )

    def run_researcher(self, topic, research_tokens, temperature):
        """
        研究员：调研主题
        """
        system_prompt = """你是一名专注于人工智能与软件开发的技术研究员，擅长从官方文档、GitHub、技术博客和论文中提炼关键信息，特别了解中国开发者社区（如 CSDN、知乎）的内容偏好。"""

        user_prompt = f"""调研 {topic} 的最新发展，包括：
1) 核心技术原理；
2) 典型应用场景；
3) 主流工具/框架；
4) 社区讨论热点。

请聚焦对中国开发者有价值的信息，提供一份结构化的中文调研报告，每点不少于 3 条具体信息，并附上可信来源（如 GitHub、官方文档链接）。"""

        return self.call_llm(system_prompt, user_prompt, research_tokens, temperature)

    def run_outline_planner(self, research_content, topic, outline_tokens, temperature):
        """
        博客架构师：设计大纲
        """
        system_prompt = """你是一位资深 CSDN 博主，熟悉平台热门文章结构。你擅长设计包含'引言-核心内容-总结-参考'的四段式结构，并能合理使用小标题、代码块提示、加粗关键词等 Markdown 元素。"""

        user_prompt = f"""基于以下调研结果，为关于「{topic}」的CSDN博客设计一个详细大纲：

{research_content}

要求：
1. 包含吸引人的标题（不超过20字）
2. 包含引言部分
3. 包含3-5个带编号的小节标题
4. 包含总结部分
5. 在合适位置标注'可插入代码示例'或'配图建议'

请输出一个完整的 Markdown 风格博客大纲，语言简洁有力。"""

        return self.call_llm(system_prompt, user_prompt, outline_tokens, temperature)

    def run_writer(self, outline_content, topic, blog_tokens, temperature):
        """
        技术博主：撰写博客
        """
        system_prompt = """你是 CSDN 平台上拥有数万粉丝的技术博主，文风亲切、逻辑清晰，善于用通俗语言解释复杂概念，常在文中加入'💡小贴士'、'⚠️注意'等互动元素，提升读者体验。"""

        user_prompt = f"""根据以下大纲，撰写一篇关于「{topic}」的完整CSDN风格技术博客：

{outline_content}

要求：
1. 全中文，语言流畅，技术准确，段落分明
2. 适当使用 **加粗**、`代码片段`、> 引用块等 Markdown 语法
3. 结尾包含'总结'和'参考资料'部分
4. 文中可适当加入'💡小贴士'、'⚠️注意'等互动元素

请输出一篇可直接发布到 CSDN 的 Markdown 格式博客全文，无需额外说明，仅输出博客内容。"""

        return self.call_llm(system_prompt, user_prompt, blog_tokens, temperature)

    def one_step_generation(self, topic, blog_tokens, temperature, style="标准技术博客"):
        """
        一步生成完整博客
        """
        style_prompts = {
            "标准技术博客": """你是一位CSDN技术博主，请撰写一篇高质量的技术博客。""",
            "入门教程": """你是一位有经验的导师，请撰写一篇适合初学者的入门教程。""",
            "深度解析": """你是一位技术专家，请撰写一篇深度技术解析文章。""",
            "实战指南": """你是一位实战派开发者，请撰写一篇包含完整代码的实战指南。""",
            "最佳实践": """你是一位架构师，请撰写一篇关于最佳实践的文章。"""
        }

        system_prompt = style_prompts.get(style, style_prompts["标准技术博客"])

        user_prompt = f"""请撰写一篇关于「{topic}」的CSDN技术博客，要求：

# 文章要求
1. **标题**：吸引人且包含关键词
2. **引言**：介绍主题的重要性和背景
3. **核心内容**：
   - 相关概念和原理
   - 安装和配置教程
   - 实战示例代码
   - 最佳实践和注意事项
4. **总结**：核心要点总结
5. **参考资料**：相关链接和资源

# 格式要求
- 使用Markdown格式
- 适当使用 **加粗**、`代码块`、> 引用
- 包含💡小贴士和⚠️注意提示
- 代码示例要完整可运行
- 结构清晰，逻辑严谨

请开始撰写："""

        return self.call_llm(system_prompt, user_prompt, blog_tokens, temperature)


# 设置页面配置
st.set_page_config(
    page_title=" BlogGenerator AI 博客生成器",
    page_icon="📝",
    layout="wide",
    initial_sidebar_state="expanded"
)

# 自定义CSS
st.markdown("""
<style>
.stButton button {
    width: 100%;
}
.success-box {
    padding: 1rem;
    border-radius: 0.5rem;
    background-color: #d4edda;
    border: 1px solid #c3e6cb;
    color: #155724;
}
.info-box {
    padding: 1rem;
    border-radius: 0.5rem;
    background-color: #d1ecf1;
    border: 1px solid #bee5eb;
    color: #0c5460;
}
.step-box {
    padding: 1rem;
    border-radius: 0.5rem;
    background-color: #f8f9fa;
    border: 1px solid #e9ecef;
    margin-bottom: 1rem;
}
.api-badge {
    display: inline-block;
    padding: 2px 8px;
    border-radius: 12px;
    font-size: 12px;
    font-weight: bold;
    margin-left: 8px;
}
.zenmux-badge {
    background-color: #6366f1;
    color: white;
}
.deepseek-badge {
    background-color: #10b981;
    color: white;
}
</style>
""", unsafe_allow_html=True)

# 标题
st.title("📝 BlogGenerator AI 博客生成器")
st.markdown("使用多种大模型API生成高质量的CSDN技术博客")

# 初始化session state
if 'generator' not in st.session_state:
    st.session_state.generator = None
if 'available_models' not in st.session_state:
    st.session_state.available_models = []
if 'api_provider' not in st.session_state:
    st.session_state.api_provider = None
if 'generation_in_progress' not in st.session_state:
    st.session_state.generation_in_progress = False
if 'research_content' not in st.session_state:
    st.session_state.research_content = ""
if 'outline_content' not in st.session_state:
    st.session_state.outline_content = ""
if 'blog_content' not in st.session_state:
    st.session_state.blog_content = ""

# 侧边栏配置
with st.sidebar:
    st.header("⚙️ 配置设置")

    # API配置
    zenmux_api_key, zenmux_base_url, deepseek_api_key = setup_environment()

    # API提供商选择
    st.subheader("🔌 API提供商")
    api_provider_options = []

    if zenmux_api_key:
        api_provider_options.append("ZenMux")
    if deepseek_api_key:
        api_provider_options.append("DeepSeek")

    if not api_provider_options:
        st.error("❌ 未检测到任何API Key")
        st.stop()

    selected_provider = st.radio(
        "选择API提供商:",
        api_provider_options,
        help="选择要使用的API提供商",
        key="api_provider_select"
    )

    # 根据选择的提供商显示不同的配置
    if selected_provider == "ZenMux":
        api_key = zenmux_api_key
        base_url = zenmux_base_url
        default_model = "openai/gpt-5.2-pro"
        api_badge = "zenmux-badge"
    else:  # DeepSeek
        api_key = deepseek_api_key
        base_url = None
        default_model = "deepseek-chat"
        api_badge = "deepseek-badge"

    st.markdown(f'<span class="api-badge {api_badge}">{selected_provider}</span>', unsafe_allow_html=True)

    # 测试连接按钮
    if st.button("测试API连接", key="test_connection"):
        with st.spinner("正在测试连接..."):
            try:
                if selected_provider == "ZenMux":
                    client = openai.OpenAI(
                        base_url=base_url,
                        api_key=api_key,
                    )

                    # 测试 ZenMux API
                    try:
                        response = client.chat.completions.create(
                            model="openai/gpt-5.2-pro",
                            messages=[{"role": "user", "content": "测试"}],
                            max_tokens=16
                        )
                        api_working = True
                        error_message = None
                    except Exception as e:
                        api_working = False
                        error_message = f"ZenMux API连接失败: {e}"

                        # ZenMux 失败，尝试切换到 DeepSeek
                        if deepseek_api_key:
                            st.warning("ZenMux API不可用，正在尝试切换到DeepSeek...")
                            try:
                                # 测试 DeepSeek API
                                test_client = DeepSeekClient(deepseek_api_key)
                                test_response, _ = test_client.call_llm("", "测试", max_tokens=16)
                                api_working = True
                                error_message = None
                                selected_provider = "DeepSeek"
                                st.session_state.api_provider = "DeepSeek"
                                st.success("✅ 已自动切换到DeepSeek API")
                            except Exception as deepseek_error:
                                api_working = False
                                error_message = f"所有API都不可用:\n- ZenMux: {e}\n- DeepSeek: {deepseek_error}"
                else:  # DeepSeek
                    client = DeepSeekClient(api_key)

                    try:
                        response, _ = client.call_llm("", "测试", max_tokens=16)
                        api_working = True
                        error_message = None
                    except Exception as e:
                        api_working = False
                        error_message = f"DeepSeek API连接失败: {e}"

                if api_working:
                    # 创建生成器
                    st.session_state.api_provider = selected_provider
                    st.session_state.generator = ZenMuxBlogGenerator(
                        api_key=api_key,
                        base_url=base_url if selected_provider == "ZenMux" else "",
                        api_provider=selected_provider.lower()
                    )

                    # 获取可用模型
                    with st.spinner("正在获取可用模型..."):
                        st.session_state.available_models = st.session_state.generator.get_available_models()

                    st.success(f"✅ {selected_provider} API连接测试成功")
                else:
                    st.error(f"❌ {error_message}")
                    st.session_state.generator = None

            except Exception as e:
                st.error(f"❌ API连接测试失败: {e}")
                st.session_state.generator = None

    if st.session_state.generator and st.session_state.available_models:
        # 模型选择
        st.subheader("🎯 模型选择")

        # 根据API提供商设置默认模型
        if selected_provider == "ZenMux":
            if "openai/gpt-5.2-pro" in st.session_state.available_models:
                default_model = "openai/gpt-5.2-pro"
            else:
                default_model = st.session_state.available_models[
                    0] if st.session_state.available_models else "openai/gpt-5.2-pro"
        else:  # DeepSeek
            if "deepseek-chat" in st.session_state.available_models:
                default_model = "deepseek-chat"
            elif "deepseek-coder" in st.session_state.available_models:
                default_model = "deepseek-coder"
            else:
                default_model = st.session_state.available_models[
                    0] if st.session_state.available_models else "deepseek-chat"

        selected_model = st.selectbox(
            "选择模型:",
            st.session_state.available_models,
            index=st.session_state.available_models.index(
                default_model) if default_model in st.session_state.available_models else 0,
            key="model_select"
        )
        st.session_state.generator.model = selected_model

        # 显示模型信息
        with st.expander("📊 模型信息"):
            st.write(f"**API提供商:** {selected_provider}")
            st.write(f"**已选择模型:** {selected_model}")
            st.write(f"**可用模型数:** {len(st.session_state.available_models)}")
            if len(st.session_state.available_models) > 0:
                st.write("**可用模型列表:**")
                for model in st.session_state.available_models:
                    st.write(f"- {model}")
    else:
        st.info("👆 请先测试API连接")
        st.stop()

    # 生成模式
    st.subheader("🚀 生成模式")
    generation_mode = st.radio(
        "选择生成模式:",
        ["多智能体工作流", "一步生成"],
        help="多智能体工作流：分三步（调研、大纲、写作）生成更高质量内容\n一步生成：快速生成完整博客",
        key="generation_mode"
    )

    # 主题输入
    st.subheader("📋 博客主题")
    topic = st.text_input(
        "请输入博客主题:",
        value="多智能体协作的提示链实践",
        help="例如：CrewAI框架实战、Python异步编程、机器学习部署等",
        key="topic_input"
    )

    # 高级设置
    st.subheader("⚡ 高级设置")

    if generation_mode == "多智能体工作流":
        col1, col2 = st.columns(2)
        with col1:
            research_tokens = st.slider("调研阶段Token数", 500, 5000, 1500, 100, key="research_tokens")
            outline_tokens = st.slider("大纲阶段Token数", 300, 3000, 1000, 100, key="outline_tokens")
        with col2:
            blog_tokens = st.slider("写作阶段Token数", 1000, 8000, 3000, 100, key="blog_tokens")
            temperature = st.slider("温度参数", 0.1, 1.0, 0.7, 0.1, key="temperature")
    else:
        blog_tokens = st.slider("生成Token数", 1000, 8000, 3500, 100, key="blog_tokens_single")
        temperature = st.slider("温度参数", 0.1, 1.0, 0.7, 0.1, key="temperature_single")
        blog_style = st.selectbox(
            "博客风格:",
            ["标准技术博客", "入门教程", "深度解析", "实战指南", "最佳实践"],
            key="blog_style"
        )

    # 显示API状态
    st.divider()
    st.markdown("### 🔄 API状态")
    if st.session_state.api_provider:
        status_color = "🟢" if st.session_state.generator else "🟡"
        st.markdown(f"{status_color} **当前API:** {st.session_state.api_provider}")
        if st.session_state.api_provider == "zenmux" and not st.session_state.generator:
            st.warning("ZenMux API可能已失效，建议在.env中设置DeepSeek API Key")
    else:
        st.warning("未连接API")

    # 开始生成按钮
    st.divider()
    generate_button = st.button("🚀 开始生成博客", type="primary", use_container_width=True, key="generate_button")

# 主内容区域
if generate_button and topic and not st.session_state.generation_in_progress:
    st.session_state.generation_in_progress = True

    if generation_mode == "多智能体工作流":
        # 运行多智能体工作流
        progress_bar = st.progress(0)
        status_text = st.empty()

        # 步骤1: 调研
        status_text.text("🔍 步骤1/3: AI研究员正在调研主题...")
        with st.spinner("正在调研..."):
            try:
                research, research_used_tokens = st.session_state.generator.run_researcher(topic, research_tokens,
                                                                                           temperature)
            except Exception as e:
                st.error(f"调研阶段失败: {e}")
                st.session_state.generation_in_progress = False
                st.stop()

        progress_bar.progress(33)
        st.session_state.research_content = research

        with st.expander("📊 调研报告", expanded=True):
            st.markdown(research)
            st.caption(f"使用Token数: {research_used_tokens}")

        # 步骤2: 设计大纲
        status_text.text("📝 步骤2/3: 博客架构师正在设计大纲...")
        with st.spinner("正在设计大纲..."):
            try:
                outline, outline_used_tokens = st.session_state.generator.run_outline_planner(research, topic,
                                                                                              outline_tokens,
                                                                                              temperature)
            except Exception as e:
                st.error(f"大纲阶段失败: {e}")
                st.session_state.generation_in_progress = False
                st.stop()

        progress_bar.progress(66)
        st.session_state.outline_content = outline

        with st.expander("🗒️ 博客大纲", expanded=True):
            st.markdown(outline)
            st.caption(f"使用Token数: {outline_used_tokens}")

        # 步骤3: 撰写博客
        status_text.text("✍️ 步骤3/3: 技术博主正在撰写博客...")
        with st.spinner("正在撰写博客..."):
            try:
                blog, blog_used_tokens = st.session_state.generator.run_writer(outline, topic, blog_tokens, temperature)
            except Exception as e:
                st.error(f"写作阶段失败: {e}")
                st.session_state.generation_in_progress = False
                st.stop()

        progress_bar.progress(100)
        status_text.text("✅ 博客生成完成！")
        st.session_state.blog_content = blog

        # 显示最终结果
        st.success("🎉 博客生成完成！")

        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("调研Token数", research_used_tokens)
        with col2:
            st.metric("大纲Token数", outline_used_tokens)
        with col3:
            st.metric("写作Token数", blog_used_tokens)

        st.divider()
        st.subheader("📄 生成的博客")

        # 博客展示区域
        blog_tab1, blog_tab2 = st.tabs(["预览", "源代码"])

        with blog_tab1:
            st.markdown(blog)

        with blog_tab2:
            st.code(blog, language="markdown")

        # 下载按钮
        st.download_button(
            label="📥 下载博客",
            data=blog,
            file_name=f"{topic.replace(' ', '_')}_blog.md",
            mime="text/markdown"
        )

    else:
        # 运行一步生成
        progress_bar = st.progress(0)
        status_text = st.empty()

        status_text.text("🚀 正在生成博客...")
        with st.spinner("正在生成中，请稍候..."):
            try:
                blog, used_tokens = st.session_state.generator.one_step_generation(topic, blog_tokens, temperature,
                                                                                   blog_style)
            except Exception as e:
                st.error(f"生成失败: {e}")
                st.session_state.generation_in_progress = False
                st.stop()

        progress_bar.progress(100)
        status_text.text("✅ 博客生成完成！")
        st.session_state.blog_content = blog

        # 显示结果
        st.success(f"🎉 博客生成完成！使用Token数: {used_tokens}")

        st.divider()
        st.subheader("📄 生成的博客")

        # 博客展示区域
        blog_tab1, blog_tab2 = st.tabs(["预览", "源代码"])

        with blog_tab1:
            st.markdown(blog)

        with blog_tab2:
            st.code(blog, language="markdown")

        # 统计信息
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("总字数", len(blog))
        with col2:
            st.metric("使用Token数", used_tokens)
        with col3:
            st.metric("生成模式", "一步生成")

        # 下载按钮
        st.download_button(
            label="📥 下载博客",
            data=blog,
            file_name=f"{topic.replace(' ', '_')}_blog.md",
            mime="text/markdown"
        )

    st.session_state.generation_in_progress = False

else:
    # 显示使用说明
    st.info("👈 请在左侧配置参数，然后点击'开始生成博客'")

    # 显示示例
    with st.expander("📖 使用示例", expanded=True):
        st.markdown("""
        ### 多智能体工作流模式：
        1. **调研阶段**：AI研究员调研主题，生成详细报告
        2. **大纲阶段**：博客架构师设计文章结构
        3. **写作阶段**：技术博主撰写完整文章

        ### 一步生成模式：
        - 快速生成完整的博客文章
        - 适合简单主题或快速原型

        ### 参数说明：
        - **Token数**：控制生成内容的长度
        - **温度参数**：控制创造性（值越高越有创意，值越低越稳定）
        - **博客风格**：选择不同的写作风格
        """)

    # 显示快速开始
    col1, col2, col3 = st.columns(3)
    with col1:
        if st.button("🤖 AI框架实战", use_container_width=True, key="ai_framework"):
            st.session_state.topic_input = "LangChain框架实战指南"
    with col2:
        if st.button("🐍 Python编程", use_container_width=True, key="python_programming"):
            st.session_state.topic_input = "Python异步编程最佳实践"
    with col3:
        if st.button("🔧 工具教程", use_container_width=True, key="tool_tutorial"):
            st.session_state.topic_input = "Docker容器化部署完整教程"

with st.sidebar:
    st.divider()
    st.subheader("📚 批量处理")

    batch_mode = st.checkbox("启用批量处理模式", value=False, key="batch_mode")

    if batch_mode:
        batch_topics = st.text_area(
            "输入多个主题（每行一个）：",
            value="""具身智能之机器人灵巧手：其概念，其实现原理，其适用的场景，常见的应用，以及未来布局的产业和市场，以及涉及的人物，其优缺点有哪些
具身智能之仿生机器人：其概念，其实现原理，其适用的场景，常见的应用，以及未来布局的产业和市场，以及涉及的人物，其优缺点有哪些
具身智能之人形机器人：其概念，其实现原理，其适用的场景，常见的应用，以及未来布局的产业和市场，以及涉及的人物，其优缺点有哪些""",
            height=150,
            help="每个主题占一行，支持任何技术主题"
        )
        col1, col2 = st.columns(2)
        with col1:
            if st.button("📋 加载示例主题", key="load_sample", use_container_width=True):
                st.session_state.batch_topics = SAMPLE_TOPICS
                st.rerun()
        with col2:
            if st.button("🧹 清空输入", key="clear_input", use_container_width=True):
                st.session_state.batch_topics = ""
                st.rerun()

        # 设置输出目录
        output_dir = st.text_input(
            "输出文件夹路径：",
            value=r"C:\Users\Administrator\Desktop\csdn封面",
            help="生成的Markdown文件将保存在此文件夹"
        )

        batch_generate_button = st.button(
            "🚀 批量生成博客",
            type="primary",
            use_container_width=True,
            key="batch_generate_button"
        )

# 在主内容区域添加批量处理逻辑
if batch_mode and batch_generate_button and st.session_state.generator:
    if not batch_topics.strip():
        st.error("请输入要生成的主题列表")
    else:
        with st.spinner("正在批量生成博客..."):
            try:
                # 获取生成模式
                generation_mode = st.session_state.get("generation_mode", "多智能体工作流")

                # 获取token配置
                if generation_mode == "多智能体工作流":
                    tokens_config = {
                        'research': st.session_state.get("research_tokens", 1500),
                        'outline': st.session_state.get("outline_tokens", 1000),
                        'blog': st.session_state.get("blog_tokens", 3000)
                    }
                else:
                    tokens_config = {
                        'blog': st.session_state.get("blog_tokens_single", 3500)
                    }

                # 获取温度参数
                temperature = st.session_state.get("temperature", 0.7)
                if generation_mode != "多智能体工作流":
                    temperature = st.session_state.get("temperature_single", 0.7)

                # 执行批量处理
                result = st.session_state.generator.process_topics(
                    topics_text=batch_topics,
                    generation_mode=generation_mode,
                    tokens_config=tokens_config,
                    temperature=temperature,
                    output_dir=output_dir
                )

                if result["success"]:
                    summary = result["summary"]

                    st.success(f"✅ 批量生成完成！")

                    # 显示统计信息
                    col1, col2, col3, col4 = st.columns(4)
                    with col1:
                        st.metric("总主题数", summary["total_topics"])
                    with col2:
                        st.metric("成功", summary["success"])
                    with col3:
                        st.metric("失败", summary["failed"])
                    with col4:
                        st.metric("总Token数", summary["total_tokens_used"])

                    # 显示详细信息
                    with st.expander("📊 详细结果", expanded=True):
                        for r in summary["results"]:
                            if r["status"] == "success":
                                st.success(f"✅ {r['index']}. {r['topic']} (Token: {r['tokens_used']})")
                                st.info(f"   保存到: {r['file_path']}")
                            else:
                                st.error(f"❌ {r['index']}. {r['topic']} - 错误: {r.get('error', '未知错误')}")

                    # 显示输出文件夹
                    st.info(f"📁 所有文件已保存到: {summary['batch_dir']}")

                else:
                    st.error(f"批量生成失败: {result.get('message', '未知错误')}")

            except Exception as e:
                st.error(f"批量处理过程中出错: {str(e)}")

# 保存中间结果的功能
if st.session_state.blog_content:
    st.sidebar.divider()
    if st.sidebar.button("💾 保存所有结果", key="save_all"):
        import datetime
        import os

        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        topic_safe = topic.replace(' ', '_').replace('/', '_')
        folder_name = f"blogs/{timestamp}_{topic_safe}"

        try:
            os.makedirs(folder_name, exist_ok=True)

            # 保存调研报告
            if st.session_state.research_content:
                with open(f"{folder_name}/1_research.md", "w", encoding="utf-8") as f:
                    f.write(st.session_state.research_content)

            # 保存大纲
            if st.session_state.outline_content:
                with open(f"{folder_name}/2_outline.md", "w", encoding="utf-8") as f:
                    f.write(st.session_state.outline_content)

            # 保存博客
            with open(f"{folder_name}/3_final_blog.md", "w", encoding="utf-8") as f:
                f.write(st.session_state.blog_content)

            st.sidebar.success(f"✅ 已保存到 {folder_name}/")
        except Exception as e:
            st.sidebar.error(f"❌ 保存失败: {e}")

# 底部信息
st.sidebar.markdown("---")
st.sidebar.caption(f"当前API提供商: {st.session_state.api_provider if st.session_state.api_provider else '未连接'}")