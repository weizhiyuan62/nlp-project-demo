"""
日志和错误处理模块
使用 Hydra 统一管理日志，提供重试机制
"""

import logging
import time
import functools
from typing import Callable, Any


def get_logger(version: str = "2.0.0") -> logging.Logger:
    """
    获取统一的日志记录器
    
    由于使用 Hydra 管理日志，此函数直接返回已配置的 logger
    
    Args:
        version: 系统版本号
        
    Returns:
        配置好的日志记录器
    """
    return logging.getLogger(f"智览系统v{version}")


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
                logger = logging.getLogger("智览系统")
            
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
            logger = logging.getLogger("智览系统")
        
        start_time = time.time()
        logger.info(f"开始执行: {func.__name__}")
        
        try:
            result = func(*args, **kwargs)
            elapsed_time = time.time() - start_time
            logger.info(f"完成执行: {func.__name__} (耗时 {elapsed_time:.2f} 秒)")
            return result
        except Exception as e:
            elapsed_time = time.time() - start_time
            logger.error(f"执行失败: {func.__name__} (耗时 {elapsed_time:.2f} 秒) - {e}")
            raise
    
    return wrapper


def handle_exceptions(func: Callable) -> Callable:
    """
    异常处理装饰器，记录详细的错误信息
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
            logger = logging.getLogger("智览系统")
        
        try:
            return func(*args, **kwargs)
        except Exception as e:
            logger.exception(f"函数 {func.__name__} 发生未捕获的异常: {e}")
            raise
    
    return wrapper
