import urllib.request
import urllib.error
import urllib.parse
import json
from .market import Market
import http.client
import urllib
import json
import hashlib
import time


class OKCoin(Market):
    def __init__(self, currency, code):
        super().__init__(currency)
        self.code = code
        self.update_rate = 1
        self.event = 'depth_okcoin'
        self.start_websocket_depth()

    def update_depth_old(self):
        url = 'https://www.okcoin.cn/api/depth.do?size=10&symbol=' + self.code
        req = urllib.request.Request(url, headers={
            "Content-Type": "application/x-www-form-urlencoded",
            "Accept": "*/*",
            "User-Agent": "curl/7.24.0 (x86_64-apple-darwin12.0)"})
        res = urllib.request.urlopen(req)
        depth = json.loads(res.read().decode('utf8'))
        self.depth = self.format_depth(depth)

    def update_depth(self):
        url = 'https://www.okex.com/api/v1/depth.do?symbol=' + self.code
        req = urllib.request.Request(url, headers={
            "Content-Type": "application/x-www-form-urlencoded",
            "Accept": "*/*",
            "User-Agent": "curl/7.24.0 (x86_64-apple-darwin12.0)"})
        res = urllib.request.urlopen(req)
        depth = json.loads(res.read().decode('utf8'))
        self.depth = self.format_depth(depth)

    #获取OKCOIN现货市场深度信息
    def depth(self,symbol = ''):
        DEPTH_RESOURCE = "/api/v1/depth.do"
        params=''
        if symbol:
            params = 'symbol=%(symbol)s' %{'symbol':symbol}
        return httpGet(self.__url,DEPTH_RESOURCE,params)

    def httpGet(url,resource,params=''):
        conn = http.client.HTTPSConnection(url, timeout=10)
        conn.request("GET",resource + '?' + params)
        response = conn.getresponse()
        data = response.read().decode('utf-8')
        return json.loads(data)