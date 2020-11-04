from typing import Optional

from fastapi import FastAPI
from pydantic import BaseModel
import requests
import numpy
import math

# deploy 2
# example
# r = requests.get('https://api.github.com/user', auth=('user', 'pass'))
app = FastAPI()

class Item(BaseModel):
    name: str
    price: float
    is_offer: Optional[bool] = None

@app.get("/")
def read_root():
    return {"Hello": "World"}


@app.get("/items/{item_id}")
def read_item(item_id: int, q: Optional[str] = None):
    return {"item_id": item_id, "q": q}

@app.put("/items/{item_id}")
def update_item(item_id: int, item: Item):
    return {"item_name": item.name, "item_id": item_id}

@app.get("/volatility/{window_size}")
def read_item(window_size: int, trading_symbol: Optional[str] = "BTC"):
    # example crypto data pull URL stirng in ObjC
    # https://min-api.cryptocompare.com/data/histoday?fsym=%@&tsym=USD&limit=2000
    data_api = 'https://min-api.cryptocompare.com/data/histoday'
    args = {'fsym' : trading_symbol, 'tsym' : 'USD', 'limit' : window_size}
    r = requests.get(data_api, params=args)
    response_json = r.json() # parse response JSON
    if response_json["Response"] == "Success":
        # last item in array is most recent
        time_series = response_json["Data"] # array of dictionaries
        closing_prices = []
        returns = []
        for time_step in range(0, len(time_series)): # loop over time steps
            closing_prices.append(time_series[time_step]["close"]) # extract closing price
            if time_step > 0:
                daily_return = closing_prices[time_step]/closing_prices[time_step - 1]
                returns.append(daily_return)

        stdev = numpy.std(returns)
  
    # "json" : response_json # for debug of raw data

    return {"data_url" : r.url, "window_size": window_size, "trading_symbol": trading_symbol, "daily_volatility" : stdev * 100, "annualized_volatility" : stdev*100*math.sqrt(365)}