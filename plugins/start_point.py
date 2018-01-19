from slackbot.bot import respond_to     # @botname: で反応するデコーダ
from slackbot.bot import listen_to      # チャネル内発言で反応するデコーダ
from slackbot.bot import default_reply  # 該当する応答がない場合に反応するデコーダ

import re

from . import outputportfolio
from .coinmarketcap import CoinMarketCap

@respond_to("仮想通貨")
def ping_func(message):
    res = outputportfolio.doit()
    message.channel.upload_file("graph", "pie_graph.png")
    message.reply(res)  

@listen_to(r"^いくら？*.")
def market_value(message):
    text = message.body["text"]
    match = re.match("^いくら？(.*)" , text)
    if match:
        coin = match.group(1)
        cmc = CoinMarketCap()

        jpy, btc = cmc.price(id=coin, symbol=coin)
        if jpy:
            message.reply("{j}円、{b}BTC".format(j=jpy,b=btc))
        else:
            message.reply("{}は登録されてません".format(coin))
