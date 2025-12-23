"""
多源信息采集模块
支持从Bing Search、NewsAPI、arXiv等多个数据源采集信息
"""

import requests
import time
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
from urllib.parse import quote, urlencode
import hashlib
from concurrent.futures import ThreadPoolExecutor, as_completed
from bs4 import BeautifulSoup
import re


class DataCollector:
    """多源数据采集器"""
    
    def __init__(self, config_manager, logger_manager):
        """
        初始化数据采集器
        
        Args:
            config_manager: 配置管理器实例
            logger_manager: 日志管理器实例
        """
        self.config = config_manager
        self.logger = logger_manager.get_logger()
        self.logger_manager = logger_manager
        self.collected_items = []
        self.seen_hashes = set()  # 用于去重
    
    def collect_all(self, topics: List[str], start_date: datetime, end_date: datetime) -> List[Dict[str, Any]]:
        """
        从所有启用的数据源采集信息
        
        Args:
            topics: 主题列表
            start_date: 开始日期
            end_date: 结束日期
            
        Returns:
            采集到的信息列表
        """
        self.logger.info(f"开始采集信息 - 主题: {topics}, 时间范围: {start_date} 到 {end_date}")
        
        # 检查断点
        checkpoint = self.logger_manager.load_checkpoint('data_collection')
        if checkpoint:
            self.logger.info("发现断点，从断点继续...")
            self.collected_items = checkpoint.get('collected_items', [])
            self.seen_hashes = set(checkpoint.get('seen_hashes', []))
        
        all_items = []
        
        with ThreadPoolExecutor(max_workers=3) as executor:
            futures = []
            
            # 提交各个数据源的采集任务
            for topic in topics:
                if self.config.is_service_enabled('bing_search'):
                    futures.append(executor.submit(self.collect_from_bing, topic, start_date, end_date))
                
                if self.config.is_service_enabled('newsapi'):
                    futures.append(executor.submit(self.collect_from_newsapi, topic, start_date, end_date))
                
                if self.config.is_service_enabled('arxiv'):
                    futures.append(executor.submit(self.collect_from_arxiv, topic, start_date, end_date))
            
            # 收集结果
            for future in as_completed(futures):
                try:
                    items = future.result()
                    all_items.extend(items)
                except Exception as e:
                    self.logger.error(f"数据采集任务失败: {e}")
        
        # 去重
        unique_items = self._deduplicate(all_items)
        self.logger.info(f"采集完成: 总计 {len(all_items)} 条，去重后 {len(unique_items)} 条")
        
        # 保存断点
        self.logger_manager.save_checkpoint('data_collection', {
            'collected_items': unique_items,
            'seen_hashes': list(self.seen_hashes)
        })
        
        return unique_items
    
    def collect_from_bing(self, query: str, start_date: datetime, end_date: datetime) -> List[Dict[str, Any]]:
        """
        从Bing搜索网页采集信息（模拟浏览器访问）
        
        Args:
            query: 搜索查询
            start_date: 开始日期
            end_date: 结束日期
            
        Returns:
            采集到的信息列表
        """
        self.logger.info(f"从Bing搜索采集（网页爬取）: {query}")
        
        # 构建搜索URL
        search_url = "https://www.bing.com/search"
        
        # 模拟浏览器的HTTP头
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
            'Accept-Encoding': 'gzip, deflate, br',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1'
        }
        
        items = []
        
        try:
            # 分批次请求（每次获取10条结果）
            max_results = 50
            for offset in range(0, max_results, 10):
                params = {
                    'q': query,
                    'first': offset + 1,  # Bing的分页参数
                    'FORM': 'PERE',
                    'setlang': 'zh-CN'
                }
                
                # 添加日期过滤（如果适用）
                freshness = self._get_freshness_param(start_date, end_date)
                if freshness:
                    params['filters'] = f'ex1:"ez{freshness.lower()}"'
                
                response = requests.get(search_url, params=params, headers=headers, timeout=30)
                response.raise_for_status()
                
                # 解析HTML
                soup = BeautifulSoup(response.text, 'html.parser')
                
                # 查找搜索结果
                # Bing的搜索结果通常在 class="b_algo" 的元素中
                results = soup.find_all('li', class_='b_algo')
                
                if not results:
                    self.logger.warning(f"第 {offset//10 + 1} 页未找到搜索结果")
                    break
                
                for result in results:
                    try:
                        # 提取标题和链接
                        title_elem = result.find('h2')
                        if not title_elem:
                            continue
                        
                        link_elem = title_elem.find('a')
                        if not link_elem:
                            continue
                        
                        title = link_elem.get_text(strip=True)
                        url = link_elem.get('href', '')
                        
                        # 提取摘要
                        snippet_elem = result.find('p') or result.find('div', class_='b_caption')
                        snippet = snippet_elem.get_text(strip=True) if snippet_elem else ''
                        
                        # 提取日期（如果有）
                        date_elem = result.find('span', class_='news_dt')
                        date_published = date_elem.get_text(strip=True) if date_elem else datetime.now().isoformat()
                        
                        # 提取来源网站
                        cite_elem = result.find('cite')
                        source_name = cite_elem.get_text(strip=True).split('/')[0] if cite_elem else 'Unknown'
                        
                        item = {
                            'title': title,
                            'url': url,
                            'snippet': snippet,
                            'date_published': date_published,
                            'source': 'Bing Search',
                            'source_name': source_name
                        }
                        items.append(item)
                        
                    except Exception as e:
                        self.logger.warning(f"解析单个搜索结果失败: {e}")
                        continue
                
                # 添加延迟，避免请求过快
                time.sleep(1)
                
                # 如果结果少于10条，说明已经是最后一页
                if len(results) < 10:
                    break
            
            self.logger.info(f"从Bing采集到 {len(items)} 条信息")
            return items
            
        except requests.exceptions.RequestException as e:
            self.logger.error(f"Bing搜索网页访问失败: {e}")
            return []
        except Exception as e:
            self.logger.error(f"解析Bing搜索结果失败: {e}")
            return []
    
    def collect_from_newsapi(self, query: str, start_date: datetime, end_date: datetime) -> List[Dict[str, Any]]:
        """
        从NewsAPI采集新闻信息
        
        Args:
            query: 搜索查询
            start_date: 开始日期
            end_date: 结束日期
            
        Returns:
            采集到的信息列表
        """
        self.logger.info(f"从NewsAPI采集: {query}")
        
        api_config = self.config.get_api_config('newsapi')
        api_key = api_config.get('api_key')
        endpoint = api_config.get('endpoint')
        
        if api_key == "YOUR_NEWSAPI_KEY":
            self.logger.warning("NewsAPI密钥未配置，跳过")
            return []
        
        params = {
            'q': query,
            'apiKey': api_key,
            'from': start_date.strftime('%Y-%m-%d'),
            'to': end_date.strftime('%Y-%m-%d'),
            'language': 'zh',
            'sortBy': 'relevancy',
            'pageSize': 50
        }
        
        try:
            response = requests.get(endpoint, params=params, timeout=30)
            response.raise_for_status()
            data = response.json()
            
            items = []
            for article in data.get('articles', []):
                item = {
                    'title': article.get('title', ''),
                    'url': article.get('url', ''),
                    'snippet': article.get('description', '') or article.get('content', ''),
                    'date_published': article.get('publishedAt', datetime.now().isoformat()),
                    'source': 'NewsAPI',
                    'source_name': article.get('source', {}).get('name', 'Unknown')
                }
                items.append(item)
            
            self.logger.info(f"从NewsAPI采集到 {len(items)} 条信息")
            return items
            
        except requests.exceptions.RequestException as e:
            self.logger.error(f"NewsAPI调用失败: {e}")
            return []
    
    def collect_from_arxiv(self, query: str, start_date: datetime, end_date: datetime) -> List[Dict[str, Any]]:
        """
        从arXiv API采集学术论文信息
        
        Args:
            query: 搜索查询
            start_date: 开始日期
            end_date: 结束日期
            
        Returns:
            采集到的信息列表
        """
        self.logger.info(f"从arXiv采集: {query}")
        
        api_config = self.config.get_api_config('arxiv')
        endpoint = api_config.get('endpoint')
        
        # 构建查询参数
        search_query = quote(f'all:{query}')
        max_results = self.config.get('collection', 'max_items_per_topic', default=50)
        url = f"{endpoint}?search_query={search_query}&start=0&max_results={max_results}&sortBy=submittedDate&sortOrder=descending"
        
        try:
            response = requests.get(url, timeout=30)
            response.raise_for_status()
            
            # 解析XML响应
            import xml.etree.ElementTree as ET
            root = ET.fromstring(response.content)
            
            # 定义命名空间
            ns = {
                'atom': 'http://www.w3.org/2005/Atom',
                'arxiv': 'http://arxiv.org/schemas/atom'
            }
            
            items = []
            for entry in root.findall('atom:entry', ns):
                published = entry.find('atom:published', ns)
                if published is not None:
                    pub_date = datetime.fromisoformat(published.text.replace('Z', '+00:00'))
                    # 过滤日期范围
                    if pub_date < start_date or pub_date > end_date:
                        continue
                
                title_elem = entry.find('atom:title', ns)
                summary_elem = entry.find('atom:summary', ns)
                link_elem = entry.find('atom:id', ns)
                
                item = {
                    'title': title_elem.text.strip() if title_elem is not None else '',
                    'url': link_elem.text if link_elem is not None else '',
                    'snippet': summary_elem.text.strip() if summary_elem is not None else '',
                    'date_published': published.text if published is not None else datetime.now().isoformat(),
                    'source': 'arXiv',
                    'source_name': 'arXiv.org'
                }
                items.append(item)
            
            self.logger.info(f"从arXiv采集到 {len(items)} 条信息")
            return items
            
        except Exception as e:
            self.logger.error(f"arXiv API调用失败: {e}")
            return []
    
    def _deduplicate(self, items: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        对采集到的信息进行去重
        
        Args:
            items: 待去重的信息列表
            
        Returns:
            去重后的信息列表
        """
        unique_items = []
        
        for item in items:
            # 使用标题和URL的组合计算哈希值
            content = f"{item.get('title', '')}{item.get('url', '')}"
            content_hash = hashlib.md5(content.encode('utf-8')).hexdigest()
            
            if content_hash not in self.seen_hashes:
                self.seen_hashes.add(content_hash)
                unique_items.append(item)
        
        return unique_items
    
    def _get_freshness_param(self, start_date: datetime, end_date: datetime) -> str:
        """
        根据日期范围生成Bing的freshness参数
        
        Args:
            start_date: 开始日期
            end_date: 结束日期
            
        Returns:
            freshness参数值
        """
        days_diff = (end_date - start_date).days
        
        if days_diff <= 1:
            return 'Day'
        elif days_diff <= 7:
            return 'Week'
        elif days_diff <= 30:
            return 'Month'
        else:
            return 'Year'


if __name__ == "__main__":
    # 测试数据采集器
    from config import get_config
    from logger import LoggerManager
    
    config = get_config()
    log_manager = LoggerManager(config)
    collector = DataCollector(config, log_manager)
    
    # 测试采集
    topics = config.get_topics()[:1]  # 只测试第一个主题
    start_date, end_date = config.get_time_range()
    
    items = collector.collect_all(topics, start_date, end_date)
    print(f"采集到 {len(items)} 条信息")
    if items:
        print(f"示例: {items[0]}")
