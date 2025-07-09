from binance.client import Client
from binance.enums import *
from dotenv import load_dotenv
import time 
import os
import logging
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
        self.client.REQUEST_TIMEOUT=30

    def client_ping(self):
        try:
            self.client.ping()
            logging.info("Client is reachable.")
            return True 
        except Exception as e:  
            logging.error(f"Error pinging client: {e}")
            return False
    def get_account_info(self):
        try:
            info = self.client.futures_account()
            return info
        except Exception as e:
            logging.error(f"Error fetching account info: {e}")
            return {}
    
    def get_balance(self):
        try:
            accounts = self.client.futures_account_balance()
            return accounts
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
        
    def place_order(self,symbol, side, order_type, quantity, price=None, stopPrice=None):
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
            elif order_type in [FUTURE_ORDER_TYPE_STOP, FUTURE_ORDER_TYPE_STOP_MARKET]:
                params.update({
                    "stopPrice": stopPrice,
                    "price": price if order_type == FUTURE_ORDER_TYPE_STOP else None,
                    "timeInForce": TIME_IN_FORCE_GTC if price else None
                })
            
            order = self.client.futures_create_order(**params)
            logging.info(f"Order placed: {order}")
            return order
        except Exception as e:
            logging.error(f"Error placing order: {e}")
            return {}

    def cancel_order(self,symbol, orderId):
        try:
            result = self.client.futures_cancel_order(symbol=symbol, orderId=orderId)
            logging.info(f"Order cancelled: {result}")
            return result
        except Exception as e:
            logging.error(f"Error cancelling order: {e}")
            return {}
    
    def get_all_orders(self):
        try:
            orders = self.client.futures_get_all_orders()  
            logging.info(f"Order status: {orders}")
            return orders 
        except Exception as e:
            logging.error(f"Error fetching order status: {e}")
            return {}
    
    def get_trading_pairs(self):
        try:
            exchange_info = self.client.futures_exchange_info()
            trading_pairs = [
                symbol["symbol"]
                for symbol in exchange_info["symbols"]
                if symbol["contractType"] == "PERPETUAL"
            ]
            return trading_pairs
        except Exception as e:
            logging.error(f"Error fetching trading pairs: {e}")
            return []
        
    def get_position_info(self,symbol="BTCUSDT"):
        position_info = self.client.futures_position_information(symbol=symbol)
        position_amt = float(position_info[0]["positionAmt"])
        return position_amt

    def place_twap_order(self, symbol, side, quantity, order_type="MARKET", intervals=5, dealy_sec=5, base_price = None, base_stop_price =None, price_step =0, stop_step =0):
        try:
            chunk_qty = round(quantity / intervals, 6)
            orders= []
            for i in range(intervals):
                params = {
                    "symbol": symbol.upper(),
                    "side": side,
                    "type": order_type,
                    "quantity": chunk_qty,
                }


                if order_type == ORDER_TYPE_LIMIT:
                    price = round(base_price + (price_step * i), 2) if side == SIDE_BUY else round(base_price - (price_step * i), 2)
                    params.update({
                        "price": price,
                        "timeInForce": TIME_IN_FORCE_GTC
                    })

                elif order_type == FUTURE_ORDER_TYPE_STOP:
                    stop_price = round(base_stop_price + (stop_step * i), 2) if side == SIDE_BUY else round(base_stop_price - (stop_step * i), 2) 
                    limit_price = round(base_price + (price_step * i), 2) if side == SIDE_BUY else round(base_price - (price_step * i), 2)
                    params.update({
                        "stopPrice": stop_price,
                        "price": limit_price,
                        "timeInForce": TIME_IN_FORCE_GTC
                    })

                order = self.client.futures_create_order(**params)
                orders.append(order)
                logging.info(f"TWAP order {i+1}/{intervals}: {order}")                
                time.sleep(dealy_sec)

            return orders
        except Exception as e:
            logging.error(f"Error placing TWAP order: {e}")
            return []
        
    def place_grid_orders(self, symbol,side, base_price, quantity, grid_size=5,stop_percent= 0.5):
        try:
            if side not in ["BUY", "SELL"]:
                raise ValueError("Invalid side: must be 'BUY' or 'SELL'")
            
            orders = []
            for i in range(1,grid_size+1):
                step = base_price * (stop_percent / 100) * i

                buy_price = round(base_price - step, 2)
                sell_price = round(base_price + step,2)

                order = self.client.futures_create_order(
                    symbol=symbol.upper(),
                    side=SIDE_BUY if side == "BUY" else SIDE_SELL,
                    type=ORDER_TYPE_LIMIT,
                    quantity=quantity,
                    price= buy_price if side == "BUY" else sell_price,
                    timeInForce=TIME_IN_FORCE_GTC
                )
                
                orders.append(order)

            return orders
        
        except Exception as e:
            logging.error(f"Error placing grid orders: {e}")
            return []









#  Testing functions for BOT
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
    