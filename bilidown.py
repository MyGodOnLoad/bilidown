import os
import random
import re
import time
from concurrent.futures.thread import ThreadPoolExecutor

import requests
import json
from contextlib import closing

print("""
/*********************/
支持分集下载 支持的链接格式如下
https://b23.tv/*
https://www.bilibili.com/video/BV*
https://www.bilibili.com/video/av*
项目地址：https://github.com/5ime/bilidown
/*********************/
""")

cookies = input('''请粘贴你的哔哩哔哩cookies\n''')
cookie = {
    'Cookie': cookies
}
header = {
    'User-Agent': 'Mozilla/5.0 (iPhone; CPU iPhone OS 11_0 like Mac OS X) AppleWebKit/604.1.38 (KHTML, like Gecko) Version/11.0 Mobile/15A372 Safari/604.1',
    'Referer': 'https://www.bilibili.com'
}
s = requests.session()

my_info = json.loads(
    s.get('http://api.bilibili.com/x/space/myinfo', cookies=cookie).text)
print("\n欢迎你！" + my_info['data']['name'])

url = input("""\n请粘贴哔哩哔哩视频链接\n""")
if 'https://b23.tv' in url:
    loc = s.get(url, allow_redirects=False)
    url = loc.headers['location']

if 'video/av' in url:
    av = json.loads(s.get(
        'https://api.bilibili.com/x/web-interface/archive/stat?aid=' + url,
        headers=header, cookies=cookie).text)
    url = av['data']['bvid']

video_id = re.findall("[\w.]*[\w:\-\+\%]", url)[3]
vid = json.loads(
    s.get('https://api.bilibili.com/x/web-interface/view?bvid=' + video_id,
          headers=header, cookies=cookie).text)

title = vid['data']['title']
while True:
    try:
        if not os.path.exists(title):
            os.mkdir(title)
        break
    except OSError:
        title = input('请重命名文件夹:')


def Download(video_url, video_name, header):
    file_name = os.path.join(title, video_name + '.flv')
    if os.path.exists(file_name):
        print(f'{video_name} 已存在！')
        return

    print("\n视频标题：%s\n下载链接：%s" % (video_name, video_url))
    with closing(s.get(video_url, headers=header, stream=True)) as response:
        chunk_size = 1024  # 单次请求最大值

        with open(file_name, 'wb') as file:
            for data in response.iter_content(chunk_size=chunk_size):
                file.write(data)
            print(f'{video_name} 下载成功！')


print(f"视频共{len(vid['data']['pages'])}集")
print("""
正在自动下载视频中，切勿关闭窗口
如下载失败请自行复制下载链接下载(需设置Referer)
""")


def preprocessing(args):
    index, page = args
    video_name = f'{index}.{page["part"]}'
    video = page['cid']

    video_info = json.loads(s.get(
        'https://api.bilibili.com/x/player/playurl?bvid=' + video_id + '&cid='
        + str(video) + '&qn=80&otype=json', headers=header, cookies=cookie).text)
    video_url = video_info['data']['durl'][0]['url']
    Download(video_url, video_name, header)


page_list = list(enumerate(vid['data']['pages']))

start = time.time()
pool = ThreadPoolExecutor(max_workers=5)
futures = pool.map(preprocessing, page_list)
pool.shutdown(wait=True)
end = time.time()
print(f'下载结束，共耗时：{end - start}s')
