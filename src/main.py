"""
智览系统主程序
使用 Hydra 进行配置管理，整合所有模块实现完整的自动化信息分析流程
"""

import sys
import logging
from pathlib import Path

import hydra
from omegaconf import DictConfig, OmegaConf

# 添加src目录到路径
sys.path.insert(0, str(Path(__file__).parent))

from config import ConfigManager, init_config, get_logger
from logger import log_execution_time, handle_exceptions
from data_collector import DataCollector
from analyzer import InformationAnalyzer
from visualizer import DataVisualizer
from report_generator import ReportGenerator
from latex_compiler import LaTeXCompiler


class ZhiLanSystem:
    """智览系统主类"""
    
    def __init__(self, config: ConfigManager):
        """
        初始化智览系统
        
        Args:
            config: 配置管理器实例
        """
        self.config = config
        self.logger = get_logger(f"智览系统v{config.version}")
        
        self.logger.info("=" * 60)
        self.logger.info(f"智览信息聚合与分析系统启动 v{config.version}")
        self.logger.info(f"工作目录: {config.working_dir}")
        self.logger.info(f"结果目录: {config.results_dir}")
        self.logger.info("=" * 60)
        
        # 初始化各个模块
        self.collector = DataCollector(self.config)
        self.analyzer = InformationAnalyzer(self.config)
        self.visualizer = DataVisualizer(self.config)
        self.report_generator = ReportGenerator(self.config)
        self.latex_compiler = LaTeXCompiler(self.config)
    
    @log_execution_time
    @handle_exceptions
    def run(self):
        """运行完整的分析流程"""
        self.logger.info("开始执行完整分析流程...")
        
        # Step 1: 获取配置
        topics = self.config.get_topics()
        start_date, end_date = self.config.get_time_range()
        
        self.logger.info(f"分析主题: {', '.join(topics)}")
        self.logger.info(f"时间范围: {start_date.date()} 至 {end_date.date()}")
        
        # Step 2: 数据采集
        self.logger.info("\n" + "=" * 60)
        self.logger.info("Step 1: 多源信息采集")
        self.logger.info("=" * 60)
        
        collected_items = self.collector.collect_all(topics, start_date, end_date)
        
        if not collected_items:
            self.logger.warning("未采集到任何信息，流程终止")
            return
        
        # Step 3: 智能分析
        self.logger.info("\n" + "=" * 60)
        self.logger.info("Step 2: 智能信息分析")
        self.logger.info("=" * 60)
        
        analysis_result = self.analyzer.analyze_items(collected_items, topics)
        
        if not analysis_result.get('filtered_items'):
            self.logger.warning("没有通过质量筛选的信息，流程终止")
            return
        
        # Step 4: 数据可视化
        self.logger.info("\n" + "=" * 60)
        self.logger.info("Step 3: 数据可视化")
        self.logger.info("=" * 60)
        
        visualization_paths = self.visualizer.generate_all_visualizations(analysis_result)
        
        # Step 5: 报告生成
        self.logger.info("\n" + "=" * 60)
        self.logger.info("Step 4: 报告生成")
        self.logger.info("=" * 60)
        
        markdown_report = self.report_generator.generate_report(
            topics, analysis_result, visualization_paths
        )
        
        self.logger.info(f"Markdown报告已生成: {markdown_report}")
        
        # Step 6: PDF编译（可选）
        if 'pdf' in self.config.get('output', 'formats', default=['markdown']):
            self.logger.info("\n" + "=" * 60)
            self.logger.info("Step 5: PDF编译")
            self.logger.info("=" * 60)
            
            pdf_report = self.latex_compiler.markdown_to_pdf(markdown_report)
            
            if pdf_report:
                self.logger.info(f"PDF报告已生成: {pdf_report}")
            else:
                self.logger.warning("PDF编译失败，但Markdown报告已生成")
        
        # 完成
        self.logger.info("\n" + "=" * 60)
        self.logger.info("分析流程完成！")
        self.logger.info("=" * 60)
        
        # 输出结果摘要
        self._print_summary(analysis_result, markdown_report)
    
    def _print_summary(self, analysis_result, report_path):
        """
        打印结果摘要
        
        Args:
            analysis_result: 分析结果
            report_path: 报告路径
        """
        statistics = analysis_result.get('statistics', {})
        
        summary = f"""
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
                        结果摘要
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

✓ 采集信息总数: {len(analysis_result.get('scored_items', []))} 条
✓ 高质量信息: {statistics.get('total_count', 0)} 条
✓ 平均质量评分: {statistics.get('average_score', 0):.2f}/1.0
✓ 覆盖信息源: {len(statistics.get('source_distribution', {}))} 个
✓ 时间跨度: {len(statistics.get('date_distribution', {}))} 天

✓ 报告文件: {report_path}

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
"""
        
        print(summary)
        self.logger.info(summary)


@hydra.main(version_base=None, config_path="../conf", config_name="config")
def main(cfg: DictConfig):
    """
    主函数 - 使用 Hydra 进行配置管理
    
    Args:
        cfg: Hydra 配置对象
    """
    try:
        # 打印配置信息
        logger = logging.getLogger(f"智览系统v{cfg.project.version}")
        logger.info("配置加载完成")
        logger.debug(f"完整配置:\n{OmegaConf.to_yaml(cfg)}")
        
        config = init_config(cfg, Path.cwd())  # 初始化全局配置
        
        system = ZhiLanSystem(config)          # 创建系统实例
        
        system.run()                           # 运行分析流程
        
    except KeyboardInterrupt:
        print("\n\n用户中断执行")
        sys.exit(0)
    except Exception as e:
        print(f"\n\n系统执行出错: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
