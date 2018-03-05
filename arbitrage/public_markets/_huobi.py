# Copyright (C) 2017, JackYao <yaozihao@yaozihao.cn>

import urllib.request
import urllib.error
import urllib.parse
import requests
import json
from .market import Market

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
        _type = "step0"
        params = {'symbol': self.code,
                  'type': _type}

        url = MARKET_URL + '/market/depth'
        res = self.http_get_request(url, params)
        depth = res["tick"]
        self.depth = self.format_depth(depth)

    def http_get_request(self, url, params, add_to_headers=None):
        headers = {
            "Content-type": "application/x-www-form-urlencoded",
            'User-Agent': 'Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/39.0.2171.71 Safari/537.36',
        }
        if add_to_headers:
            headers.update(add_to_headers)
        postdata = urllib.parse.urlencode(params)
        response = requests.get(url, postdata, headers=headers, timeout=5)
        try:

            if response.status_code == 200:
                return response.json()
            else:
                return
        except BaseException as e:
            print("httpGet failed, detail is:%s,%s" % (response.text, e))
            return