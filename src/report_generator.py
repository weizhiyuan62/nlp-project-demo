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
        
        # 各个章节
        for section in self.sections:
            if section == 'executive_summary':
                report_content.append(self._generate_executive_summary(analysis_result))
            elif section == 'key_events':
                report_content.append(self._generate_key_events(analysis_result))
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
        
        header = f"""# 智览信息分析报告

## 主题: {' | '.join(topics)}

**生成时间**: {datetime.now().strftime('%Y年%m月%d日 %H:%M')}  
**报告风格**: {self._get_style_name()}  
**分析数量**: {statistics.get('total_count', 0)} 条高质量信息  
**平均评分**: {statistics.get('average_score', 0):.2f}

---
"""
        return header
    
    def _generate_executive_summary(self, analysis_result: Dict[str, Any]) -> str:
        """生成执行摘要"""
        key_points = analysis_result.get('key_points', [])
        statistics = analysis_result.get('statistics', {})
        
        summary = """## 一、执行摘要

本报告基于多源信息采集和智能分析，对当前关注主题进行了全面梳理。通过大语言模型的深度分析，我们识别出以下核心要点：

"""
        
        if key_points:
            for i, point in enumerate(key_points, 1):
                summary += f"{i}. {point}\n"
        else:
            summary += "暂无关键要点提取。\n"
        
        summary += f"""
**信息概览**:
- 共采集分析 {statistics.get('total_count', 0)} 条高质量信息
- 覆盖 {len(statistics.get('source_distribution', {}))} 个主要信息源
- 时间跨度 {len(statistics.get('date_distribution', {}))} 天
- 平均质量评分 {statistics.get('average_score', 0):.2f}/1.0
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
            title = item.get('title', '无标题')
            snippet = item.get('snippet', '无摘要')[:150]
            source = item.get('source_name', '未知来源')
            score = item.get('score', 0)
            url = item.get('url', '')
            
            events += f"""### {i}. {title}

**评分**: {score:.2f} | **来源**: {source}

{snippet}...

[查看详情]({url})

---

"""
        
        return events
    
    def _generate_trend_analysis(self, analysis_result: Dict[str, Any]) -> str:
        """生成趋势分析"""
        statistics = analysis_result.get('statistics', {})
        date_dist = statistics.get('date_distribution', {})
        
        trend = """## 三、趋势分析

### 信息发布趋势

"""
        
        if date_dist:
            sorted_dates = sorted(date_dist.items())
            
            # 找出发布高峰
            max_date = max(sorted_dates, key=lambda x: x[1])
            min_date = min(sorted_dates, key=lambda x: x[1])
            
            trend += f"""基于时间序列分析，我们观察到以下趋势：

- **发布高峰**: {max_date[0]} ({max_date[1]} 条信息)
- **发布低谷**: {min_date[0]} ({min_date[1]} 条信息)
- **总体趋势**: {'上升' if sorted_dates[-1][1] > sorted_dates[0][1] else '下降'}

信息发布的时间分布反映了该主题在近期的关注度变化。"""
        else:
            trend += "暂无足够的时间序列数据进行趋势分析。"
        
        trend += "\n\n### 信息来源分析\n\n"
        
        source_dist = statistics.get('source_distribution', {})
        if source_dist:
            trend += "主要信息来源分布：\n\n"
            sorted_sources = sorted(source_dist.items(), key=lambda x: x[1], reverse=True)
            for source, count in sorted_sources:
                percentage = count / sum(source_dist.values()) * 100
                trend += f"- **{source}**: {count} 条 ({percentage:.1f}%)\n"
        
        return trend
    
    def _generate_statistics(self, analysis_result: Dict[str, Any], 
                            visualization_paths: Dict[str, str]) -> str:
        """生成数据统计章节"""
        statistics_section = """## 四、数据统计与可视化

本章节通过多维度统计和可视化图表，呈现信息采集和分析的整体情况。

"""
        
        # 插入可视化图表
        if 'wordcloud' in visualization_paths:
            statistics_section += """### 热点词云图

![热点词云](./assets/wordcloud.png)

词云图展示了本次分析中出现频率最高的关键词，词汇大小代表其出现频次。

"""
        
        if 'timeline' in visualization_paths:
            statistics_section += """### 时间趋势图

![时间趋势](./assets/timeline.png)

时间趋势图展示了信息发布的时间分布，反映主题热度的变化。

"""
        
        if 'source_distribution' in visualization_paths:
            statistics_section += """### 信息源分布

![信息源分布](./assets/source_distribution.png)

信息源分布图展示了各数据源的贡献占比。

"""
        
        if 'score_distribution' in visualization_paths:
            statistics_section += """### 质量评分分布

![评分分布](./assets/score_distribution.png)

质量评分分布图展示了筛选后信息的质量分布情况。

"""
        
        return statistics_section
    
    def _generate_recommendations(self, analysis_result: Dict[str, Any]) -> str:
        """生成建议章节"""
        recommendations = """## 五、相关建议

基于以上分析，我们提出以下建议：

### 关注要点

1. **持续监测**: 建议持续关注高评分信息源，及时获取最新动态
2. **深度分析**: 对重点事件进行更深入的调研和分析
3. **趋势预判**: 结合历史数据和当前趋势，预判未来发展方向

### 信息质量

- 本次分析的信息经过多维度评分筛选，整体质量较高
- 建议重点关注评分在0.8以上的信息
- 对于来源单一的信息，建议进行交叉验证

### 后续行动

1. 针对重点事件制定应对策略
2. 定期更新分析报告，把握最新动态
3. 建立信息监测机制，确保不遗漏重要信息
"""
        
        return recommendations
    
    def _generate_appendix(self, analysis_result: Dict[str, Any]) -> str:
        """生成附录"""
        appendix = """## 附录

### 分析方法说明

本报告采用"智览"智能信息聚合与分析系统生成，该系统具有以下特点：

1. **多源采集**: 整合Bing Search、NewsAPI、arXiv等多个数据源
2. **智能筛选**: 使用大语言模型进行多维度评分（相关性、重要性、时效性、可靠性）
3. **深度分析**: 提取关键要点，识别信息关联关系
4. **可视化呈现**: 生成词云、趋势图等多种可视化图表
5. **自动化流程**: 全流程自动化，支持定期更新

### 评分标准

- **相关性**: 0-1分，衡量信息与主题的关联程度
- **重要性**: 0-1分，衡量信息的重要性和影响力
- **时效性**: 0-1分，衡量信息的新鲜度
- **可靠性**: 0-1分，衡量信息来源的权威性

综合评分 = 0.3×相关性 + 0.3×重要性 + 0.2×时效性 + 0.2×可靠性

### 技术栈

- 数据采集: Requests, BeautifulSoup
- 智能分析: 大语言模型API (Qwen/GPT)
- 数据可视化: Matplotlib, Seaborn, WordCloud
- 文本处理: Jieba
- 报告生成: Markdown, LaTeX

---

*本报告由智览系统自动生成于 {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}*
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
            'source_distribution': {'NewsAPI': 15, 'Bing': 12, 'arXiv': 8},
            'date_distribution': {'2025-12-21': 8, '2025-12-22': 12, '2025-12-23': 15}
        }
    }
    
    test_viz_paths = {
        'wordcloud': 'assets/wordcloud.png',
        'timeline': 'assets/timeline.png'
    }
    
    report_path = generator.generate_report(['人工智能'], test_analysis, test_viz_paths)
    print(f"报告已生成: {report_path}")
