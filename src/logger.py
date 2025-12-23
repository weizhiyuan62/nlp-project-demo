"""
日志和错误处理模块
提供统一的日志记录、错误捕获、重试机制和断点续传功能
"""

import logging
import colorlog
import json
import time
import functools
from pathlib import Path
from typing import Callable, Any, Optional
from datetime import datetime


class LoggerManager:
    """日志管理器"""
    
    def __init__(self, config_manager):
        """
        初始化日志管理器
        
        Args:
            config_manager: 配置管理器实例
        """
        self.config = config_manager
        self.log_dir = config_manager.get_log_dir()
        self.logger = self._setup_logger()
        self.checkpoint_dir = Path(config_manager.project_root) / \
            config_manager.get('error_handling', 'checkpoint', 'checkpoint_dir', default='logs/checkpoints')
        self.checkpoint_dir.mkdir(parents=True, exist_ok=True)
    
    def _setup_logger(self) -> logging.Logger:
        """设置日志记录器"""
        logger = logging.getLogger('智览系统')
        
        # 获取配置的日志级别
        log_level = self.config.get('logging', 'level', default='INFO')
        logger.setLevel(getattr(logging, log_level))
        
        # 清除已有的处理器
        logger.handlers.clear()
        
        # 控制台处理器（彩色输出）
        if self.config.get('logging', 'console', default=True):
            console_handler = logging.StreamHandler()
            console_handler.setLevel(getattr(logging, log_level))
            
            # 彩色格式化
            color_formatter = colorlog.ColoredFormatter(
                '%(log_color)s%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                datefmt='%Y-%m-%d %H:%M:%S',
                log_colors={
                    'DEBUG': 'cyan',
                    'INFO': 'green',
                    'WARNING': 'yellow',
                    'ERROR': 'red',
                    'CRITICAL': 'red,bg_white',
                }
            )
            console_handler.setFormatter(color_formatter)
            logger.addHandler(console_handler)
        
        # 文件处理器
        if self.config.get('logging', 'file', default=True):
            log_file = self.log_dir / f"zhilan_{datetime.now().strftime('%Y%m%d')}.log"
            file_handler = logging.FileHandler(log_file, encoding='utf-8')
            file_handler.setLevel(getattr(logging, log_level))
            
            file_formatter = logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(funcName)s:%(lineno)d - %(message)s',
                datefmt='%Y-%m-%d %H:%M:%S'
            )
            file_handler.setFormatter(file_formatter)
            logger.addHandler(file_handler)
        
        return logger
    
    def get_logger(self) -> logging.Logger:
        """获取日志记录器"""
        return self.logger
    
    def save_checkpoint(self, checkpoint_name: str, data: dict):
        """
        保存断点数据
        
        Args:
            checkpoint_name: 断点名称
            data: 要保存的数据
        """
        if not self.config.get('error_handling', 'checkpoint', 'enabled', default=True):
            return
        
        checkpoint_file = self.checkpoint_dir / f"{checkpoint_name}.json"
        try:
            with open(checkpoint_file, 'w', encoding='utf-8') as f:
                json.dump({
                    'timestamp': datetime.now().isoformat(),
                    'data': data
                }, f, ensure_ascii=False, indent=2)
            self.logger.debug(f"保存断点: {checkpoint_name}")
        except Exception as e:
            self.logger.error(f"保存断点失败 {checkpoint_name}: {e}")
    
    def load_checkpoint(self, checkpoint_name: str) -> Optional[dict]:
        """
        加载断点数据
        
        Args:
            checkpoint_name: 断点名称
            
        Returns:
            断点数据，如果不存在返回None
        """
        if not self.config.get('error_handling', 'checkpoint', 'enabled', default=True):
            return None
        
        checkpoint_file = self.checkpoint_dir / f"{checkpoint_name}.json"
        if not checkpoint_file.exists():
            return None
        
        try:
            with open(checkpoint_file, 'r', encoding='utf-8') as f:
                checkpoint = json.load(f)
            self.logger.debug(f"加载断点: {checkpoint_name}")
            return checkpoint.get('data')
        except Exception as e:
            self.logger.error(f"加载断点失败 {checkpoint_name}: {e}")
            return None
    
    def clear_checkpoint(self, checkpoint_name: str):
        """
        清除断点数据
        
        Args:
            checkpoint_name: 断点名称
        """
        checkpoint_file = self.checkpoint_dir / f"{checkpoint_name}.json"
        if checkpoint_file.exists():
            try:
                checkpoint_file.unlink()
                self.logger.debug(f"清除断点: {checkpoint_name}")
            except Exception as e:
                self.logger.error(f"清除断点失败 {checkpoint_name}: {e}")


