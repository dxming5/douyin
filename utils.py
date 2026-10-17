# -*- coding: utf-8 -*-
"""
工具函数模块
包含文件读写、编码处理、通用工具函数
"""

import sys
import re
import os
import shutil

from config import ENCODING, LEGACY_ENCODINGS


def configure_encoding():
    """配置终端/标准输入输出使用 UTF-8 编码"""
    for _stream in (sys.stdout, sys.stderr, sys.stdin):
        try:
            _stream.reconfigure(encoding=ENCODING)
        except (AttributeError, ValueError, OSError):
            pass


def read_txt(txt_dir):
    """
    以 UTF-8 读取文本文档，返回非空行组成的列表；
    若文件是历史遗留的 GBK 编码，则自动回退读取，保证平滑迁移
    """
    if not os.path.exists(txt_dir):
        return []
    with open(txt_dir, mode='rb') as file_handle:
        raw = file_handle.read()
    for encoding in (ENCODING,) + LEGACY_ENCODINGS:
        try:
            text = raw.decode(encoding)
            break
        except (UnicodeDecodeError, LookupError):
            continue
    else:
        text = raw.decode(ENCODING, errors='ignore')
    return [line.strip() for line in text.splitlines() if line.strip()]


def write_txt(txt_dir, text):
    """追加写一行到txt文档（UTF-8）"""
    with open(txt_dir, mode='a', encoding=ENCODING) as file_handle:
        file_handle.write(text + '\n')


def write_list_txt(txt_dir, content_list):
    """整体覆盖写入列表到txt文档（UTF-8）"""
    with open(txt_dir, mode='w', encoding=ENCODING) as file_handle:
        for item in content_list:
            file_handle.write(item + '\n')


def make_dir(dir_path):
    """创建目录（如果不存在）"""
    if not os.path.exists(dir_path):
        os.makedirs(dir_path)


def make_txt(txt_str):
    """创建空文本文件（如果不存在）"""
    with open(txt_str, mode='a', encoding=ENCODING):
        pass


def rm_dir(dir_path):
    """删除目录（如果存在）"""
    if os.path.exists(dir_path):
        shutil.rmtree(dir_path)


def safe_name(name):
    """剔除不符合 Windows 文件夹名的字符：\\/:*?"<>|"""
    name = re.sub(r'[\\/:*?"<>|\r\n\t]', '', name)
    return name.strip().rstrip('.').strip()


def read_int(prompt):
    """读取整数，输入非法时提示重新输入"""
    while True:
        value = input(prompt).strip()
        try:
            return int(value)
        except ValueError:
            print('  请输入数字！')
