"""
智能信息分析模块
使用大语言模型对采集的信息进行评分、筛选和关联分析
"""

import json
import requests
from typing import List, Dict, Any, Tuple
from datetime import datetime
import tqdm

class InformationAnalyzer:
    """信息智能分析器"""
    
    def __init__(self, config_manager, logger_manager):
        """
        初始化信息分析器
        
        Args:
            config_manager: 配置管理器实例
            logger_manager: 日志管理器实例
        """
        self.config = config_manager
        self.logger = logger_manager.get_logger()
        self.logger_manager = logger_manager
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
        
        # 检查断点
        checkpoint = self.logger_manager.load_checkpoint('analysis')
        if checkpoint:
            self.logger.info("从断点恢复分析...")
            return checkpoint
        
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
        
        result = {
            'scored_items': scored_items,
            'filtered_items': filtered_items,
            'key_points': key_points,
            'relationships': relationships,
            'statistics': statistics,
            'analysis_time': datetime.now().isoformat()
        }
        
        # 保存断点
        self.logger_manager.save_checkpoint('analysis', result)
        
        return result
    
    def _score_items_batch(self, items: List[Dict[str, Any]], topics: List[str]) -> List[Dict[str, Any]]:
        """
        批量对信息进行评分
        
        Args:
            items: 信息列表
            topics: 主题列表
            
        Returns:
            带评分的信息列表
        """
        self.logger.info("开始批量评分...")
        scored_items = []
        batch_size = 10  # 每批处理10条信息
        
        for i in tqdm.tqdm(range(0, len(items), batch_size), desc="评分进度:(已评分数据/总数据)"):
            batch = items[i:i+batch_size]
            try:
                batch_scores = self._call_llm_for_scoring(batch, topics)
                
                # 合并评分结果
                for j, item in enumerate(batch):
                    if j < len(batch_scores):
                        item.update(batch_scores[j])
                    else:
                        # 如果LLM返回结果不足，使用默认评分
                        item['score'] = 0.5
                        item['relevance'] = 0.5
                        item['importance'] = 0.5
                        item['timeliness'] = 0.5
                        item['reliability'] = 0.5
                    scored_items.append(item)
                
            except Exception as e:
                self.logger.error(f"批量评分失败: {e}")
                # 使用默认评分
                for item in batch:
                    item['score'] = 0.5
                    scored_items.append(item)
        
        self.logger.info(f"完成 {len(scored_items)} 条信息的评分")
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
