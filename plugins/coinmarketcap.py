import requests
import matplotlib as mpl
mpl.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.dates as md
import datetime as dt
import time
import re
import json
import os

class CoinMarketCap:

    def __init__(self, cnvert="JPY"):
        self.convert = cnvert

    __ticker = None

    def __get_ticker(self, limit=5000, force_update=False):
        if self.__ticker is None:
            self.stack_ticker(limit, force_update)
        return self.__ticker

    def stack_ticker(self, limit=5000, force_update=False):

        cmc_cache = "cmc.json"
        if os.path.exists(cmc_cache) and force_update == False:
            print("load cache")
            f = open(cmc_cache, "r")
            self.__ticker = json.load(f)
            f.close()
            #print(self.__ticker)
        else:
            print("update cache")
            self.__ticker = requests.get("https://api.coinmarketcap.com/v1/ticker/?limit={l}&convert={c}".format(l=limit, c=self.convert)).json()
            f = open(cmc_cache, "w")
            json.dump(self.__ticker, f)
            f.close()

    def ticker(self, id="bitcoin", symbol="BTC"):
        for coin in self.__get_ticker():
            if coin["id"].upper() == id.upper():
                return coin
                
            elif coin["symbol"].upper() == symbol.upper():
                return coin
        return False

    def price(self, id="bitcoin", symbol="BTC"):
        coin = self.ticker(id=id, symbol=symbol)
        btc = self.ticker(id="bitcoin")
        if coin:
            return float(coin["price_jpy"]), float(coin["price_jpy"])/float(btc["price_jpy"])
        else:
            return False, False

    def chart_by_symbol(self, symbol="BTC", out_fname="chart.png"):
        for coin in self.__get_ticker():
            if coin["symbol"].upper() == symbol.upper():
                self.chart(coin["id"], out_fname)
                return True
        return False


    def chart(self, id="bitcoin", out_fname="chart.png"):
        print("chart : " + id)
        try:
            data = requests.get("https://graphs2.coinmarketcap.com/currencies/{}/".format(id)).json()
        except Exception:
            print("json error")
            return False

        if not "price_usd" in data:
            return False

        price_usd = data["price_usd"]
        x_1 = []
        y_1 = []
        for p_b in price_usd:
            unix = float(p_b[0])/1000.
            d = dt.datetime.fromtimestamp(unix)
            x_1.append(d)
            y_1.append(p_b[1])


        price_btc = data["price_btc"]
        x_2 = []
        y_2 = []
        for p_b in price_btc:
            unix = float(p_b[0])/1000.
            d = dt.datetime.fromtimestamp(unix)
            x_2.append(d)
            y_2.append(p_b[1])

        plt.figure()
        fig, ax1 = plt.subplots()
        ln1 = ax1.plot(x_1, y_1, label="usd", color="#729ECE")
        ax2 = ax1.twinx()
        ln2 = ax2.plot(x_2, y_2, label="btc", color="#FF9E4A")
        lns = ln1+ln2
        labs = [l.get_label() for l in lns]
        ax1.legend(lns, labs, loc=0)
        plt.title("{} chart".format(id))
        plt.ylabel(id)
        plt.tight_layout()
        ax=plt.gca()
        xfmt = md.DateFormatter("%Y-%m-%d")
        ax.xaxis.set_major_formatter(xfmt)

        plt.savefig(out_fname, bbox_inches="tight")

        return True

    def search_symbol(self, target_symbol=""):
        if target_symbol == "":
            return []

        ret = []

        for coin in self.__get_ticker():
            match = re.match(target_symbol , coin["symbol"], re.IGNORECASE)
            if match:
                ret.append(coin["symbol"] + " : " + coin["id"])
        return ret
        


    def search_id(self, target_id=""):
        if target_id == "":
            return []

        ret = []

        for coin in self.__get_ticker():
            match = re.match(target_id , coin["id"], re.IGNORECASE)
            if match:
                ret.append(coin["id"] + " : " + coin["symbol"])
        return ret
        
        