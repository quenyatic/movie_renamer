# renamer
import requests
import os
import re
from bs4 import BeautifulSoup
from urllib.parse import urlparse, urlencode, quote_plus
import urllib.request


def get_folder_list():
    folder_list_file = './folder_list.txt'
    fp = open(folder_list_file, mode='r', encoding='utf-8')
    folder_list = []
    while True:
        folder_path_temp = fp.readline().strip()
        if not folder_path_temp: break

        if os.path.isdir(folder_path_temp):
            folder_list.append(folder_path_temp)
    fp.close()

    return folder_list


def folder_parser(movie_folder):
    pattern = '([a-zA-Z0-9].*)(19\d{2}|20\d{2})'
    regex = re.compile(pattern)
    folder_parse_info = regex.findall(movie_folder)

    if len(folder_parse_info) == 0:
        return {}

    folder_info = {
        'year': int(folder_parse_info[0][1]),
        'title': folder_parse_info[0][0],
        'search': '',
    }

    if len(folder_info['title']) > 0 and folder_info['year'] > 1800 < 2200:
        folder_info['search'] = quote_plus(folder_parse_info[0][0].strip(' '))
    else:
        folder_info = {}

    return folder_info


def get_naver_info(folder_info):
    remove_string = ['\\', '/', ':', '*', '?', '"', '<', '>', '|']
    prefix_list = ['genre', 'nation', 'year', '/bi/pi/basic']
    year = folder_info['year']

    # 네이버에서 가져오기
    naver_movie_link = 'http://movie.naver.com/movie/search/result.nhn?section=movie&query=' + folder_info['search']

    # 가져오기
    req = requests.get(naver_movie_link)
    html = req.text
    soup = BeautifulSoup(html, 'html.parser')

    item_list = soup.select('ul.search_list_1 > li')

    rename_info_list = []
    for item in item_list:
        img_src = item.select('p.result_thumb img')[0]['src']
        img_url_parse = urlparse(img_src)
        img_src = img_src.replace(img_url_parse.query, '')
        img_src = img_src.replace('?', '')

        title = item.select('dl > dt > a')[0].get_text()
        for replace_string in remove_string:
            title = title.replace(replace_string, '-')

        etc_info = item.select('dl > dd.etc a')

        prefix_info = {}
        for etc in etc_info:
            for prefix in prefix_list:
                if etc['href'].find(prefix) > 0 and prefix not in prefix_info:
                    prefix_info[prefix] = etc.get_text()
                elif etc['href'].find(prefix) > 0 and '/bi/pi/basic' in prefix_info:
                    prefix_info[prefix] = prefix_info[prefix] + '.' + etc.get_text()

        # 연도가 있음 비교하기
        if 'year' in prefix_info and (int(prefix_info['year']) < year - 1 or int(prefix_info['year']) > year + 1):
            continue

        if 'year' not in prefix_info:
            prefix_info['year'] = year

        if 'nation' not in prefix_info:
            prefix_info['nation'] = '불명'

        if 'genre' not in prefix_info:
            prefix_info['genre'] = '불명'

        if '/bi/pi/basic' not in prefix_info:
            prefix_info['/bi/pi/basic'] = ''

        folder_name = ('[ %s %s %s ] %s' % (prefix_info['nation'], prefix_info['genre'], prefix_info['year'], title))

        # 폴더명 변경
        for remove_str in remove_string:
            folder_name = folder_name.replace(remove_str, '.')

        rename_info_list.append({'folder': folder_name, 'img_src': img_src, 'person': prefix_info['/bi/pi/basic']})

    return rename_info_list


def set_renamer(origin_info, rename_info, key=0):
    # 이미지 전송
    dst = origin_info['path'] + os.sep + rename_info[key]['folder']
    src = origin_info['path'] + os.sep + origin_info['folder_name']
    poster_path = src + os.sep + 'poster.jpg'

    # 동일 폴더명 체크
    folder_check = False
    for pre_folder in os.listdir(origin_info['path']):
        if pre_folder == rename_info[key]['folder']:
            print('동일 폴더가 존재합니다.')
            folder_check = True

    if not folder_check:
        print('')
        print('[기존] : ' + origin_info['folder_name'])
        print('[변경] : ' + rename_info[key]['folder'])
        answer = (input('변경 할까요? [Y/n]: ') or 'y')

        if answer.lower() == 'y':
            if os.path.isfile(rename_info[key]['img_src']) is False:
                urllib.request.urlretrieve(rename_info[key]['img_src'], poster_path)

            os.rename(src, dst)

    return True


def main():
    # read folder list
    folder_list = get_folder_list()

    for movie_path in folder_list:
        print('[작업진행] ' + movie_path)
        for movie_folder_name in os.listdir(movie_path):
            origin_info = {
                'path': movie_path,
                'folder_name': movie_folder_name
            }

            if os.path.isfile(origin_info['path'] + os.sep + origin_info['folder_name']):
                continue
            
            movie_folder = origin_info['folder_name'].replace('(', '').replace(')', '')
            if movie_folder[0] == '[':
                continue

            folder_info = folder_parser(movie_folder)
            if len(folder_info) == 0:
                continue

            movie_info_list = get_naver_info(folder_info)

            if len(movie_info_list) == 1:
                set_renamer(origin_info, movie_info_list)
            elif len(movie_info_list) > 1:
                i = 1
                origin_title = '[기존] ' + origin_info['folder_name']
                print(origin_title)
                print('-' * len(origin_title))

                for movie_info in movie_info_list:
                    folder_name = (' %d => %s | %s' % (i, movie_info['folder'], movie_info['person']))
                    print(folder_name)
                    i = i + 1

                answer = (input('변경한다면 번호를 선택해주세요. [1-10 / N]: ') or 'n')
                if answer.lower() != 'n' and int(answer) >= 1:
                    set_renamer(origin_info, movie_info_list, int(answer) - 1)

            print('')


if __name__ == "__main__":
    main()