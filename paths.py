# -*- coding: utf-8 -*-
"""
路径管理模块
包含目录/文件路径管理、创建等功能
"""

import os

from config import CONFIGURED_DOWNLOAD_DIR, DEFAULT_DOWNLOAD_DIR
from utils import make_dir, make_txt


# 全局路径变量
download_dir = ''
aweme_list_dir = ''
blogger_dir = ''
blogger_url_txt_dir = ''


def normalize_dir(dir_path):
    """目录路径统一使用 / 结尾，便于拼接"""
    return dir_path.rstrip('/\\') + os.sep


def set_total_path():
    """设置总下载目录路径"""
    global download_dir, aweme_list_dir
    for candidate in (CONFIGURED_DOWNLOAD_DIR, DEFAULT_DOWNLOAD_DIR):
        if not candidate:
            continue
        try:
            make_dir(candidate)
            download_dir = normalize_dir(candidate)
            break
        except OSError as error:
            print('  下载目录不可用（{}）：{}'.format(candidate, error))
    if not download_dir:
        download_dir = normalize_dir(DEFAULT_DOWNLOAD_DIR)
        make_dir(download_dir)

    aweme_list_dir = os.path.join(download_dir, 'aweme_list.json')
    make_txt(aweme_list_dir)


def set_sub_path(blogger_name):
    """设置博主子目录路径"""
    global blogger_dir, blogger_url_txt_dir
    blogger_dir = normalize_dir(os.path.join(download_dir, blogger_name))
    make_dir(blogger_dir)
    blogger_url_txt_dir = os.path.join(blogger_dir, 'url.txt')
    make_txt(blogger_url_txt_dir)


def get_json_log_path():
    """
    json.log 优先取脚本目录下的，其次取下载目录下的（兼容旧用法）
    """
    from config import BASE_DIR
    script_log = os.path.join(BASE_DIR, 'json.log')
    if os.path.exists(script_log):
        return script_log
    return os.path.join(download_dir, 'json.log')
