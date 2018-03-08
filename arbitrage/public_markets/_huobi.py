# Copyright (C) 2017, JackYao <yaozihao@yaozihao.cn>

import urllib.request
import urllib.error
import urllib.parse
import requests
import json
from .market import Market
from exchange_api.huobi_rest import HuobiServices

# API 请求地址
MARKET_URL = "https://api.huobi.pro"
TRADE_URL = "https://api.huobi.pro"


class Huobi(Market):
    def __init__(self, currency, code):
        super().__init__(currency)
        self.code = code
        self.update_rate = 1
        self.event = 'depth_huobi'
        self.start_websocket_depth()

    def update_depth_old(self):
        url = 'http://api.huobi.com/staticmarket/depth_%s_50.js' % self.code
        req = urllib.request.Request(url, headers={
            "Content-Type": "application/x-www-form-urlencoded",
            "Accept": "*/*",
            "User-Agent": "curl/7.24.0 (x86_64-apple-darwin12.0)"})
        res = urllib.request.urlopen(req)
        depth = json.loads(res.read().decode('utf8'))
        self.depth = self.format_depth(depth)

    # 获取marketdepth
    def update_depth(self):
        """
        :param symbol
        :param type: 可选值：{ percent10, step0, step1, step2, step3, step4, step5 }
        :return:
        """
        symbol = self.code
        depth_type = "step0"
        response = HuobiServices.get_depth(symbol, depth_type)
        self.depth = self.format_depth(response["tick"])

