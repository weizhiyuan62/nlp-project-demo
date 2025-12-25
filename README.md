# 智览 (ZhiLan) - 基于大模型的智能信息聚合与分析系统

[![Python Version](https://img.shields.io/badge/python-3.8%2B-blue)](https://www.python.org/)
[![Hydra](https://img.shields.io/badge/config-Hydra-89b8cd)](https://hydra.cc/)
[![License](https://img.shields.io/badge/license-MIT-green)](LICENSE)

## 项目简介

**智览**是一个基于大语言模型的智能信息聚合与分析系统，能够自动从多个数据源采集信息，通过AI进行智能筛选和分析，并生成高质量的可视化分析报告。

### 主要功能

- **多源信息采集**: 整合Google Search(SerpAPI代理)、NewsAPI、arXiv等多个数据源  
- **智能分析筛选**: 使用大模型进行多维度评分（相关性、重要性、时效性、可靠性）  
- **数据可视化**: 自动生成词云图、时间趋势图、信息源分布图等  
- **报告自动生成**: 生成结构化的Markdown和PDF格式报告  
- **Hydra配置管理**: 使用Hydra统一管理配置和日志，支持多次运行结果分类存储

## 快速开始

### 环境要求

- Python 3.8+, 推荐使用3.10
- LaTeX环境（用于生成PDF，可选）
  - macOS: `brew install --cask mactex`
  - Linux: `sudo apt-get install texlive-full`

### 安装步骤

1. **克隆项目**

```bash
git clone <repository-url>
cd nlp-project-demo
```

2. **conda虚拟环境配置**
```bash
conda create -n zhilan python=3.10 -y
conda activate zhilan
pip install -r requirements.txt
```

3. **配置API密钥**

编辑 [conf/api/default.yaml](conf/api/default.yaml) 文件，填入你的API密钥：

```yaml
# 搜索引擎配置（SerpAPI 代理的 Google 搜索）
serpapi_google:
  enabled: true
  api_key: "YOUR_SERPAPI_KEY"
  google_domain: "google.com"
  gl: "us"
  hl: "zh-cn"
  num: 10
  max_results: 50

# 新闻API配置
newsapi:
  enabled: true
  api_key: "YOUR_NEWSAPI_KEY"

# 大模型API配置
llm:
  provider: "qwen"
  api_key: "YOUR_LLM_API_KEY"
  model: "qwen3-max"
```

### 运行系统

```bash
python src/main.py
```

### 命令行参数覆盖

Hydra支持通过命令行覆盖配置：
或者直接修改conf中对应的配置文件

```bash
# 修改主题
python main.py collection.topics="[大模型, ChatGPT]"

# 修改时间范围
python main.py collection.time_range=last_week

# 修改报告风格
python main.py report.style=academic

# 组合多个参数
python main.py collection.topics="[人工智能]" report.style=brief
```

## 配置说明

### Hydra 配置结构

```
conf/
├── config.yaml          # 主配置文件
└── api/
    └── default.yaml     # API密钥配置
```

### 运行目录管理

每次运行会在 `outputs/` 下创建按日期时间分类的目录：

```
outputs/
├── 2025-12-23/
│   ├── 10-30-00/           # 第一次运行
│   │   ├── .hydra/         # Hydra配置备份
│   │   ├── zhilan.log      # 运行日志
│   │   └── results/        # 结果目录
│   │       ├── assets/     # 可视化图表
│   │       ├── report_*.md # Markdown报告
│   │       └── report_*.pdf# PDF报告
│   └── 14-20-00/           # 第二次运行
│       └── ...
└── 2025-12-24/
    └── ...
```

### 主要配置项

#### 信息采集配置
```yaml
collection:
  topics:
    - "人工智能"
    - "机器学习"
  time_range: "last_3_days"  # today, last_3_days, last_week, custom
  max_items_per_topic: 50
```

#### 分析配置
```yaml
analysis:
  scoring:
    relevance_weight: 0.3
    importance_weight: 0.3
    timeliness_weight: 0.2
    reliability_weight: 0.2
  min_score: 0.6
```

#### 报告配置
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

#### SerpAPI (Google Search)
1. 访问 [SerpAPI 官网](https://serpapi.com/)
2. 注册并获取 `api_key`
3. 参考官方文档配置参数：`google_domain`、`gl`、`hl` 等

#### NewsAPI
1. 访问 [NewsAPI官网](https://newsapi.org/)
2. 注册账号
3. 在个人页面获取API密钥

#### 通义千问API
1. 访问 [阿里云DashScope](https://dashscope.aliyun.com/)
2. 开通服务
3. 获取API-KEY

## 项目结构

```
nlp-project-demo/
├── conf/                    # Hydra 配置目录
│   ├── config.yaml          # 主配置文件
│   └── api/                 # API配置
│       └── default.yaml     # API密钥配置
├── src/                     # 源代码
│   ├── main.py              # 主程序入口 (@hydra.main)
│   ├── config.py            # 配置管理模块 (Hydra + OmegaConf)
│   ├── logger.py            # 日志和错误处理（装饰器）
│   ├── data_collector.py    # 多源数据采集模块
│   ├── analyzer.py          # LLM智能分析模块（多线程并行评分）
│   ├── visualizer.py        # 数据可视化模块
│   ├── report_generator.py  # Markdown报告生成模块
│   └── latex_compiler.py    # LaTeX/PDF编译模块
├── templates/               # LaTeX模板
│   └── report_template.tex  # PDF报告模板
├── proposal/                # 项目计划书
│   └── proposal.tex         # LaTeX格式计划书
├── outputs/                 # Hydra 输出目录 (自动按日期分类)
│   └── YYYY-MM-DD/
│       └── HH-MM-SS/
│           ├── .hydra/      # Hydra配置快照
│           ├── zhilan.log   # 运行日志
│           └── results/     # 结果目录
│               ├── assets/  # 可视化图表
│               ├── report_*.md   # Markdown报告
│               └── report_*.pdf  # PDF报告
├── requirements.txt         # Python依赖包列表
├── report.md                # 项目演示报告
└── README.md                # 项目说明文档
```

## 日志系统

系统使用 Hydra 统一管理日志，每个模块使用统一的 logger：

```python
import logging
logger = logging.getLogger(f"智览系统v{version}")
```

日志输出到每次运行的目录：`outputs/YYYY-MM-DD/HH-MM-SS/zhilan.log`

## 高级功能

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

## Q&A

### Q1: 安装依赖时出错？
A: 建议使用虚拟环境，确保Python版本≥3.8

### Q2: API调用失败？
A: 检查配置文件中的API密钥是否正确，网络是否正常

### Q3: 中文显示乱码？
A: 可以修改visualizer.py中的字体设置

## 开发计划

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

## 许可证

本项目采用 MIT 许可证 - 详见 [LICENSE](LICENSE) 文件

## 贡献者

- 魏知原 (2300012875)

## 致谢

- 感谢阿里云通义千问提供的大模型API
- 感谢各数据源平台提供的开放API
- 感谢开源社区的各类工具和库

## 联系方式

如有问题或建议，请通过以下方式联系：

- Issue: 在GitHub上提交Issue
- Email: [weizhiyuan12875@stu.pku.edu.cn]

---

**注意**: 本项目仅供学习和研究使用，请遵守各API平台的使用条款和限制。
