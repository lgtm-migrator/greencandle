#!/usr/bin/env python
# PYTHON_ARGCOMPLETE_OK
#pylint: disable=no-member,consider-iterating-dictionary

"""
Get ohlc (Opunknownen, High, Low, Close) values from given cryptos
and detect trends using candlestick patterns
"""

from __future__ import print_function
import json
import argparse
import time
import calendar
from concurrent.futures import ThreadPoolExecutor
import pickle
import numpy
import talib
import argcomplete
import pandas
import binance
from lib.binance_common import get_binance_klines
from lib.graph import create_graph
from lib.morris import KnuthMorrisPratt
from indicator import SuperTrend, RSI
import order

POOL = ThreadPoolExecutor(max_workers=200)

def make_float(arr):
    """Convert dataframe array into float array"""
    return numpy.array([float(x) for x in arr.values])

class Events(dict):
    """ Represent events created from data & indicators """

    def __init__(self, pairs):
        """
        Initialize class
        Create hold and event dicts
        Fetch initial data from binance and store within object
        """

        self.pairs = pairs
        self.dataframe = None
        self["hold"] = {}
        self["event"] = {}
        self.data, self.dataframes = self.get_ohlcs()
        pickle.dump(self.data, open("data.p", "wb"))
        pickle.dump(self.dataframes, open("dataframes.p", "wb"))

        super(Events, self).__init__()

    @staticmethod
    def get_ohlc(pair, interval):
        """
        get ohlc for single pair
        Return both a full pandas dataframe and a tuple of float values
        """
        dataframe = get_binance_klines(pair, interval=interval)
        ohlc = (make_float(dataframe.open),
                make_float(dataframe.high),
                make_float(dataframe.low),
                make_float(dataframe.close))
        return ohlc, dataframe

    def get_ohlcs(self, graph=False, interval="5m"):
        """ Get details from binance API """
        ohlcs = {}
        dataframe = {}
        results = {}
        for pair in self.pairs:
            event = {}
            event["symbol"] = pair
            event['data'] = {}
            #ohlcs.append(POOL.submit(self.get_ohlc, pair=pair, interval=interval))
            results[pair] = POOL.submit(self.get_ohlc, pair=pair, interval=interval)

            #ohlcs[pair], dataframe[pair] = x.result()

            if graph:
                create_graph(self.ataframe, pair)
        #return [ohlc.result() for ohlc in ohlcs]
        for key, value in results.items():
            ohlcs[key] = value.result()[0]
            dataframe[key] = value.result()[1]
            #create_graph(value.result()[1], key)
        return ohlcs, dataframe

    def print_text(self):
        """
        Print text output to stdout
        """

        red = "\033[31m"
        white = "\033[0m"
        if not self.values:
            print("ERROR")
        for value in self.values():
            if not "direction" in value or "HOLD" in value["direction"]:
                #no_change.append(value["symbol"])
                continue
            try:
                print("Symbol:", value['symbol'])
                print("URL:", value["url"])
                if value["direction"] != "HOLD":
                    print("direction:", red, value["direction"], white)
                else:
                    print("direction:", value["direction"])
                print("event:", red, value["event"], white)
                print("time:", value["time"])
                for key2, value2 in value["data"].items():
                    print(key2, value2)
            except KeyError as key_error:
                print("KEYERROR", value, key_error)
                continue
            print("\n")

    def get_json(self):
        """return serialized JSON of dict """
        return json.dumps(self)

    def get_data(self):
        """
        Iterate through data and trading pairs to extract data
        Return dict containing alert data and hold data
        """
        print("Starting get_data method")

        for pair in self.pairs:
        #for pair, klines in self.data.items():
            # get indicators supertrend, and API for each trading pair

            POOL.submit(self.get_indicators, pair, self.data[pair])
            POOL.submit(self.get_supertrend, pair, self.dataframes[pair])
            POOL.submit(self.get_rsi, pair, self.dataframes[pair])
            #self.get_indicators(pair, self.data[pair])
            #self.get_supertrend(pair, self.dataframes[pair])
            #self.get_rsi(pair, self.dataframes[pair])
        POOL.shutdown(wait=True)
        return self

    def get_rsi(self, pair="PPTBTC", klines=None):
        """ get RSI oscillator values for given pair"""
        dataframe = self.renamed_dataframe_columns(klines)
        scheme = {}
        mine = dataframe.apply(pandas.to_numeric)
        rsi = RSI(mine)
        df_list = rsi['RSI_21'].tolist()
        df_list = ["%.1f" % float(x) for x in df_list]
        scheme["data"] = {"RSI": df_list[-10:]}
        scheme["url"] = self.get_url(pair)
        scheme["time"] = calendar.timegm(time.gmtime())
        scheme["symbol"] = pair
        if float(df_list[-1]) > 70:
            direction = "overbought"
        elif float(df_list[-1]) < 30:
            direction = "oversold"
        else:
            direction = "HOLD"
        scheme["direction"] = direction
        scheme["event"] = "RSI"
        self.add_scheme(scheme)

    @staticmethod
    def renamed_dataframe_columns(klines=None):
        """Return dataframe with ordered/renamed coulumns"""
        dataframe = pandas.DataFrame(klines, columns=['openTime', 'open', 'high',
                                                      'low', 'close', 'volume'])
        columns = ["date", "Open", "High", "Low", "Close", "Volume"]  # rename columns
        for index, item in enumerate(columns):
            dataframe.columns.values[index] = item
        return dataframe

    def get_supertrend(self, pair="XRPETH", klines=None):
        """ get the super trend values """
        scheme = {}

        dataframe = self.renamed_dataframe_columns(klines)

        mine = dataframe.apply(pandas.to_numeric)
        supertrend = SuperTrend(mine, 10, 3)
        df_list = supertrend['STX_10_3'].tolist()
        scheme["data"] = {"SUPERTREND": df_list[-10:]}
        scheme["url"] = self.get_url(pair)
        scheme["time"] = calendar.timegm(time.gmtime())
        scheme["symbol"] = pair
        scheme["direction"] = self.get_supertrend_direction(pair, df_list[-10:])
        scheme["event"] = "Supertrend"
        self.add_scheme(scheme)

    @staticmethod
    def get_url(pair):
        """return graph URL for given pair"""
        return "https://uk.tradingview.com/symbols/{0}/".format(pair)

    @staticmethod
    def get_supertrend_direction(pair, supertrend):
        """Get new direction of supertrend from pattern"""
        if 7 in [s for s in KnuthMorrisPratt(supertrend, ["down", "up", "up"])]:
            action = "BUY"
            price = order.get_buy_price(pair)
        elif 8 in [s for s in KnuthMorrisPratt(supertrend, ["up", "down"])]:
            action = "SELL"
            price = order.get_sell_price(pair)
        elif 3 in [s for s in KnuthMorrisPratt(supertrend, ["nan", "nan", "nan", "nan"])]:
            action = "UNKNOWN!"
            price = "irreverent"
        else:
            action = "HOLD"
            price = binance.prices()[pair]
        return action

    def get_indicators(self, pair, klines):
        """ Cross Reference data against trend indicators """
        trends = {"HAMMER": {100: "bullish", 0:"HOLD"},
                  "INVERTEDHAMMER": {100: "bearish", 0:"HOLD"},
                  "ENGULFING": {-100:"bearish", 100:"bullish", 0:"HOLD"},
                  "DOJI": {100: "unknown", 0:"HOLD"}}
        results = {}
        for check in trends.keys():
            j = getattr(talib, "CDL" + check)(*klines).tolist()[-10:]
            results.update({check: j})

        for check in trends.keys():
            scheme = {}
            try:
                result = trends[check][results[check][-1]]
                if "data" not in scheme:
                    scheme['data'] = {}
                scheme["data"] = results   # convert from array to list
                scheme["url"] = self.get_url(pair)
                scheme["time"] = calendar.timegm(time.gmtime())
                scheme["symbol"] = pair
                scheme["direction"] = result
                scheme["event"] = check
            except KeyError:
                print("KEYERROR")
                continue
        self.add_scheme(scheme)

    def add_scheme(self, scheme):
        """ add scheme to correct structure """
        if scheme["direction"] == "HOLD":
            self["hold"][id(scheme)] = scheme
        else:
            self["event"][id(scheme)] = scheme


def main():
    """ main function """
    parser = argparse.ArgumentParser()
    parser.add_argument('-g', '--graph', action='store_true', default=False)
    parser.add_argument('-j', '--json', action='store_true', default=False)
    parser.add_argument('-t', '--test', action='store_true', default=False)
    parser.add_argument('-p', '--pair')
    argcomplete.autocomplete(parser)
    args = parser.parse_args()
    agg_data = {}

    if args.pair:
        pairs = [args.pair]
    else:
        pairs = [price for price in binance.prices().keys() if price != '123456']


    events = Events(pairs)
    data = events.get_data()
    if args.json:
        print(json.dumps(events, indent=4))
    else:
        events.print_text()

    agg_data.update(data)
    return agg_data

if __name__ == '__main__':
    main()
