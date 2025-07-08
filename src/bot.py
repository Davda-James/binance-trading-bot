from binance.client import Client
from binance.enums import *
from dotenv import load_dotenv
import os
import logging
import asyncio
load_dotenv()

BINANCE_TESTNET_API_KEY= os.getenv('BINANCE_TESTNET_API_KEY')
BINANCE_TESTNET_API_SECRET = os.getenv('BINANCE_TESTNET_API_SECRET')
TESTNET_URL = os.getenv('BINANCE_BASE_URL')

class BinanceBot:
    def __init__(self,api_key,api_secret,testnet=True):
        self.api_key = api_key
        self.api_secret = api_secret
        self.client=None
        self.client = Client(self.api_key, self.api_secret,testnet=True)
        if testnet:     
            self.client.FUTURES_URL= f"{TESTNET_URL}/fapi"


    def client_ping(self):
        try:
            self.client.ping()
            logging.info("Client is reachable.")
        except Exception as e:
            logging.error(f"Error pinging client: {e}")

    def get_account_info(self):
        info = self.client.futures_account()
        return info
    
    def get_balance(self,asset='USDT'):
        try:
            accounts = self.client.futures_account_balance()
            print(accounts)
            for a in accounts:
                if a['asset'] == asset:
                    return a
            return {}
        except Exception as e:
            logging.error(f"Error fetching balance: {e}")
            return {}
        
    def get_available_symbols(self, quote_asset='USDT'):
        try:
            exchange_info = self.client.futures_exchange_info()
            quote_assets = {
                symbol["quoteAsset"]
                for symbol in exchange_info["symbols"]
                if symbol["contractType"] == "PERPETUAL"
            }
            return sorted(quote_assets)
        except Exception as e:
            logging.error(f"Error fetching symbols: {e}")
            return []
        
    def place_order(self,symbol, side, order_type, quantity, price=None):
        try:
            params = {
                "symbol": symbol.upper(),
                "side": side,
                "type": order_type,
                "quantity": quantity
            }
            if order_type == ORDER_TYPE_LIMIT:
                params.update({
                    "price": price,
                    "timeInForce": TIME_IN_FORCE_GTC
                })
            
            order = self.client.futures_create_order(**params)
            logging.info(f"Order placed: {order}")
            return order
        except Exception as e:
            logging.error(f"Error placing order: {e}")
            return {"error": str(e)}

    def cancel_order(self,symbol, orderId):
        try:
            result = self.client.futures_cancel_order(symbol=symbol, orderId=orderId)
            logging.info(f"Order cancelled: {result}")
            return result
        except Exception as e:
            logging.error(f"Error cancelling order: {e}")
            return {"error": str(e)}
    
    def get_all_orders(self):
        try:
            orders = self.client.futures_get_all_orders()  
            logging.info(f"Order status: {orders}")
            return orders 
        except Exception as e:
            logging.error(f"Error fetching order status: {e}")
            return {}
        
    def get_position_info(self,symbol="BTCUSDT"):
        position_info = self.client.futures_position_information(symbol=symbol)
        position_amt = float(position_info[0]["positionAmt"])
        print(f"Position Amount: {position_amt}")
        return position_amt


# Testing functions for BOT
# def main():
#     bot = BinanceBot(BINANCE_TESTNET_API_KEY, BINANCE_TESTNET_API_SECRET)
    # info = bot.place_order(
    #         symbol="BTCUSDT",
    #         side=SIDE_BUY,
    #         order_type=ORDER_TYPE_MARKET,
    #         quantity=0.001    
    #     )
    # info = bot.place_order(
    #         symbol="BTCUSDT",
    #         side=SIDE_SELL,
    #         order_type=ORDER_TYPE_MARKET,
    #         quantity=0.001
    #     )
    # print(info)
    # print(bot.get_all_orders())
    # bot.cancel_order(symbol="BTCUSDT", orderId=5224206155)
    

# if __name__=="__main__":
#    main()
    