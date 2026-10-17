# -*- coding: utf-8 -*-
'''
v1.1 优化获取所有url
v1.2
v2.0 非手机查看网页
v2.0 浏览器开发者工具获取当前页url
......
v4.0 1.使用json存储下载博主列表 {{"uid":"2321777100592404","nickname":"王乔熙"}...}
     2.获取url修改，允许一次下载多个作者的内容
v5.0 1.全部文件（源码、日志、列表、URL记录）统一使用 UTF-8 编码读写，
        不再依赖 Windows 系统默认的 GBK 编码，避免中文乱码/UnicodeDecodeError
     2.修复 get_all_url 返回值错误（视频字典被图片字典覆盖）
     3.使用 os.path.join 拼接路径，修复 "\\picture" 硬编码导致的跨平台问题
     4.下载时携带请求头并支持超时重试，解决 urlretrieve 无 UA 被拒的问题
     5.已下载 URL 去重改为集合比对，避免 O(n²) 遍历
'''

'''
目录结构如下
/douyin/
     /aweme_list.json （记录所有作者的uid和名字）
     /{name}/
            /（所有视频：使用发布时间做文件名“2023-07-26 12.00.00.mp4”）
            /download_url.txt（记录已下载视频/图片的url）
            /picture/（所有图片：使用发布时间+编号做文件名“2023-07-26 12.00.00 - 1.jpg”）
     /json.log
     /cfg.ini（配置文件）

各文件格式如下：
aweme_list.json文件：
2321777100592404 王乔熙
89911799238 噜噜不困 

download_url.txt文件：
2023-07-26 12.00.00.mp4
http://v3-webc.douyinvod.com/72a56dbd834fb6f68d0dda34d9ad12e3/64bcb225/video****
2023-07-26 12.00.00 - 1.jpg
http://v3-webc.douyinvod.com/72a56dbd834fb6f68d0dda34d9ad12e3/64bcb225/audio****

cfg.ini文件：


'''

''' 从json中获取需要的信息并保存
[
    {
        "nickname":"王乔熙",
        "create_time":"1648883773",
        "mode":"audio(或video)",
        "url_list":["url1","url2",...]
    },
    ...
]
'''

import sys
import os
import re
import ssl
import json
import time
import random
import shutil
from urllib import request
from PIL import Image
from datetime import datetime

# 统一编码：所有文本文件的读写都使用 UTF-8
ENCODING = 'utf-8'
# 兼容历史遗留文件：这些文件可能是在未指定编码时（GBK）写入的
LEGACY_ENCODINGS = ('gbk', 'mbcs')

# 终端/标准输入输出同样强制 UTF-8，避免 Windows 控制台（GBK）下中文输出报错
for _stream in (sys.stdout, sys.stderr, sys.stdin):
    try:
        _stream.reconfigure(encoding=ENCODING)
    except (AttributeError, ValueError, OSError):
        pass


class CDownloadInfo(object):
    m_NickName = ""     # 名字
    m_CreateTime = ""   # 创建时间
    m_Mode = ""         # 模式：图片或视频
    m_UrlList = []      # url列表：视频只有一个url；图片有多个


header = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/106.0.0.0 Safari/537.36 Edg/106.0.1370.52',
    'Accept': 'application/json, text/plain, */*',
    'Referer': 'https://www.douyin.com/user/MS4wLjABAAAACJyXOoE3noz3e-F1pRXwVnYvz2yMIgHx_1s3LaDYB4q1FVWRm-GDWRAbUdvPwPGq'
}

context = ssl._create_unverified_context()

# 下载单个文件的超时时间（秒）与最大重试次数
DOWNLOAD_TIMEOUT = 30
MAX_RETRY = 3

# 脚本所在目录
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
# 首选下载目录（可自行修改）；不可用时自动回退到脚本目录下的 download/
CONFIGURED_DOWNLOAD_DIR = 'F:/图片/douyin/'
DEFAULT_DOWNLOAD_DIR = os.path.join(BASE_DIR, 'download')


# 如下为全局变量
download_dir = ''
aweme_list_dir = ''
blogger_dir = ''
blogger_url_txt_dir = ''


def make_dir(dir):
    if not os.path.exists(dir):
        os.makedirs(dir)


def make_txt(txt_str):
    with open(txt_str, mode='a', encoding=ENCODING):
        pass


def rm_dir(dir):
    if os.path.exists(dir):
        shutil.rmtree(dir)


def read_txt(txt_dir):
    '''以 UTF-8 读取文本文档，返回非空行组成的列表；
    若文件是历史遗留的 GBK 编码，则自动回退读取，保证平滑迁移'''
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
    '追加写一行到txt文档（UTF-8）'
    with open(txt_dir, mode='a', encoding=ENCODING) as file_handle:
        file_handle.write(text + '\n')


