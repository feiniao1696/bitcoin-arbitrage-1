#-*- coding:utf-8 -*-s = u’示例’
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
from lib.exchange import exchange
from lib.settings import HUOBI_API_URL
import sys
import traceback
import config
import logging
from exchange_api.huobi_rest import HuobiServices


class PrivateHuobiCNY(Market):
    def __init__(self,HUOBI_API_KEY=None, HUOBI_SECRET_TOKEN=None):
        super().__init__()
        if HUOBI_API_KEY == None:
            HUOBI_API_KEY = config.HUOBI_API_KEY
            HUOBI_SECRET_TOKEN = config.HUOBI_SECRET_TOKEN
        # self.market = exchange(HUOBI_API_URL, HUOBI_API_KEY, HUOBI_SECRET_TOKEN, 'huobi')
        self.currency = "CNY"
        self.get_info()

    def _buy(self, amount, price):
        """Create a buy limit order"""
        symbol = "btcusdt"
        # amount = 0.001
        source = "api"  # margin-api
        _type = "buy-limit"  # buy-market：市价买, sell-market：市价卖, buy-limit：限价买, sell-limit：限价卖
        # _price = 0.01  # unit: USDT
        amount = 0.000001
        price = 0.000001
        response = HuobiServices.send_order(amount, source, symbol, _type, price=price)
        # {'data': '2008245436', 'status': 'ok'}
        # order_id = order["data"]
        # cancel_order(order_id)

        if response["status"] == "ok":
            logging.info("send_order OK: buy_limit: %s @ %s, order id: %s ok" % (amount, price, response["data"]))
        else:
            logging.warn("send_order Failed: buy_limit: %s @ %s, order id: %s" % (amount, price, response["data"]), response)
            return False

        # response = self.market.buy(amount, price)
        # if response and "code" in response:
        #     logging.warn("buy ex:%s", response)
        #     return False

        if not response:
            return response

        # return response['id']
        return response['order']

    def _sell(self, amount, price):
        """Create a sell limit order"""
        symbol = "btcusdt"
        # amount = 0.001
        source = "api"  # margin-api
        _type = "sell-limit"  # buy-market：市价买, sell-market：市价卖, buy-limit：限价买, sell-limit：限价卖
        # _price = 0.01  # unit: USDT
        amount = 0.0000001
        price = 10000000000
        response = HuobiServices.send_order(amount, source, symbol, _type, price=price)
        # {'data': '2008245436', 'status': 'ok'}
        # order_id = order["data"]
        # cancel_order(order_id)

        if not response:
            return response

        if response["status"] == "ok":
            logging.info("send_order OK: sell_limit: %s @ %s, order id: %s ok" % (amount, price, response["data"]))
        else:
            logging.warn("send_order Failed: sell_limit: %s @ %s, order id: %s" % (amount, price, response["data"]), response)
            return False

        # return response['id']
        return response['order']

    def _cancel_order(self, order_id):
        # response = self.market.cancel(order_id)
        response = HuobiServices.cancel_order(order_id)
        if not response:
            return response
        if response["status"] == "ok":
            logging.info("cancel_order OK: %s " % (order_id))
        else:
            logging.warn('%s', str(response))
            return False

        if "code" in response:
            logging.warn ('%s', str(response))
            return False
        if response['result'] == 'success':
            return True
        return False

    def _get_order(self, order_id):
        # response = self.market.orderInfo(order_id)
        response = HuobiServices.order_info(order_id)
        if not response:
            return response

        if not response["status"] == "ok":
            logging.warn(response)
            return False

        resp = {}
        resp['order_id'] = response['id']
        resp['amount'] = float(response['data']['amount'])
        resp['price'] = float(response['data']['price'])
        # to do
        resp['deal_size'] = float(response['data']['field-amount'])
        resp['avg_price'] = float(response['data']['field-cash-amount'])
        status = response['data']['state']  # submitted filled partial-canceled canceled

        if status == "canceled":
            resp['status'] = 'CANCELED'
        elif status == "filled":
            resp['status'] = 'CLOSE'
        else:
            resp['status'] = 'OPEN'

        return resp

    def get_info(self):
        """Get balance"""
        self.btc_balance = 100000000
        self.cny_balance = 100000000

        response_empty_flag = True
        while response_empty_flag :
            try:
                # response = self.market.accountInfo()
                response = HuobiServices.get_balance()
                if response:
                    if response["status"] == "ok":
                        self.btc_balance = float([val["balance"] for val in response["data"]["list"] if (val["currency"] == "btc") and (val["type"] == "trade")][0])
                        self.cny_balance = float([val["balance"] for val in response["data"]["list"] if (val["currency"] == "usdt") and (val["type"] == "trade")][0])
                        self.btc_frozen = float([val["balance"] for val in response["data"]["list"] if (val["currency"] == "btc") and (val["type"] == "frozen")][0])
                        self.cny_frozen = float([val["balance"] for val in response["data"]["list"] if (val["currency"] == "usdt") and (val["type"] == "frozen")][0])
                        response_empty_flag = False
                    else:
                        logging.warn(response)
                        return False
                        raise TradeException(response["message"])
            except Exception as ex:
                logging.warn("get_info failed :%s" % ex)
                traceback.print_exc()
                return False


if __name__ == '__main__':
    symbol = "btcusdt"
    period = "1min"
    depth_type = "step0"
    print(get_symbols())
    print(get_kline(symbol, period, size=150))
    print(get_depth(symbol, depth_type))
    print(get_trade(symbol))
    print(get_ticker(symbol))
    print(get_detail(symbol))
    print(get_symbols(long_polling=None))
    print(get_accounts())
    print(get_balance(acct_id=None))

    amount = 0.001
    source = "api"  # margin-api
    _type = "buy-limit"   # buy-market：市价买, sell-market：市价卖, buy-limit：限价买, sell-limit：限价卖
    _price = 0.01  # unit: USDT
    order = send_order(amount, source, symbol, _type, price=_price)
    # {'data': '2008245436', 'status': 'ok'}
    order_id = order["data"]

'''
response["data"].keys()
Out[7]: dict_keys(['id', 'type', 'state', 'list'])
response["data"]["list"]
{'balance': '0.279342388400000000', 'currency': 'btc', 'type': 'trade'},
{'balance': '0.000000000000000000', 'currency': 'btc', 'type': 'frozen'},   

  order_info:
  {'data': {'account-id': 2103374,
  'amount': '0.001000000000000000',
  'canceled-at': 0,
  'created-at': 1520122184216,
  'field-amount': '0.0',
  'field-cash-amount': '0.0',
  'field-fees': '0.0',
  'finished-at': 0,
  'id': 2008245436,
  'price': '0.010000000000000000',
  'source': 'api',
  'state': 'submitted',
  'symbol': 'btcusdt',
  'type': 'buy-limit'},
 'status': 'ok'}
'''