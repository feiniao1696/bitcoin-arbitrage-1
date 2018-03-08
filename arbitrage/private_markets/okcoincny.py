# Copyright (C) 2017, JackYao <yaozihao@yaozihao.cn>

from .market import Market, TradeException
import time
import base64
import hmac
import urllib.request
import urllib.parse
import urllib.error
import hashlib
import sys
import json
import config
from lib.exchange import exchange
from lib.settings import OKCOIN_API_URL
import logging
from exchange_api.okex_rest.OkcoinSpotAPI import OKCoinSpot


class PrivateOkCoinCNY(Market):
    def __init__(self,OKCOIN_API_KEY = None, OKCOIN_SECRET_TOKEN = None):
        super().__init__()
        if OKCOIN_API_KEY == None:
            OKCOIN_API_KEY = config.OKCOIN_API_KEY
            OKCOIN_SECRET_TOKEN = config.OKCOIN_SECRET_TOKEN
        # self.market = exchange(OKCOIN_API_URL, OKCOIN_API_KEY, OKCOIN_SECRET_TOKEN, 'okcoin')
        self.okcoinSpot = OKCoinSpot(OKCOIN_REST_URL, OKCOIN_API_KEY, OKCOIN_SECRET_TOKEN)
        self.currency = "CNY"
        self.get_info()

    def _buy(self, amount, price):
        """Create a buy limit order"""
        # response = self.market.buy(amount, price)
        symbol = "btc_usdt"
        # okcoinSpot.trade('ltc_usd','buy','0.1','0.2')
        # trade(self, symbol, tradeType, price='', amount='')
        response = self.okcoinSpot.trade(symbol,'buy', price, amount)
        if response and response["data"]["result"] == False:
            logging.warn(response)
            return False
        if not response:
            return response

        return response["data"]['order_id']

    def _sell(self, amount, price):
        """Create a sell limit order"""
        # response = self.market.sell(amount, price)
        symbol = "btc_usdt"
        # okcoinSpot.trade('ltc_usd','buy','0.1','0.2')
        # trade(self, symbol, tradeType, price='', amount='')
        response = self.okcoinSpot.trade(symbol, 'sell', price, amount)
        if response and response["data"]["result"] == False:
            logging.warn(response)
            return False
        if not response:
            return response

        return response["data"]['order_id']

    def _get_order(self, order_id):
        # response = self.market.orderInfo(order_id)
        symbol = "btc_usdt"
        response = self.okcoinSpot.orderinfo(symbol, order_id)
        if not response:
            return response

        if response["data"]["result"] == False:
            logging.warn (response)
            return False

        order = response['data']["orders"][0]
        resp = {}
        resp['order_id'] = order['order_id']
        resp['amount'] = order['amount']
        resp['price'] = order['price']
        resp['deal_size'] = order['deal_amount']
        resp['avg_price'] = order['avg_price']

        # -1:已撤销  0:未成交  1:部分成交  2:完全成交 4:撤单处理中,5:撤单处理中
        status = order['status']
        if status == -1:
            resp['status'] = 'CANCELED'
        elif status == 2:
            resp['status'] = 'CLOSE'
        else:
            resp['status'] = 'OPEN'
        return resp

    def _cancel_order(self, order_id):
        # response = self.market.cancel(order_id)
        symbol = "btc_usdt"
        response = self.okcoinSpot.cancelOrder(symbol, '18243073')
        if not response:
            return response

        if not response["data"]["result"]:
            logging.warn(response)
            return False
            
        if response["data"]['result']:
            return True
        else:
            return False

    def get_info(self):
        """Get balance"""
        # response = self.market.accountInfo()
        response = json.loads(self.okcoinSpot.userinfo())
        if response:
            if response["result"] == True:
                self.btc_balance = float(response['info']['funds']['free']['btc'])
                self.cny_balance = float(response['info']['funds']['free']['usdt'])
                self.btc_frozen =  float(response['info']['funds']['freezed']['btc'])
                self.cny_frozen =  float(response['info']['funds']['freezed']['usdt'])
            else:
                logging.warn(response)
                return False
        # tmp
        self.btc_balance = 100000000
        self.cny_balance = 100000000
        return response

if __name__ == '__main__':
    symbol = "btcusdt"
    period = "1min"
    depth_type = "step0"
    amount = 0.001
    source = "api"  # margin-api
    _type = "buy-limit"  # buy-market：市价买, sell-market：市价卖, buy-limit：限价买, sell-limit：限价卖
    _price = 0.01  # unit: USDT


    print (u' 现货历史交易信息 ')
    print (okcoinSpot.trades())

    print (u' 用户现货账户信息 ')
    print (okcoinSpot.userinfo())

    print (u' 现货下单 ')
    print (okcoinSpot.trade('ltc_usd','buy','0.1','0.2'))
