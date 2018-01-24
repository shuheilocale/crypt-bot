import matplotlib as mpl
mpl.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.dates as md
import requests
import pandas as pd
import numpy as np
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
        for coin in self.__get_ticker(force_update=True):
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

        #x_1 # index
        dti = pd.DatetimeIndex(x_1)
        df = pd.DataFrame(np.array(y_1), index=dti, columns=["price_usd"])
        df["price_btc"] = np.array(y_2)
        #print(df)

        df = df.resample('D').mean()

        mean25 = df["price_usd"].rolling(window=25, min_periods=10).mean()
        mean75 = df["price_usd"].rolling(window=75, min_periods=10).mean()

        # とりあえず直近30日
        df = df.ix[ -30: , :]
        date = df.index
        mean25 = mean25.ix[ -30:]
        mean75 = mean75.ix[ -30:]


        plt.figure()
        fig, ax1 = plt.subplots()
        ln1 = ax1.plot(date, df["price_usd"], label="usd", color="#729ECE", linewidth=2.0)
        ln2 = ax1.plot(date, mean25, label="usd-mean25", color="#720E0E", linewidth=0.5)
        ln3 = ax1.plot(date, mean75, label="usd-mean75", color="#000FBF", linewidth=0.5)
        ax2 = ax1.twinx()
        ln4 = ax2.plot(date, df["price_btc"], label="btc", color="#FF9E4A", linewidth=2.0, linestyle="dashed")
        lns = ln1+ln2+ln3+ln4
        labs = [l.get_label() for l in lns]
        ax1.legend(lns, labs, loc=0)
        plt.title("{} chart".format(id))
        plt.ylabel(id)
        plt.tight_layout()
        ax=plt.gca()
        xfmt = md.DateFormatter("%Y-%m-%d-%H-%M")
        ax.xaxis.set_major_formatter(xfmt)
        fig.autofmt_xdate()

        plt.savefig(out_fname, bbox_inches="tight")

        return True

    def search_symbol(self, target_symbol=""):
        if target_symbol == "":
            return []

        ret = []

        for coin in self.__get_ticker():
            match = re.match(target_symbol, coin["symbol"], re.IGNORECASE)
            if match:
                ret.append((coin["symbol"], coin["id"]))
        return ret
        


    def search_id(self, target_id=""):
        if target_id == "":
            return []

        ret = []

        for coin in self.__get_ticker():
            match = re.match(target_id, coin["id"], re.IGNORECASE)
            if match:
                ret.append((coin["id"], coin["symbol"]))
        return ret
        
        
if __name__ == "__main__":
    cmc = CoinMarketCap()
    cmc.chart()