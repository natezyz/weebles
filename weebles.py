#!/bin/bash

from lxml import html
import csv,os,json
import requests
from time import sleep

# 0078458137
DESIRED_MARGIN = 200
headers = {'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/42.0.2311.90 Safari/537.36'}

def fetch_asins(keyword='biology', year='2008', max_price='2', binding='H'):
    url = 'https://www.alibris.com/booksearch?fiction=N&qyear={}}&qtopic={}}&qpricehi={}}&binding={}}&mtype=B&qsort=p'.format(year, keyword, max_price, binding)
    page = requests.get(url, headers=headers)
    doc = html.fromstring(page.content)

    data = {}
    BOOK = '//*[@id="works"]/li'
    ISBN = '//*[@id="works"]/li'
    doc.xpath()

def AmazonParser(asin):
    url = 'https://smile.amazon.com/gp/offer-listing/{}/ref=olp_f_primeEligible?f_primeEligible=true'.format(asin)
    print('Processing url',url)
    page = requests.get(url, headers=headers)
    while True:
        sleep(2)
        try:
            doc = html.fromstring(page.content)
            OFFER_BASE='//*[@id="olpOfferList"]/div/div/div[contains(@class, "olpOffer")]'
            PRICES = OFFER_BASE + '/div[contains(@class, "olpPriceColumn")]/span[contains(@class, "olpOfferPrice")]/text()'

            raw_prices = doc.xpath(PRICES)
            price = min([float(i.strip().lstrip('$')) for i in raw_prices])
            return {'asin': asin, 'price': price}
        except Exception as e:
            print(e)

def AlibrisParser(isbn, maxPrice=2):
    url = 'https://www.alibris.com/booksearch?qpricehi={}&isbn={}&mtype=B&qsort=p'.format(maxPrice, isbn)
    print('Processing url',url)
    page = requests.get(url.format(isbn), headers=headers)
    while True:
        try:
            doc = html.fromstring(page.content)
            BASE = '//*[@id="all-carousel"]/div/div/div/ul'
            PRICE = '/li/table/tbody/tr/td[3]/p/text()'
            CONDITION = '/li/table/tbody/tr/td[1]/p[1]/a/text()'

            prices = [float(i.strip().lstrip('$')) for i in doc.xpath(BASE + PRICE)]
            conditions = [i.strip() for i in doc.xpath(BASE + CONDITION)]
            return [{'price': p, 'condition': c, 'shipping': 3.99, 'url': url, 'asin': isbn} for p, c in zip(prices, conditions)]
        except Exception as e:
            print(e)

def Read():
    AsinList = ['0078458137']
    search_amazon = []
    for i in AsinList:
        ali_books = AlibrisParser(i, maxPrice=10)
        ali_books = list(filter(lambda a: a['condition'] != 'Fair' , ali_books))
        search_amazon.append(min(ali_books, key=lambda x: x['price']))

    flippable_books = []
    for book in search_amazon:
        amazon_book = AmazonParser(book['asin'])
        book_margin = margin(book['price'] + book['shipping'], amazon_book['price'])
        if book_margin > DESIRED_MARGIN:
            book['margin'] = book_margin
            book['amazon_price'] = amazon_book['price']
            flippable_books.append(book)

    print(flippable_books)
    f = open('data.json', 'w')
    json.dump(flippable_books, f, indent=4)

def amazon_fee(price):
    return 6.25 + 1.8 + (.15 * float(price))

def margin(used, prime):
    proceeds = prime - amazon_fee(used)
    net_profit = proceeds - used
    return (net_profit / prime) * 100

if __name__ == '__main__':
    Read()