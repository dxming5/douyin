# -*- coding: utf-8 -*-
"""
程序入口模块
负责初始化和协调各模块运行
"""

from utils import configure_encoding
import paths  # 导入模块而非具体变量，以便动态获取更新后的值
from cli import run_cli


def main():
    """主函数：初始化并启动CLI交互界面"""
    # 配置编码
    configure_encoding()
    # 设置下载目录
    paths.set_total_path()
    # 打印信息
    print('  下载目录：{}'.format(paths.download_dir))
    print('  json.log：{}'.format(paths.get_json_log_path()))
    # 启动命令行交互
    run_cli()


if __name__ == '__main__':
    main()
