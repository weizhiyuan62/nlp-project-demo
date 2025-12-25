"""
报告生成模块
基于分析结果和可视化图表生成结构化的Markdown报告
"""

import logging
from typing import Dict, Any, List
from datetime import datetime
from pathlib import Path


class ReportGenerator:
    """报告生成器"""
    
    def __init__(self, config_manager):
        """
        初始化报告生成器
        
        Args:
            config_manager: 配置管理器实例
        """
        self.config = config_manager
        self.logger = logging.getLogger(f"智览系统v{config_manager.version}")
        self.output_dir = config_manager.get_output_dir()
        self.report_style = config_manager.get_report_style()
        self.sections = config_manager.get_report_sections()
    
    def generate_report(self, 
                       topics: List[str],
                       analysis_result: Dict[str, Any],
                       visualization_paths: Dict[str, str]) -> str:
        """
        生成完整的Markdown报告
        
        Args:
            topics: 主题列表
            analysis_result: 分析结果
            visualization_paths: 可视化图表路径字典
            
        Returns:
            报告文件路径
        """
        self.logger.info("开始生成报告...")
        
        # 构建报告内容
        report_content = []
        
        # 标题和元数据
        report_content.append(self._generate_header(topics, analysis_result))
        
        # markdown TOC add
        report_content.append('[TOC]\n')
        
        # 各个章节
        for section in self.sections:
            if section == 'executive_summary':
                report_content.append(self._generate_executive_summary(analysis_result))
            elif section == 'key_events':
                report_content.append(self._generate_key_events(analysis_result))
            elif section == 'overall_analysis':
                report_content.append(self._generate_overall_analysis(analysis_result, topics))
            elif section == 'trend_analysis':
                report_content.append(self._generate_trend_analysis(analysis_result))
            elif section == 'statistics':
                report_content.append(self._generate_statistics(analysis_result, visualization_paths))
            elif section == 'recommendations':
                report_content.append(self._generate_recommendations(analysis_result))
        
        # 附录
        report_content.append(self._generate_appendix(analysis_result))
        
        # 合并内容
        full_report = '\n\n'.join(report_content)
        
        # 保存报告
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        report_filename = f"report_{timestamp}.md"
        report_path = self.output_dir / report_filename
        
        with open(report_path, 'w', encoding='utf-8') as f:
            f.write(full_report)
        
        self.logger.info(f"报告已生成: {report_path}")
        return str(report_path)
    
    def _generate_header(self, topics: List[str], analysis_result: Dict[str, Any]) -> str:
        """生成报告头部"""
        statistics = analysis_result.get('statistics', {})
        topic_str = ' | '.join(topics)
        gen_time = datetime.now().strftime('%Y年%m月%d日 %H:%M')
        style_name = self._get_style_name()
        total_count = statistics.get('total_count', 0)
        avg_score = statistics.get('average_score', 0)
        
        header = f"""# 智览信息分析报告

> **主题**: {topic_str}

| 项目 | 内容 |
|:-----|:-----|
| 生成时间 | {gen_time} |
| 报告风格 | {style_name} |
| 分析数量 | {total_count} 条高质量信息 |
| 平均评分 | {avg_score:.2f} / 1.0 |

---
"""
        return header
    
    def _generate_executive_summary(self, analysis_result: Dict[str, Any]) -> str:
        """生成执行摘要"""
        key_points = analysis_result.get('key_points', [])
        statistics = analysis_result.get('statistics', {})
        
        total_count = statistics.get('total_count', 0)
        source_count = len(statistics.get('source_distribution', {}))
        date_count = len(statistics.get('date_distribution', {}))
        avg_score = statistics.get('average_score', 0)
        
        summary = """## 一、执行摘要

本报告基于多源信息采集和智能分析，对当前关注主题进行了全面梳理。通过大语言模型的深度分析，我们识别出以下核心要点：

"""
        
        # 关键要点列表
        if key_points:
            for i, point in enumerate(key_points, 1):
                summary += f"{i}. {point}\n"
        else:
            summary += "*暂无关键要点提取。*\n"
        
        # 信息概览表格
        summary += f"""
### 信息概览

| 指标 | 数值 |
|:-----|-----:|
| 高质量信息数 | {total_count} 条 |
| 信息源数量 | {source_count} 个 |
| 时间跨度 | {date_count} 天 |
| 平均质量评分 | {avg_score:.2f} / 1.0 |
"""
        
        return summary
    
    def _generate_key_events(self, analysis_result: Dict[str, Any]) -> str:
        """生成重点事件解读"""
        filtered_items = analysis_result.get('filtered_items', [])
        
        # 选取评分最高的前10条
        top_items = sorted(filtered_items, key=lambda x: x.get('score', 0), reverse=True)[:10]
        
        events = """## 二、重点事件解读

以下是经过智能评分筛选的高质量信息要点：

"""
        
        for i, item in enumerate(top_items, 1):
            title = item.get('title', '无标题').strip()
            snippet = item.get('snippet', '').strip()
            # 截取摘要，保证完整句子
            if len(snippet) > 150:
                snippet = snippet[:150].rsplit('。', 1)[0]
                if not snippet.endswith('。'):
                    snippet += '...'
            source = item.get('source_name', '未知来源')
            score = item.get('score', 0)
            url = item.get('url', '#')
            
            events += f"""### {i}. {title}

> **评分**: `{score:.2f}` &nbsp;|&nbsp; **来源**: {source}

{snippet if snippet else '*暂无摘要*'}

🔗 [查看原文]({url})

"""
        
        return events
    
    def _generate_overall_analysis(self, analysis_result: Dict[str, Any], topics: List[str]) -> str:
        """生成总体分析章节"""
        overall_analysis = analysis_result.get('overall_analysis', '')
        topic_str = '、'.join(topics)
        
        section = f"""## 三、智览总体分析

> 基于以上采集的信息和重点事件，智览系统对「{topic_str}」进行的深度总体分析如下：

"""
        
        if overall_analysis:
            # 确保 LLM 返回的分析内容格式统一，将可能的 ## 标题降级为 ###
            formatted = overall_analysis.replace('## ', '### ').replace('# ', '### ')
            section += formatted
        else:
            section += '*暂无总体分析数据。*'
        
        return section
    
    def _generate_trend_analysis(self, analysis_result: Dict[str, Any]) -> str:
        """生成趋势分析"""
        statistics = analysis_result.get('statistics', {})
        date_dist = statistics.get('date_distribution', {})
        
        trend = """## 四、趋势分析

### 4.1 信息发布趋势

"""
        
        if date_dist:
            sorted_dates = sorted(date_dist.items())
            max_date = max(sorted_dates, key=lambda x: x[1])
            min_date = min(sorted_dates, key=lambda x: x[1])
            trend_direction = '📈 上升' if sorted_dates[-1][1] > sorted_dates[0][1] else '📉 下降'
            
            trend += f"""基于时间序列分析，我们观察到以下趋势：

| 指标 | 日期 | 数量 |
|:-----|:-----|-----:|
| 发布高峰 | {max_date[0]} | {max_date[1]} 条 |
| 发布低谷 | {min_date[0]} | {min_date[1]} 条 |

**总体趋势**: {trend_direction}

信息发布的时间分布反映了该主题在近期的关注度变化。
"""
        else:
            trend += "*暂无足够的时间序列数据进行趋势分析。*\n"
        
        trend += "\n### 4.2 信息来源分析\n\n"
        
        source_dist = statistics.get('source_distribution', {})
        if source_dist:
            total = sum(source_dist.values())
            sorted_sources = sorted(source_dist.items(), key=lambda x: x[1], reverse=True)
            
            trend += "| 来源 | 数量 | 占比 |\n|:-----|-----:|-----:|\n"
            for source, count in sorted_sources:
                percentage = count / total * 100
                trend += f"| {source} | {count} 条 | {percentage:.1f}% |\n"
        else:
            trend += "*暂无信息来源数据。*\n"
        
        return trend
    
    def _generate_statistics(self, analysis_result: Dict[str, Any], 
                            visualization_paths: Dict[str, str]) -> str:
        """生成数据统计章节"""
        statistics_section = """## 五、数据统计与可视化

本章节通过多维度统计和可视化图表，呈现信息采集和分析的整体情况。

"""
        
        viz_items = [
            ('wordcloud', '5.1 热点词云图', 'wordcloud.png', 
             '词云图展示了本次分析中出现频率最高的关键词，词汇大小代表其出现频次。'),
            ('timeline', '5.2 时间趋势图', 'timeline.png', 
             '时间趋势图展示了信息发布的时间分布，反映主题热度的变化。'),
            ('source_distribution', '5.3 信息源分布', 'source_distribution.png', 
             '信息源分布图展示了各数据源的贡献占比。'),
            ('score_distribution', '5.4 质量评分分布', 'score_distribution.png', 
             '质量评分分布图展示了筛选后信息的质量分布情况。'),
        ]
        
        has_viz = False
        for key, title, filename, desc in viz_items:
            if key in visualization_paths:
                has_viz = True
                statistics_section += f"""### {title}

<div align="center">

![{title}](./assets/{filename})

</div>

{desc}

"""
        
        if not has_viz:
            statistics_section += "*暂无可视化图表。*\n"
        
        return statistics_section
    
    def _generate_recommendations(self, analysis_result: Dict[str, Any]) -> str:
        """生成建议章节"""
        statistics = analysis_result.get('statistics', {})
        avg_score = statistics.get('average_score', 0)
        
        # 根据平均分给出不同建议
        quality_note = '整体质量较高' if avg_score >= 0.7 else '建议扩大采集范围以获取更多高质量信息'
        
        recommendations = f"""## 六、相关建议

基于以上分析，我们提出以下建议：

### 6.1 关注要点

| 序号 | 建议 | 说明 |
|:----:|:-----|:-----|
| 1 | **持续监测** | 持续关注高评分信息源，及时获取最新动态 |
| 2 | **深度分析** | 对重点事件进行更深入的调研和分析 |
| 3 | **趋势预判** | 结合历史数据和当前趋势，预判未来发展方向 |

### 6.2 信息质量

- 本次分析的信息经过多维度评分筛选，{quality_note}
- 建议重点关注评分在 **0.8 以上** 的信息
- 对于来源单一的信息，建议进行交叉验证

### 6.3 后续行动

1. 针对重点事件制定应对策略
2. 定期更新分析报告，把握最新动态
3. 建立信息监测机制，确保不遗漏重要信息
"""
        
        return recommendations
    
    def _generate_appendix(self, analysis_result: Dict[str, Any]) -> str:
        """生成附录"""
        gen_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        
        appendix = f"""---

## 附录

### A. 分析方法说明

本报告采用 **智览** 智能信息聚合与分析系统生成，该系统具有以下特点：

| 特点 | 说明 |
|:-----|:-----|
| 多源采集 | 整合 Google Search (SerpAPI)、NewsAPI、arXiv 等多个数据源 |
| 智能筛选 | 使用大语言模型进行多维度评分（相关性、重要性、时效性、可靠性） |
| 深度分析 | 提取关键要点，识别信息关联关系 |
| 可视化呈现 | 生成词云、趋势图等多种可视化图表 |
| 自动化流程 | 全流程自动化，支持定期更新 |

### B. 评分标准

| 维度 | 权重 | 说明 |
|:-----|:----:|:-----|
| 相关性 (relevance) | 30% | 衡量信息与主题的关联程度 |
| 重要性 (importance) | 30% | 衡量信息的重要性和影响力 |
| 时效性 (timeliness) | 20% | 衡量信息的新鲜度 |
| 可靠性 (reliability) | 20% | 衡量信息来源的权威性 |

**综合评分公式**: `score = 0.3×relevance + 0.3×importance + 0.2×timeliness + 0.2×reliability`

### C. 技术栈

| 模块 | 技术 |
|:-----|:-----|
| 数据采集 | Requests, SerpAPI, BeautifulSoup |
| 智能分析 | 大语言模型 API (Qwen / GPT) |
| 数据可视化 | Matplotlib, Seaborn, WordCloud |
| 文本处理 | Jieba, NLTK |
| 报告生成 | Markdown, LaTeX |

---

<div align="center">

*本报告由智览系统自动生成于 {gen_time}*

</div>
"""
        
        return appendix
    
    def _get_style_name(self) -> str:
        """获取报告风格名称"""
        style_names = {
            'brief': '简明新闻风格',
            'detailed': '深度分析风格',
            'academic': '学术刊物风格'
        }
        return style_names.get(self.report_style, self.report_style)


if __name__ == "__main__":
    # 测试报告生成器
    from config import get_config
    from logger import LoggerManager
    
    config = get_config()
    log_manager = LoggerManager(config)
    generator = ReportGenerator(config, log_manager)
    
    # 模拟测试数据
    test_analysis = {
        'filtered_items': [
            {
                'title': 'GPT-4发布重大更新',
                'snippet': '人工智能领域迎来新突破',
                'source_name': 'TechCrunch',
                'score': 0.9,
                'url': 'https://example.com'
            }
        ],
        'key_points': ['要点1', '要点2'],
        'statistics': {
            'total_count': 35,
            'average_score': 0.75,
            'source_distribution': {'NewsAPI': 15, 'Google (SerpAPI)': 12, 'arXiv': 8},
            'date_distribution': {'2025-12-21': 8, '2025-12-22': 12, '2025-12-23': 15}
        }
    }
    
    test_viz_paths = {
        'wordcloud': 'assets/wordcloud.png',
        'timeline': 'assets/timeline.png'
    }
    
    report_path = generator.generate_report(['Test Case: 自然语言处理'], test_analysis, test_viz_paths)
    print(f"报告已生成: {report_path}")
