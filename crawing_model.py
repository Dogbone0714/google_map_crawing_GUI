import random
import pandas as pd
import time
from bs4 import BeautifulSoup
import requests
import json
import emoji
import csv
import re
import numpy as np

# 根據輸入店家id返回店家名稱

def get_store_name(store_id):

    headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; WOW64) "
               "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/55.0.2883.87 Safari/537.36"}
    url = f'https://www.google.com.tw/maps/place/%E9%9A%B1%E5%AE%B6%E6%8B%89%E9%BA%B5+%E8%B5%A4%E5%B3%B0%E5%BA%97/data=!4m5!3m4!1s{store_id}!8m2!3d25.0564743!4d121.5204167?authuser=0&hl=zh-TW&rclk=1'
    r = requests.get(url, headers=headers)
    soup = BeautifulSoup(r.text, "lxml")
    meta_list=soup.find_all('meta')
    store_name=[]
    for i in meta_list:
        if '''itemprop="name"''' in str(i):
            store_name.append(re.search('".*·',str(i)).group()[1:-2])
    store_name=store_name[0]

    return store_name

# 根據輸入店家名返回相關店家

def get_interrelate_store_name(store_name):

    headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.s0; WOW64) "
               "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/55.0.2883.87 Safari/537.36"}
    url = f'https://www.google.com.tw/maps/search/{store_name}'
    r = requests.get(url, headers=headers)
    soup = BeautifulSoup(r.text, "lxml")
    store_id_list = set(re.findall(
        '0x.{16}:0x.{16}', str(soup)))  # 正規表示法搜尋id格式
    store_id_list = [store_id.replace('\\', '') for store_id in store_id_list]

    store_name_list = []
    for store_id in store_id_list:
        try:
            store_name_list.append(get_store_name(store_id))
        except:
            pass

    store_dict = {index: letter for index,
                  letter in zip(store_name_list, store_id_list)}

    return store_dict

# 獲取評論

def get_comment(store_id):

    store_id_lidt = store_id.split(':')

    headers = {
        'user-agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_6) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/85.0.4183.83 Safari/537.36 Edg/85.0.564.41'
    }

    url1 = f"https://www.google.com.tw/maps/preview/review/listentitiesreviews?authuser=0&hl=zh-TW&gl=tw&authuser=0&pb=!1m2!1y{store_id_lidt[0]}!2y{store_id_lidt[1]}!2m2!1i"
    url3 = "!2i10!3e1!4m5!3b1!4b1!5b1!6b1!7b1!5m2!1s!7e81"

    # 爬取評論數

    time = []  # 評論時間/相對
    replay_time = []  # 評論時間/絕對
    author = []  # 評論者
    author_id = []  # 評論者id
    comment = []  # 評論內容
    rating = []  # 評論評分
    grade = []  # 評論者等級
    state = []  # 評論者狀態

    for i in range(0, 10000):

        try:

            url2 = (i*10)
            url = url1+str(url2)+url3
            text = requests.get(url, headers=headers).text
            pretext = ')]}\''
            text = text.replace(pretext, '')
            text = emoji.demojize(text)
            soup = json.loads(text)
            conlist = soup[2]

            for i in conlist:
                try:
                    comment.append(str(i[3]).replace('\n', ''))
                except:
                    comment.append(np.nan)
                try:
                    time.append(str(i[1]))
                except:
                    time.append(np.nan)
                try:
                    author.append(str(i[0][1]))
                except:
                    author.append(np.nan)
                try:
                    rating.append(str(i[4]))
                except:
                    rating.append(np.nan)
                try:
                    author_id.append(str(i[6]))
                except:
                    author_id.append(np.nan)

                # 日期格式處理
                try:
                    reply_time = str(([str(number) if number > 9 else '0'+str(number) for number in i[14][0][-1][-2][-2][:3]])
                                     ).replace('[', '').replace(']', '').replace('\'', '').replace(',', '-').replace(' ', '')
                    replay_time.append(reply_time)
                except:
                    replay_time.append(np.nan)

                try:
                    grade.append(str(i[12][1][0][0]))
                except:
                    grade.append(np.nan)
                try:
                    state.append(str(i[12][1][12][0]))
                except:
                    state.append(np.nan)

        except:
            break
        
    google_comment_df = pd.DataFrame({
        "評論者": author,
        "評論者id": author_id,
        "評論者狀態": state,
        "評論者等級": grade,
        "留言時間": time,
        "留言日期": replay_time,
        "評論": comment,
        "評論分數": rating,
    })

    return google_comment_df

# 新增景點所在縣市功能
def get_spot_city(spot_name):
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; WOW64) "
                      "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/55.0.2883.87 Safari/537.36"
    }
    url = f"https://www.google.com.tw/maps/search/{spot_name}"
    response = requests.get(url, headers=headers)
    soup = BeautifulSoup(response.text, "lxml")
    
    # 提取完整地址資訊
    address_tag = soup.find("meta", itemprop="address")
    address = address_tag.get("content", "") if address_tag else "無法獲取地址"
    
    # 嘗試提取縣市（假設地址格式為「台北市信義區XXX」或「台中市XXX」）
    city_match = re.search(r"[\u4e00-\u9fa5]{2,3}(市|縣)", address)
    city = city_match.group() if city_match else "無法判斷縣市"
    
    return city

# 修改景點介紹功能以包含縣市資訊
def get_spot_info(spot_name):
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; WOW64) "
                      "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/55.0.2883.87 Safari/537.36"
    }
    url = f"https://www.google.com.tw/maps/search/{spot_name}"
    response = requests.get(url, headers=headers)
    soup = BeautifulSoup(response.text, "lxml")
    
    # 提取景點名稱
    title = soup.find("h1", class_="fontHeadlineLarge").text if soup.find("h1", class_="fontHeadlineLarge") else "無法獲取名稱"
    
    # 提取簡介描述
    description = None
    description_tag = soup.find("meta", attrs={"name": "description"})
    if description_tag:
        description = description_tag.get("content", "").split(".")[0]  # 通常第一句是簡介
    
    # 提取評分和評論數
    rating = soup.find("span", class_="fontBodyLarge").text if soup.find("span", class_="fontBodyLarge") else "無評分"
    review_count = re.search(r"\d+ 則評論", response.text)
    review_count = review_count.group() if review_count else "無評論數"
    
    # 提取所在縣市
    city = get_spot_city(spot_name)
    
    # 整理為字典
    spot_info = {
        "景點名稱": title,
        "簡介": description,
        "評分": rating,
        "評論數": review_count,
        "縣市": city
    }
    
    return spot_info
