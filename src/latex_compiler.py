"""
LaTeX编译模块
将Markdown报告转换并编译为PDF格式
"""

import logging
import subprocess
import re
from pathlib import Path
from typing import Optional
from jinja2 import Template


class LaTeXCompiler:
    """LaTeX编译器"""
    
    def __init__(self, config_manager):
        """
        初始化LaTeX编译器
        
        Args:
            config_manager: 配置管理器实例
        """
        self.config = config_manager
        self.logger = logging.getLogger(f"智览系统v{config_manager.version}")
        self.output_dir = config_manager.get_output_dir()
        self.assets_dir = config_manager.get_assets_dir()
        self.templates_dir = Path(config_manager.project_root) / "templates"
        self.compiler = config_manager.get('output', 'pdf', 'compiler', default='xelatex')
    
    def markdown_to_pdf(self, markdown_path: str, output_name: Optional[str] = None) -> Optional[str]:
        """
        将Markdown报告编译为PDF
        
        Args:
            markdown_path: Markdown文件路径
            output_name: 输出PDF文件名（不含扩展名）
            
        Returns:
            PDF文件路径，失败返回None
        """
        self.logger.info(f"开始编译PDF: {markdown_path}")
        
        try:
            # 读取Markdown内容
            with open(markdown_path, 'r', encoding='utf-8') as f:
                markdown_content = f.read()
            
            # 转换为LaTeX
            latex_content = self._markdown_to_latex(markdown_content)
            
            # 生成LaTeX文件
            if output_name is None:
                output_name = Path(markdown_path).stem
            
            tex_path = self.output_dir / f"{output_name}.tex"
            with open(tex_path, 'w', encoding='utf-8') as f:
                f.write(latex_content)
            
            self.logger.info(f"LaTeX文件已生成: {tex_path}")
            
            # 编译PDF
            pdf_path = self._compile_latex(tex_path)
            
            if pdf_path:
                self.logger.info(f"PDF编译成功: {pdf_path}")
                return pdf_path
            else:
                self.logger.error("PDF编译失败")
                return None
                
        except Exception as e:
            self.logger.error(f"Markdown转PDF失败: {e}")
            return None
    
    def _markdown_to_latex(self, markdown_content: str) -> str:
        """
        将Markdown内容转换为LaTeX格式
        
        Args:
            markdown_content: Markdown内容
            
        Returns:
            LaTeX内容
        """
        # 使用模板
        template_path = self.templates_dir / "report_template.tex"
        
        if template_path.exists():
            with open(template_path, 'r', encoding='utf-8') as f:
                template_str = f.read()
        else:
            # 使用默认模板
            template_str = self._get_default_template()
        
        # 处理Markdown内容
        processed_content = self._process_markdown(markdown_content)
        
        # 渲染模板
        template = Template(template_str)
        latex_content = template.render(content=processed_content)
        
        return latex_content
    
    def _process_markdown(self, markdown: str) -> str:
        """
        处理Markdown内容，转换为LaTeX兼容格式
        
        Args:
            markdown: Markdown内容
            
        Returns:
            处理后的内容
        """
        # 转义特殊字符
        content = markdown
        
        # 处理标题
        content = re.sub(r'^# (.*?)$', r'\\section*{\1}', content, flags=re.MULTILINE)
        content = re.sub(r'^## (.*?)$', r'\\section{\1}', content, flags=re.MULTILINE)
        content = re.sub(r'^### (.*?)$', r'\\subsection{\1}', content, flags=re.MULTILINE)
        content = re.sub(r'^#### (.*?)$', r'\\subsubsection{\1}', content, flags=re.MULTILINE)
        
        # 处理粗体和斜体
        content = re.sub(r'\*\*(.*?)\*\*', r'\\textbf{\1}', content)
        content = re.sub(r'\*(.*?)\*', r'\\textit{\1}', content)
        
        # 处理列表
        content = re.sub(r'^\- (.*?)$', r'\\item \1', content, flags=re.MULTILINE)
        content = re.sub(r'^\d+\. (.*?)$', r'\\item \1', content, flags=re.MULTILINE)
        
        # 处理图片链接
        # ![alt](path) -> \includegraphics{path}
        content = re.sub(
            r'!\[(.*?)\]\((\.\./)?(assets/.*?)\)',
            r'\\begin{figure}[h]\n\\centering\n\\includegraphics[width=0.8\\textwidth]{\3}\n\\caption{\1}\n\\end{figure}',
            content
        )
        
        # 处理URL链接
        content = re.sub(r'\[(.*?)\]\((.*?)\)', r'\\href{\2}{\1}', content)
        
        # 处理水平线
        content = re.sub(r'^---$', r'\\hrule', content, flags=re.MULTILINE)
        
        # 转义特殊LaTeX字符
        special_chars = {
            '%': '\\%',
            '&': '\\&',
            '#': '\\#',
            '_': '\\_',
            '$': '\\$'
        }
        for char, escaped in special_chars.items():
            content = content.replace(char, escaped)
        
        return content
    
    def _compile_latex(self, tex_path: Path) -> Optional[str]:
        """
        编译LaTeX文件为PDF
        
        Args:
            tex_path: LaTeX文件路径
            
        Returns:
            PDF文件路径，失败返回None
        """
        try:
            # 切换到输出目录
            original_dir = Path.cwd()
            output_dir = tex_path.parent
            
            # 编译命令
            cmd = [
                self.compiler,
                '-interaction=nonstopmode',
                '-output-directory', str(output_dir),
                str(tex_path)
            ]
            
            self.logger.info(f"执行编译命令: {' '.join(cmd)}")
            
            # 编译两次以确保引用正确
            for i in range(2):
                result = subprocess.run(
                    cmd,
                    capture_output=True,
                    text=True,
                    timeout=120
                )
                
                if result.returncode != 0:
                    self.logger.error(f"LaTeX编译失败 (第{i+1}次):")
                    self.logger.error(result.stdout)
                    self.logger.error(result.stderr)
                    
                    # 尝试解析错误并修复
                    if i == 0:
                        self._try_fix_latex_errors(tex_path, result.stdout)
                    else:
                        return None
            
            # 检查PDF是否生成
            pdf_path = tex_path.with_suffix('.pdf')
            if pdf_path.exists():
                return str(pdf_path)
            else:
                self.logger.error("PDF文件未生成")
                return None
                
        except subprocess.TimeoutExpired:
            self.logger.error("LaTeX编译超时")
            return None
        except Exception as e:
            self.logger.error(f"编译过程出错: {e}")
            return None
    
    def _try_fix_latex_errors(self, tex_path: Path, error_log: str):
        """
        尝试自动修复常见的LaTeX错误
        
        Args:
            tex_path: LaTeX文件路径
            error_log: 错误日志
        """
        self.logger.info("尝试自动修复LaTeX错误...")
        
        try:
            with open(tex_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # 修复常见错误
            # 1. 图片路径问题
            if '! LaTeX Error: File' in error_log and 'not found' in error_log:
                content = re.sub(r'\\includegraphics\[.*?\]\{(.*?)\}',
                               lambda m: f'\\includegraphics[width=0.8\\textwidth]{{{self.assets_dir / m.group(1)}}}',
                               content)
            
            # 2. 特殊字符转义
            content = content.replace('~', '\\textasciitilde{}')
            content = content.replace('^', '\\textasciicircum{}')
            
            # 保存修复后的文件
            with open(tex_path, 'w', encoding='utf-8') as f:
                f.write(content)
            
            self.logger.info("LaTeX文件已修复")
            
        except Exception as e:
            self.logger.error(f"自动修复失败: {e}")
    
    def _get_default_template(self) -> str:
        """获取默认LaTeX模板"""
        return r"""\documentclass[12pt,a4paper]{article}

% 基本包
\usepackage[UTF8]{ctex}
\usepackage{geometry}
\usepackage{graphicx}
\usepackage{hyperref}
\usepackage{xcolor}
\usepackage{fancyhdr}
\usepackage{titlesec}

% 页面设置
\geometry{left=2.5cm,right=2.5cm,top=3cm,bottom=3cm}

% 超链接设置
\hypersetup{
    colorlinks=true,
    linkcolor=blue,
    urlcolor=blue,
    citecolor=blue
}

% 页眉页脚
\pagestyle{fancy}
\fancyhf{}
\fancyhead[L]{智览信息分析报告}
\fancyhead[R]{\today}
\fancyfoot[C]{\thepage}

% 标题格式
\titleformat{\section}{\Large\bfseries}{\thesection}{1em}{}
\titleformat{\subsection}{\large\bfseries}{\thesubsection}{1em}{}

\begin{document}

{{ content }}

\end{document}
"""


if __name__ == "__main__":
    # 测试LaTeX编译器
    from config import get_config
    from logger import LoggerManager
    
    config = get_config()
    log_manager = LoggerManager(config)
    compiler = LaTeXCompiler(config, log_manager)
    
    # 创建测试Markdown
    test_md = config.get_output_dir() / "test_report.md"
    with open(test_md, 'w', encoding='utf-8') as f:
        f.write("""# 测试报告

## 这是一个测试

测试**粗体**和*斜体*。

- 列表项1
- 列表项2

[链接](https://example.com)
""")
    
    pdf_path = compiler.markdown_to_pdf(str(test_md))
    if pdf_path:
        print(f"PDF生成成功: {pdf_path}")
