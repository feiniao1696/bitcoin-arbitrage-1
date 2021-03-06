# -*- coding: utf-8 -*-
#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Date    : 2017-12-20 15:40:03
# @Author  : KlausQiu
# @QQ      : 375235513
# @github  : https://github.com/KlausQIU
import sys
from exchange_api.huobi_rest.Utils import *

'''
Market data API
'''


# 获取KLine
def get_kline(symbol, period, size=150):
    """
    :param symbol
    :param period: 可选值：{1min, 5min, 15min, 30min, 60min, 1day, 1mon, 1week, 1year }
    :param size: 可选值： [1,2000]
    :return:
    """
    params = {'symbol': symbol,
              'period': period,
              'size': size}

    url = MARKET_URL + '/market/history/kline'
    return http_get_request(url, params)


# 获取marketdepth
def get_depth(symbol, type):
    """
    :param symbol
    :param type: 可选值：{ percent10, step0, step1, step2, step3, step4, step5 }
    :return:
    """
    params = {'symbol': symbol,
              'type': type}
    
    url = MARKET_URL + '/market/depth'
    return http_get_request(url, params)


# 获取tradedetail
def get_trade(symbol):
    """
    :param symbol
    :return:
    """
    params = {'symbol': symbol}

    url = MARKET_URL + '/market/trade'
    return http_get_request(url, params)


# 获取merge ticker
def get_ticker(symbol):
    """
    :param symbol: 
    :return:
    """
    params = {'symbol': symbol}

    url = MARKET_URL + '/market/detail/merged'
    return http_get_request(url, params)


# 获取 Market Detail 24小时成交量数据
def get_detail(symbol):
    """
    :param symbol
    :return:
    """
    params = {'symbol': symbol}

    url = MARKET_URL + '/market/detail'
    return http_get_request(url, params)

# 获取  支持的交易对
def get_symbols(long_polling=None):
    """

    """
    params = {}
    if long_polling:
        params['long-polling'] = long_polling
    path = '/v1/common/symbols'
    return api_key_get(params, path)

'''
Trade/Account API
'''


def get_accounts():
    """
    :return: 
    """
    path = "/v1/account/accounts"
    params = {}
    return api_key_get(params, path)


# 获取当前账户资产
def get_balance(acct_id=None):
    """
    :param acct_id
    :return:
    """

    if not acct_id:
        accounts = get_accounts()
        acct_id = accounts['data'][0]['id'];

    url = "/v1/account/accounts/{0}/balance".format(acct_id)
    params = {"account-id": acct_id}
    return api_key_get(params, url)


# 下单

# 创建并执行订单
def send_order(amount, source, symbol, _type, price=0):
    """
    :param amount: 
    :param source: 如果使用借贷资产交易，请在下单接口,请求参数source中填写'margin-api'
    :param symbol: 
    :param _type: 可选值 {buy-market：市价买, sell-market：市价卖, buy-limit：限价买, sell-limit：限价卖}
    :param price: 
    :return: 
    """
    try:
        accounts = get_accounts()
        acct_id = accounts['data'][0]['id']
    except BaseException as e:
        print ('get acct_id error.%s' % e)
        acct_id = ACCOUNT_ID

    params = {"account-id": acct_id,
              "amount": amount,
              "symbol": symbol,
              "type": _type,
              "source": source}
    if price:
        params["price"] = price

    url = '/v1/order/orders/place'
    return api_key_post(params, url)


# 撤销订单
def cancel_order(order_id):
    """
    
    :param order_id: 
    :return: 
    """
    params = {}
    url = "/v1/order/orders/{0}/submitcancel".format(order_id)
    return api_key_post(params, url)


# 查询某个订单
def order_info(order_id):
    """
    
    :param order_id: 
    :return: 
    """
    params = {}
    url = "/v1/order/orders/{0}".format(order_id)
    return api_key_get(params, url)


# 查询某个订单的成交明细
def order_matchresults(order_id):
    """
    
    :param order_id: 
    :return: 
    """
    params = {}
    url = "/v1/order/orders/{0}/matchresults".format(order_id)
    return api_key_get(params, url)


