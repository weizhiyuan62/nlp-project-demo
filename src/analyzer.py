"""
智能信息分析模块
使用大语言模型对采集的信息进行评分、筛选和关联分析
"""

import logging
import json
import requests
from typing import List, Dict, Any, Tuple
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor, as_completed
import threading

# 美观的多进度条显示
from rich.progress import Progress, SpinnerColumn, BarColumn, TextColumn, TaskProgressColumn, TimeElapsedColumn, TimeRemainingColumn
from rich.console import Console
from rich.live import Live
from rich.table import Table
from rich.panel import Panel


class InformationAnalyzer:
    """信息智能分析器"""
    
    def __init__(self, config_manager):
        """
        初始化信息分析器
        
        Args:
            config_manager: 配置管理器实例
        """
        self.config = config_manager
        self.logger = logging.getLogger(f"智览系统v{config_manager.version}")
        self.llm_config = config_manager.get_api_config('llm')
        self.scoring_weights = config_manager.get('analysis', 'scoring', default={})
        self.min_score = config_manager.get('analysis', 'min_score', default=0.6)
    
    def analyze_items(self, items: List[Dict[str, Any]], topics: List[str]) -> Dict[str, Any]:
        """
        对采集的信息进行全面分析
        
        Args:
            items: 待分析的信息列表
            topics: 主题列表
            
        Returns:
            分析结果字典，包含评分、筛选后的信息、关键要点等
        """
        self.logger.info(f"开始分析 {len(items)} 条信息")
        
        if not items:
            self.logger.warning("没有信息需要分析")
            return {
                'scored_items': [],
                'filtered_items': [],
                'key_points': [],
                'relationships': [],
                'statistics': {},
                'analysis_time': datetime.now().isoformat()
            }
        
        # 批量评分
        scored_items = self._score_items_batch(items, topics)
        
        # 筛选高分信息
        filtered_items = [item for item in scored_items if item.get('score', 0) >= self.min_score]
        self.logger.info(f"筛选后保留 {len(filtered_items)} 条高质量信息")
        
        # 提取关键要点
        key_points = self._extract_key_points(filtered_items, topics)
        
        # 识别关联关系
        relationships = self._identify_relationships(filtered_items)
        
        # 统计分析
        statistics = self._compute_statistics(filtered_items)
        
        # 生成总体分析（使用LLM整合所有信息生成深度分析）
        overall_analysis = self._generate_overall_analysis(filtered_items, key_points, topics, statistics)
        
        result = {
            'scored_items': scored_items,
            'filtered_items': filtered_items,
            'key_points': key_points,
            'relationships': relationships,
            'statistics': statistics,
            'overall_analysis': overall_analysis,
            'analysis_time': datetime.now().isoformat()
        }
        
        return result
    
    def _score_items_batch(self, items: List[Dict[str, Any]], topics: List[str]) -> List[Dict[str, Any]]:
        """
        批量对信息进行评分（多线程并行处理，带美观多进度条显示）
        
        Args:
            items: 信息列表
            topics: 主题列表
            
        Returns:
            带评分的信息列表
        """
        self.logger.info("开始批量评分（多线程并行）...")
        
        batch_size = 10  # 每批处理10条信息
        max_workers = 5  # 并行线程数，可根据 API 限流调整
        
        # 将 items 分成多个 batch
        batches = []
        for i in range(0, len(items), batch_size):
            batch = items[i:i+batch_size]
            batches.append((i, batch))  # 记录原始索引和批次数据
        
        total_batches = len(batches)
        
        # 用于存放结果的字典，按原始索引排序
        results_dict: Dict[int, List[Dict[str, Any]]] = {}
        results_lock = threading.Lock()
        
        # 用于跟踪每个 worker 的状态
        worker_status: Dict[int, Dict[str, Any]] = {}
        status_lock = threading.Lock()
        
        console = Console()
        
        def score_single_batch(batch_info: Tuple[int, List[Dict[str, Any]]], worker_id: int, 
                              progress: Progress, task_ids: Dict[int, Any], overall_task: Any) -> None:
            """线程任务：评分单个批次"""
            batch_start_idx, batch = batch_info
            batch_num = batch_start_idx // batch_size + 1
            
            # 更新 worker 进度条描述
            with status_lock:
                worker_status[worker_id] = {'batch': batch_num, 'status': '处理中'}
            progress.update(task_ids[worker_id], description=f"[cyan]Worker {worker_id+1}[/] 批次 {batch_num}/{total_batches}")
            progress.start_task(task_ids[worker_id])
            
            try:
                batch_scores = self._call_llm_for_scoring(batch, topics)
                
                scored_batch = []
                for j, item in enumerate(batch):
                    item_copy = item.copy()
                    if j < len(batch_scores):
                        item_copy.update(batch_scores[j])
                    else:
                        # 如果LLM返回结果不足，使用默认评分
                        item_copy['score'] = 0.5
                        item_copy['relevance'] = 0.65
                        item_copy['importance'] = 0.5
                        item_copy['timeliness'] = 0.5
                        item_copy['reliability'] = 0.5
                    scored_batch.append(item_copy)
                
                with results_lock:
                    results_dict[batch_start_idx] = scored_batch
                
                # 更新 worker 状态为完成
                with status_lock:
                    worker_status[worker_id] = {'batch': batch_num, 'status': '完成'}
                progress.update(task_ids[worker_id], completed=100, 
                              description=f"[green]Worker {worker_id+1}[/] 批次 {batch_num} ✓")
                    
            except Exception as e:
                self.logger.error(f"批次评分失败 (起始索引 {batch_start_idx}): {e}")
                # 使用默认评分
                scored_batch = []
                for item in batch:
                    item_copy = item.copy()
                    item_copy['score'] = 0.5
                    item_copy['relevance'] = 0.5
                    item_copy['importance'] = 0.5
                    item_copy['timeliness'] = 0.5
                    item_copy['reliability'] = 0.5
                    scored_batch.append(item_copy)
                with results_lock:
                    results_dict[batch_start_idx] = scored_batch
                
                with status_lock:
                    worker_status[worker_id] = {'batch': batch_num, 'status': '失败'}
                progress.update(task_ids[worker_id], completed=100,
                              description=f"[red]Worker {worker_id+1}[/] 批次 {batch_num} ✗")
            
            # 更新总进度
            progress.advance(overall_task)
        
        # 使用 rich Progress 显示多进度条
        with Progress(
            SpinnerColumn(),
            TextColumn("[bold blue]{task.description}"),
            BarColumn(bar_width=30),
            TaskProgressColumn(),
            TimeElapsedColumn(),
            console=console,
            transient=False,
        ) as progress:
            
            # 创建总进度任务
            overall_task = progress.add_task(
                f"[bold yellow]📊 总进度 ({len(items)} 条数据, {total_batches} 批次)[/]", 
                total=total_batches
            )
            
            # 为每个 worker 创建进度条
            task_ids: Dict[int, Any] = {}
            for i in range(max_workers):
                task_id = progress.add_task(
                    f"[dim]Worker {i+1}[/] 等待中...", 
                    total=100,
                    start=False
                )
                task_ids[i] = task_id
            
            # 使用线程池并行处理
            with ThreadPoolExecutor(max_workers=max_workers) as executor:
                # 分配任务给 workers
                futures = []
                for idx, batch_info in enumerate(batches):
                    worker_id = idx % max_workers
                    future = executor.submit(
                        score_single_batch, 
                        batch_info, 
                        worker_id, 
                        progress, 
                        task_ids, 
                        overall_task
                    )
                    futures.append(future)
                
                # 等待所有任务完成
                for future in as_completed(futures):
                    try:
                        future.result()
                    except Exception as e:
                        self.logger.error(f"线程执行异常: {e}")
        
        # 按原始顺序合并结果
        scored_items = []
        for batch_start_idx in sorted(results_dict.keys()):
            scored_items.extend(results_dict[batch_start_idx])
        
        # 打印完成统计
        console.print(Panel(
            f"[bold green]✅ 评分完成[/]\n"
            f"• 总数据量: {len(scored_items)} 条\n"
            f"• 批次数量: {total_batches} 批\n"
            f"• 并行线程: {max_workers} 个",
            title="[bold]评分统计[/]",
            border_style="green"
        ))
        
        self.logger.info(f"完成 {len(scored_items)} 条信息的并行评分")
        return scored_items
    
    def _call_llm_for_scoring(self, items: List[Dict[str, Any]], topics: List[str]) -> List[Dict[str, Any]]:
        """
        调用大模型对信息进行评分
        
        Args:
            items: 信息列表
            topics: 主题列表
            
        Returns:
            评分结果列表
        """
        # 构建prompt
        prompt = self._build_scoring_prompt(items, topics)
        
        # 调用大模型API
        if self.llm_config.get('provider') == 'qwen':
            return self._call_qwen_api(prompt, task_type='scoring')
        else:
            self.logger.warning(f"不支持的LLM提供商: {self.llm_config.get('provider')}")
            return []
    
    def _build_scoring_prompt(self, items: List[Dict[str, Any]], topics: List[str]) -> str:
        """构建评分prompt"""
        items_text = "\n\n".join([
            f"[信息{i+1}]\n标题: {item.get('title', '')}\n摘要: {item.get('snippet', '')[:200]}\n来源: {item.get('source_name', '')}\n发布时间: {item.get('date_published', '')}"
            for i, item in enumerate(items)
        ])
        
        prompt = f"""你是一位专业的信息分析专家。请对以下信息进行多维度评分。

关注主题: {', '.join(topics)}

待评分信息:
{items_text}

请从以下四个维度对每条信息进行0-1之间的评分:
1. 相关性(relevance): 与主题的相关程度
2. 重要性(importance): 信息的重要性和影响力
3. 时效性(timeliness): 信息的新鲜度和时效性
4. 可靠性(reliability): 信息来源的可靠性

最后给出综合评分(score)，计算公式为:
score = 0.3*relevance + 0.3*importance + 0.2*timeliness + 0.2*reliability

请严格按照以下JSON格式返回评分结果（不要添加任何其他文字）:
[
  {{
    "index": 1,
    "relevance": 0.8,
    "importance": 0.7,
    "timeliness": 0.9,
    "reliability": 0.8,
    "score": 0.8,
    "brief_analysis": "简要分析原因"
  }},
  ...
]
"""
        return prompt
    
    def _extract_key_points(self, items: List[Dict[str, Any]], topics: List[str]) -> List[str]:
        """
        提取关键要点
        
        Args:
            items: 已筛选的高质量信息列表
            topics: 主题列表
            
        Returns:
            关键要点列表
        """
        self.logger.info("提取关键要点...")
        
        if not items:
            return []
        
        # 选取评分最高的前20条信息
        top_items = sorted(items, key=lambda x: x.get('score', 0), reverse=True)[:20]
        
        # 构建prompt
        items_text = "\n\n".join([
            f"标题: {item.get('title', '')}\n摘要: {item.get('snippet', '')[:300]}\n评分: {item.get('score', 0):.2f}"
            for item in top_items
        ])
        
        prompt = f"""基于以下关于"{', '.join(topics)}"的高质量信息，请提取5-10个最重要的关键要点。

信息内容:
{items_text}

请用简洁的语言列出关键要点，每个要点一行，格式如下:
- 要点1
- 要点2
...
"""
        
        try:
            response = self._call_qwen_api(prompt, task_type='extraction')
            # 解析要点
            key_points = [line.strip('- ').strip() for line in response.split('\n') if line.strip().startswith('-')]
            self.logger.info(f"提取到 {len(key_points)} 个关键要点")
            return key_points
        except Exception as e:
            self.logger.error(f"关键要点提取失败: {e}")
            return []
    
    def _identify_relationships(self, items: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        识别信息间的关联关系
        
        Args:
            items: 信息列表
            
        Returns:
            关联关系列表
        """
        self.logger.info("识别信息关联关系...")
        
        # 简化实现：基于关键词共现识别关系
        relationships = []
        
        # 提取标题中的关键词
        from collections import Counter
        all_words = []
        for item in items:
            title = item.get('title', '')
            # 简单的中文分词（这里简化处理，实际应该使用jieba）
            words = [w for w in title if len(w) > 1]
            all_words.extend(words)
        
        # 找出高频词
        word_counts = Counter(all_words)
        top_keywords = [word for word, count in word_counts.most_common(10) if count > 1]
        
        self.logger.info(f"识别到 {len(top_keywords)} 个关键词")
        
        return relationships
    
    def _generate_overall_analysis(self, items: List[Dict[str, Any]], key_points: List[str], 
                                   topics: List[str], statistics: Dict[str, Any]) -> str:
        """
        生成总体分析：整合所有信息，分析主题的总体趋势和洞察
        
        Args:
            items: 筛选后的高质量信息列表
            key_points: 提取的关键要点
            topics: 主题列表
            statistics: 统计信息
            
        Returns:
            总体分析文本
        """
        self.logger.info("生成总体分析...")
        
        if not items:
            return "暂无足够数据进行总体分析。"
        
        # 选取评分最高的前15条信息用于分析
        top_items = sorted(items, key=lambda x: x.get('score', 0), reverse=True)[:15]
        
        # 构建信息摘要
        items_summary = "\n".join([
            f"- {item.get('title', '')[:80]}... (来源: {item.get('source_name', '')}, 评分: {item.get('score', 0):.2f})"
            for item in top_items
        ])
        
        # 关键要点摘要
        key_points_text = "\n".join([f"- {point}" for point in key_points[:8]]) if key_points else "暂无关键要点"
        
        # 统计信息
        source_info = ", ".join([f"{k}: {v}条" for k, v in statistics.get('source_distribution', {}).items()])
        date_info = statistics.get('date_distribution', {})
        date_range = f"{min(date_info.keys()) if date_info else 'N/A'} 至 {max(date_info.keys()) if date_info else 'N/A'}"
        
        prompt = f"""你是一位资深的信息分析专家和行业观察家。请基于以下收集到的信息，对「{", ".join(topics)}」这一主题进行深度总体分析。

## 采集信息概况
- 总信息数: {statistics.get('total_count', 0)} 条
- 平均质量评分: {statistics.get('average_score', 0):.2f}
- 信息来源: {source_info}
- 时间范围: {date_range}

## 重点信息摘要
{items_summary}

## 已提取的关键要点
{key_points_text}

---

请生成一份「智览总体分析」，包含以下内容：

1. **总体态势判断**: 该主题在近期的总体发展态势是什么？（上升/下降/平稳/波动）

2. **核心发现**: 最重要的3-5个发现是什么？这些发现之间有什么关联？

3. **热点子主题**: 该主题下最受关注的2-3个子方向是什么？为什么？

4. **趋势预判**: 基于当前数据，该主题未来1-2周可能的发展方向是什么？

5. **关注建议**: 对于关注该主题的人，应该重点关注什么？

请用专业但易懂的语言，提供有洞察力的分析。每个部分用 Markdown 格式输出，总字数控制在 600-1000 字。
"""
        
        try:
            response = self._call_qwen_api(prompt, task_type='analysis')
            if response and not response.startswith('模拟'):
                self.logger.info("总体分析生成完成")
                return response
            else:
                return self._generate_fallback_analysis(topics, statistics, key_points)
        except Exception as e:
            self.logger.error(f"总体分析生成失败: {e}")
            return self._generate_fallback_analysis(topics, statistics, key_points)
    
    def _generate_fallback_analysis(self, topics: List[str], statistics: Dict[str, Any], key_points: List[str]) -> str:
        """
        生成备用的总体分析（当LLM不可用时）
        """
        topic_str = "、".join(topics)
        total = statistics.get('total_count', 0)
        avg_score = statistics.get('average_score', 0)
        sources = list(statistics.get('source_distribution', {}).keys())
        
        analysis = f"""### 总体态势

基于本次采集的 {total} 条高质量信息（平均评分 {avg_score:.2f}），「{topic_str}」主题在近期保持较高的关注度。

### 核心发现

"""
        if key_points:
            for i, point in enumerate(key_points[:5], 1):
                analysis += f"{i}. {point}\n"
        else:
            analysis += "暂无足够数据提取核心发现。\n"
        
        analysis += f"""
### 信息来源分布

本次分析的信息主要来自: {"、".join(sources) if sources else "暂无数据"}

### 关注建议

建议持续关注该主题的最新发展，特别是高评分信息源的更新。
"""
        return analysis
    
    def _compute_statistics(self, items: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        计算统计信息
        
        Args:
            items: 信息列表
            
        Returns:
            统计信息字典
        """
        from collections import Counter
        
        # 信息源分布
        source_distribution = Counter([item.get('source', 'Unknown') for item in items])
        
        # 按日期统计
        date_distribution = Counter()
        for item in items:
            try:
                date_str = item.get('date_published', '')
                date = datetime.fromisoformat(date_str.replace('Z', '+00:00'))
                date_key = date.strftime('%Y-%m-%d')
                date_distribution[date_key] += 1
            except:
                pass
        
        # 评分分布
        score_ranges = {'0.6-0.7': 0, '0.7-0.8': 0, '0.8-0.9': 0, '0.9-1.0': 0}
        for item in items:
            score = item.get('score', 0)
            if 0.6 <= score < 0.7:
                score_ranges['0.6-0.7'] += 1
            elif 0.7 <= score < 0.8:
                score_ranges['0.7-0.8'] += 1
            elif 0.8 <= score < 0.9:
                score_ranges['0.8-0.9'] += 1
            elif score >= 0.9:
                score_ranges['0.9-1.0'] += 1
        
        statistics = {
            'total_count': len(items),
            'source_distribution': dict(source_distribution),
            'date_distribution': dict(sorted(date_distribution.items())),
            'score_distribution': score_ranges,
            'average_score': sum(item.get('score', 0) for item in items) / len(items) if items else 0
        }
        
        return statistics
    
    def _call_qwen_api(self, prompt: str, task_type: str = 'general') -> Any:
        """
        调用通义千问API
        
        Args:
            prompt: 提示词
            task_type: 任务类型
            
        Returns:
            API响应结果
        """
        api_key = self.llm_config.get('api_key')
        
        if api_key == "YOUR_LLM_API_KEY":
            self.logger.warning("LLM API密钥未配置，使用模拟数据")
            # 返回模拟数据
            if task_type == 'scoring':
                return [{'index': i+1, 'relevance': 0.7, 'importance': 0.7, 
                        'timeliness': 0.7, 'reliability': 0.7, 'score': 0.7,
                        'brief_analysis': '模拟评分'} for i in range(10)]
            return "模拟响应"
        
        headers = {
            'Authorization': f'Bearer {api_key}',
            'Content-Type': 'application/json'
        }
        
        data = {
            'model': self.llm_config.get('model', 'qwen-plus'),
            'input': {
                'messages': [
                    {'role': 'system', 'content': '你是一位专业的信息分析专家。'},
                    {'role': 'user', 'content': prompt}
                ]
            },
            'parameters': {
                'max_tokens': self.llm_config.get('max_tokens', 2000),
                'temperature': self.llm_config.get('temperature', 0.7)
            }
        }
        
        try:
            response = requests.post(
                self.llm_config.get('endpoint'),
                headers=headers,
                json=data,
                timeout=60
            )
            response.raise_for_status()
            result = response.json()
            
            # 提取回复内容
            content = result.get('output', {}).get('choices', [{}])[0].get('message', {}).get('content', '')
            
            # 如果是评分任务，解析JSON
            if task_type == 'scoring':
                try:
                    # 尝试提取JSON部分
                    json_start = content.find('[')
                    json_end = content.rfind(']') + 1
                    if json_start >= 0 and json_end > json_start:
                        json_str = content[json_start:json_end]
                        return json.loads(json_str)
                except json.JSONDecodeError as e:
                    self.logger.error(f"JSON解析失败: {e}")
                    return []
            
            return content
            
        except Exception as e:
            self.logger.error(f"调用LLM API失败: {e}")
            raise


if __name__ == "__main__":
    # 测试分析器
    from config import get_config
    from logger import LoggerManager
    
    config = get_config()
    log_manager = LoggerManager(config)
    analyzer = InformationAnalyzer(config, log_manager)
    
    # 模拟测试数据
    test_items = [
        {
            'title': 'GPT-4发布重大更新',
            'snippet': 'OpenAI发布了GPT-4的最新版本...',
            'source': 'NewsAPI',
            'source_name': 'TechCrunch',
            'date_published': '2025-12-20T10:00:00Z'
        }
    ]
    
    result = analyzer.analyze_items(test_items, ['人工智能'])
    print(f"分析完成，筛选出 {len(result['filtered_items'])} 条高质量信息")
