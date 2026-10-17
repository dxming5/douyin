# -*- coding: utf-8 -*-
"""
JSON 解析与 URL 提取模块
负责解析 json.log 文件，提取博主信息、图片URL和视频URL
"""

import json
from datetime import datetime

from config import IMAGE_TYPES, VIDEO_TYPES
from utils import read_txt, write_txt, safe_name
import paths  # 导入模块而非具体变量，以便动态获取更新后的值


def get_all_url():
    """
    解析 json.log 文件，提取博主名、图片URL字典、视频URL字典
    
    Returns:
        tuple: (blogger_name, all_picture_url_dict, all_video_url_dict)
            - blogger_name: 博主昵称
            - all_picture_url_dict: key=发布时间, value=图片URL列表
            - all_video_url_dict: key=发布时间, value=视频URL列表
    """
    blogger_name = ''
    # 记录所有图片的url：字典结构，key=发布时间，value=每条抖音中图片的url list
    all_picture_url_dict = dict()
    # 记录所有视频的url：字典结构，key=发布时间，value=每条抖音中视频的url list
    all_video_url_dict = dict()

    json_log_path = paths.get_json_log_path()
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
                blogger_list = read_txt(paths.aweme_list_dir)
                if blogger_name in blogger_list:
                    print(' 当前blogger <' + blogger_name + '> 已在列表中，名字无需修正！')
                else:
                    change_name = input(
                        " 当前blogger<{}>不在列表中，名字是否修正（需要修正：输入修正名字；不需要修正：按回车键）：".format(blogger_name))
                    if change_name:
                        blogger_name = safe_name(change_name)
                    # 新下载的blogger写入到文本文档bloglist.txt
                    write_txt(paths.aweme_list_dir, blogger_name)

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