def write_list_txt(txt_dir, content_list):
    '整体覆盖写入列表到txt文档（UTF-8）'
    with open(txt_dir, mode='w', encoding=ENCODING) as file_handle:
        for item in content_list:
            file_handle.write(item + '\n')


def normalize_dir(dir_path):
    '目录路径统一使用 / 结尾，便于拼接'
    return dir_path.rstrip('/\\') + os.sep


# 设置总目录路径
def set_total_path():
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


# 设置子目录路径
def set_sub_path(blogger_name):
    global blogger_dir, blogger_url_txt_dir
    blogger_dir = normalize_dir(os.path.join(download_dir, blogger_name))
    make_dir(blogger_dir)
    blogger_url_txt_dir = os.path.join(blogger_dir, 'url.txt')
    make_txt(blogger_url_txt_dir)


def get_json_log_path():
    'json.log 优先取脚本目录下的，其次取下载目录下的（兼容旧用法）'
    script_log = os.path.join(BASE_DIR, 'json.log')
    if os.path.exists(script_log):
        return script_log
    return os.path.join(download_dir, 'json.log')


# 剔除不符合 Windows 文件夹名的字符：\/:*?"<>|
def safe_name(name):
    name = re.sub(r'[\\/:*?"<>|\r\n\t]', '', name)
    return name.strip().rstrip('.').strip()


# 视频/图片的 aweme_type
IMAGE_TYPES = (68,)
VIDEO_TYPES = (0, 51, 55, 61, 66)


# 获取需要的信息
def get_all_url():
    blogger_name = ''
    # 记录所有图片的url：字典结构，key=发布时间，value=每条抖音中图片的url list
    all_picture_url_dict = dict()
    # 记录所有视频的url：字典结构，key=发布时间，value=每条抖音中视频的url list
    all_video_url_dict = dict()

    json_log_path = get_json_log_path()
    json_data_list = read_txt(json_log_path)
    if not json_data_list:
        print('  未在 {} 中读取到有效数据，请先把接口返回的 JSON 按行追加进去！'.format(json_log_path))
        return blogger_name, all_picture_url_dict, all_video_url_dict

    for json_data in json_data_list:
        try:
            resp_json = json.loads(json_data)
        except ValueError:
            print('  跳过一行无法解析的 JSON 数据')
            continue

        if 'aweme_list' not in resp_json:
            print(" 当前response key 无 'aweme_list'!")
            continue

        # 获取当页所有视频URL
        for aweme_list in resp_json['aweme_list']:
            if 'create_time' not in aweme_list:
                continue

            # 获取博主名字
            if not blogger_name:
                author = aweme_list.get('author', {})
                blogger_name = safe_name(author.get('nickname', ''))
                if not blogger_name:
                    continue
                blogger_list = read_txt(aweme_list_dir)
                if blogger_name in blogger_list:
                    print(' 当前blogger <' + blogger_name + '> 已在列表中，名字无需修正！')
                else:
                    change_name = input(
                        " 当前blogger<{}>不在列表中，名字是否修正（需要修正：输入修正名字；不需要修正：按回车键）：".format(blogger_name))
                    if change_name:
                        blogger_name = safe_name(change_name)
                    # 新下载的blogger写入到文本文档bloglist.txt
                    write_txt(aweme_list_dir, blogger_name)

            # 获取抖音发布时间
            time_tick = aweme_list['create_time']
            dt = datetime.fromtimestamp(time_tick)
            create_time = dt.strftime("%Y-%m-%d %H.%M.%S")

            picture_url_mblog = []  # 记录每条抖音图片url
            video_url_mblog = []  # 记录每条抖音视频 url
            aweme_type = aweme_list.get('aweme_type')
            # 图片抖音
            if aweme_type in IMAGE_TYPES:
                for image_list in aweme_list.get('images') or []:
                    url_list = image_list.get('url_list') or []
                    if url_list:
                        picture_url_mblog.append(url_list[0])
            # 视频抖音
            elif aweme_type in VIDEO_TYPES:
                play_addr = aweme_list.get('video', {}).get('play_addr', {})
                url_list = play_addr.get('url_list') or []
                if url_list:
                    video_url_mblog.append(url_list[0])
            else:
                print("  aweme_type = {}，非0、51、55、61、68！".format(aweme_type))

            if picture_url_mblog:
                all_picture_url_dict[create_time] = picture_url_mblog
            if video_url_mblog:
                all_video_url_dict[create_time] = video_url_mblog

    return blogger_name, all_picture_url_dict, all_video_url_dict


def build_opener():
    '构造带请求头与忽略证书校验的下载器'
    opener = request.build_opener(request.HTTPSHandler(context=context))
    opener.addheaders = list(header.items())
    return opener


