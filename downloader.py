# -*- coding: utf-8 -*-
"""
下载与格式转换模块
包含网络下载、去重比对、webp转jpg等功能
"""

import os
import random
import time
import shutil
from urllib import request

from config import HEADER, SSL_CONTEXT, DOWNLOAD_TIMEOUT, MAX_RETRY
from utils import read_txt, write_txt, make_dir, append_list_txt
import paths  # 导入模块而非具体变量，以便动态获取更新后的值


# 全局失败记录
_download_failures = []


def build_opener():
    """构造带请求头与忽略证书校验的下载器"""
    opener = request.build_opener(request.HTTPSHandler(context=SSL_CONTEXT))
    opener.addheaders = list(HEADER.items())
    return opener


def save_single_url(url, file_name):
    """下载单个 url 到 file_name，最多重试 MAX_RETRY 次"""
    global _download_failures
    for attempt in range(MAX_RETRY + 1):
        try:
            opener = build_opener()
            with opener.open(url, timeout=DOWNLOAD_TIMEOUT) as response, \
                    open(file_name, 'wb') as file_handle:
                shutil.copyfileobj(response, file_handle)
            return True
        except Exception as error:
            # 清理下载失败产生的半截文件
            if os.path.exists(file_name):
                try:
                    os.remove(file_name)
                except OSError:
                    pass
            if attempt >= MAX_RETRY:
                error_msg = '超过最大重试次数，最后异常：{}'.format(error)
                print("\n    -->当前url({})下载异常次数超过{}次，退出下载！".format(url, MAX_RETRY))
                # 记录失败信息
                _download_failures.append({
                    'url': url,
                    'file': file_name,
                    'error': error_msg
                })
                return False
            time.sleep(random.uniform(0.5, 1.5))
    return False


def get_url_signature(url, start_tag, end_tag):
    """提取 url 中不变的片段用于去重比对（url 本身带有时效参数，会变动）"""
    start = url.find(start_tag)
    if start < 0:
        return url
    start += len(start_tag)
    end = url.find(end_tag, start)
    if end < 0:
        return url[start:]
    return url[start:end]


def convert_webp_to_jpg(file_name):
    """webp 转 jpg，转换成功后删除源 webp 文件，返回是否成功"""
    from PIL import Image  # 延迟导入，避免启动时依赖 PIL
    try:
        im = Image.open(file_name)
        if im.mode == "RGBA":
            im.load()  # required for png.split()
            background = Image.new("RGB", im.size, (255, 255, 255))
            background.paste(im, mask=im.split()[3])
        save_name = os.path.splitext(file_name)[0] + '.jpg'
        im.save('{}'.format(save_name), 'JPEG')
        im.close()
        if os.path.exists(file_name):
            os.remove(file_name)
        return True
    except Exception as error:
        print('\n    -->图片转换失败（{}）：{}'.format(file_name, error))
        return False


