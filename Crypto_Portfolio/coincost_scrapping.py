import os
import time
import json
import pickle
import requests
import datetime


import numpy as np
import pandas as pd


from requests import Session
from requests.exceptions import ConnectionError, Timeout, TooManyRedirects


import Crypto_Portfolio.src.generic_algorithms as algos

def top_coins(_number, _dir):

    with open("api_keys.json", 'r') as json_file:
        api_keys = json.load(json_file)

    url = "https://pro-api.coinmarketcap.com/v1/cryptocurrency/listings/latest"
    limit = str(_number)
    parameters = {
      "start": "1",
      "limit": limit,
      "convert": "USD"
    }
    headers = {
      "Accepts": "application/json",
      "X-CMC_PRO_API_KEY": api_keys["cmc"],  # input your token
    }

    session = Session()
    session.headers.update(headers)

    try:
        response = session.get(url, params=parameters)
        data = json.loads(response.text)
        # print(data)
    except (ConnectionError, Timeout, TooManyRedirects) as e:
        print(e)

    coin_data = data["data"]
    coins = [coin["symbol"] for coin in coin_data]

    if _number <= 100:
        _var = "short_list"
    else:
        _var = "long_list"

    print(f"\nTop {limit} coins: {coins}\n")
    with open(f"{_dir}/top_coins_{_var}.pickle", "wb") as handle:
        pickle.dump(coins, handle, protocol=pickle.HIGHEST_PROTOCOL)

    return coins
class BinanceDataProcessor:

    def __init__(self):
        self.extracted_data = dict()
        self.etl_data = pd.DataFrame

    def get_historical_data_binance(self, crypto_symbol, days):
        crypto_pair = crypto_symbol + "USDT"
        url = f"https://api.binance.com/api/v3/klines"
        params = {
            'symbol': crypto_pair,
            'interval': '1d',
            'limit': days
        }
        response = requests.get(url, params=params)
        self.extracted_data = response.json()

    def process_data(self, data, crypto_symbol):
        if type(data) != list:
            print(f"Data for {crypto_symbol} not found\n")
            return np.nan

        processed_data = []

        for day_data in data:
            date = datetime.datetime.fromtimestamp(day_data[0] / 1000).strftime('%Y-%m-%d')
            close_price = float(day_data[4])

            processed_data.append({
                'date': date,
                crypto_symbol: close_price,
            })

        processed_data_df = pd.DataFrame(processed_data)
        return processed_data_df

    def merge_dfs_on_common_col(self, dfs_dict, common_col):
        valid_dfs = [df for df in dfs_dict.values() if df is not np.nan]
        merged_df = valid_dfs[0]

        for df in valid_dfs[1:]:
            if df.shape[0] != merged_df.shape[0]:
                print(f"Not enough data for {df.columns[-1]}")
            else:
                merged_df = pd.merge(merged_df, df, on=common_col, how='inner')

        merged_df.set_index("date", inplace=True, drop=True)
        return merged_df

    def etl_binance(self, coins, limit):
        all_data = dict()
        for coin in coins:
            self.get_historical_data_binance(coin, limit)
            processed_data = self.process_data(self.extracted_data, coin)
            all_data[coin] = processed_data

        self.etl_data = self.merge_dfs_on_common_col(all_data, "date")


