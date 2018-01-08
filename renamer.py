# renamer
import requests, os, re
from bs4 import BeautifulSoup
from urllib.parse import urlparse
import urllib.request

# 기본 설정값
movie_path = os.getcwd()
remove_string = ['\\','/',':','*','?','"','<','>','|']
pattern = '([a-zA-Z0-9].*)(19\d{2}|20\d{2})'
prefix_list = ['genre', 'nation', 'year']

regex = re.compile(pattern)

year = 2016
postor_path = movie_path + '\postor.jpg'

for movie_folder_name in os.listdir(movie_path):
    movie_folder = movie_folder_name.replace('(','').replace(')','')
    if movie_folder[0] == '[':
        continue
    
    folder_info = regex.findall(movie_folder)
    if len(folder_info) > 0 and int(folder_info[0][1]) > 1800 and int(folder_info[0][1]) < 2200:
        year = int(folder_info[0][1])
        movie_title_info = folder_info[0][0].split('.')
        search_word = [];
        for title_temp in movie_title_info:
            if title_temp.strip() != '':
                search_word.append(title_temp.lower())
        search_text = "+".join(search_word)

        if search_text == '':
            continue

        # search_text = 'self+less'
        # 네이버에서 가져오기
        naver_movie_link = 'http://movie.naver.com/movie/search/result.nhn?section=movie&query=' + search_text

        # 가져오기
        req = requests.get(naver_movie_link)
        html = req.text
        soup = BeautifulSoup(html, 'html.parser')

        item_list = soup.select('ul.search_list_1 > li')

        rename_info = []
        max_count = 5
        for item in item_list:
            if max_count == 0:
                continue

            max_count -= 1
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

            # 연도가 있음 비교하기
            if 'year' in prefix_info and (int(prefix_info['year']) < year - 1 or int(prefix_info['year']) > year + 1):
                continue

            if 'year' not in prefix_info:
                prefix_info['year'] = year

            if 'nation' not in prefix_info:
                prefix_info['nation'] = '불명'

            if 'genre' not in prefix_info:
                prefix_info['genre'] = '불명'
        
            folder_name = ('[ %s %s %s ] %s' % (prefix_info['nation'], prefix_info['genre'], prefix_info['year'], title))

            # 폴더명 변경
            for remove_str in remove_string:
                folder_name = folder_name.replace(remove_str, '.')

            # dnlsehdn 
            rename_info.append({'folder': folder_name, 'img_src': img_src})             

        if len(rename_info) == 1:
            # 이미지 전송
            dst = movie_path + '\\' + rename_info[0]['folder']
            src = movie_path + '\\' + movie_folder_name
            
            # 동일 폴더명 체크
            folder_check = False
            for pre_folder in os.listdir(movie_path):
                if pre_folder == rename_info[0]['folder']:
                    folder_check = True

            if not folder_check:
                print('[기존] : ' + movie_folder_name)
                print('[변경] : ' + rename_info[0]['folder'])
                answer = input('변경 할까요? [Y/n]: ')
                if answer == '':
                    answer = 'y'

                if answer.lower() == 'y':
                    urllib.request.urlretrieve(rename_info[0]['img_src'], src + '\postor.jpg')
                    os.rename(src, dst) 

                print('')
        else:
            print(rename_info)
            pass
