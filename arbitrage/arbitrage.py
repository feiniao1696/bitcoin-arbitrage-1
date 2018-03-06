# Copyright (C) 2017, Jack Yao <yaozihao@yaozihao.cn>

import logging
import argparse
import sys
import public_markets
import glob
import os
import inspect
from arbitrer import Arbitrer
from logging.handlers import RotatingFileHandler
import lib.broker_api as exchange_api
from observers.emailer import send_email
import datetime
import time
import config
import traceback

class ArbitrerCLI:
    def __init__(self):
        self.inject_verbose_info()

    def inject_verbose_info(self):
        logging.VERBOSE = 15
        logging.verbose = lambda x: logging.log(logging.VERBOSE, x)
        logging.addLevelName(logging.VERBOSE, "VERBOSE")

    def main(self):
        parser = argparse.ArgumentParser()
        parser.add_argument("-d", "--debug", help="debug verbose mode",
                            action="store_true")
        parser.add_argument("-v", "--verbose", help="info verbose mode",
                            action="store_true")
        parser.add_argument("-o", "--observers", type=str,
                            help="observers, example: -oLogger,Emailer")
        parser.add_argument("-m", "--markets", type=str,
                            help="markets, example: -mHaobtcCNY,Bitstamp")
        parser.add_argument("-s", "--status", help="status", action="store_true")
        parser.add_argument("command", nargs='*', default="watch",
                            help='verb: "watch|replay-history|get-balance|list-public-markets|get-broker-balance"')
        args = parser.parse_args()
        self.init_logger(args)
        self.exec_command(args)

    def init_logger(self, args):
        level = logging.INFO
        if args.verbose:
            level = logging.VERBOSE
        if args.debug:
            level = logging.DEBUG
        logging.basicConfig(format='%(asctime)s [%(levelname)s] %(message)s',
                            level=level)

        Rthandler = RotatingFileHandler('arbitrage.log', maxBytes=100*1024*1024,backupCount=10)
        Rthandler.setLevel(level)
        formatter = logging.Formatter('%(asctime)-12s [%(levelname)s] %(message)s')
        Rthandler.setFormatter(formatter)
        logging.getLogger('').addHandler(Rthandler)

        logging.getLogger("requests").setLevel(logging.WARNING)
        logging.getLogger("urllib3").setLevel(logging.WARNING)

    def exec_command(self, args):
        logging.debug('exec_command:%s' % args)
        if "watch" in args.command:
            self.create_arbitrer(args)
            self.arbitrer.loop()
        if "replay-history" in args.command:
            self.create_arbitrer(args)
            self.arbitrer.replay_history(args.replay_history)
        if "list-public-markets" in args.command:
            self.list_markets()
        if "get-balance" in args.command:
            self.get_balance(args)
        if "get-broker-balance" in args.command:
            self.get_broker_balance(args)

    def create_arbitrer(self, args):
        self.arbitrer = Arbitrer()
        if args.observers:
            self.arbitrer.init_observers(args.observers.split(","))
        if args.markets:
            self.arbitrer.init_markets(args.markets.split(","))

    def list_markets(self):
        logging.debug('list_markets')
        for filename in glob.glob(os.path.join(public_markets.__path__[0], "*.py")):
            module_name = os.path.basename(filename).replace('.py', '')
            if not module_name.startswith('_'):
                module = __import__("public_markets." + module_name)
                test = eval('module.' + module_name)
                for name, obj in inspect.getmembers(test):
                    if inspect.isclass(obj) and 'Market' in (j.__name__ for j in obj.mro()[1:]):
                        if not obj.__module__.split('.')[-1].startswith('_'):
                            print(obj.__name__)
        sys.exit(0)

    def get_balance(self, args):
        if not args.markets:
            logging.error("You must use --markets argument to specify markets")
            sys.exit(2)
        pmarkets = args.markets.split(",")
        pmarketsi = []
        for pmarket in pmarkets:
            exec('import private_markets.' + pmarket.lower())
            market = eval('private_markets.' + pmarket.lower()
                          + '.Private' + pmarket + '()')
            pmarketsi.append(market)
        for market in pmarketsi:
            print(market)

    def get_broker_balance(self, args):
        last_email_time = 0
        cny_init = config.cny_init
        btc_init = config.btc_init
        price_init = config.price_init

        exchange_api.init_broker()
        while True:
            try:
                accounts = exchange_api.exchange_get_account()
                ticker = exchange_api.exchange_get_ticker()
            except Exception as e:
                traceback.print_exc()
                exchange_api.init_broker()
                time.sleep(3)
                continue

            if accounts:
                cny_balance = 0
                btc_balance = 0
                cny_frozen = 0
                btc_frozen = 0

                broker_msg = '\n----------------------------Hedge Fund statistics------------------------------\n'
                broker_msg += 'datetime\t %s\n\n' % str(datetime.datetime.now())
                for account in accounts:
                    cny_balance += account.available_cny
                    btc_balance += account.available_btc
                    cny_frozen += account.frozen_cny
                    btc_frozen += account.frozen_btc

                    broker_msg += "%s:\t\t %s\n" % (account.exchange, str({"cny_balance": account.available_cny,
                                                                           "btc_balance": account.available_btc,
                                                                           "cny_frozen": account.frozen_cny,
                                                                           "btc_frozen": account.frozen_btc}))
                broker_msg += '------------------------------------------------------------------------------------\n'
                broker_msg += "%s:\t\t %s\n" % ('Asset0', str({"cny": '%.2f' % cny_init,
                                                               "btc": '%.2f' % btc_init, "price": '%.2f' % price_init}))

                broker_msg += "%s:\t\t %s\n" % ('AssetN', str({"cny": '%.2f' % (cny_balance + cny_frozen),
                                                               "btc": '%.2f' % (btc_balance + btc_frozen),
                                                               "price": '%.2f' % ticker.bid}))

                cny_total = (btc_balance + btc_frozen) * ticker.bid + cny_balance + cny_frozen
                btc_total = btc_balance + btc_frozen + (cny_balance + cny_frozen) / ticker.bid
                cny_diff = cny_balance + cny_frozen - cny_init
                btc_diff = btc_balance + btc_frozen - btc_init

                btc_bonus = 0
                btc_bonus = cny_diff / ticker.bid
                cny_bonus = 0
                cny_bonus = btc_diff * ticker.bid

                broker_msg += "%s: %s\n" % ('AssetN CNY Base', str({"cny": '%.2f' % cny_init,
                                                                    "btc": '%.2f' % (
                                                                    btc_balance + btc_frozen + btc_bonus)}))

                broker_msg += "%s: %s\n" % (
                'AssetN BTC Base', str({"cny": '%.2f' % (cny_balance + cny_frozen + cny_bonus),
                                        "btc": '%.2f' % btc_init}))

                broker_msg += "%s:\t\t %s\n" % (
                'Profit', str({"profit": '%.2fCNY / %.2fBTC' % (cny_diff + cny_bonus, btc_bonus + btc_diff)}))

                broker_msg += '------------------------------------------------------------------------------------\n'

                broker_msg += "%s: %s\n" % ('Asset0 CNY Conv', str({"cny": '%.2f' % (cny_init + btc_init * price_init),
                                                                    "btc": 0}))
                broker_msg += "%s: %s\n" % ('Asset0 BTC Conv', str({"cny": 0,
                                                                    "btc": '%.2f' % (
                                                                    btc_init + cny_init / price_init)}))

                broker_msg += "%s: %s\n" % ('AssetN CNY Conv', str({"cny": '%.2f' % cny_total,
                                                                    "btc": 0}))
                broker_msg += "%s: %s\n" % ('AssetN BTC Conv', str({"cny": 0,
                                                                    "btc": '%.2f' % btc_total}))
                broker_msg += "%s:\t %s\n" % ('Profit Conv', str({"profit-conv": '%.2fCNY / %.2fBTC' % (
                cny_total - (cny_init + btc_init * price_init), btc_total - (btc_init + cny_init / price_init))}))

                broker_msg += '\n------------------------------------------------------------------------------------\n'

                logging.info(broker_msg)

                if not args.status:
                    send_email('Hedge Fund Statistics', broker_msg)
                    break
                if time.time() - last_email_time > 60 * 10:
                    last_email_time = time.time()
                    send_email('Hedge Fund Statistics', broker_msg)
                time.sleep(20)