def save_single_url(url, file_name):
    '下载单个 url 到 file_name，最多重试 MAX_RETRY 次'
    for attempt in range(MAX_RETRY + 1):
        try:
            opener = build_opener()
            with opener.open(url, timeout=DOWNLOAD_TIMEOUT) as response, \
                    open(file_name, 'wb') as file_handle:
                shutil.copyfileobj(response, file_handle)
            return True
        except Exception:
            # 清理下载失败产生的半截文件
            if os.path.exists(file_name):
                try:
                    os.remove(file_name)
                except OSError:
                    pass
            if attempt >= MAX_RETRY:
                print("\n    -->当前url({})下载异常次数超过{}次，退出下载！".format(url, MAX_RETRY))
                return False
            time.sleep(random.uniform(0.5, 1.5))
    return False


def get_url_signature(url, start_tag, end_tag):
    '提取 url 中不变的片段用于去重比对（url 本身带有时效参数，会变动）'
    start = url.find(start_tag)
    if start < 0:
        return url
    start += len(start_tag)
    end = url.find(end_tag, start)
    if end < 0:
        return url[start:]
    return url[start:end]


# 根据类型下载dict中所有的url
def download_by_type(all_url_dict, blogger_url_txt_dir, media_type):
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

    saved_signature_set = {get_url_signature(saved_url, start_tag, end_tag)
                           for saved_url in saved_url_list}

    download_mblog_num = 0
    for creat_time, url_mblog in all_url_dict.items():
        for index in range(0, len(url_mblog)):
            url = url_mblog[index]
            print('\r [{}已下载进度：{}%({}/{})] 开始下载<{}>时刻第{}张(条){}：{}'.format(
                media_type, int(download_mblog_num / all_mblog_num * 100), download_mblog_num,
                all_mblog_num, creat_time, index + 1, media_type, url), end='')

            if get_url_signature(url, start_tag, end_tag) in saved_signature_set:
                continue

            if media_type == '图片':
                file_name = os.path.join(picture_dir, '{} - {}{}'.format(creat_time, index + 1, ext))
            else:
                file_name = os.path.join(blogger_dir, '{}{}'.format(creat_time, ext))

            if save_single_url(url, file_name):
                saved_url_list.append(url)
                saved_signature_set.add(get_url_signature(url, start_tag, end_tag))
                write_txt(blogger_url_txt_dir, url)
                # webp转为jpg
                if media_type == '图片' and os.path.exists(file_name):
                    convert_webp_to_jpg(file_name)

        download_mblog_num += 1
        print('\r [{}已下载进度：{}%({}/{})]'.format(media_type, int(download_mblog_num / all_mblog_num * 100),
                                                    download_mblog_num, all_mblog_num), end='')
    print()


def convert_webp_to_jpg(file_name):
    'webp 转 jpg，转换成功后删除源 webp 文件'
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
    except Exception as error:
        print('\n    -->图片转换失败（{}）：{}'.format(file_name, error))


# 下载图片/视频
def download():
    blogger_name, all_picture_dict, all_video_dict = get_all_url()
    if not blogger_name:
        return
    set_sub_path(blogger_name)
    print('*' * 20 + ' <blogger：' + blogger_name + '> ' + '*' * 20)
    print(' <{}>视频抖音{}条，图片抖音{}条'.format(blogger_name, len(all_video_dict), len(all_picture_dict)))

    # 下载视频
    download_by_type(all_video_dict, blogger_url_txt_dir, '视频')
    # 下载图片
    download_by_type(all_picture_dict, blogger_url_txt_dir, '图片')

    print('*' * 45 + '\n')


def delete_blogger(blogger_list):
    for i in range(0, len(blogger_list)):
        print(str(int(i + 1)) + '：' + blogger_list[i])
    blog_id = read_int('输入对应得blog id：')
    while blog_id <= 0 or blog_id > len(blogger_list):
        blog_id = read_int('blog id 输入错误，重新输入：')
    blogger_name = blogger_list[blog_id - 1]
    rm_dir(os.path.join(download_dir, blogger_name))
    blogger_list.remove(blogger_name)
    write_list_txt(aweme_list_dir, blogger_list)
    print('  已删除 <{}> 及其下载内容'.format(blogger_name))


def read_int(prompt):
    '读取整数，输入非法时提示重新输入'
    while True:
        value = input(prompt).strip()
        try:
            return int(value)
        except ValueError:
            print('  请输入数字！')


def show_blogger_list(blogger_list):
    if not blogger_list:
        print('  博主列表为空')
        return
    for i in range(0, len(blogger_list)):
        print(str(int(i + 1)) + '：' + blogger_list[i])


if __name__ == '__main__':
    set_total_path()
    print('  下载目录：{}'.format(download_dir))
    print('  json.log：{}'.format(get_json_log_path()))
    while True:
        function_selection = input('\n  a:下载 b:删除blog c:获取blogger列表 x:退出程序 \n请输入对应得指令：').strip().lower()
        blogger_list = read_txt(aweme_list_dir)
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
