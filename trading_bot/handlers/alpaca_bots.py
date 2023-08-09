import asyncio
from alpaca.trading.client import TradingClient
from alpaca.trading.stream import TradingStream
from alpaca.trading.requests import GetAssetsRequest, MarketOrderRequest, GetOrdersRequest
from alpaca.trading.enums import AssetClass, OrderSide, TimeInForce
from alpaca.data.historical import StockHistoricalDataClient, CryptoHistoricalDataClient
from alpaca.data.requests import StockLatestQuoteRequest, CryptoLatestQuoteRequest,\
    StockBarsRequest, CryptoBarsRequest
from alpaca.data.live import StockDataStream, CryptoDataStream
from alpaca.data.timeframe import TimeFrame
from datetime import datetime
from ..settings import config
import json

API_KEY = config['alpaca']['API_KEY']
SECRET_KEY = config['alpaca']['SECRET_KEY']
DATE_FORMAT = "%Y-%m-%d"

class AlpacaTradeBot:
    def __init__(self):
        self.trading_client = TradingClient(API_KEY, SECRET_KEY, paper=True)

    def get_account(self):
        account = self.trading_client.get_account()
        # for property_name, value in account:
        #     print(f"\"{property_name}\": {value}")
        buy_power = account.buying_power
        regt_buy_power = account.regt_buying_power
        daytr_buy_power = account.daytrading_buying_power
        non_margin_buy_power = account.non_marginable_buying_power
        cash = account.cash
        portfolio_value = account.portfolio_value
        equity = account.equity
        last_equity = account.last_equity
        long_market_value = account.long_market_value
        short_market_value = account.short_market_value
        initial_margin = account.initial_margin
        maintenance_margin = account.maintenance_margin
        last_maintenance_margin = account.last_maintenance_margin
        sma = account.sma
        return { "buying_power": buy_power, "regt_buying_power": regt_buy_power,
                "daytrading_buying_power": daytr_buy_power, "non_marginable_buying_power": non_margin_buy_power,
                "cash": cash, "portfolio_value": portfolio_value, "equity": equity, "last_equity": last_equity,
                "long_market_value": long_market_value, "short_market_value": short_market_value,
                "initial_margin": initial_margin, "maintenance_margin": maintenance_margin,
                "last_maintenance_margin": last_maintenance_margin, "sma": sma
                }

    def get_asset_types(self):
        asset_types = [a.value for a in AssetClass] # "us_equity", "crypto"
        print(asset_types) 
        print([s.value for s in OrderSide]) # "buy", "sell"
        return asset_types
    
    def get_all_assets(self, type="crypto"):
        search_params = GetAssetsRequest(asset_class=type)
        assets = self.trading_client.get_all_assets(search_params)
        # print(assets[0])
        parsed_assets = list(map(lambda a: { "id": a.id.hex, "name": a.name,
        "symbol": a.symbol, "tradable": a.tradable, "marginable": a.marginable,
        "shortable": a.shortable, "easy_to_borrow": a.easy_to_borrow, "fractionable": a.fractionable,
        "min_order_size": a.min_order_size, "min_trade_increment": a.min_trade_increment,
        "price_increment": a.price_increment, "maintenance_margin_requirement": a.maintenance_margin_requirement,
        }, assets))
        return parsed_assets
    
    def get_asset(self, id_or_symbol):
        asset = self.trading_client.get_asset(id_or_symbol)
        print(asset)
        return asset
    
    def make_order(self, symbol, qty, side="buy", type="us_equity"):
        # preparing orders
        time_in_force = TimeInForce.DAY if type == "us_equity" else TimeInForce.GTC
        market_order_data = MarketOrderRequest(
                            symbol=symbol,
                            qty=qty,
                            side=side,
                            time_in_force=time_in_force
                            )

        # Market order
        market_order = self.trading_client.submit_order(
                        order_data=market_order_data
                    )
        # print(market_order)
        return market_order
        
    def get_orders(self, status, side):
        # params to filter orders by
        request_params = GetOrdersRequest(status=status, side=side)
        orders = self.trading_client.get_orders(filter=request_params)
        return orders
    
    def cancel_all_orders(self):
        cancel_statuses = self.trading_client.cancel_orders()
        print(cancel_statuses)
        return cancel_statuses
    
    def cancel_order(self, id):
        cancel_status = self.trading_client.cancel_order_by_id(id)
        return cancel_status
    
    def get_all_positions(self):
        positions = self.trading_client.get_all_positions()
        print(positions)
        return json.dumps(positions, default=str)


