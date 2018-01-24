from slackbot.bot import respond_to     # @botname: で反応するデコーダ
from slackbot.bot import listen_to      # チャネル内発言で反応するデコーダ
from slackbot.bot import default_reply  # 該当する応答がない場合に反応するデコーダ

import re
import math

from . import outputportfolio
from .coinmarketcap import CoinMarketCap


def adjust_digit(num, digit=10):
    if not isinstance(num, float):
        num = float(num)

    str_num = "{:,}".format(num)
    itg = int(math.log10(num) + 1)
    dcm = digit-itg
    if dcm > 0:
        n = str_num.split(".")
        return "{}.{}".format(n[0], n[1][:dcm])
    return str_num


@respond_to("仮想通貨")
def out_portfolio(message):
    res = outputportfolio.doit()
    message.channel.upload_file("graph", "pie_graph.png")
    message.reply(res)  

@listen_to("チャート？")
def out_chart(message):
    text = message.body["text"]
    match = re.match("^チャート？(.*)" , text, re.IGNORECASE)
    if match:
        coin = match.group(1)
        cmc = CoinMarketCap()
        
        if coin == "":
            coin = "BTC"

        ret = cmc.chart_by_symbol(symbol=coin, out_fname="chart.png")
        if ret:
            symbols = cmc.search_symbol(coin)
            message.channel.upload_file("chart", "chart.png")
            message.reply("https://coinmarketcap.com/currencies/{}/".format(symbols[0][1]))
        else:
           message.reply("失敗。ログ見てね。")
    
@listen_to("symbol?")
def search_symbol(message):
    text = message.body["text"]
    match = re.match("^symbol\?(.*)" , text, re.IGNORECASE)
    if match:
        symbol = match.group(1)
        print(symbol)
        cmc = CoinMarketCap()

        symbols = cmc.search_symbol(symbol)
        res =  "```"
        for symbol in symbols:
            res += "{} : {}\r\n".format(symbol[0],symbol[1])
        res +=  "```"

        message.reply(res)


@listen_to("id?")
def search_id(message):
    text = message.body["text"]
    match = re.match("^id\?(.*)" , text, re.IGNORECASE)
    if match:
        id = match.group(1)
        print(id)
        cmc = CoinMarketCap()

        ids = cmc.search_id(id)
        res =  "```"
        for id in ids:
            res += "{} : {}\r\n".format(id[0],id[1])
        res +=  "```"

        message.reply(res)

@listen_to(r"^いくら？.*")
def market_value(message):
    text = message.body["text"]
    match = re.match("^いくら？(.*)" , text, re.IGNORECASE)
    if match:
        coin = match.group(1)
        cmc = CoinMarketCap()

        if coin == "":
            coin = "btc"

        coins = coin.split(",")
        price = {}
        max_str = 0
        max_jpy_str = 0
        max_btc_str = 0
        for c in coins:
            max_str = max(max_str, len(c))
            jpy, btc = cmc.price(id=c, symbol=c)
            if jpy:
                jpy = adjust_digit(jpy,7)
                btc = adjust_digit(btc,5)

                max_jpy_str = max(max_jpy_str,len(jpy))
                max_btc_str = max(max_btc_str,len(btc))

        
                price[c] = {"jpy": jpy, "btc": btc}

        
        # stringfy
        res =  "```"
        for c in price:
            res += "{c} {j} {b}\r\n".format(c=c.ljust(max_str), j=price[c]["jpy"].ljust(max_jpy_str), b=price[c]["btc"].ljust(max_jpy_str))
        res +=  "```"

        message.reply(res)
