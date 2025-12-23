"""
智览 (ZhiLan) - 基于大模型的智能信息聚合与分析系统
"""

__version__ = "1.0.0"
__author__ = "魏知原"
__email__ = "weizhiyuan@example.com"

from .config import get_config, ConfigManager
from .logger import LoggerManager
from .data_collector import DataCollector
from .analyzer import InformationAnalyzer
from .visualizer import DataVisualizer
from .report_generator import ReportGenerator
from .latex_compiler import LaTeXCompiler

__all__ = [
    'get_config',
    'ConfigManager',
    'LoggerManager',
    'DataCollector',
    'InformationAnalyzer',
    'DataVisualizer',
    'ReportGenerator',
    'LaTeXCompiler',
]
