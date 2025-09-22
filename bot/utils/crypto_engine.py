import random
from datetime import datetime, timedelta

class CryptoEngine:
    def __init__(self):
        self.prices = {
            "bitcrystal": 100.0,
            "astrotoken": 150.0
        }
        self.last_update = datetime.utcnow()

    def update_prices(self):
        now = datetime.utcnow()
        if (now - self.last_update).total_seconds() > 3600:
            for currency in self.prices:
                change = random.uniform(-0.1, 0.1)
                self.prices[currency] = round(self.prices[currency] * (1 + change), 2)
            self.last_update = now

    def get_price(self, currency="bitcrystal"):
        self.update_prices()
        return self.prices.get(currency, 100.0)

    def convert_coins_to_crypto(self, coins, currency="bitcrystal"):
        price = self.get_price(currency)
        return round(coins / price, 4)

    def convert_crypto_to_coins(self, crypto, currency="bitcrystal"):
        price = self.get_price(currency)
        return int(crypto * price)

crypto_engine = CryptoEngine()