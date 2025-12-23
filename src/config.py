"""
配置管理模块
负责加载和验证YAML配置文件
"""

import yaml
import os
from pathlib import Path
from typing import Dict, Any, List
from datetime import datetime, timedelta


class ConfigManager:
    """配置管理器类"""
    
    def __init__(self, config_path: str = None):
        """
        初始化配置管理器
        
        Args:
            config_path: 配置文件路径，默认为config/config.yaml
        """
        if config_path is None:
            # 获取项目根目录
            self.project_root = Path(__file__).parent.parent
            config_path = self.project_root / "config" / "config.yaml"
        else:
            config_path = Path(config_path)
            self.project_root = config_path.parent.parent
        
        self.config_path = config_path
        self.config = self._load_config()
        self._validate_config()
        self._setup_paths()
    
    def _load_config(self) -> Dict[str, Any]:
        """
        加载YAML配置文件
        
        Returns:
            配置字典
        """
        if not self.config_path.exists():
            raise FileNotFoundError(f"配置文件不存在: {self.config_path}")
        
        with open(self.config_path, 'r', encoding='utf-8') as f:
            config = yaml.safe_load(f)
        
        return config
    
    def _validate_config(self):
        """验证配置文件的必要字段"""
        required_sections = ['project', 'collection', 'api', 'analysis', 'report', 'output']
        
        for section in required_sections:
            if section not in self.config:
                raise ValueError(f"配置文件缺少必要部分: {section}")
        
        # 验证API密钥配置
        if self.config['api']['llm']['api_key'] == "YOUR_LLM_API_KEY":
            print("警告: 大模型API密钥未配置，某些功能可能无法使用")
    
    def _setup_paths(self):
        """设置项目路径"""
        # 创建必要的目录
        dirs_to_create = [
            self.get_output_dir(),
            self.get_assets_dir(),
            self.get_log_dir(),
            Path(self.project_root) / self.config.get('error_handling', {}).get('checkpoint', {}).get('checkpoint_dir', 'logs/checkpoints')
        ]
        
        for dir_path in dirs_to_create:
            dir_path.mkdir(parents=True, exist_ok=True)
    
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
        value = self.config
        for key in keys:
            if isinstance(value, dict) and key in value:
                value = value[key]
            else:
                return default
        return value
    
    def get_topics(self) -> List[str]:
        """获取关注的主题列表"""
        return self.config['collection']['topics']
    
    def get_time_range(self) -> tuple:
        """
        获取时间范围
        
        Returns:
            (start_date, end_date) 元组
        """
        time_range = self.config['collection']['time_range']
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
                self.config['collection']['custom_start_date'], 
                '%Y-%m-%d'
            )
            end_date = datetime.strptime(
                self.config['collection']['custom_end_date'], 
                '%Y-%m-%d'
            )
        else:
            raise ValueError(f"不支持的时间范围: {time_range}")
        
        return start_date, end_date
    
    def get_output_dir(self) -> Path:
        """获取输出目录路径"""
        return Path(self.project_root) / self.config['output']['output_dir']
    
    def get_assets_dir(self) -> Path:
        """获取资源目录路径"""
        return Path(self.project_root) / self.config['output']['assets_dir']
    
    def get_log_dir(self) -> Path:
        """获取日志目录路径"""
        return Path(self.project_root) / self.config['logging']['log_dir']
    
    def get_api_config(self, service: str) -> Dict[str, Any]:
        """
        获取指定服务的API配置
        
        Args:
            service: 服务名称 (如 'llm', 'bing_search', 'newsapi')
            
        Returns:
            API配置字典
        """
        return self.config['api'].get(service, {})
    
    def is_service_enabled(self, service: str) -> bool:
        """
        检查服务是否启用
        
        Args:
            service: 服务名称
            
        Returns:
            是否启用
        """
        service_config = self.config['api'].get(service, {})
        return service_config.get('enabled', False)
    
    def get_report_style(self) -> str:
        """获取报告风格"""
        return self.config['report']['style']
    
    def get_report_sections(self) -> List[str]:
        """获取报告章节列表"""
        return self.config['report']['sections']
    
    def should_generate_visualization(self, viz_type: str) -> bool:
        """
        检查是否应该生成指定类型的可视化
        
        Args:
            viz_type: 可视化类型
            
        Returns:
            是否生成
        """
        return self.config['report']['visualization'].get(viz_type, False)
    
    def __repr__(self) -> str:
        return f"ConfigManager(config_path={self.config_path})"


# 创建全局配置实例（可选）
def get_config(config_path: str = None) -> ConfigManager:
    """
    获取配置管理器实例
    
    Args:
        config_path: 配置文件路径
        
    Returns:
        ConfigManager实例
    """
    return ConfigManager(config_path)


if __name__ == "__main__":
    # 测试配置管理器
    config = get_config()
    print(f"项目名称: {config.get('project', 'name')}")
    print(f"关注主题: {config.get_topics()}")
    print(f"时间范围: {config.get_time_range()}")
    print(f"报告风格: {config.get_report_style()}")
    print(f"输出目录: {config.get_output_dir()}")
