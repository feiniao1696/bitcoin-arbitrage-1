#-*- coding: utf-8 -*-
# Copyright (C) 2017, Jack Yao <yaozihao@yaozihao.cn>

import public_markets
import observers
import config
import time
import logging
import json
from concurrent.futures import ThreadPoolExecutor, wait
import traceback

import re,sys,re
import string
import signal


def sigint_handler(signum, frame):
    global is_sigint_up
    is_sigint_up = True
    print ('catched interrupt signal!')
 
is_sigint_up = False


class Arbitrer(object):
    def __init__(self):
        self.markets = []
        self.observers = []
        self.depths = {}
        self.init_markets(config.markets)
        self.init_observers(config.observers)
        self.threadpool = ThreadPoolExecutor(max_workers=10)

    def init_markets(self, _markets):
        logging.debug("_markets:%s" % _markets)
        self.market_names = _markets
        for market_name in _markets:
            try:
                exec('import public_markets.' + market_name.lower())
                market = eval('public_markets.' + market_name.lower() + '.' +
                              market_name + '()')
                self.markets.append(market)
            except (ImportError, AttributeError) as e:
                print("%s market name is invalid: Ignored (you should check your config file)" % (market_name))
                logging.warn("exception import:%s" % e)
                traceback.print_exc()

    def init_observers(self, _observers):
        logging.debug("_observers:%s" % _observers)

        self.observer_names = _observers
        for observer_name in _observers:
            try:
                exec('import observers.' + observer_name.lower())
                observer = eval('observers.' + observer_name.lower() + '.' +
                                observer_name + '()')
                self.observers.append(observer)
            except (ImportError, AttributeError) as e:
                print("%s observer name is invalid: Ignored (you should check your config file)" % (observer_name))
                print(e)

    def loop(self):
        #
        signal.signal(signal.SIGINT, sigint_handler)

        # 以下那句在windows python2.4不通过,但在freebsd下通过
        signal.signal(signal.SIGHUP, sigint_handler)

        signal.signal(signal.SIGTERM, sigint_handler)

        while True:
            # {'asks': [{'price': 0, 'amount': 0}], 'bids': [{'price': 0, 'amount': 0}]}
            self.depths = self.update_depths()
            # print(self.depths)
            self.tickers()
            self.tick()
            time.sleep(config.refresh_rate)

            if is_sigint_up:
                # 中断时需要处理的代码
                self.terminate()
                print("Exit")
                break

    def update_depths(self):
        depths = {}
        futures = []
        for market in self.markets:
            futures.append(self.threadpool.submit(self.__get_market_depth,
                                                  market, depths))
        wait(futures, timeout=20)
        return depths

    def __get_market_depth(self, market, depths):
        depths[market.name] = market.get_depth()

    def tickers(self):
        for market in self.markets:
            logging.verbose("ticker: " + market.name + " - " + str(
                market.get_ticker()))

    def tick(self):
        for observer in self.observers:
            observer.begin_opportunity_finder(self.depths)

        for kmarket1 in self.depths:
            for kmarket2 in self.depths:
                if kmarket1 == kmarket2:  # same market
                    continue
                market1 = self.depths[kmarket1]
                market2 = self.depths[kmarket2]
                if market1["asks"] and market2["bids"] \
                   and len(market1["asks"]) > 0 and len(market2["bids"]) > 0:
                    if float(market1["asks"][0]['price']) \
                       < float(market2["bids"][0]['price']):
                        print("Ask: ", kmarket1, market1["asks"][0], "Bid: ", kmarket2, market2["bids"][0])
                        self.arbitrage_opportunity(kmarket1, market1["asks"][0],
                                                   kmarket2, market2["bids"][0])

        for observer in self.observers:
            observer.end_opportunity_finder()

    # 第一档卖，便宜卖的交易所， 第一档买，买价高的交易所
    def arbitrage_opportunity(self, kask, ask, kbid, bid):
        # 买价 高于 卖价的比例
        perc = (bid["price"] - ask["price"]) / bid["price"] * 100
        # 计算买卖不同档位操作时，得到最优收益时的价格和量，
        profit, volume, buyprice, sellprice, weighted_buyprice,\
            weighted_sellprice = self.arbitrage_depth_opportunity(kask, kbid)
        if volume == 0 or buyprice == 0:
            return
        # 发送买价 高于 发送卖价的比例
        perc2 = (weighted_sellprice-weighted_buyprice)/buyprice * 100

        print("Buy: ", weighted_buyprice, "@", kask,
              " Sell: ", weighted_sellprice, "@", kbid, " Volume: ", volume,
              " Expected profit: ", profit, perc2)

        # -- call trader bot
        for observer in self.observers:
            # 预期收益，发送成交量，可卖最深档的价格（小于买一/i），便宜卖的交易所，可买最深档的价格（大于卖一/i），买的高交易所，高的比例，发送买价，发送卖价
            # 结合各自余额，更新发送成交量，生成自己的潜在trade，在end处执行交易
            observer.opportunity(
                profit, volume, buyprice, kask, sellprice, kbid,
                perc2, weighted_buyprice, weighted_sellprice)

    # 计算买卖最优价格，最优收益
    def arbitrage_depth_opportunity(self, kask, kbid):
        # 计算maxi 第卖几档可被买一覆盖，maxj 第买几档可被卖一覆盖
        maxi, maxj = self.get_max_depth(kask, kbid)
        best_profit = 0
        best_i, best_j = (0, 0)
        best_w_buyprice, best_w_sellprice = (0, 0)
        best_volume = 0
        for i in range(maxi + 1):
            for j in range(maxj + 1):
                # 计算买卖不同档位的利润，取利润最大的
                profit, volume, w_buyprice, w_sellprice = self.get_profit_for(
                    i, j, kask, kbid)
                if profit >= 0 and profit >= best_profit:
                    best_profit = profit
                    best_volume = volume
                    best_i, best_j = (i, j)
                    best_w_buyprice, best_w_sellprice = (
                        w_buyprice, w_sellprice)
        return best_profit, best_volume, \
               self.depths[kask]["asks"][best_i]["price"], \
               self.depths[kbid]["bids"][best_j]["price"], \
               best_w_buyprice, best_w_sellprice

    def get_max_depth(self, kask, kbid):
        i = 0
        # 卖所在交易的所有卖单，买所在交易所的所有买单
        if len(self.depths[kbid]["bids"]) != 0 and \
           len(self.depths[kask]["asks"]) != 0:
            # 计算买一价格大于至卖第i挡
            while self.depths[kask]["asks"][i]["price"] \
                  < self.depths[kbid]["bids"][0]["price"]:
                if i >= len(self.depths[kask]["asks"]) - 1:
                    break
                # logging.debug("i:%s,%s/%s,%s/%s", i, kask, self.depths[kask]["asks"][i]["price"],
                #   kbid, self.depths[kbid]["bids"][0]["price"])

                i += 1

        j = 0
        if len(self.depths[kask]["asks"]) != 0 and \
           len(self.depths[kbid]["bids"]) != 0:
            # 计算卖一价格低于至卖第i挡
            while self.depths[kask]["asks"][0]["price"] \
                  < self.depths[kbid]["bids"][j]["price"]:
                if j >= len(self.depths[kbid]["bids"]) - 1:
                    break
                # logging.debug("j:%s,%s/%s,%s/%s", j, kask, self.depths[kask]["asks"][0]["price"],
                #     kbid, self.depths[kbid]["bids"][j]["price"])

                j += 1

        return i, j

    def get_profit_for(self, mi, mj, kask, kbid):
        if self.depths[kask]["asks"][mi]["price"] >= self.depths[kbid]["bids"][mj]["price"]:
            return 0, 0, 0, 0

        max_amount_buy = 0
        for i in range(mi + 1):
            max_amount_buy += self.depths[kask]["asks"][i]["amount"]

        max_amount_sell = 0
        for j in range(mj + 1):
            max_amount_sell += self.depths[kbid]["bids"][j]["amount"]
        # 取最多买，最多卖，最大3个btc之间的最小，此为最终交易量的结果
        max_amount = min(max_amount_buy, max_amount_sell, config.max_tx_volume)

        # 计算买卖价格：根据不同档位的交易量*价，得到交易总额，除以总交易量，定为买或者卖的价格
        buy_total = 0
        w_buyprice = 0
        for i in range(mi + 1):
            price = self.depths[kask]["asks"][i]["price"]
            amount = min(max_amount, buy_total + self.depths[
                         kask]["asks"][i]["amount"]) - buy_total
            if amount <= 0:
                break
            buy_total += amount
            if w_buyprice == 0:
                w_buyprice = price
            else:
                w_buyprice = (w_buyprice * (buy_total - amount) + price * amount) / buy_total

        # 计算买卖价格：根据不同档位的交易量*价，得到交易总额，除以总交易量，定为买或者卖的价格
        sell_total = 0
        w_sellprice = 0
        for j in range(mj + 1):
            price = self.depths[kbid]["bids"][j]["price"]
            amount = min(max_amount, sell_total + self.depths[
                         kbid]["bids"][j]["amount"]) - sell_total
            if amount < 0:
                break
            sell_total += amount
            if w_sellprice == 0 or sell_total == 0:
                w_sellprice = price
            else:
                w_sellprice = (w_sellprice * (
                    sell_total - amount) + price * amount) / sell_total
        if abs(sell_total-buy_total) > 0.00001:
            logging.warn("sell_total=%s,buy_total=%s", sell_total, buy_total)

        profit = sell_total * w_sellprice - buy_total * w_buyprice
        return profit, sell_total, w_buyprice, w_sellprice

    def replay_history(self, directory):
        import os
        import json
        import pprint
        files = os.listdir(directory)
        files.sort()
        for f in files:
            depths = json.load(open(directory + '/' + f, 'r'))
            self.depths = {}
            for market in self.market_names:
                if market in depths:
                    self.depths[market] = depths[market]
            self.tick()

    def terminate(self):
        for observer in self.observers:
            observer.terminate()

        for market in self.markets:
            market.terminate()

