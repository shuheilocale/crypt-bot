from slackbot import settings

import requests
import io
import urllib
import hmac
import hashlib
import time
import json
import pybitflyer
from zaifapi import *
from coincheck import order, market, account

from .coinmarketcap import CoinMarketCap


import matplotlib as mpl
mpl.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.cm as cm
import numpy as np

def req(url, headers=None):

    if headers is None:
        headers={"User-Agent":"Mozilla/5.0 (Macintosh; Intel Mac OS X 10_9_5) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/42.0.2311.50 Safari/537.36"}
    elif not "User-Agent" in headers:
        headers["User-Agent"] = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_9_5) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/42.0.2311.50 Safari/537.36"
    
    ret = requests.get(url, headers=headers)
    return ret


def get_binance():

    s_key = settings.BINANCE_SEC_KEY
    api_key = settings.BINANCE_API_KEY

    #timestamp 
    timestamp = req("https://api.binance.com/api/v1/time").json()
    timestamp = timestamp["serverTime"]
    recv_window = 6000000
    message = bytes("timestamp={t}&recvWindow={r}".format(t=timestamp,r=recv_window),"latin-1")
    secretkey = bytes(s_key, "latin-1")
    signature = hmac.new(secretkey, message, hashlib.sha256).hexdigest()
    url = "https://api.binance.com/api/v3/account?timestamp={t}&recvWindow={r}&signature={s}".format(t=timestamp, r=recv_window, s=signature)
    headers = {"X-MBX-APIKEY" : format(api_key)}
    ret = req(url, headers).json()

    #レート
    ret_al = req("https://api.binance.com/api/v1/ticker/allPrices").json()

    dict, rates = binance_to_dict(ret, ret_al)
    return dict, rates

def binance_to_dict(binance, rates):

    dict = {}
    to_btc_rate = {}
    for coin in binance["balances"]:
        c_code = coin["asset"].upper()
        c_code_prx = "BCH" if c_code == "BCC" else c_code

        amount = float(coin["free"]) + float(coin["locked"])
        if amount > 0.0:
            dict[c_code_prx] = amount
            # レート登録
            symbol = c_code+"BTC"
            for rate in rates:
                if rate["symbol"] == symbol:
                    to_btc_rate[c_code_prx] = float(rate["price"])
                    break

    return dict, to_btc_rate


def get_bitflyer():
    api = pybitflyer.API(api_key=settings.BITFLYER_API_KEY, api_secret=settings.BITFLYER_SEC_KEY)
    res = api.getbalance()
    return bitflyer_to_dict(res)

def bitflyer_to_dict(bitflyer):
    dict = {}
    for coin in bitflyer:
        c_code = coin["currency_code"]
        amount = float(coin["amount"])
        if amount > 0.0:
            dict[c_code] = amount

    return dict

def get_zaif():
    key = settings.ZAIF_API_KEY
    secret = settings.ZAIF_SEC_KEY
    
    zaif = ZaifTradeApi(key, secret)
    ret = zaif.get_info2()

    #レート
    rate = {}
    zaif_pub = ZaifPublicApi()
    #currency_pairs = zaif_pub.currency_pairs("all")
    rate["MONA"] = float(zaif_pub.last_price("mona_btc")["last_price"])
    rate["ZAIF"] = float(zaif_pub.last_price("zaif_btc")["last_price"])
    rate["XEM"] = float(zaif_pub.last_price("xem_btc")["last_price"])
    btc_jpy = float(zaif_pub.last_price("btc_jpy")["last_price"])
    rate["MOSAIC.CMS"] = float(zaif_pub.last_price("mosaic.cms_jpy")["last_price"]) / btc_jpy
    rate["JPY"] = 1.0 / btc_jpy

    return zaif_to_dict(ret), rate
                                                          
                                                          
def zaif_to_dict(zaif):
    dict = {}
    for coin in zaif["funds"].keys():
        c_code = coin.upper()
        amount = zaif["funds"][coin]

        if amount > 0.0:
            if c_code == "MOSAIC.CMS":
                c_code = "CMS"

            dict[c_code] = amount

    return dict

def get_coincheck():
    key = settings.COINCHECK_API_KEY
    secret = settings.COINCHECK_SEC_KEY
    a1 = account.Account(secret_key=secret, access_key=key)

    return coincheck_to_dict(a1.get_balance())

def coincheck_to_dict(coincheck):
    dict ={}

    for coin in coincheck.keys():
        if coin == "success":
            continue

        c_code = coin.upper()

        amount = float(coincheck[coin])

        if amount > 0.0:
            dict[c_code] = amount
    return dict

