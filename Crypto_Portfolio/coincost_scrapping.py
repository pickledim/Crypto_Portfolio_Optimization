from requests import Session
from requests.exceptions import ConnectionError, Timeout, TooManyRedirects
import json
import os
import pickle


def top_coins(_number, _dir):

    url = "https://pro-api.coinmarketcap.com/v1/cryptocurrency/listings/latest"
    limit = str(_number)
    parameters = {
      "start": "1",
      "limit": limit,
      "convert": "USD"
    }
    headers = {
      "Accepts": "application/json",
      "X-CMC_PRO_API_KEY": " ",  # input your token
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
    coins = []
    for coin in coin_data:
        coins.append(coin["symbol"])
    if _number <= 100:
        n = 100
        _var = "short_list"
    else:
        n = 1000
        _var = "long_list"
    print(f"\nTop {limit} coins: {coins}\n")
    with open(f"{_dir}/top_coins_{_var}.pickle", "wb") as handle:
        pickle.dump(coins, handle, protocol=pickle.HIGHEST_PROTOCOL)


if __name__ == "__main__":
    number = 20
    top_coins(number, os.getcwd())
