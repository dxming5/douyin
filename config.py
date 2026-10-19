# -*- coding: utf-8 -*-
"""
配置常量模块
包含全局配置、数据类型定义、网络请求参数等
"""

import os
import ssl


# 编码配置
ENCODING = 'utf-8'
LEGACY_ENCODINGS = ('gbk', 'mbcs')

# 抖音内容类型
IMAGE_TYPES = (68,)
VIDEO_TYPES = (0, 51, 55, 61, 66)

# HTTP 请求头
HEADER = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/106.0.0.0 Safari/537.36 Edg/106.0.1370.52',
    'Accept': 'application/json, text/plain, */*',
    'Referer': 'https://www.douyin.com/user/MS4wLjABAAAACJyXOoE3noz3e-F1pRXwVnYvz2yMIgHx_1s3LaDYB4q1FVWRm-GDWRAbUdvPwPGq'
}

# SSL 上下文（忽略证书验证）
SSL_CONTEXT = ssl._create_unverified_context()

# 下载配置
DOWNLOAD_TIMEOUT = 30
MAX_RETRY = 3

# 路径配置
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
CONFIGURED_DOWNLOAD_DIR = 'F:/图片/douyin/'
DEFAULT_DOWNLOAD_DIR = os.path.join(BASE_DIR, 'download')


