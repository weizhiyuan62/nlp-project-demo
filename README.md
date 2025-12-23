# 智览 (ZhiLan) - 基于大模型的智能信息聚合与分析系统

[![Python Version](https://img.shields.io/badge/python-3.8%2B-blue)](https://www.python.org/)
[![License](https://img.shields.io/badge/license-MIT-green)](LICENSE)

## 📋 项目简介

**智览**是一个基于大语言模型的智能信息聚合与分析系统，能够自动从多个数据源采集信息，通过AI进行智能筛选和分析，并生成高质量的可视化分析报告。

### 主要功能

✨ **多源信息采集**: 整合Bing Search、NewsAPI、arXiv等多个数据源  
🤖 **智能分析筛选**: 使用大模型进行多维度评分（相关性、重要性、时效性、可靠性）  
📊 **数据可视化**: 自动生成词云图、时间趋势图、信息源分布图等  
📄 **报告自动生成**: 生成结构化的Markdown和PDF格式报告  
🔄 **容错机制**: 支持断点续传、自动重试、错误恢复

## 🚀 快速开始

### 环境要求

- Python 3.8+
- LaTeX环境（用于生成PDF，可选）
  - macOS: `brew install --cask mactex`
  - Linux: `sudo apt-get install texlive-full`

### 安装步骤

1. **克隆项目**

```bash
git clone <repository-url>
cd my-project-demo
```

2. **创建虚拟环境**

```bash
conda create -n zhilan python=3.9
conda activate zhilan
```

3. **安装依赖**

```bash
pip install -r requirements.txt
```

4. **配置API密钥**

编辑 `config/config.yaml` 文件，填入你的API密钥：

```yaml
api:
  # 搜索引擎配置
  bing_search:
    enabled: true
    api_key: "YOUR_BING_SEARCH_API_KEY"  # 替换为你的密钥
  
  # 新闻API配置
  newsapi:
    enabled: true
    api_key: "YOUR_NEWSAPI_KEY"  # 替换为你的密钥
  
  # 大模型API配置
  llm:
    provider: "qwen"
    api_key: "YOUR_LLM_API_KEY"  # 替换为你的密钥
    model: "qwen-plus"
```

### 运行系统

```bash
cd src
python main.py
```

## 📖 使用指南

### 配置说明

主要配置文件位于 `config/config.yaml`，包含以下配置项：

#### 1. 项目信息
```yaml
project:
  name: "智览信息聚合系统"
  version: "1.0.0"
```

#### 2. 信息采集配置
```yaml
collection:
  topics:
    - "人工智能"
    - "机器学习"
  time_range: "last_3_days"  # today, last_3_days, last_week, custom
  max_items_per_topic: 50
```

#### 3. 分析配置
```yaml
analysis:
  scoring:
    relevance_weight: 0.3
    importance_weight: 0.3
    timeliness_weight: 0.2
    reliability_weight: 0.2
  min_score: 0.6
```

#### 4. 报告配置
```yaml
report:
  style: "detailed"  # brief, detailed, academic
  language: "zh-CN"
  visualization:
    wordcloud: true
    timeline: true
    source_distribution: true
```

### 获取API密钥

#### Bing Search API
1. 访问 [Azure Portal](https://portal.azure.com/)
2. 创建"Bing Search v7"资源
3. 在"密钥和终结点"中获取API密钥

#### NewsAPI
1. 访问 [NewsAPI官网](https://newsapi.org/)
2. 注册账号
3. 在个人页面获取API密钥

#### 通义千问API
1. 访问 [阿里云DashScope](https://dashscope.aliyun.com/)
2. 开通服务
3. 获取API-KEY

## 🏗️ 项目结构

```
my-project-demo/
├── config/              # 配置文件
│   └── config.yaml      # 主配置文件
├── src/                 # 源代码
│   ├── main.py         # 主程序入口
│   ├── config.py       # 配置管理模块
│   ├── logger.py       # 日志和错误处理
│   ├── data_collector.py    # 数据采集模块
│   ├── analyzer.py     # 智能分析模块
│   ├── visualizer.py   # 数据可视化模块
│   ├── report_generator.py  # 报告生成模块
│   └── latex_compiler.py    # LaTeX编译模块
├── templates/           # LaTeX模板
│   └── report_template.tex
├── assets/             # 生成的图表
├── outputs/            # 输出报告
├── logs/               # 日志文件
├── requirements.txt    # 依赖包列表
├── proposal.tex        # 项目计划书
└── README.md          # 项目说明
```

## 📊 输出示例

运行完成后，系统会生成以下输出：

- **Markdown报告**: `outputs/report_YYYYMMDD_HHMMSS.md`
- **PDF报告**: `outputs/report_YYYYMMDD_HHMMSS.pdf` (如果配置了PDF生成)
- **可视化图表**: `assets/*.png`
- **日志文件**: `logs/zhilan_YYYYMMDD.log`

## 🔧 高级功能

### 断点续传

系统支持断点续传功能，如果运行过程中意外中断，再次运行时会从断点继续：

```python
# 在logger.py中实现
log_manager.save_checkpoint('data_collection', data)
data = log_manager.load_checkpoint('data_collection')
```

### 自动重试

API调用失败时会自动重试，支持指数退避：

```python
@retry_on_failure(max_attempts=3, backoff_factor=2.0)
def api_call():
    # API调用代码
    pass
```

### 自定义报告风格

支持三种报告风格：
- **brief**: 简明新闻风格，突出要点
- **detailed**: 深度分析风格，详细阐述（默认）
- **academic**: 学术刊物风格，严谨规范

## 🐛 常见问题

### Q1: 安装依赖时出错？
A: 建议使用虚拟环境，确保Python版本≥3.8

### Q2: API调用失败？
A: 检查配置文件中的API密钥是否正确，网络是否正常

### Q3: PDF生成失败？
A: 确保已安装LaTeX环境，或在配置中禁用PDF生成

### Q4: 中文显示乱码？
A: macOS需要安装中文字体，可以修改visualizer.py中的字体设置

## 📝 开发计划

- [x] 多源信息采集
- [x] 智能分析筛选
- [x] 数据可视化
- [x] Markdown报告生成
- [x] PDF报告生成
- [x] 日志和错误处理
- [ ] 多模态图片生成
- [ ] Web界面
- [ ] 定时任务调度
- [ ] 数据库存储

## 📄 许可证

本项目采用 MIT 许可证 - 详见 [LICENSE](LICENSE) 文件

## 👥 贡献者

- 魏知原 (2300012875)

## 🙏 致谢

- 感谢阿里云通义千问提供的大模型API
- 感谢各数据源平台提供的开放API
- 感谢开源社区的各类工具和库

## 📧 联系方式

如有问题或建议，请通过以下方式联系：

- Issue: 在GitHub上提交Issue
- Email: [your-email@example.com]

---

**注意**: 本项目仅供学习和研究使用，请遵守各API平台的使用条款和限制。
