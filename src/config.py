"""
配置管理模块
使用 Hydra 进行统一配置管理，支持 OmegaConf
"""

import logging
from pathlib import Path
from typing import Any, List, Optional
from datetime import datetime, timedelta
from omegaconf import DictConfig, OmegaConf


def get_logger(name: str = "智览系统") -> logging.Logger:
    """
    获取统一的日志记录器
    
    Args:
        name: 日志记录器名称
        
    Returns:
        配置好的日志记录器
    """
    return logging.getLogger(name)


class ConfigManager:
    """配置管理器类 - Hydra版本"""
    
    def __init__(self, cfg: DictConfig, working_dir: Optional[Path] = None):
        """
        初始化配置管理器
        
        Args:
            cfg: Hydra 配置对象
            working_dir: 工作目录（Hydra运行目录）
        """
        self.cfg = cfg
        self.version = cfg.project.version
        
        # 工作目录（Hydra 自动设置的输出目录）
        if working_dir is None:
            working_dir = Path.cwd()
        self.working_dir = Path(working_dir)
        
        # 项目根目录（src的父目录）
        self.project_root = Path(__file__).parent.parent
        
        # 设置结果和资源目录
        self._setup_paths()
        
        # 获取日志记录器
        self.logger = get_logger(f"智览系统v{self.version}")
    
    def _setup_paths(self):
        """设置项目路径"""
        # 结果目录（在 Hydra 运行目录下）
        self.results_dir = self.working_dir / self.cfg.output.results_dir
        self.results_dir.mkdir(parents=True, exist_ok=True)
        
        # 资源目录（在结果目录下）
        self.assets_dir = self.results_dir / self.cfg.output.assets_dir
        self.assets_dir.mkdir(parents=True, exist_ok=True)
    
    def get(self, *keys, default=None) -> Any:
        """
        获取配置值，支持嵌套访问
        
        Args:
            *keys: 配置键路径
            default: 默认值
            
        Returns:
            配置值
            
        Example:
            config.get('api', 'llm', 'model')
        """
        value = self.cfg
        for key in keys:
            if hasattr(value, key):
                value = getattr(value, key)
            elif isinstance(value, dict) and key in value:
                value = value[key]
            else:
                return default
        return value
    
    def get_topics(self) -> List[str]:
        """获取关注的主题列表"""
        return list(self.cfg.collection.topics)
    
    def get_time_range(self) -> tuple:
        """
        获取时间范围
        
        Returns:
            (start_date, end_date) 元组
        """
        time_range = self.cfg.collection.time_range
        today = datetime.now()
        
        if time_range == 'today':
            start_date = today.replace(hour=0, minute=0, second=0, microsecond=0)
            end_date = today
        elif time_range == 'last_3_days':
            start_date = today - timedelta(days=3)
            end_date = today
        elif time_range == 'last_week':
            start_date = today - timedelta(days=7)
            end_date = today
        elif time_range == 'custom':
            start_date = datetime.strptime(
                self.cfg.collection.custom_start_date, 
                '%Y-%m-%d'
            )
            end_date = datetime.strptime(
                self.cfg.collection.custom_end_date, 
                '%Y-%m-%d'
            )
        else:
            raise ValueError(f"不支持的时间范围: {time_range}")
        
        return start_date, end_date
    
    def get_results_dir(self) -> Path:
        """获取结果目录路径"""
        return self.results_dir
    
    def get_assets_dir(self) -> Path:
        """获取资源目录路径"""
        return self.assets_dir
    
    def get_output_dir(self) -> Path:
        """获取输出目录路径（兼容旧接口）"""
        return self.results_dir
    
    def get_log_dir(self) -> Path:
        """获取日志目录路径"""
        return self.working_dir
    
    def get_api_config(self, service: str) -> dict:
        """
        获取指定服务的API配置
        
        Args:
            service: 服务名称 (bing_search, newsapi, arxiv, llm, image_generation)
            
        Returns:
            API配置字典
        """
        if hasattr(self.cfg.api, service):
            return OmegaConf.to_container(getattr(self.cfg.api, service), resolve=True)
        return {}
    
    def is_service_enabled(self, service: str) -> bool:
        """
        检查服务是否启用
        
        Args:
            service: 服务名称
            
        Returns:
            是否启用
        """
        api_config = self.get_api_config(service)
        return api_config.get('enabled', False)
    
    def get_report_style(self) -> str:
        """获取报告风格"""
        return self.cfg.report.style
    
    def get_report_sections(self) -> List[str]:
        """获取报告章节配置"""
        return list(self.cfg.report.sections)
    
    def should_generate_visualization(self, viz_type: str) -> bool:
        """
        检查是否应该生成指定类型的可视化
        
        Args:
            viz_type: 可视化类型 (wordcloud, timeline, source_distribution, topic_network)
            
        Returns:
            是否生成
        """
        return self.cfg.report.visualization.get(viz_type, False)
    
    def get_retry_config(self) -> dict:
        """获取重试配置"""
        return OmegaConf.to_container(self.cfg.error_handling.retry, resolve=True)
    
    def __repr__(self) -> str:
        return f"ConfigManager(version={self.version}, working_dir={self.working_dir})"


# 全局配置实例（在 Hydra 初始化后设置）
_config_instance: Optional[ConfigManager] = None


def init_config(cfg: DictConfig, working_dir: Optional[Path] = None) -> ConfigManager:
    """
    初始化全局配置实例
    
    Args:
        cfg: Hydra 配置对象
        working_dir: 工作目录
        
    Returns:
        配置管理器实例
    """
    global _config_instance
    _config_instance = ConfigManager(cfg, working_dir)
    return _config_instance


def get_config() -> Optional[ConfigManager]:
    """
    获取全局配置实例
    
    Returns:
        配置管理器实例
    """
    return _config_instance
