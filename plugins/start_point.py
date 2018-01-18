from slackbot.bot import respond_to     # @botname: で反応するデコーダ
from slackbot.bot import listen_to      # チャネル内発言で反応するデコーダ
from slackbot.bot import default_reply  # 該当する応答がない場合に反応するデコーダ
from slackbot import settings

import requests
import pycurl
import io
import urllib
import hmac
import hashlib
import time
import json
import pybitflyer
from zaifapi import *
from coincheck import order, market, account

import matplotlib as mpl
mpl.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.cm as cm
import numpy as np


@respond_to("仮想通貨")
def ping_func(message):
    res = exec()
    message.channel.upload_file("graph", "pie_graph.png")
    message.reply(res)

cryptocurrency={
    "BTC":0,
    "BCH":0,
    "ETH":0,
    "LTC":0,
    "MONA":0,
    "XRP":0,
    "MOSAIC.CMS":0,
    "ZAIF":0,
    "XEM":0,
    "XP":0,
    "QTUM":0,
    "ZNY":0,
    "CRYPTERIUM":0,
    "ACO":0,
    "DOGE":0,
    "JPY":0,
    "LEND":0,
    "XVG":0,
    "BNB":0,
    "NEO":0,
    "PAC":0,
    "LSK":0,
    "CMPCO":0,
    "B3":0,
    "XCS":0,
    "OTHER":0   
}

def do_curl(url, encode="utf-8"):
    curl = pycurl.Curl() 
    b = io.BytesIO()
    curl.setopt(pycurl.URL, url)
    curl.setopt(curl.WRITEFUNCTION, b.write)
    curl.perform()
    ret = b.getvalue().decode("utf-8")
    return ret


def get_binance():

    s_key = settings.BINANCE_SEC_KEY
    api_key = settings.BINANCE_API_KEY

    #timestamp 
    timestamp = json.loads(do_curl("https://api.binance.com/api/v1/time"))
    timestamp = timestamp["serverTime"]
    #timestamp = int(time.time()*1000)
    recv_window = 6000000
    message = bytes("timestamp={t}&recvWindow={r}".format(t=timestamp,r=recv_window),"latin-1")
    secretkey = bytes(s_key, "latin-1")
    signature = hmac.new(secretkey, message, hashlib.sha256).hexdigest()
    url = "https://api.binance.com/api/v3/account?timestamp={t}&recvWindow={r}&signature={s}".format(t=timestamp, r=recv_window, s=signature)
    curl = pycurl.Curl() 
    b = io.BytesIO()
    header = ["X-MBX-APIKEY: {}".format(api_key)]
    curl.setopt(pycurl.HTTPHEADER, header)
    curl.setopt(pycurl.URL, url)
    curl.setopt(curl.WRITEFUNCTION, b.write)
    curl.perform()
    ret = b.getvalue().decode("utf-8")
    print("------------------")
    #print(ret)

    #レート
    b_a = io.BytesIO()
    allprices_url = "https://api.binance.com/api/v1/ticker/allPrices"
    curl.setopt(pycurl.URL, allprices_url)
    curl.setopt(curl.WRITEFUNCTION, b_a.write)
    curl.perform()
    ret_al = b_a.getvalue().decode("utf-8")
    print(type(ret_al))

    dict, rates = binance_to_dict(json.loads(ret), json.loads(ret_al))
    return dict, rates

def binance_to_dict(binance, rates):

    dict = {}
    to_btc_rate = {}
    for coin in binance["balances"]:
        c_code = coin["asset"].upper()
        c_code_prx = "BCH" if c_code == "BCC" else c_code

        if c_code_prx in cryptocurrency:
            dict[c_code_prx] = float(coin["free"]) + float(coin["locked"])
            # レート登録
            symbol = c_code+"BTC"
            for rate in rates:
                if rate["symbol"] == symbol:
                    to_btc_rate[c_code_prx] = float(rate["price"])
                    break

                
        else:
            dict["OTHER"] = float(coin["free"]) + float(coin["locked"])
    return dict, to_btc_rate


def get_bitflyer():
    api = pybitflyer.API(api_key=settings.BITFLYER_API_KEY, api_secret=settings.BITFLYER_SEC_KEY)
    res = api.getbalance()
    return bitflyer_to_dict(res)

def bitflyer_to_dict(bitflyer):
    dict = {}
    for coin in bitflyer:
        c_code = coin["currency_code"]

        if c_code in cryptocurrency:
            dict[c_code] = float(coin["amount"])
        else:
            dict["OTHER"] = float(coin["amount"])

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

        if c_code in cryptocurrency:
            dict[c_code] = float(zaif["funds"][coin])
        else:
            dict["OTHER"] = float(zaif["funds"][coin])

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
        if c_code in cryptocurrency:
            dict[c_code] = float(coincheck[coin])
        else:
            dict["OTHER"] = float(coincheck[coin])
    return dict