class AlpacaDataBot:
    def __init__(self, type="crypto"): #type = "stock", "crypto"; 
        self.client = CryptoHistoricalDataClient(API_KEY, SECRET_KEY) if type == "crypto" \
            else StockHistoricalDataClient(API_KEY, SECRET_KEY)
        self.type = type
    
    def get_latest_quote(self, symbol_or_symbols):
        if self.type == "crypto":
            request_params = CryptoLatestQuoteRequest(symbol_or_symbols=symbol_or_symbols)
            latest_quote = self.client.get_crypto_latest_quote(request_params, feed="us")
        else:
            request_params = StockLatestQuoteRequest(symbol_or_symbols=symbol_or_symbols)
            latest_quote = self.client.get_stock_latest_quote(request_params)
        return latest_quote
    
    def get_history(self, symbol_or_symbols, start, end):
        if self.type == "crypto":
            request_params = CryptoBarsRequest(
                            symbol_or_symbols=symbol_or_symbols,
                            timeframe=TimeFrame.Day,
                            start=datetime.strptime(start, DATE_FORMAT),
                            end=datetime.strptime(end, DATE_FORMAT)
                        )
            bars = self.client.get_crypto_bars(request_params)
            # convert to dataframe
            bars.df
        else:
            request_params = StockBarsRequest(
                            symbol_or_symbols=symbol_or_symbols,
                            timeframe=TimeFrame.Day,
                            start=datetime.strptime(start, DATE_FORMAT),
                            end=datetime.strptime(end, DATE_FORMAT)
                        )
            bars = self.client.get_stock_bars(request_params)
            # convert to dataframe
            bars.df
        return bars

#paper trading:  wss://paper-api.alpaca.markets/stream 
#live trading:   wss://api.alpaca.markets/stream
class AlpacaRealTimeBot:
    def __init__(self, type="crypto"):
        self.data_stream = CryptoDataStream(api_key=API_KEY, secret_key=SECRET_KEY, feed="us")  \
            if type == "crypto" else StockDataStream(API_KEY, SECRET_KEY)
        self.trading_stream = TradingStream(API_KEY, SECRET_KEY, paper=True)

        self.type = type
        self.sample_count = 0
        self.sample_rate = 5
        self.trading = False
    
    def set_trading(self, trading):
        self.trading = trading

    async def subscribe(self, symbols, ws, action_callback):
        print("subscribing...", symbols)
        async def quote_handler(data):
            rsp = data.json()
            if self.sample_count % self.sample_rate == 0:
                await ws.send_json(rsp)
                if self.trading:
                    res = await action_callback(rsp)
                    await ws.send_json(res)

            self.sample_count += 1

        async def trade_handler(data):
            rsp = data.json()
            # print(rsp)
            await ws.send_json(rsp)
        
        async def updated_bar_handler(data):
            rsp = data.json()
            # print(rsp)
            await ws.send_json(rsp)

        self.data_stream.subscribe_quotes(quote_handler, *symbols)
        # self.data_stream.subscribe_ dated_bars(updated_bar_handler, *symbols)
        
        try:
            self.data_stream.run()
            
        except Exception as e:
            print(f'Exception from websocket connection: {e}')
        finally:
            print("Trying to re-establish connection")
            self.data_stream.run()

    
    async def unsubscribe(self, symbols):
        print("unsubscribing...", symbols)
        # self.data_stream._unsubscribe()
        self.data_stream.unsubscribe_quotes(*symbols)
        # self.data_stream.unsubscribe_trades(*symbols)
        # self.data_stream.unsubscribe_updated_bars(*symbols)
        # self.data_stream.stop()
        # await self.stop()
        await asyncio.sleep(0)



    async def stop(self):
        self.data_stream.stop()
        await self.data_stream.stop_ws()
        await self.data_stream.close()


    def subscribe_trade_updates(self):
        # async handler
        async def update_handler(data):
            # trade updates will arrive here
            print(data)

        self.trading_stream.subscribe_trade_updates(update_handler)

        self.trading_stream.run()