def main():
    cli = ArbitrerCLI()
    cli.main()

if __name__ == "__main__":
    main()


'''
2018-03-07 01:00:34,554 [INFO] Buy @OKCoinCNY/10950.00 and sell @HuobiCNY/10951.04 0.04 BTC
2018-03-07 01:00:34,554 [INFO] 0.1 HuobiCNY btc:10.0 < 50.0,cny:5000 < 10.0,  reverse
2018-03-07 01:00:34,554 [WARNING] HuobiCNY cny is insufficent


response = requests.get(url, postdata, headers=headers, timeout=5)
        
  File "/Users/liziheng/anaconda3/lib/python3.6/site-packages/requests/adapters.py", line 496, in send
    raise ConnectTimeout(e, request=request)
requests.exceptions.ConnectTimeout: HTTPSConnectionPool(host='api.huobi.pro', port=443): Max retries exceeded with url: /market/depth?symbol=btcusdt&type=step0 (Caused by ConnectTimeoutError(<urllib3.connection.VerifiedHTTPSConnection object at 0x110f74b38>, 'Connection to api.huobi.pro timed out. (connect timeout=5)'))
    (self.host, self.timeout))
urllib3.exceptions.ConnectTimeoutError: (<urllib3.connection.VerifiedHTTPSConnection object at 0x10e9b74a8>, 'Connection to api.huobi.pro timed out. (connect timeout=5)')

'''