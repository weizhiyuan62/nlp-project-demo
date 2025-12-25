"""
智览 (ZhiLan) - 基于大模型的智能信息聚合与分析系统
使用 Hydra 进行配置管理
"""

__version__ = "2.0.0"
__author__ = "魏知原"
__email__ = "weizhiyuan@example.com"

from .config import get_config, ConfigManager, init_config, get_logger
from .logger import retry_on_failure, log_execution_time, handle_exceptions
from .data_collector import DataCollector
from .analyzer import InformationAnalyzer
from .visualizer import DataVisualizer
from .report_generator import ReportGenerator
from .latex_compiler import LaTeXCompiler

__all__ = [
    'get_config',
    'ConfigManager',
    'init_config',
    'get_logger',
    'retry_on_failure',
    'log_execution_time',
    'handle_exceptions',
    'DataCollector',
    'InformationAnalyzer',
    'DataVisualizer',
    'ReportGenerator',
    'LaTeXCompiler',
]