# 查询当前委托、历史委托
def orders_list(symbol, states, types=None, start_date=None, end_date=None, _from=None, direct=None, size=None):
    """
    
    :param symbol: 
    :param states: 可选值 {pre-submitted 准备提交, submitted 已提交, partial-filled 部分成交, partial-canceled 部分成交撤销, filled 完全成交, canceled 已撤销}
    :param types: 可选值 {buy-market：市价买, sell-market：市价卖, buy-limit：限价买, sell-limit：限价卖}
    :param start_date: 
    :param end_date: 
    :param _from: 
    :param direct: 可选值{prev 向前，next 向后}
    :param size: 
    :return: 
    """
    params = {'symbol': symbol,
              'states': states}

    if types:
        params[types] = types
    if start_date:
        params['start-date'] = start_date
    if end_date:
        params['end-date'] = end_date
    if _from:
        params['from'] = _from
    if direct:
        params['direct'] = direct
    if size:
        params['size'] = size
    url = '/v1/order/orders'
    return api_key_get(params, url)


# 查询当前成交、历史成交
def orders_matchresults(symbol, types=None, start_date=None, end_date=None, _from=None, direct=None, size=None):
    """
    
    :param symbol: 
    :param types: 可选值 {buy-market：市价买, sell-market：市价卖, buy-limit：限价买, sell-limit：限价卖}
    :param start_date: 
    :param end_date: 
    :param _from: 
    :param direct: 可选值{prev 向前，next 向后}
    :param size: 
    :return: 
    """
    params = {'symbol': symbol}

    if types:
        params[types] = types
    if start_date:
        params['start-date'] = start_date
    if end_date:
        params['end-date'] = end_date
    if _from:
        params['from'] = _from
    if direct:
        params['direct'] = direct
    if size:
        params['size'] = size
    url = '/v1/order/matchresults'
    return api_key_get(params, url)



# 申请提现虚拟币
def withdraw(address, amount, currency, fee=0, addr_tag=""):
    """

    :param address_id: 
    :param amount: 
    :param currency:btc, ltc, bcc, eth, etc ...(火币Pro支持的币种)
    :param fee: 
    :param addr-tag:
    :return: {
              "status": "ok",
              "data": 700
            }
    """
    params = {'address': address,
              'amount': amount,
              "currency": currency,
              "fee": fee,
              "addr-tag": addr_tag}
    url = '/v1/dw/withdraw/api/create'

    return api_key_post(params, url)

# 申请取消提现虚拟币
def cancel_withdraw(address_id):
    """

    :param address_id: 
    :return: {
              "status": "ok",
              "data": 700
            }
    """
    params = {}
    url = '/v1/dw/withdraw-virtual/{0}/cancel'.format(address_id)

    return api_key_post(params, url)


'''
借贷API
'''

# 创建并执行借贷订单


def send_margin_order(amount, source, symbol, _type, price=0):
    """
    :param amount: 
    :param source: 'margin-api'
    :param symbol: 
    :param _type: 可选值 {buy-market：市价买, sell-market：市价卖, buy-limit：限价买, sell-limit：限价卖}
    :param price: 
    :return: 
    """
    try:
        accounts = get_accounts()
        acct_id = accounts['data'][0]['id']
    except BaseException as e:
        print ('get acct_id error.%s' % e)
        acct_id = ACCOUNT_ID

    params = {"account-id": acct_id,
              "amount": amount,
              "symbol": symbol,
              "type": _type,
              "source": 'margin-api'}
    if price:
        params["price"] = price

    url = '/v1/order/orders/place'
    return api_key_post(params, url)

# 现货账户划入至借贷账户


def exchange_to_margin(symbol, currency, amount):
    """
    :param amount: 
    :param currency: 
    :param symbol: 
    :return: 
    """
    params = {"symbol": symbol,
              "currency": currency,
              "amount": amount}

    url = "/v1/dw/transfer-in/margin"
    return api_key_post(params, url)

# 借贷账户划出至现货账户


def margin_to_exchange(symbol, currency, amount):
    """
    :param amount: 
    :param currency: 
    :param symbol: 
    :return: 
    """
    params = {"symbol": symbol,
              "currency": currency,
              "amount": amount}

    url = "/v1/dw/transfer-out/margin"
    return api_key_post(params, url)

# 申请借贷
def get_margin(symbol, currency, amount):
    """
    :param amount: 
    :param currency: 
    :param symbol: 
    :return: 
    """
    params = {"symbol": symbol,
              "currency": currency,
              "amount": amount}
    url = "/v1/margin/orders"
    return api_key_post(params, url)

# 归还借贷
def repay_margin(order_id, amount):
    """
    :param order_id: 
    :param amount: 
    :return: 
    """
    params = {"order-id": order_id,
              "amount": amount}
    url = "/v1/margin/orders/{0}/repay".format(order_id)
    return api_key_post(params, url)

