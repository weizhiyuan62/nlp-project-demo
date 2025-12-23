#!/bin/bash

# 智览系统启动脚本

echo "================================================"
echo "  智览 (ZhiLan) 信息聚合与分析系统"
echo "  版本: 1.0.0"
echo "================================================"
echo ""

# 检查Python环境
if ! command -v python &> /dev/null; then
    echo "❌ 错误: 未找到Python环境"
    echo "请先安装Python 3.8或更高版本"
    exit 1
fi

# 显示Python版本
PYTHON_VERSION=$(python --version 2>&1)
echo "✓ Python环境: $PYTHON_VERSION"

# 检查虚拟环境
if [[ "$VIRTUAL_ENV" != "" ]]; then
    echo "✓ 虚拟环境: $VIRTUAL_ENV"
else
    echo "⚠️  警告: 未在虚拟环境中运行"
    echo "建议使用虚拟环境: conda activate zhilan"
    echo ""
fi

# 检查依赖
echo "检查依赖包..."
if ! python -c "import yaml, requests, matplotlib, jieba" &> /dev/null; then
    echo "❌ 缺少必要的依赖包"
    echo "正在安装依赖..."
    pip install -r requirements.txt
    if [ $? -ne 0 ]; then
        echo "❌ 依赖安装失败"
        exit 1
    fi
fi
echo "✓ 依赖检查完成"
echo ""

# 检查配置文件
if [ ! -f "config/config.yaml" ]; then
    echo "❌ 错误: 配置文件不存在"
    echo "请创建 config/config.yaml 文件并配置API密钥"
    exit 1
fi
echo "✓ 配置文件: config/config.yaml"
echo ""

# 创建必要的目录
mkdir -p logs assets outputs logs/checkpoints
echo "✓ 目录结构检查完成"
echo ""

# 运行系统
echo "启动智览系统..."
echo "================================================"
echo ""

cd src
python main.py

# 检查运行结果
if [ $? -eq 0 ]; then
    echo ""
    echo "================================================"
    echo "✓ 系统运行完成"
    echo "报告文件位于: outputs/"
    echo "可视化图表位于: assets/"
    echo "日志文件位于: logs/"
    echo "================================================"
else
    echo ""
    echo "================================================"
    echo "❌ 系统运行出错"
    echo "请查看日志文件: logs/zhilan_*.log"
    echo "================================================"
    exit 1
fi
