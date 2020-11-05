from typing import Optional

from fastapi import FastAPI
from pydantic import BaseModel
import requests
import numpy
import math
import scipy.stats

# based on fastapi hello world, add /volatility path at end

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

# stat_type = [mean | stdev | skew | kurt | percentile | tail_ratio]
# if percentile, set input_value_1 to indicate percentile level 0 to 100

# tail_ratio is 95th percentile over abs(5th percentile) of daily returns 
# to indicate if more extreme values are on the high side or on the low side
# tail_ratio = 1 --> balanced extreme values
# tail_ratio > 1 --> more extreme values on high end
# tail_ratio < 1 --> more extreme values on low end

@app.get("/stats/{stat_type}/{window_size}")
def read_item(stat_type: str, window_size: int, trading_symbol: Optional[str] = "BTC", input_value_1: Optional[float] = 0):

    data_api = 'https://min-api.cryptocompare.com/data/histoday'
    args = {'fsym' : trading_symbol, 'tsym' : 'USD', 'limit' : window_size}
    r = requests.get(data_api, params=args)
    response_json = r.json() # parse response JSON

    # compute daily returns from prices as in previous example
    if response_json["Response"] == "Success":
        # last item in array is most recent
        time_series = response_json["Data"] # array of dictionaries
        closing_prices = []
        returns = []
        for time_step in range(0, len(time_series)): # loop over time steps
            closing_prices.append(time_series[time_step]["close"]) # extract closing price
            if time_step > 0:
                daily_return = closing_prices[time_step]/closing_prices[time_step - 1] - 1 # make 0-centered for this example
                returns.append(daily_return)

        the_stat = 0

        if stat_type == 'mean':
            the_stat = numpy.mean(returns) # since we have 1-centered returns, go back to ordinary zero-centered
        elif stat_type == 'stdev':
            the_stat = numpy.std(returns)
        elif stat_type == 'skew':
            the_stat = scipy.stats.skew(returns)
        elif stat_type == 'kurt':
            the_stat = scipy.stats.kurtosis(returns)
        elif stat_type == 'percentile':
            the_stat = numpy.percentile(returns, input_value_1)
        elif stat_type == 'tail_ratio':
            the_stat = numpy.percentile(returns, 95)/numpy.abs(numpy.percentile(returns, 5))
        else:
            the_stat = 0 # default dont know
            stat_type = "unknown" # to tell caller dont know
                    
    return {"data_url" : r.url, "stat_type" : stat_type, "window_size": window_size, "trading_symbol": trading_symbol, "stat" : the_stat}

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