# 借贷订单
def loan_orders(symbol, currency, start_date="", end_date="", start="", direct="", size=""):
    """
    :param symbol: 
    :param currency: 
    :param direct: prev 向前，next 向后
    :return: 
    """
    params = {"symbol": symbol,
              "currency": currency}
    if start_date:
        params["start-date"] = start_date
    if end_date:
        params["end-date"] = end_date
    if start:
        params["from"] = start
    if direct and direct in ["prev", "next"]:
        params["direct"] = direct
    if size:
        params["size"] = size
    url = "/v1/margin/loan-orders"
    return api_key_get(params, url)


# 借贷账户详情,支持查询单个币种
def margin_balance(symbol):
    """
    :param symbol: 
    :return: 
    """
    params = {}
    url = "/v1/margin/accounts/balance"
    if symbol:
        params['symbol'] = symbol
    
    return api_key_get(params, url)


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

    sys.exit(0)
    amount = 0.001
    source = "api"  # margin-api
    _type = "buy-limit"   # buy-market：市价买, sell-market：市价卖, buy-limit：限价买, sell-limit：限价卖
    _price = 0.01  # unit: USDT
    order = send_order(amount, source, symbol, _type, price=_price)
    # {'data': '2008245436', 'status': 'ok'}
    order_id = order["data"]
    cancel_order(order_id)
    order_info(order_id)
    order_matchresults(order_id)
    _start_date = "2018-03-03"
    _end_date = "2018-03-03"
    _direct = "prev"
    _states = "submitted,submitted,partial-filled,partial-canceled,filled,canceled"
    # pre-submitted 准备提交, submitted 已提交, partial-filled 部分成交, partial-canceled 部分成交撤销, filled 完全成交, canceled 已撤销
    # types ： buy - market：市价买, sell - market：市价卖, buy - limit：限价买, sell - limit：限价卖
    # direct prev 向前，next 向后
    orders_list(symbol, states=_states, types=None, start_date=_start_date, end_date=_end_date, _from=None, direct=_direct, size=None)
    orders_matchresults(symbol, types=None, start_date=None, end_date=None, _from=None, direct=None, size=None)

'''
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

order_list:
{'data': [{'account-id': 2103374,
   'amount': '0.334700000000000000',
   'canceled-at': 0,
   'created-at': 1520044131719,
   'field-amount': '0.334700000000000000',
   'field-cash-amount': '3765.371653000000000000',
   'field-fees': '0.000669400000000000',
   'finished-at': 1520044159750,
   'id': 1984348586,
   'price': '11249.990000000000000000',
   'source': 'spot-app',
   'state': 'filled',
   'symbol': 'btcusdt',
   'type': 'buy-limit'},
 {'account-id': 2103374,
   'amount': '0.100000000000000000',
   'canceled-at': 1520088402088,
   'created-at': 1520088267123,
   'field-amount': '0.019500000000000000',
   'field-cash-amount': '222.787110000000000000',
   'field-fees': '0.445574220000000000',
   'finished-at': 1520088402290,
   'id': 1997914380,
   'price': '11424.980000000000000000',
   'source': 'spot-app',
   'state': 'partial-canceled',
   'symbol': 'btcusdt',
   'type': 'sell-limit'},
  {'account-id': 2103374,
   'amount': '0.100000000000000000',
   'canceled-at': 1520089674510,
   'created-at': 1520089654616,
   'field-amount': '0.0',
   'field-cash-amount': '0.0',
   'field-fees': '0.0',
   'finished-at': 1520089674590,
   'id': 1998331682,
   'price': '11439.980000000000000000',
   'source': 'spot-app',
   'state': 'canceled',
   'symbol': 'btcusdt',
   'type': 'sell-limit'},

  {'account-id': 2673234,
   'amount': '0.037500000000000000',
   'canceled-at': 0,
   'created-at': 1520089979255,
   'field-amount': '0.037500000000000000',
   'field-cash-amount': '428.629875000000000000',
   'field-fees': '0.000075000000000000',
   'finished-at': 1520089979812,
   'id': 1998429535,
   'price': '11430.130000000000000000',
   'source': 'margin-app',
   'state': 'filled',
   'symbol': 'btcusdt',
   'type': 'buy-limit'},
  {'account-id': 2673234,
   'amount': '0.010000000000000000',
   'canceled-at': 0,
   'created-at': 1520090219408,
   'field-amount': '0.010000000000000000',
   'field-cash-amount': '114.476800000000000000',
   'field-fees': '0.228953600000000000',
   'finished-at': 1520090224352,
   'id': 1998499004,
   'price': '11447.680000000000000000',
   'source': 'margin-app',
   'state': 'filled',
   'symbol': 'btcusdt',
   'type': 'sell-limit'}],
 'status': 'ok'}




cancel_order(order_id)
Out[38]: {'data': '2008245436', 'status': 'ok'}


'''
