from pycoingecko import CoinGeckoAPI
import numpy as np
from time import sleep
import time
from tqdm import tqdm
import pandas as pd
import os.path
from datetime import datetime
from sys import stdout
import matplotlib.pyplot as plt

cg = CoinGeckoAPI()


# 1. filter through all coins to find biggest climbers/lowest volatility
# get ids
def get_coin_ids():
    coins = cg.get_coins_list()
    coins_id = []
    for coin in coins:
        for k, v in coin.items():
            if k == 'id' and v != '':
                coins_id.append(v)
    return coins_id


# get market data for last x days for all coins
def get_ten_day_records(coin_ids, days=10):
    all_coin_records = {}
    for id in tqdm(range(len(coin_ids))):
        records = cg.get_coin_market_chart_by_id(id=coin_ids[id], vs_currency='usd', days=days)
        prices = [i for i in records['prices']]
        if len(prices) != 241:
            if len(prices) == 242:
                prices.pop(0)
            else:
                sleep(1.2)
                continue
        prices = [x.pop(1) for x in prices if len(x) > 1]
        all_coin_records[f'{coin_ids[id]}'] = prices
        id += 1
        sleep(1.2)
    records = pd.DataFrame.from_dict(all_coin_records)
    records.to_csv("latest_data.csv")


# calculate gains vs losses & negative volatility
def calc_change(records):
    for k, v in records.items():
        agg_change = 0
        volatility = []
        for n, price in enumerate(v):
            if n == 0:
                last = price
            else:
                agg_change += price - last
                if price - last < 0:
                    volatility.append(abs(price - last))
                last = price
        v.append(np.mean(volatility) if volatility else 0)
        v.append(agg_change)
        v.append()
    return records


# convert seconds to mins/hours
def convert_secs(start):
    num = time.time() - start
    if num >= 60 and num < 3600:
        num /= 60
        num = round(num, 2)
        output = str(num) + " minutes"
    elif num >= 3600:
        num /= 3600
        num = round(num, 2)
        output = str(num) + " hours"
    else:
        num = round(num, 2)
        output = str(num) + " seconds"
    return output


# get price change for a coin every 1.2 seconds according to api limit, save to csv
def get_price(coin_ids):
    start = time.time()
    enum = 0
    while True:
        coin_id = coin_ids[enum]
        price = cg.get_price(coin_id, 'usd')
        now = datetime.now()
        path = f"{coin_id}.csv"
        if not os.path.isfile(path):
            with open(path, 'w'):
                continue
        with open(path, 'a') as coin_data:
            coin_data.write(f'\n{now.strftime("%d/%m/%Y, %H%M%S")}, {price[coin_id]["usd"]}')
            stdout.write(f'\rRunning for {convert_secs(start)}')  # keep one-line progress printed to console
            stdout.flush()
            enum = enum + 1 if enum < 4 else 0
            sleep(1.2)


# clean and plot data
def plot_data(fname):
    with open(fname) as data:
        reader = data.readlines()[1:]
        y_data = []
        for line in reader:
            line = line.split(',')
            for c in line[2]:
                if not c.isdigit():
                    line[2].replace(c, '')
            if line[2].isdigit():
                y_data.append(int(line[2]))
    x_data = [x for x in range(len(y_data))]
    plt.plot(x_data, y_data)
    plt.show()
