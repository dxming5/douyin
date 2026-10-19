# -*- coding: utf-8 -*-
"""
命令行交互界面模块
包含菜单控制、博主列表显示、删除等功能
"""

import sys
import os

from utils import read_txt, read_int, rm_dir, write_list_txt
import paths  # 导入模块而非具体变量，以便动态获取更新后的值
from downloader import download


def delete_blogger(blogger_list):
    """删除指定博主及其下载内容"""
    for i in range(0, len(blogger_list)):
        print(str(int(i + 1)) + '：' + blogger_list[i])
    blog_id = read_int('输入对应的 blog id：')
    while blog_id <= 0 or blog_id > len(blogger_list):
        blog_id = read_int('blog id 输入错误，重新输入：')
    blogger_name = blogger_list[blog_id - 1]
    rm_dir(os.path.join(paths.download_dir, blogger_name))
    blogger_list.remove(blogger_name)
    write_list_txt(paths.aweme_list_dir, blogger_list)
    print('  已删除 <{}> 及其下载内容'.format(blogger_name))


def show_blogger_list(blogger_list):
    """显示博主列表"""
    if not blogger_list:
        print('  博主列表为空')
        return
    for i in range(0, len(blogger_list)):
        print(str(int(i + 1)) + '：' + blogger_list[i])


def run_cli():
    """运行交互式命令行循环"""
    while True:
        function_selection = input('\n  a:下载 b:删除blog c:获取blogger列表 x:退出程序 \n请输入对应的指令：').strip().lower()
        blogger_list = read_txt(paths.aweme_list_dir)
        if function_selection == 'a':
            # blogger_response = input('blogger response:')
            download()
        elif function_selection == 'b':
            delete_blogger(blogger_list)
        elif function_selection == 'c':
            show_blogger_list(blogger_list)
        elif function_selection == 'x':
            sys.exit(0)
        else:
            print('指令输入错误，请重新输入！')
