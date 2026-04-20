
'''
v1.1 优化获取所有url
v1.2
v2.0 非手机查看网页
v2.0 浏览器开发者工具获取当前页url
......
v4.0 1.使用json存储下载博主列表 {{"uid":"2321777100592404","nickname":"王乔熙"}...}
     2.获取url修改，允许一次下载多个作者的内容
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
class CDownloadInfo(object):
    m_NickName = ""     #名字
    m_CreateTime = ""   #创建时间
    m_Mode = ""         #模式：图片或视频
    m_UrlList = []      #url列表：视频只有一个url；图片有多个


from urllib import request
import re
import ssl
import os
import shutil
import time
import random
import socket
import json
from PIL import Image
from datetime import datetime

header = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/106.0.0.0 Safari/537.36 Edg/106.0.1370.52',
    'Accept': 'application/json, text/plain, */*',
    'Referer': 'https://www.douyin.com/user/MS4wLjABAAAACJyXOoE3noz3e-F1pRXwVnYvz2yMIgHx_1s3LaDYB4q1FVWRm-GDWRAbUdvPwPGq'
}

context = ssl._create_unverified_context()


# 如下为全局变量
download_dir  = ''
aweme_list_dir = ''
blogger_dir = ''
blogger_url_txt_dir = ''

def make_dir(dir):
    if not  os.path.exists(dir):
        os.makedirs(dir)
def make_txt(txt_str):
    file_handle = open(txt_str, mode='a')
    file_handle.close()
def rm_dir(dir):
    if os.path.exists(dir):
        shutil.rmtree(dir)
#以每一行格式读取txt文档，返回一个列表
def read_txt(txt_dir):
    txt_list = []
    file_handle = open(txt_dir, mode='r')
    while True:
        line = file_handle.readline().splitlines()
        if line:
            #print(line[0])
            txt_list.append(line[0])
        else:
            break
    file_handle.close()
    return txt_list

#追加写一行到txt文档
def write_txt(txt_dir, str):
    file_handle = open(txt_dir, mode = 'a')
    file_handle.write(str + '\n')
    file_handle.close()
def write_list_txt(txt_dir, list, length):
    file_handle = open(txt_dir, mode='w')
    for index in range(0,length):
        file_handle.write(list[index]+'\n')
    file_handle.close()

#设置总目录路径
def set_total_path():
    path_mode = '1'
    #path_mode = input("  0:相对路径；1:绝对路径：")
    global download_dir
    while True:
        if path_mode == '0':
            download_dir = './download/'
            break
        elif path_mode == '1':
            download_dir = 'F:/图片/douyin/'
            # download_dir = input("请输入绝对路径：")
            break
        else:
            print("选择路径指令错误，请重新输入！")
    make_dir(download_dir)
    global aweme_list_dir
    aweme_list_dir = download_dir + 'aweme_list.json'
    make_txt(aweme_list_dir)

#设置子目录路径
def set_sub_path(blogger_name):
    global blogger_dir
    blogger_dir = download_dir + blogger_name + '/'
    make_dir(blogger_dir)
    global blogger_url_txt_dir
    blogger_url_txt_dir = download_dir + blogger_name + '/url.txt'
    make_txt(blogger_url_txt_dir)

# 获取需要的信息

def get_all_url():
    blogger_name = ''
    # 记录所有图片的url：字典结构，key=发布时间，value=每条抖音中图片的url list
    all_picture_url_dict = dict()
    # 记录所有视频的url：字典结构，key=发布时间，value=每条抖音中视频的url list
    all_video_url_dict = dict()
    json_data_list = read_txt(download_dir + 'json.log')
    for json_data in json_data_list:
        resp_json = json.loads(json_data)
        if 'aweme_list' not in resp_json:
            print(" 当前response key 无 'aweme_list'!")
            return blogger_name, all_picture_url_dict, all_picture_url_dict

        # 获取当页所有视频URL
        for aweme_list in resp_json['aweme_list']:
            if 'create_time' not in aweme_list:
                continue
            else:
                # 锟斤拷取锟斤拷锟斤拷锟斤拷锟斤拷
                if not blogger_name:
                    # 剔除不符合文件夹名的字符：\/:*?"<>|
                    blogger_name = aweme_list['author']['nickname'].replace('\\', '').replace('/', '').\
                        replace(':', '').replace('*', '').replace('?', '').replace('"', '').replace('<', '')\
                        .replace('>', '').replace('|', '')
                    blogger_list = read_txt(aweme_list_dir)
                    if blogger_name in blogger_list:
                        print(' 当前blogger <' + blogger_name + '> 已在列表中，名字无需修正！')
                    else:
                        change_name = input(
                            " 当前blogger<{}>不在列表中，名字是否修正（需要修正：输入修正名字；不需要修正：按回车键）：".format(blogger_name))
                        if change_name:
                            blogger_name = change_name
                        # 新下载的blogger写入到文本文档bloglist.txt
                        write_txt(aweme_list_dir, blogger_name)

                # 获取抖音发布时间
                time_tick = aweme_list['create_time']
                dt = datetime.fromtimestamp(time_tick)
                create_time = dt.strftime("%Y-%m-%d %H.%M.%S")

                picture_url_mblog = []  # 记录每条微博图片url
                video_url_mblog = []  # 记录每条微博视频 url
                # 图片抖音
                if aweme_list['aweme_type'] == 68:
                    for image_list in aweme_list['images']:
                        if 'url_list' in image_list:
                            #print(image_list['url_list'][0])
                            picture_url_mblog.append(image_list['url_list'][0])
                # 视频抖音
                elif aweme_list['aweme_type'] == 0 or aweme_list['aweme_type'] == 55 or aweme_list['aweme_type'] == 51 or aweme_list['aweme_type'] == 61 or aweme_list['aweme_type'] == 66:
                    video_url_mblog.append(aweme_list['video']['play_addr']['url_list'][0])
                else:
                    print("  aweme_type = {}，非0、51、55、61、68！".format(aweme_list['aweme_type']))


                if picture_url_mblog:
                    all_picture_url_dict[create_time] = picture_url_mblog
                if video_url_mblog:
                    all_video_url_dict[create_time] = video_url_mblog
    return blogger_name, all_picture_url_dict, all_video_url_dict


def save_single_url(url, file_name):
    i = 0
    # 重新下载次数
    num = 3
    while True:
        # 最多下载三次，否则跳过
        if i > num:
            print("\n    -->当前url({})下载异常次数超过{}次，退出下载！".format(url, num))
            return False
        try:
            # if i != 0:
            #    print("    -->第" + str(i) + "次重新下载：" + url)
            # request.urlretrieve下载超时5s，重新下载，防止线程堵塞
            socket.setdefaulttimeout(5)
            request.urlretrieve(url, file_name)  # 锟斤拷锟?99999
            return True
        except Exception as error:
            i += 1
            #print(' ', end='')
            # print(error)
            # print(url)

# 根据类型下载dict中所有得url
def download_by_type(all_url_dict, blogger_url_txt_dir, type):
    saved_url_list = read_txt(blogger_url_txt_dir)
    all_mblog_num = len(all_url_dict)
    if all_mblog_num:
        download_mblog_num = 0
        for creat_time, url_mblog in all_url_dict.items():
            for index in range(0, len(url_mblog)):
                url = url_mblog[index]
                print('\r [{}已下载进度：{}%({}/{})] 开始下载<{}>时刻第{}张(条){}：{}'.format(
                    type, int(download_mblog_num / all_mblog_num * 100), download_mblog_num,
                    all_mblog_num, creat_time, index + 1, type, url), end='')
                file_name = ''
                is_need_download = True
                if type == '图片' :
                    make_dir(blogger_dir + '\picture')
                    file_name = blogger_dir + '\picture\\' + creat_time + ' - ' + str(index + 1) + '.webp'
                    # 图片url是动态的，所以使用"/tos-cn-i-......~tplv-dy-aweme-images"字符串来存储比较
                    start_tag = '/tos-cn-i-'
                    end_tag = '~tplv-dy-aweme-images'
                    url_start = url.find(start_tag) + len(start_tag)
                    url_end = url.find(end_tag)
                    for saved_url in saved_url_list:
                        saved_url_start = saved_url.find(start_tag) + len(start_tag)
                        saved_url_end = saved_url.find(end_tag)
                        if url[url_start:url_end] == saved_url[saved_url_start:saved_url_end]:
                            is_need_download = False
                elif type == '视频':
                    file_name = blogger_dir + creat_time + '.mp4'
                    # 视频url是动态的，所以使用"&ft=......&mime_type"字符串来存储比较
                    start_tag = '&rc='
                    end_tag = '&l='
                    url_start = url.find(start_tag) + len(start_tag)
                    url_end = url.find(end_tag)
                    for saved_url in saved_url_list:
                        saved_url_start = saved_url.find(start_tag) + len(start_tag)
                        saved_url_end = saved_url.find(end_tag)
                        if url[url_start:url_end] == saved_url[saved_url_start:saved_url_end]:
                            is_need_download = False

                if is_need_download and save_single_url(url_mblog[index], file_name):
                    saved_url_list.append(url)
                    write_txt(blogger_url_txt_dir, url)
                    # webp转为jpg
                    if type == '图片' and os.path.exists(file_name):
                        im = Image.open(file_name)
                        if im.mode == "RGBA":
                            im.load()  # required for png.split()
                            background = Image.new("RGB", im.size, (255, 255, 255))
                            background.paste(im, mask=im.split()[3])
                        save_name = file_name.replace('webp', 'jpg')
                        # 此处会保存到源filename路径下
                        im.save('{}'.format(save_name), 'JPEG')
                        if os.path.exists(file_name):
                            os.remove(file_name)

            download_mblog_num += 1
            print('\r [{}已下载进度：{}%({}/{})]'.format(type, int(download_mblog_num / all_mblog_num * 100),
                                                          download_mblog_num, all_mblog_num), end='')
        print()


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


if __name__ == '__main__':
    set_total_path()
    while True:
        function_selection = input('\n  a:下载 b:删除blog c:获取blogger列表 x:退出程序 \n请输入对应得指令：')
        blogger_list = read_txt(aweme_list_dir)
        if function_selection == 'a':
            # blogger_response = input('blogger response:')
            download()
        elif function_selection == 'b':
            for i in range(0, len(blogger_list)):
                print(str(int(i + 1)) + '：' + blogger_list[i])
            blog_id = int(input('输入对应得blog id：'))
            while True:
                if blog_id <= 0 or blog_id > len(blogger_list):
                    blog_id = int(input('blog id 输入错误，重新输入：'))
                else:
                    break
            blogger_name = blogger_list[blog_id - 1]
            rm_dir(download_dir + blogger_name + '/')
            blogger_list.remove(blogger_name)
            write_list_txt(aweme_list_dir, blogger_list, len(blogger_list))
        elif function_selection == 'c':
            for i in range(0, len(blogger_list)):
                print(str(int(i + 1)) + '：' + blogger_list[i])
        elif function_selection == 'x':
            exit()
        else:
            print('指令输入错误，请重新输入！')