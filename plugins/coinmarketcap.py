import requests

class CoinMarketCap:
    def __init__():
        pass

    @staticmethod
    def ticker(id="bitcoin", symbol="BTC"):
        ret = requests.get("https://api.coinmarketcap.com/v1/ticker/?limit=4000&convert=JPY").json()
        for coin in ret:
            if coin["id"] == id:
                return coin
                
            elif coin["symbol"] == symbol:
                return coin
        return False

    @staticmethod
    def price_jpy(id="bitcoin", symbol="BTC"):
        coin = CoinMarketCap.ticker(id=id, symbol=symbol)
        if coin:
            return coin["price_jpy"]
        else:
            return False


