#!/usr/bin/python3.7
# -*- coding: utf-8 -*-  

import requests
from bs4 import BeautifulSoup
import time
import random
import csv
import pymongo

index = 0

def get_html(base_url):
    proxy_addr = {'http': '118.114.77.47:8080'}
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/67.0.3396.99 Safari/537.36'}
    html = requests.get(base_url, headers=headers, proxies=proxy_addr)
    return html


def get_pageurl(base_url):
    soup = BeautifulSoup(get_html(base_url).text, 'lxml')
    tags = soup.select('#content div div table tbody tr td a')
    url = []
    for tag in tags:
        tag = tag.get_text()
        href = 'https://book.douban.com/tag/'
        pageurl = href + str(tag)
        if(tag == "互联网"):
            url.append(pageurl)
    return url


# 解析出图书信息
def bookinfo(url):
    global index
    myclient = pymongo.MongoClient('mongodb://localhost:27017')
    mydb = myclient["e-book-images"]
    mycol = mydb["bookimage"]

    html = requests.get(url)
    soup = BeautifulSoup(html.text, 'lxml')
    tag = url.split("?")[0].split("/")[-1]
    booknames = soup.select('#subject_list ul  div.info h2 a')
    details = soup.select('#subject_list ul div.info div.pub')
    ratings = soup.select('#subject_list div.info div.star.clearfix span.rating_nums')  # 评分
    peoples = soup.select('#subject_list  div.star.clearfix span.pl')  # 评价人数
    intros = soup.select('#subject_list  ul  div.info p')
    pics = soup.select("#subject_list  ul  li div.pic  a  img")
    data = []
    for bookname, detail, rating, person, intro, pic in zip(booknames, details, ratings, peoples, intros, pics):
        info = {}
        try:
            info["id"] = index
            info['类型'] = tag
            booktitle = bookname.get_text().split()[0]
            info['书籍名称'] = booktitle
            author = detail.get_text().split('/', 4)[0].lstrip('\n          ').rstrip('\n        ')
            info['作者'] = author
            translator = detail.get_text().split('/', 4)[1]
            info['译者'] = translator
            rating_num = rating.get_text()  # 评分
            info['豆瓣评分'] = rating_num
            press = detail.get_text().split('/', 4)[2]
            info['出版社'] = press
            date = detail.get_text().split('/', 4)[3].split('-')[0]
            info['出版日期'] = date
            price = detail.get_text().split('/', 4)[4].lstrip('\n          ').rstrip('\n        ')
            price = price.replace("元", "").replace("CNY", "").replace("NT$", "")
            info['价格'] = price
            person = get_num(person)  # 评价人数
            info['评价人数'] = person
            introduction = intro.get_text()
            info['简介'] = introduction
            info['isbn'] = get_isbn(bookname["href"])
            data.append(info)
            image_dir = {"_id": index, "image_file": requests.get(pic["src"], stream=True).content}
            mycol.insert_one(image_dir)
            index = index + 1
        except IndexError:
            continue
        except TypeError:
            continue
    return data


# 判断评价人数，没有数据的按 10 人处理
def get_num(person):
    try:
        person = int(person.get_text().split()[0][1:len(person.get_text().split()[0]) - 4])
    except ValueError:
        person = int(10)
    return person


def get_isbn(url):
    # url='http://book.douban.com/subject/6082808/?from=tag_all' # For Test
    html = requests.get(url)
    soup = BeautifulSoup(html.text, 'lxml')
    try:
        return "isbn" + str(soup.find(text='ISBN:').next_element.strip())
    except AttributeError:
        return None


def write2csv(url):
    print('正在写入文件')
    with open('C:\\Users\\hsc\\Documents\\豆瓣读书列表.csv', 'a', newline='', encoding='utf-8') as f:
        fieldnames = ['id', '类型', '书籍名称', '作者', '译者', '豆瓣评分', '出版社', '出版日期', '评价人数', '价格', '简介', 'isbn']  # 控制列的顺序
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        data = bookinfo(url)
        writer.writerows(data)
        print("写入成功")


def main():
    base_url = 'https://book.douban.com/tag/?view=cloud'
    start = time.clock()
    for urls in get_pageurl(base_url):
        urlss = [urls + "?start={}&type=T".format(str(i)) for i in range(0, 10000, 20)]
        for url in urlss:
            data = bookinfo(url)
            write2csv(url)
            time.sleep(int(format(random.randint(0, 9))))  # 爬取每页书本信息后随机等待几秒，反爬虫操作
    end = time.clock()
    print('Time Usage:', end - start)  # 爬取结束，输出爬取时间


if __name__ == '__main__':
    main()
