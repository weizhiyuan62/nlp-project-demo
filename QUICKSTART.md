# 🚀 智览系统 - 快速开始指南

## 第一步：环境准备

### 1. 检查Python版本
```bash
python --version
# 需要 Python 3.8+
```

### 2. 创建并激活虚拟环境
```bash
# 使用conda（推荐）
conda create -n zhilan python=3.9
conda activate zhilan

# 或使用venv
python -m venv venv
source venv/bin/activate  # macOS/Linux
# venv\Scripts\activate  # Windows
```

### 3. 安装依赖
```bash
pip install -r requirements.txt
```

## 第二步：配置API密钥

### 1. 编辑配置文件
```bash
# 使用你喜欢的编辑器打开配置文件
code config/config.yaml
# 或
vim config/config.yaml
```

### 2. 填写API密钥

#### 方案A：使用阿里云通义千问（推荐，免费额度）

1. 访问 https://dashscope.aliyun.com/
2. 注册/登录账号
3. 开通"通义千问"服务
4. 获取API-KEY

在配置文件中填写：
```yaml
api:
  llm:
    provider: "qwen"
    api_key: "sk-xxxxxxxxxxxxxx"  # 替换为你的API-KEY
    model: "qwen-plus"
```

#### 方案B：其他可选API

**Bing Search API**（可选）:
```yaml
api:
  bing_search:
    enabled: true  # 改为false可禁用
    api_key: "YOUR_KEY"
```

**NewsAPI**（可选）:
```yaml
api:
  newsapi:
    enabled: true  # 改为false可禁用
    api_key: "YOUR_KEY"
```

**arXiv**（免费，无需密钥）:
```yaml
api:
  arxiv:
    enabled: true  # 学术论文搜索
```

### 3. 最小配置示例

如果你只想快速测试，可以使用以下最小配置：

```yaml
api:
  # 只需要配置大模型API
  llm:
    provider: "qwen"
    api_key: "YOUR_QWEN_API_KEY"
    model: "qwen-plus"
  
  # 禁用其他API（使用免费的arXiv）
  bing_search:
    enabled: false
  
  newsapi:
    enabled: false
  
  arxiv:
    enabled: true  # 免费，无需密钥
```

## 第三步：自定义主题

编辑配置文件中的主题：

```yaml
collection:
  topics:
    - "你感兴趣的主题1"
    - "你感兴趣的主题2"
  
  time_range: "last_3_days"  # 或 today, last_week
```

示例主题：
- 人工智能、机器学习、深度学习
- 量子计算、区块链、Web3
- 经济金融、股市分析
- 科技新闻、创业动态

## 第四步：运行系统

### 方法1：使用启动脚本（推荐）
```bash
./run.sh
```

### 方法2：直接运行Python
```bash
cd src
python main.py
```

## 第五步：查看结果

运行完成后，检查以下目录：

```bash
# 查看生成的报告
ls outputs/
# 示例: report_20251223_143022.md

# 查看可视化图表
ls assets/
# 示例: wordcloud.png, timeline.png

# 查看日志
ls logs/
# 示例: zhilan_20251223.log
```

## 📊 期望输出

### Markdown报告示例
```
# 智览信息分析报告

## 主题: 人工智能 | 机器学习

**生成时间**: 2025年12月23日 14:30
**分析数量**: 35 条高质量信息
**平均评分**: 0.75

## 一、执行摘要
1. GPT-4发布重大更新...
2. 多模态AI技术突破...
...
```

### 可视化图表
- **wordcloud.png**: 热点词云
- **timeline.png**: 时间趋势图
- **source_distribution.png**: 信息源分布
- **score_distribution.png**: 质量评分分布

## ⚠️ 常见问题

### Q1: 提示"API密钥未配置"
**解决**: 
```bash
# 检查配置文件
cat config/config.yaml | grep api_key
# 确保不是 "YOUR_LLM_API_KEY"
```

### Q2: 运行报错"ModuleNotFoundError"
**解决**:
```bash
# 重新安装依赖
pip install -r requirements.txt --force-reinstall
```

### Q3: 没有采集到信息
**解决**:
```bash
# 1. 检查网络连接
ping api.bing.microsoft.com

# 2. 修改主题为更通用的词
# 例如："人工智能" 改为 "AI"

# 3. 启用更多数据源
# 在config.yaml中启用arXiv（免费）
```

### Q4: 中文乱码
**解决**:
```bash
# macOS安装中文字体
brew install --cask font-source-han-sans

# Linux
sudo apt-get install fonts-noto-cjk
```

## 🎯 测试建议

### 第一次运行（简单测试）
```yaml
collection:
  topics:
    - "AI"  # 使用简单主题
  time_range: "today"  # 缩短时间范围
  max_items_per_topic: 10  # 减少数量

output:
  formats:
    - "markdown"  # 只生成MD，跳过PDF
```

### 完整功能测试
```yaml
collection:
  topics:
    - "人工智能"
    - "机器学习"
  time_range: "last_3_days"
  max_items_per_topic: 50

output:
  formats:
    - "markdown"
    - "pdf"  # 需要LaTeX环境
```

## 📈 性能参考

| 配置 | 预计耗时 | 采集量 |
|------|---------|--------|
| 简单测试 | 2-3分钟 | ~10条 |
| 标准配置 | 5-8分钟 | ~30条 |
| 完整分析 | 10-15分钟 | ~100条 |

*实际耗时取决于网络速度和API响应*

## 🎓 下一步

完成第一次运行后，你可以：

1. **调整配置**: 尝试不同的主题和时间范围
2. **查看文档**: 阅读 [USAGE.md](USAGE.md) 了解高级用法
3. **自定义报告**: 修改报告风格和章节
4. **定时运行**: 设置cron定时任务
5. **扩展功能**: 参考源码添加新功能

## 💡 示例场景

### 场景1: 跟踪技术趋势
```yaml
collection:
  topics:
    - "ChatGPT"
    - "AIGC"
    - "Large Language Model"
  time_range: "last_week"
```

### 场景2: 行业新闻监测
```yaml
collection:
  topics:
    - "新能源汽车"
    - "电动车"
  sources:
    official_media: true
    academic: false
```

### 场景3: 学术研究追踪
```yaml
collection:
  topics:
    - "Transformer"
    - "Neural Architecture Search"
  sources:
    official_media: false
    academic: true

api:
  arxiv:
    enabled: true
```

## 🆘 获取帮助

- 📖 查看 [README.md](README.md) 了解项目详情
- 📋 查看 [USAGE.md](USAGE.md) 了解详细用法
- 📊 查看 [PROJECT_SUMMARY.md](PROJECT_SUMMARY.md) 了解项目状态
- 🐛 查看日志文件 `logs/zhilan_*.log` 排查问题

---

**预计完成时间**: 10-15分钟  
**难度等级**: ⭐⭐☆☆☆  
**最后更新**: 2025年12月23日