def retry_on_failure(max_attempts: int = 3, backoff_factor: float = 2.0, 
                     initial_delay: float = 1.0, exceptions: tuple = (Exception,)):
    """
    重试装饰器，支持指数退避
    
    Args:
        max_attempts: 最大重试次数
        backoff_factor: 退避因子
        initial_delay: 初始延迟（秒）
        exceptions: 需要捕获并重试的异常类型
    """
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs) -> Any:
            # 尝试从args或kwargs中获取logger
            logger = None
            for arg in args:
                if isinstance(arg, logging.Logger):
                    logger = arg
                    break
                if hasattr(arg, 'logger'):
                    logger = arg.logger
                    break
            
            if logger is None:
                logger = logging.getLogger('智览系统')
            
            delay = initial_delay
            last_exception = None
            
            for attempt in range(1, max_attempts + 1):
                try:
                    return func(*args, **kwargs)
                except exceptions as e:
                    last_exception = e
                    if attempt == max_attempts:
                        logger.error(f"{func.__name__} 达到最大重试次数 {max_attempts}")
                        raise
                    
                    logger.warning(
                        f"{func.__name__} 失败 (尝试 {attempt}/{max_attempts}): {e}, "
                        f"将在 {delay:.1f} 秒后重试..."
                    )
                    time.sleep(delay)
                    delay *= backoff_factor
            
            # 不应该到达这里，但为了类型检查
            if last_exception:
                raise last_exception
        
        return wrapper
    return decorator


def log_execution_time(func: Callable) -> Callable:
    """
    记录函数执行时间的装饰器
    """
    @functools.wraps(func)
    def wrapper(*args, **kwargs) -> Any:
        # 尝试获取logger
        logger = None
        for arg in args:
            if isinstance(arg, logging.Logger):
                logger = arg
                break
            if hasattr(arg, 'logger'):
                logger = arg.logger
                break
        
        if logger is None:
            logger = logging.getLogger('智览系统')
        
        start_time = time.time()
        logger.info(f"开始执行: {func.__name__}")
        
        try:
            result = func(*args, **kwargs)
            elapsed_time = time.time() - start_time
            logger.info(f"完成执行: {func.__name__} (耗时: {elapsed_time:.2f}秒)")
            return result
        except Exception as e:
            elapsed_time = time.time() - start_time
            logger.error(f"执行失败: {func.__name__} (耗时: {elapsed_time:.2f}秒) - 错误: {e}")
            raise
    
    return wrapper


def handle_exceptions(func: Callable) -> Callable:
    """
    异常处理装饰器，捕获并记录所有异常
    """
    @functools.wraps(func)
    def wrapper(*args, **kwargs) -> Any:
        # 尝试获取logger
        logger = None
        for arg in args:
            if isinstance(arg, logging.Logger):
                logger = arg
                break
            if hasattr(arg, 'logger'):
                logger = arg.logger
                break
        
        if logger is None:
            logger = logging.getLogger('智览系统')
        
        try:
            return func(*args, **kwargs)
        except Exception as e:
            logger.exception(f"{func.__name__} 发生异常: {e}")
            raise
    
    return wrapper


if __name__ == "__main__":
    # 测试日志系统
    from config import get_config
    
    config = get_config()
    log_manager = LoggerManager(config)
    logger = log_manager.get_logger()
    
    logger.debug("这是一条调试信息")
    logger.info("这是一条普通信息")
    logger.warning("这是一条警告信息")
    logger.error("这是一条错误信息")
    
    # 测试断点保存和加载
    test_data = {"step": "data_collection", "progress": 50}
    log_manager.save_checkpoint("test_checkpoint", test_data)
    loaded_data = log_manager.load_checkpoint("test_checkpoint")
    print(f"加载的断点数据: {loaded_data}")
    
    # 测试重试装饰器
    @retry_on_failure(max_attempts=3, initial_delay=0.5)
    def test_retry_function(should_fail: bool = True):
        logger.info("执行测试函数")
        if should_fail:
            raise ValueError("测试异常")
        return "成功"
    
    try:
        test_retry_function()
    except ValueError:
        logger.info("重试测试完成")