class CoinGeckoDataProcessor:
    def __init__(self, coins, date_start, date_end, vs_currency='usd'):

        with open("api_keys.json", 'r') as json_file:
            api_keys = json.load(json_file)

        self.coins = coins
        self.vs_currency = vs_currency
        self.api_key = api_keys["coin_gecko"]
        self.date_start = date_start.strftime("%d-%m-%Y")
        self.date_end = date_end.strftime("%d-%m-%Y")

        self.df_prices = pd.DataFrame
        self.big_data = pd.DataFrame
        self.df_marketcap = pd.DataFrame

    def fetch_historical_data(self, coin_id, since_date, to):

        url = f"https://api.coingecko.com/api/v3/coins/{coin_id}/market_chart/range"
        params = {
            'vs_currency': self.vs_currency,
            "x-cg-demo-api-key": self.api_key,
            "from": algos.convert_datetime_to_unix(since_date),
            "to": algos.convert_datetime_to_unix(to)
        }

        response = requests.get(url, params=params)

        if response.status_code == 200:
            data = response.json()
            return data
        elif response.status_code == 429:
            retry_after = int(response.headers.get("Retry-After", 1))
            print(f"Rate limit exceeded. Retrying after {retry_after} seconds...")
            time.sleep(retry_after)
            return self.fetch_historical_data(coin_id, since_date, to)
        else:
            print(f"Failed to fetch data. Status code: {response.status_code}, Error: {response.json()}")
            return None

    def transform_data(self, data):
        prices = [item[1] for item in data["prices"]]
        market_caps = [item[1] for item in data["market_caps"]]
        dates = [algos.convert_unix_to_date(item[0] / 1000) for item in data["market_caps"]]

        df = pd.DataFrame({
            'Date': dates,
            'Price': prices,
            'MarketCap': market_caps
        })

        return df

    def post_process_data(self, dict_data, _save=False):
        df_list = []
        for symbol, df in dict_data.items():
            df['Symbol'] = symbol
            df_list.append(df)

        self.big_data = pd.concat(df_list, ignore_index=True)
        self.big_data["Date"] = pd.to_datetime(self.big_data["Date"], format="%d-%m-%Y")
        self.big_data["Date"] = self.big_data["Date"].dt.strftime('%Y-%m-%d')
        if _save:
            self.big_data.to_csv("new_all_cryptos_data.csv")

    def pivot_big_data(self):

        self.df_prices = self.big_data.pivot(index='Date', columns='Symbol', values='Price')
        self.df_prices.index = pd.to_datetime(self.df_prices.index)

        self.df_marketcap = self.big_data.pivot(index='Date', columns='Symbol', values='MarketCap')
        self.df_marketcap.index = pd.to_datetime(self.df_marketcap.index)

    def fetch_and_process_all(self):
        data_dict = {}
        start = time.time()
        with open("crypto_mapper.json", 'r') as json_file:
            mapper = json.load(json_file)

        for i, coin in enumerate(self.coins):
            print(f"Processing {coin}...")
            coin_id = mapper.get(coin)
            if coin_id:
                data = self.fetch_historical_data(coin_id, self.date_start, self.date_end)
                if data:
                    data_dict[coin] = self.transform_data(data)
                else:
                    print(f"Failed to fetch or transform data for {coin}")
            else:
                print(f"Coin ID for {coin} not found in mapper")

        self.post_process_data(data_dict)
        self.pivot_big_data()

        end = time.time()
        print(f"Time Elapsed: {round((end - start) / 60, 2)} mins")


if __name__ == "__main__":
    from dateutil.relativedelta import relativedelta

    number = 20
    top_coins(number, os.getcwd())
    coin = 'BTC'  # you can replace this with any other trading pair symbol
    limit = 90  # number of days for historical data (3 months)
    top_coins = ['BTC', 'ETH', 'BNB', 'SOL', 'USDC', 'XRP', 'TON', 'DOGE', 'ADA', 'TRX', 'AVAX', 'SHIB', 'DOT', 'LINK', 'BCH', 'NEAR', 'DAI', 'LEO', 'LTC']
    processor = BinanceDataProcessor()
    processor.etl_binance(top_coins, limit)
    data = processor.etl_data

    end_date = datetime.datetime.now()
    start_date = end_date - relativedelta(months=11)

    processor = CoinGeckoDataProcessor(top_coins, start_date, end_date)
    processor.fetch_and_process_all()
    new_data = processor.df_prices
    new_data.index = new_data.index.strftime("%d-%m-%Y")
