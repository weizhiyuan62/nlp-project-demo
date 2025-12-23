"""
数据可视化模块
生成词云图、时间趋势图、信息源分布图等可视化图表
"""

import logging
import matplotlib.pyplot as plt
import matplotlib
matplotlib.use('Agg')  # 使用非GUI后端
import seaborn as sns
from wordcloud import WordCloud
from collections import Counter
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Any
import jieba
import jieba.analyse


# 设置中文字体
plt.rcParams['font.sans-serif'] = ['Arial Unicode MS', 'SimHei', 'DejaVu Sans']
plt.rcParams['axes.unicode_minus'] = False  # 解决负号显示问题


class DataVisualizer:
    """数据可视化器"""
    
    def __init__(self, config_manager):
        """
        初始化数据可视化器
        
        Args:
            config_manager: 配置管理器实例
        """
        self.config = config_manager
        self.logger = logging.getLogger(f"智览系统v{config_manager.version}")
        self.assets_dir = config_manager.get_assets_dir()
        self.viz_config = config_manager.get('report', 'visualization', default={})
        
        # 设置绘图风格
        sns.set_style("whitegrid")
        sns.set_palette("husl")
    
    def generate_all_visualizations(self, analysis_result: Dict[str, Any]) -> Dict[str, str]:
        """
        生成所有配置的可视化图表
        
        Args:
            analysis_result: 分析结果
            
        Returns:
            图表文件路径字典
        """
        self.logger.info("开始生成可视化图表...")
        
        visualization_paths = {}
        items = analysis_result.get('filtered_items', [])
        statistics = analysis_result.get('statistics', {})
        
        # 生成词云图
        if self.config.should_generate_visualization('wordcloud'):
            wordcloud_path = self.generate_wordcloud(items)
            if wordcloud_path:
                visualization_paths['wordcloud'] = wordcloud_path
        
        # 生成时间趋势图
        if self.config.should_generate_visualization('timeline'):
            timeline_path = self.generate_timeline(statistics.get('date_distribution', {}))
            if timeline_path:
                visualization_paths['timeline'] = timeline_path
        
        # 生成信息源分布图
        if self.config.should_generate_visualization('source_distribution'):
            source_dist_path = self.generate_source_distribution(statistics.get('source_distribution', {}))
            if source_dist_path:
                visualization_paths['source_distribution'] = source_dist_path
        
        # 生成评分分布图
        score_dist_path = self.generate_score_distribution(statistics.get('score_distribution', {}))
        if score_dist_path:
            visualization_paths['score_distribution'] = score_dist_path
        
        self.logger.info(f"生成了 {len(visualization_paths)} 个可视化图表")
        return visualization_paths
    
    def generate_wordcloud(self, items: List[Dict[str, Any]]) -> str:
        """
        生成词云图
        
        Args:
            items: 信息列表
            
        Returns:
            图表文件路径
        """
        self.logger.info("生成词云图...")
        
        try:
            # 提取所有文本
            all_text = ' '.join([
                item.get('title', '') + ' ' + item.get('snippet', '')
                for item in items
            ])
            
            # 使用jieba分词
            words = jieba.cut(all_text)
            
            # 过滤停用词和短词
            stopwords = {'的', '了', '在', '是', '和', '与', '等', '为', '将', '有', '中', '对', 
                        '这', '个', '我', '你', '他', '她', '它', '们', '及', '以', '到', '也', '就',
                        '都', '而', '要', '会', '可', '可以', '不', '并', '但', '或', '如', '如果'}
            filtered_words = [w.strip() for w in words if len(w) > 1 and w.strip() not in stopwords and w.strip()]
            
            # 生成词频字符串
            word_freq = Counter(filtered_words)
            text_for_cloud = ' '.join([word for word, count in word_freq.most_common(100)])
            
            if not text_for_cloud:
                self.logger.warning("没有足够的文本生成词云")
                return None
            
            # 创建词云（兼容不同操作系统的字体）
            import os
            font_paths = [
                '/System/Library/Fonts/PingFang.ttc',  # macOS
                '/usr/share/fonts/truetype/arphic/uming.ttc',  # Linux
                'C:/Windows/Fonts/msyh.ttc',  # Windows
                '/usr/share/fonts/truetype/droid/DroidSansFallbackFull.ttf',  # Linux备选
            ]
            font_path = None
            for fp in font_paths:
                if os.path.exists(fp):
                    font_path = fp
                    break
            
            wordcloud = WordCloud(
                width=1200,
                height=600,
                background_color='white',
                font_path=font_path,
                max_words=100,
                relative_scaling=0.5,
                colormap='viridis'
            ).generate(text_for_cloud)
            
            # 绘图
            plt.figure(figsize=(12, 6))
            plt.imshow(wordcloud, interpolation='bilinear')
            plt.axis('off')
            plt.title('热点词云图', fontsize=16, pad=20)
            
            # 保存
            output_path = self.assets_dir / 'wordcloud.png'
            plt.savefig(output_path, dpi=300, bbox_inches='tight')
            plt.close()
            
            self.logger.info(f"词云图已保存: {output_path}")
            return str(output_path)
            
        except Exception as e:
            self.logger.error(f"生成词云图失败: {e}")
            return None
    
    def generate_timeline(self, date_distribution: Dict[str, int]) -> str:
        """
        生成时间趋势图
        
        Args:
            date_distribution: 日期分布数据
            
        Returns:
            图表文件路径
        """
        self.logger.info("生成时间趋势图...")
        
        try:
            if not date_distribution:
                self.logger.warning("没有日期数据生成时间趋势图")
                return None
            
            # 排序日期
            sorted_dates = sorted(date_distribution.items())
            dates = [datetime.strptime(d, '%Y-%m-%d') for d, _ in sorted_dates]
            counts = [c for _, c in sorted_dates]
            
            # 绘图
            plt.figure(figsize=(12, 6))
            plt.plot(dates, counts, marker='o', linewidth=2, markersize=8)
            plt.fill_between(dates, counts, alpha=0.3)
            
            plt.title('信息发布时间趋势', fontsize=16, pad=20)
            plt.xlabel('日期', fontsize=12)
            plt.ylabel('信息数量', fontsize=12)
            plt.grid(True, alpha=0.3)
            plt.xticks(rotation=45)
            plt.tight_layout()
            
            # 保存
            output_path = self.assets_dir / 'timeline.png'
            plt.savefig(output_path, dpi=300, bbox_inches='tight')
            plt.close()
            
            self.logger.info(f"时间趋势图已保存: {output_path}")
            return str(output_path)
            
        except Exception as e:
            self.logger.error(f"生成时间趋势图失败: {e}")
            return None
    
    def generate_source_distribution(self, source_distribution: Dict[str, int]) -> str:
        """
        生成信息源分布饼图
        
        Args:
            source_distribution: 信息源分布数据
            
        Returns:
            图表文件路径
        """
        self.logger.info("生成信息源分布图...")
        
        try:
            if not source_distribution:
                self.logger.warning("没有信息源数据生成分布图")
                return None
            
            # 准备数据
            sources = list(source_distribution.keys())
            counts = list(source_distribution.values())
            
            # 计算百分比
            total = sum(counts)
            percentages = [c/total*100 for c in counts]
            
            # 绘制饼图
            plt.figure(figsize=(10, 8))
            colors = sns.color_palette("husl", len(sources))
            
            wedges, texts, autotexts = plt.pie(
                counts,
                labels=sources,
                autopct='%1.1f%%',
                colors=colors,
                startangle=90,
                textprops={'fontsize': 10}
            )
            
            # 美化文本
            for autotext in autotexts:
                autotext.set_color('white')
                autotext.set_weight('bold')
            
            plt.title('信息源分布', fontsize=16, pad=20)
            plt.axis('equal')
            
            # 保存
            output_path = self.assets_dir / 'source_distribution.png'
            plt.savefig(output_path, dpi=300, bbox_inches='tight')
            plt.close()
            
            self.logger.info(f"信息源分布图已保存: {output_path}")
            return str(output_path)
            
        except Exception as e:
            self.logger.error(f"生成信息源分布图失败: {e}")
            return None
    
    def generate_score_distribution(self, score_distribution: Dict[str, int]) -> str:
        """
        生成评分分布柱状图
        
        Args:
            score_distribution: 评分分布数据
            
        Returns:
            图表文件路径
        """
        self.logger.info("生成评分分布图...")
        
        try:
            if not score_distribution:
                self.logger.warning("没有评分数据生成分布图")
                return None
            
            # 准备数据
            score_ranges = list(score_distribution.keys())
            counts = list(score_distribution.values())
            
            # 绘制柱状图
            plt.figure(figsize=(10, 6))
            bars = plt.bar(score_ranges, counts, color=sns.color_palette("RdYlGn", len(score_ranges)))
            
            # 在柱子上标注数值
            for bar in bars:
                height = bar.get_height()
                plt.text(bar.get_x() + bar.get_width()/2., height,
                        f'{int(height)}',
                        ha='center', va='bottom', fontsize=11)
            
            plt.title('信息质量评分分布', fontsize=16, pad=20)
            plt.xlabel('评分区间', fontsize=12)
            plt.ylabel('信息数量', fontsize=12)
            plt.grid(axis='y', alpha=0.3)
            plt.tight_layout()
            
            # 保存
            output_path = self.assets_dir / 'score_distribution.png'
            plt.savefig(output_path, dpi=300, bbox_inches='tight')
            plt.close()
            
            self.logger.info(f"评分分布图已保存: {output_path}")
            return str(output_path)
            
        except Exception as e:
            self.logger.error(f"生成评分分布图失败: {e}")
            return None


if __name__ == "__main__":
    # 测试可视化器
    from config import get_config
    from logger import LoggerManager
    
    config = get_config()
    log_manager = LoggerManager(config)
    visualizer = DataVisualizer(config, log_manager)
    
    # 模拟测试数据
    test_analysis = {
        'filtered_items': [
            {
                'title': 'GPT-4发布重大更新',
                'snippet': '人工智能领域迎来新突破...',
                'source': 'NewsAPI'
            }
        ] * 10,
        'statistics': {
            'date_distribution': {
                '2025-12-20': 5,
                '2025-12-21': 8,
                '2025-12-22': 12,
                '2025-12-23': 10
            },
            'source_distribution': {
                'NewsAPI': 15,
                'Bing Search': 12,
                'arXiv': 8
            },
            'score_distribution': {
                '0.6-0.7': 5,
                '0.7-0.8': 15,
                '0.8-0.9': 10,
                '0.9-1.0': 5
            }
        }
    }
    
    paths = visualizer.generate_all_visualizations(test_analysis)
    print(f"生成的图表: {paths}")
