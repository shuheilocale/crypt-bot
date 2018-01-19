import requests

class CoinMarketCap:

    __ticker = None

    def stack_ticker(self, limit=5000):
        self.__ticker = requests.get("https://api.coinmarketcap.com/v1/ticker/?limit={l}&convert=JPY".format(l=limit)).json()

    def ticker(self, id="bitcoin", symbol="BTC"):
        if self.__ticker is None:
            print("stack")
            self.stack_ticker()

        for coin in self.__ticker:
            if coin["id"] == id:
                return coin
                
            elif coin["symbol"] == symbol:
                return coin
        return False

    def price(self, id="bitcoin", symbol="BTC"):
        coin = self.ticker(id=id, symbol=symbol)
        btc = self.ticker(id="bitcoin")
        if coin:
            return coin["price_jpy"], float(coin["price_jpy"])/float(btc["price_jpy"])
        else:
            return False, False


