"""
多源信息采集模块
支持从Bing Search、NewsAPI、arXiv等多个数据源采集信息
"""

import logging
import requests
import time
from typing import List, Dict, Any
from datetime import datetime
from urllib.parse import quote, urlencode
import hashlib
from concurrent.futures import ThreadPoolExecutor, as_completed
from bs4 import BeautifulSoup


class DataCollector:
    """多源数据采集器"""
    
    def __init__(self, config_manager):
        """
        初始化数据采集器
        
        Args:
            config_manager: 配置管理器实例
        """
        self.config = config_manager
        self.logger = logging.getLogger(f"智览系统v{config_manager.version}")
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
        self.logger.info(f"开始采集信息 - 主题: {topics}, 时间范围: {start_date.date()} 到 {end_date.date()}")
        
        # 重置状态，确保每次运行独立
        self.collected_items = []
        self.seen_hashes = set()
        
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
        从 arXiv OAI-PMH 接口采集学术论文信息
        
        使用 OAI-PMH v2.0 协议，基础 URL: https://oaipmh.arxiv.org/oai
        支持的元数据格式: oai_dc, arXiv, arXivRaw
        
        Args:
            query: 搜索查询（用于关键词过滤）
            start_date: 开始日期
            end_date: 结束日期
            
        Returns:
            采集到的信息列表
        """
        self.logger.info(f"从 arXiv OAI-PMH 采集: {query}")
        
        api_config = self.config.get_api_config('arxiv')
        endpoint = api_config.get('endpoint', 'https://oaipmh.arxiv.org/oai')
        metadata_format = api_config.get('metadata_format', 'arXiv')
        default_sets = api_config.get('default_sets', ['cs'])
        max_records = api_config.get('max_records', 100)
        
        items = []
        
        # 将查询关键词转换为小写用于匹配
        query_keywords = query.lower().split()
        
        try:
            # 为每个配置的 set 采集数据
            for set_spec in default_sets:
                self.logger.info(f"采集 arXiv set: {set_spec}")
                
                # 构建 OAI-PMH ListRecords 请求
                # 注意: OAI-PMH 的 datestamp 不支持按提交日期筛选，只能按修改日期
                params = {
                    'verb': 'ListRecords',
                    'metadataPrefix': metadata_format,
                    'set': set_spec,
                    'from': start_date.strftime('%Y-%m-%d'),
                    'until': end_date.strftime('%Y-%m-%d')
                }
                
                set_items = self._fetch_arxiv_records(endpoint, params, query_keywords, max_records)
                items.extend(set_items)
                
                # 避免请求过快
                time.sleep(1)
            
            self.logger.info(f"从 arXiv 采集到 {len(items)} 条信息")
            return items
            
        except Exception as e:
            self.logger.error(f"arXiv OAI-PMH 调用失败: {e}")
            return []
    
    def _fetch_arxiv_records(self, endpoint: str, params: dict, query_keywords: List[str], max_records: int) -> List[Dict[str, Any]]:
        """
        从 arXiv OAI-PMH 接口获取记录
        
        Args:
            endpoint: OAI-PMH 基础 URL
            params: 请求参数
            query_keywords: 用于过滤的关键词列表
            max_records: 最大记录数
            
        Returns:
            采集到的信息列表
        """
        import xml.etree.ElementTree as ET
        
        items = []
        resumption_token = None
        
        # OAI-PMH 命名空间
        ns = {
            'oai': 'http://www.openarchives.org/OAI/2.0/',
            'arxiv': 'http://arxiv.org/OAI/arXiv/',
            'dc': 'http://purl.org/dc/elements/1.1/',
            'oai_dc': 'http://www.openarchives.org/OAI/2.0/oai_dc/'
        }
        
        while len(items) < max_records:
            try:
                # 如果有 resumptionToken，使用它继续获取
                if resumption_token:
                    request_params = {
                        'verb': 'ListRecords',
                        'resumptionToken': resumption_token
                    }
                else:
                    request_params = params
                
                response = requests.get(endpoint, params=request_params, timeout=60)
                response.raise_for_status()
                
                root = ET.fromstring(response.content)
                
                # 检查是否有错误
                error = root.find('.//oai:error', ns)
                if error is not None:
                    error_code = error.get('code', 'unknown')
                    if error_code == 'noRecordsMatch':
                        self.logger.info("没有匹配的记录")
                        break
                    else:
                        self.logger.warning(f"OAI-PMH 错误: {error_code} - {error.text}")
                        break
                
                # 解析记录
                records = root.findall('.//oai:record', ns)
                
                for record in records:
                    if len(items) >= max_records:
                        break
                    
                    item = self._parse_arxiv_record(record, ns, query_keywords)
                    if item:
                        items.append(item)
                
                # 检查是否有更多记录
                token_elem = root.find('.//oai:resumptionToken', ns)
                if token_elem is not None and token_elem.text:
                    resumption_token = token_elem.text.strip()
                    time.sleep(1)  # 避免请求过快
                else:
                    break
                    
            except requests.exceptions.RequestException as e:
                self.logger.error(f"arXiv 请求失败: {e}")
                break
            except ET.ParseError as e:
                self.logger.error(f"arXiv XML 解析失败: {e}")
                break
        
        return items
    
    def _parse_arxiv_record(self, record, ns: dict, query_keywords: List[str]) -> Dict[str, Any]:
        """
        解析单个 arXiv OAI-PMH 记录
        
        Args:
            record: XML 记录元素
            ns: 命名空间字典
            query_keywords: 用于过滤的关键词列表
            
        Returns:
            解析后的信息字典，如果不匹配则返回 None
        """
        try:
            # 获取元数据
            metadata = record.find('.//oai:metadata', ns)
            if metadata is None:
                return None
            
            # 尝试解析 arXiv 格式
            arxiv_meta = metadata.find('.//arxiv:arXiv', ns)
            
            if arxiv_meta is not None:
                # arXiv 格式
                title_elem = arxiv_meta.find('arxiv:title', ns)
                abstract_elem = arxiv_meta.find('arxiv:abstract', ns)
                id_elem = arxiv_meta.find('arxiv:id', ns)
                created_elem = arxiv_meta.find('arxiv:created', ns)
                categories_elem = arxiv_meta.find('arxiv:categories', ns)
                
                # 获取作者
                authors = []
                for author in arxiv_meta.findall('arxiv:authors/arxiv:author', ns):
                    keyname = author.find('arxiv:keyname', ns)
                    forenames = author.find('arxiv:forenames', ns)
                    if keyname is not None:
                        name = keyname.text
                        if forenames is not None:
                            name = f"{forenames.text} {name}"
                        authors.append(name)
                
                title = title_elem.text.strip() if title_elem is not None and title_elem.text else ''
                abstract = abstract_elem.text.strip() if abstract_elem is not None and abstract_elem.text else ''
                arxiv_id = id_elem.text.strip() if id_elem is not None and id_elem.text else ''
                created = created_elem.text.strip() if created_elem is not None and created_elem.text else ''
                categories = categories_elem.text.strip() if categories_elem is not None and categories_elem.text else ''
                
            else:
                # 尝试 oai_dc 格式
                dc_meta = metadata.find('.//oai_dc:dc', ns)
                if dc_meta is None:
                    return None
                
                title_elem = dc_meta.find('dc:title', ns)
                description_elem = dc_meta.find('dc:description', ns)
                identifier_elem = dc_meta.find('dc:identifier', ns)
                date_elem = dc_meta.find('dc:date', ns)
                
                title = title_elem.text.strip() if title_elem is not None and title_elem.text else ''
                abstract = description_elem.text.strip() if description_elem is not None and description_elem.text else ''
                arxiv_id = identifier_elem.text.strip() if identifier_elem is not None and identifier_elem.text else ''
                created = date_elem.text.strip() if date_elem is not None and date_elem.text else ''
                categories = ''
                authors = [creator.text for creator in dc_meta.findall('dc:creator', ns) if creator.text]
            
            # 关键词过滤（在标题和摘要中搜索）
            if query_keywords:
                text_to_search = f"{title} {abstract}".lower()
                if not any(kw in text_to_search for kw in query_keywords):
                    return None
            
            # 构建 URL
            if arxiv_id and not arxiv_id.startswith('http'):
                url = f"https://arxiv.org/abs/{arxiv_id}"
            else:
                url = arxiv_id
            
            return {
                'title': title,
                'url': url,
                'snippet': abstract[:500] + '...' if len(abstract) > 500 else abstract,
                'date_published': created,
                'source': 'arXiv',
                'source_name': 'arXiv.org',
                'authors': ', '.join(authors[:5]) if authors else '',
                'categories': categories
            }
            
        except Exception as e:
            self.logger.warning(f"解析 arXiv 记录失败: {e}")
            return None
    
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