def get_coinechange():

    rate = {}
    #レートだけ取得
    res = req("https://www.coinexchange.io/api/v1/getmarketsummary?market_id=137")
    ret_xp_doge = res.json()
    rate["XP_DOGE"] = float(ret_xp_doge["result"]["LastPrice"])

    res = req("https://www.coinexchange.io/api/v1/getmarketsummary?market_id=396")
    ret_cmpco_btc = res.json()
    rate["CMPCO_BTC"] = float(ret_cmpco_btc["result"]["LastPrice"])

    res = req("https://www.coinexchange.io/api/v1/getmarketsummary?market_id=514")
    ret_b3_btc = res.json()
    rate["B3_BTC"] = float(ret_b3_btc["result"]["LastPrice"])

    res = req("https://www.coinexchange.io/api/v1/getmarketsummary?market_id=473")
    ret_xcs_btc = res.json()
    rate["XCS_BTC"] = float(ret_xcs_btc["result"]["LastPrice"])

    res = req("https://www.coinexchange.io/api/v1/getmarketsummary?market_id=216")
    ret_doge_lite = res.json()
    rate["DOGE_LITE"] = float(ret_doge_lite["result"]["LastPrice"])
    return rate

def get_cryptopia():

    rate = {}
    #レートだけ取得
    markets = req("https://www.cryptopia.co.nz/api/GetMarkets").json()
    for data in markets["Data"]:
        if data["Label"] == "PAC/DOGE":
            rate["PAC_DOGE"] = data["LastPrice"]
    
    return rate

def totalize(exchanges):
    assets = {}
    for exchange in exchanges:
        c_codes = exchange.keys()
        for c_code in c_codes:

            if c_code in assets:
                assets[c_code] += exchange[c_code]
            else:
                assets[c_code] = exchange[c_code]
    return assets


def out_graph(amount_map, price_jpy):
    
    amount=list(amount_map.values())
    c_code =list(amount_map.keys())

    total_jpy = 0.0
    values = {}
    for code in c_code:
        print(code)
        print(amount_map[code])
        print(price_jpy[code])
        if price_jpy[code] != False:
            values[code] = amount_map[code] * price_jpy[code]
            total_jpy += amount_map[code] * price_jpy[code]

    label = ["{c}(JPY:{v:,d}) {a:,f}".format(c=c,v=int(amount_map[c] * price_jpy[c]), a=amount_map[c]) for c in c_code]

    plt.style.use("ggplot")
    plt.rcParams.update({"font.size":15})

    size=(9,5) 
    col=cm.Spectral(np.arange(len(amount))/float(len(amount))) 

    def make_autopct(values):
        def my_autopct(pct):
            total = sum(values)
            val = int(round(pct*total/100.0))
            return "{p:.2f}%".format(p=pct) if val > 100000 else ""
        return my_autopct

    plt.figure(figsize=size,dpi=100)
    plt.pie(list(values.values()),colors=col,counterclock=False,startangle=90,autopct=make_autopct(list(values.values())))
    plt.subplots_adjust(left=0,right=0.7)
    plt.legend(label,fancybox=True,loc="center left",bbox_to_anchor=(0.9,0.5))
    plt.axis("equal")
    plt.text(-1.7,1,"{:,d}JPY".format(int(total_jpy)),fontsize=14)
    plt.savefig("pie_graph.png",bbox_inches="tight",pad_inches=0.05)

def doit():

    ##############
    # tally amount
    ##############
    ## use api

    # binance
    print("binance")
    binance, b_rates = get_binance()

    # bitflyer
    print("bitflyer")
    bitflyer = get_bitflyer()

    # zaif
    print("zaif")
    zaif, z_rates = get_zaif()

    # coincheck
    print("coincheck")
    coincheck = get_coincheck()

    print("totalize")
    amount = totalize([binance, bitflyer, zaif, coincheck])

    ## manual
    f = open("amount.json", 'r')
    manual_amount = json.load(f)
    f.close()
    amount.update(manual_amount)


    ##############
    # to jpy
    ##############
    cmc = CoinMarketCap()
    price_jpy = {}
    btc_jpy, _ = cmc.price(id="BTC")
    eth_jpy, _ = cmc.price(id="__", symbol="ETH")
    for coin in amount:

        # Not compatible 
        if coin == "ZAIF":
            jpy = btc_jpy*z_rates["ZAIF"]
        elif coin == "ACO":
            jpy = eth_jpy/1100.0 # 固定レート
        elif coin == "CRPT":
            jpy = btc_jpy*0.0001
        elif coin == "JPY":
            jpy = 1

        else:
            jpy, btc = cmc.price(id="dummy", symbol=coin)

        price_jpy[coin] = jpy

    ##############
    # output
    ##############
    print("out gpath")
    out_graph(amount, price_jpy)

    res =""
    for coin, jpy in sorted(price_jpy.items()):
        res += "{c}:{p}\r\n".format(c=coin, p=jpy)

    return res