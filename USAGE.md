# 使用示例和快速入门指南

## 快速开始

### 1. 基本使用

最简单的使用方式是直接运行：

```bash
# 激活虚拟环境
conda activate zhilan

# 运行系统
./run.sh
# 或者
cd src && python main.py
```

### 2. 自定义配置

编辑 `config/config.yaml` 来自定义你的分析需求：

```yaml
# 修改关注主题
collection:
  topics:
    - "你关心的主题1"
    - "你关心的主题2"
  
  # 修改时间范围
  time_range: "last_week"  # 可选: today, last_3_days, last_week, custom
```

### 3. 仅生成Markdown报告

如果你不需要PDF，可以在配置中禁用：

```yaml
output:
  formats:
    - "markdown"  # 移除 "pdf"
```

### 4. 调整分析敏感度

修改评分权重和筛选阈值：

```yaml
analysis:
  # 调整各维度权重
  scoring:
    relevance_weight: 0.4    # 提高相关性权重
    importance_weight: 0.3
    timeliness_weight: 0.2
    reliability_weight: 0.1
  
  # 调整筛选阈值（0-1）
  min_score: 0.7  # 提高阈值，获得更高质量的信息
```

### 5. 选择报告风格

```yaml
report:
  style: "brief"  # 简明风格
  # style: "detailed"  # 详细风格（默认）
  # style: "academic"  # 学术风格
```

## 使用技巧

### 技巧1: API密钥管理

为了安全，建议使用环境变量或单独的配置文件：

```bash
# 创建本地配置（不会被git追踪）
cp config/config.yaml config/config.yaml.local

# 在.local文件中填写真实的API密钥
# 然后修改代码加载逻辑使用.local文件
```

### 技巧2: 定时任务

使用cron定时运行分析：

```bash
# 编辑crontab
crontab -e

# 添加定时任务（每天早上9点运行）
0 9 * * * cd /path/to/my-project-demo && ./run.sh >> logs/cron.log 2>&1
```

### 技巧3: 批量分析多个主题

创建多个配置文件，分别分析不同主题：

```bash
# 复制配置文件
cp config/config.yaml config/config_ai.yaml
cp config/config.yaml config/config_finance.yaml

# 修改每个配置文件的主题
# 然后分别运行
python src/main.py --config config/config_ai.yaml
```

### 技巧4: 断点续传

如果分析中断，再次运行会自动从断点继续：

```python
# 系统会自动检查checkpoints目录
# 如果需要重新开始，删除checkpoint文件：
rm logs/checkpoints/*.json
```

## 常见使用场景

### 场景1: 技术趋势追踪

```yaml
collection:
  topics:
    - "GPT-5"
    - "Multimodal AI"
    - "AI Agent"
  sources:
    official_media: true
    academic: true
    social_media: false
```

### 场景2: 行业动态监测

```yaml
collection:
  topics:
    - "金融科技"
    - "区块链应用"
  time_range: "today"
  sources:
    official_media: true
    academic: false
```

### 场景3: 学术论文追踪

```yaml
collection:
  topics:
    - "Large Language Models"
    - "Reinforcement Learning"
  sources:
    official_media: false
    academic: true
    social_media: false

api:
  arxiv:
    enabled: true
  bing_search:
    enabled: false
  newsapi:
    enabled: false
```

## 输出文件说明

运行完成后会生成以下文件：

```
outputs/
├── report_20251223_143022.md   # Markdown报告
└── report_20251223_143022.pdf  # PDF报告（如果启用）

assets/
├── wordcloud.png               # 词云图
├── timeline.png                # 时间趋势图
├── source_distribution.png     # 信息源分布图
└── score_distribution.png      # 评分分布图

logs/
├── zhilan_20251223.log        # 运行日志
└── checkpoints/               # 断点文件
    ├── data_collection.json
    └── analysis.json
```

## 性能优化建议

1. **减少采集数量**: 降低 `max_items_per_topic` 值
2. **并行处理**: 系统已自动使用多线程，无需额外配置
3. **缓存结果**: 启用断点续传功能
4. **批量处理**: 一次处理多个主题比多次运行单个主题更高效

## 故障排除

### 问题1: API调用失败
```bash
# 检查网络连接
ping api.bing.microsoft.com

# 验证API密钥
curl -H "Ocp-Apim-Subscription-Key: YOUR_KEY" \
  "https://api.bing.microsoft.com/v7.0/search?q=test"
```

### 问题2: 内存不足
```yaml
# 减少采集数量
collection:
  max_items_per_topic: 20  # 从50降到20
```

### 问题3: PDF生成失败
```bash
# 检查LaTeX安装
xelatex --version

# 如果未安装，禁用PDF生成或安装LaTeX
brew install --cask mactex  # macOS
```

## 进阶用法

### 编程方式调用

```python
from src import ZhiLanSystem

# 创建系统实例
system = ZhiLanSystem(config_path='config/config.yaml')

# 运行分析
system.run()
```

### 模块化使用

```python
from src.config import get_config
from src.data_collector import DataCollector
from src.logger import LoggerManager

# 只使用数据采集功能
config = get_config()
log_manager = LoggerManager(config)
collector = DataCollector(config, log_manager)

topics = ["AI"]
start_date, end_date = config.get_time_range()
items = collector.collect_all(topics, start_date, end_date)

print(f"采集到 {len(items)} 条信息")
```

---

更多信息请参考 [README.md](README.md)