def download_by_type(all_url_dict, media_type):
    """根据类型下载dict中所有的url"""
    global _download_failures
    # 从 paths 模块动态获取最新值
    blogger_url_txt_dir = paths.blogger_url_txt_dir
    blogger_dir = paths.blogger_dir
    
    saved_url_list = read_txt(blogger_url_txt_dir)
    all_mblog_num = len(all_url_dict)
    if not all_mblog_num:
        return

    if media_type == '图片':
        picture_dir = os.path.join(blogger_dir, 'picture')
        make_dir(picture_dir)
        # 图片url是动态的，所以使用"/tos-cn-i-......~tplv-dy-aweme-images"字符串来存储比较
        start_tag, end_tag = '/tos-cn-i-', '~tplv-dy-aweme-images'
        ext = '.webp'
    else:
        # 视频url是动态的，所以使用"&rc=......&l="字符串来存储比较
        start_tag, end_tag = '&rc=', '&l='
        ext = '.mp4'

    # 直接存储特征码集合（无需再从URL提取）
    saved_signature_set = set(saved_url_list)

    # 记录本次新下载成功的URL（延迟写入）
    new_downloaded_urls = []
    
    download_mblog_num = 0
    for creat_time, url_mblog in all_url_dict.items():
        for index in range(0, len(url_mblog)):
            url = url_mblog[index]
            # 视频用"条"，图片用"张"
            unit = '条' if media_type == '视频' else '张'
            print('\r [{}已下载进度：{}%({}/{})] 开始下载<{}>时刻第{}{}{}'.format(
                media_type, int(download_mblog_num / all_mblog_num * 100), download_mblog_num,
                all_mblog_num, creat_time, index + 1, unit, media_type), end='')

            # 提取当前URL的特征码
            url_signature = get_url_signature(url, start_tag, end_tag)
            
            if url_signature in saved_signature_set:
                continue

            if media_type == '图片':
                file_name = os.path.join(picture_dir, '{} - {}{}'.format(creat_time, index + 1, ext))
            else:
                file_name = os.path.join(blogger_dir, '{}{}'.format(creat_time, ext))

            if save_single_url(url, file_name):
                # 添加到特征码集合（用于本次运行时的去重）
                saved_signature_set.add(url_signature)
                # 延迟写入：只保存特征码
                new_downloaded_urls.append(url_signature)
                # webp转为jpg
                if media_type == '图片' and os.path.exists(file_name):
                    if not convert_webp_to_jpg(file_name):
                        _download_failures.append({
                            'url': url,
                            'file': file_name,
                            'error': 'webp 转 jpg 失败'
                        })

        download_mblog_num += 1
        print('\r [{}已下载进度：{}%({}/{})]'.format(media_type, int(download_mblog_num / all_mblog_num * 100),
                                                    download_mblog_num, all_mblog_num), end='')
    # 清除行尾残留的"开始下载..."字符，打印简洁的完成信息
    print('\r [{}已下载进度：{}%({}/{})] 下载完成{}'.format(
        media_type, int(download_mblog_num / all_mblog_num * 100),
        download_mblog_num, all_mblog_num, ' ' * 50))
    
    # 所有URL下载完成后，统一批量追加写入文件
    if new_downloaded_urls:
        append_list_txt(blogger_url_txt_dir, new_downloaded_urls)


def get_failure_list():
    """获取下载失败列表"""
    return _download_failures.copy()


def clear_failures():
    """清空失败记录"""
    global _download_failures
    _download_failures = []


def print_failure_summary():
    """打印下载失败汇总"""
    if not _download_failures:
        return
    
    print('\n' + '=' * 60)
    print('下载失败列表（共 {} 个）：'.format(len(_download_failures)))
    print('=' * 60)
    for idx, failure in enumerate(_download_failures, 1):
        print('\n[{}]'.format(idx))
        print('  文件: {}'.format(failure['file']))
        print('  URL: {}'.format(failure['url']))
        print('  原因: {}'.format(failure['error']))
    print('\n' + '=' * 60)


def download():
    """下载协调函数：解析URL并执行下载"""
    global _download_failures
    from url_parser import get_all_url  # 延迟导入，避免循环依赖
    
    # 清空上次的失败记录
    clear_failures()
    
    blogger_name, all_picture_dict, all_video_dict = get_all_url()
    if not blogger_name:
        return
    from paths import set_sub_path
    set_sub_path(blogger_name)
    print('*' * 20 + ' <blogger：' + blogger_name + '> ' + '*' * 20)
    print(' <{}>视频抖音{}条，图片抖音{}条'.format(blogger_name, len(all_video_dict), len(all_picture_dict)))

    # 下载视频
    download_by_type(all_video_dict, '视频')
    # 下载图片
    download_by_type(all_picture_dict, '图片')
    
    # 打印失败汇总
    print_failure_summary()

    print('*' * 45 + '\n')