def get_coinechange():

    rate = {}
    #レートだけ取得
    headers={"User-Agent":"Mozilla/5.0 (Macintosh; Intel Mac OS X 10_9_5) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/42.0.2311.50 Safari/537.36"}
    xp_doge_price_url = "https://www.coinexchange.io/api/v1/getmarketsummary?market_id=137"
    ret_xp_doge = requests.get(xp_doge_price_url, headers=headers).json()
    rate["XP_DOGE"] = float(ret_xp_doge["result"]["LastPrice"])

    cmpco_btc_price_url = "https://www.coinexchange.io/api/v1/getmarketsummary?market_id=396"
    ret_cmpco_btc = requests.get(cmpco_btc_price_url, headers=headers).json()
    #print(ret_cmpco_btc)
    rate["CMPCO_BTC"] = float(ret_cmpco_btc["result"]["LastPrice"])

    b3_btc_price_url = "https://www.coinexchange.io/api/v1/getmarketsummary?market_id=514"
    ret_b3_btc = requests.get(b3_btc_price_url, headers=headers).json()
    rate["B3_BTC"] = float(ret_b3_btc["result"]["LastPrice"])

    xcs_btc_price_url = "https://www.coinexchange.io/api/v1/getmarketsummary?market_id=473"
    ret_xcs_btc = requests.get(xcs_btc_price_url, headers=headers).json()
    rate["XCS_BTC"] = float(ret_xcs_btc["result"]["LastPrice"])

    doge_lite_price_url = "https://www.coinexchange.io/api/v1/getmarketsummary?market_id=216"
    ret_doge_lite = requests.get(doge_lite_price_url, headers=headers).json()
    rate["DOGE_LITE"] = float(ret_doge_lite["result"]["LastPrice"])
    return rate

def get_cryptopia():

    rate = {}
    #レートだけ取得
    curl = pycurl.Curl()
    b_x = io.BytesIO()
    markets_url = "https://www.cryptopia.co.nz/api/GetMarkets"
    curl.setopt(pycurl.URL, markets_url)
    curl.setopt(curl.WRITEFUNCTION, b_x.write)
    curl.perform()

    markets = json.loads(b_x.getvalue().decode("utf-8"))
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


def calc_amount_denominated_in_btc(assets, rates):
    ret={}
    c_codes = assets.keys()
    for c_code in c_codes:
        if c_code == "OTHER":
            ret[c_code] = 0.0
            continue
        rate = rates[c_code]
        price = assets[c_code]*rate
        ret[c_code] = price
    return ret


def btc_to_jpy(assets, bct_jpy):
    ret={}
    total = 0.0
    c_codes = assets.keys()
    for c_code in c_codes:
        price = assets[c_code]/bct_jpy
        ret[c_code] = price
        total += price

    return ret, total


def out_graph(in_jpy,total_jpy,assets):
    
    data=list(in_jpy.values())
    c_code =list(in_jpy.keys())
    label = ["{c}(JPY:{v:,d}) {a:,f}".format(c=i,v=int(j), a=assets[i]) for i,j in zip(c_code, data)]

    plt.style.use("ggplot")
    plt.rcParams.update({"font.size":15})

    size=(9,5) 
    col=cm.Spectral(np.arange(len(data))/float(len(data))) 

    def make_autopct(values):
        def my_autopct(pct):
            total = sum(values)
            val = int(round(pct*total/100.0))
            return "{p:.2f}%".format(p=pct) if val > 100000 else ""
        return my_autopct

    plt.figure(figsize=size,dpi=100)
    plt.pie(data,colors=col,counterclock=False,startangle=90,autopct=make_autopct(data))
    plt.subplots_adjust(left=0,right=0.7)
    plt.legend(label,fancybox=True,loc="center left",bbox_to_anchor=(0.9,0.5))
    plt.axis("equal")
    plt.text(-1.7,1,"{:,d}JPY".format(int(total_jpy)),fontsize=17)
    plt.savefig("pie_graph.png",bbox_inches="tight",pad_inches=0.05)



def exec():
    print("binance")
    binance, b_rates = get_binance()
    print("bitflyer")
    bitflyer = get_bitflyer()
    print("zaif")
    zaif, z_rates = get_zaif()
    print("coincheck")
    coincheck = get_coincheck()
    
    print("totalize")
    assets = totalize([binance, bitflyer, zaif, coincheck])


    #API非管理の通貨を追加する

    #XP
    print("coinexchange")
    rate_ce = get_coinechange()
    xp_rate = rate_ce["XP_DOGE"]*rate_ce["DOGE_LITE"]*b_rates["LTC"]

    #PAC
    print("cryptopia")
    rate_crp = get_cryptopia()
    pac_rate = rate_crp["PAC_DOGE"]*rate_ce["DOGE_LITE"]*b_rates["LTC"]

    #総量
    f = open("amount.json", 'r')
    amount = json.load(f)
    f.close()

    assets["XP"] = amount["XP"]
    assets["ACO"] = amount["ACO"]
    assets["CRYPTERIUM"] = amount["CRYPTERIUM"]
    assets["PAC"] = amount["PAC"]
    assets["XCS"] = amount["XCS"]
    assets["CMPCO"] = amount["CMPCO"]
    assets["B3"] = amount["B3"]

    #BTC建てに変換する
    b_rates.update(z_rates)
    aco = b_rates["ETH"]/1100.0 # 固定レート
    b_rates.update({"BTC":1.0, "CRYPTERIUM":0.0001, "ACO":aco, "XP":xp_rate,
                    "PAC":pac_rate, "XCS":rate_ce["XCS_BTC"], "CMPCO":rate_ce["CMPCO_BTC"], "B3":rate_ce["B3_BTC"]})

    print("calc amount denominated in btc")
    in_btc = calc_amount_denominated_in_btc(assets, b_rates)

    #円建て変換(JPYは既に円建てになっていることに注意！)
    print("bt to jpy")
    in_jpy, total_jpy = btc_to_jpy(in_btc, b_rates["JPY"])

    print("out gpath")
    out_graph(in_jpy,total_jpy,assets)

    res = ""
    for c in in_jpy:
        if assets[c] != 0:
            res += "{c}:{p}\r\n".format(c=c, p=in_jpy[c]/assets[c])

    return res