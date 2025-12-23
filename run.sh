#!/bin/bash
# 智览系统运行脚本

# 切换到项目目录
cd "$(dirname "$0")"

# 检查 Python 环境
if ! command -v python &> /dev/null; then
    echo "错误: 未找到 Python，请确保已安装 Python 3.8+"
    exit 1
fi

# 检查必要的依赖
python -c "import hydra" 2>/dev/null || {
    echo "正在安装必要依赖..."
    pip install hydra-core omegaconf colorlog -q
}

# 运行主程序
echo "启动智览系统..."
cd src
python main.py "$@"
