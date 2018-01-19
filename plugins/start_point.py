from slackbot.bot import respond_to     # @botname: で反応するデコーダ
from slackbot.bot import listen_to      # チャネル内発言で反応するデコーダ
from slackbot.bot import default_reply  # 該当する応答がない場合に反応するデコーダ

import re

from . import outputportfolio

@respond_to("仮想通貨")
def ping_func(message):
    res = outputportfolio.doit()
    message.channel.upload_file("graph", "pie_graph.png")
    message.reply(res)  

@respond_to(r"^いくら？*.")
def market_value(message):
    text = message.body["text"]
    match = re.match("^いくら？(.*)" , text)
    if match:
        message.reply(match.group(1))
