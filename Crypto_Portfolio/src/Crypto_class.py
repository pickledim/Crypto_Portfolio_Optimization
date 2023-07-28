import os
import re
import time
import pickle


import pandas as pd

import Crypto_Portfolio.src.clean_dir as cd
import Crypto_Portfolio.src.generic_algorithms as algos

from Crypto_Portfolio.params import BASE_DIR

base_dir = BASE_DIR


class Cryptos:
    """
    A class for performing cryptocurrency data analysis and portfolio optimization.

    Attributes:
        top_hundred (bool): Flag to choose between top 100 and top 1000 coins.
        _budget (float): The total budget for the portfolio.
        _n_coins (int): The number of coins to consider for portfolio optimization.
        _hodl (bool): Flag to indicate whether to hold the portfolio or trade after one year of investment.
        coins (list): List of cryptocurrency coins.
        csv_name (str): Name of the CSV file to save the scraped data.
        budget (float): The total budget for the portfolio.
        hodl (bool): Flag to indicate whether to hold the portfolio or trade after one year of investment.
        _n_coins (int): The number of coins to consider for portfolio optimization.
        p_l (int): Profit-loss of the selected coins.
        selected_coins_of_past (list): List of selected coins for the past portfolio.
        selected_coins (list): List of selected coins for the current portfolio.
        market_cap (list): List containing historic market cap data for each coin.
        date (pd.DataFrame): DataFrame containing date information for price data.
        df_prices (pd.DataFrame): DataFrame containing historical price data of selected coins.
        df_market_cap (pd.DataFrame): DataFrame containing historical market cap data of selected coins.
        df_prices_past (pd.DataFrame): DataFrame containing historical price data up to a specific number of days.
        portfolio_from_past (pd.DataFrame): DataFrame representing the optimized portfolio for the past.
        portfolio (pd.DataFrame): DataFrame representing the current optimized portfolio.
    """

    def __init__(self, top_hundred, _budget, _n_coins, _hodl, save_dir):
        """
        Initialize the Cryptos portfolio management object.

        Parameters:
            :param top_hundred: Flag to choose between the top 100 coins or all crypto coins.
            :type top_hundred: bool

            :param _budget: The total budget for the portfolio.
            :type _budget: float

            :param _n_coins: Number of coins to consider for portfolio optimization.
            :type _n_coins: int

            :param _hodl: Flag to determine whether to hodl or trade (check prices after one year of investment).
            :type _hodl: bool
        """

        if top_hundred:
            # load the top100 coins
            with open(f"{base_dir}/new_data/top_100.pickle", "rb") \
                    as input_file:
                self.coins = list(pickle.load(input_file))
            self.csv_name = "Top_100_cryptos"
        else:
            # load all the crypto coins
            with open(f"{base_dir}/legacy_data/top_1000.pickle", "rb") \
                    as input_file:
                self.coins = list(pickle.load(input_file))
            self.csv_name = "All_cryptos"

        self.save_dir = save_dir
        self.budget = _budget
        self.hodl = _hodl
        self._n_coins = _n_coins
        self.top_hundred = top_hundred
        self.p_l = int()
        self.selected_coins_of_past = list()
        self.selected_coins = list()
        self.market_cap = list()
        self.date = pd.DataFrame()
        self.df_prices = pd.DataFrame()
        self.df_market_cap = pd.DataFrame()
        self.df_prices_past = pd.DataFrame()
        self.portfolio_from_past = pd.DataFrame()
        self.portfolio = pd.DataFrame()
        self.stablecoins = ["USDT", "USDC", "CUSDC", "BUSD", "UST", "PAX", "DAI", "CDAI",
                            "HUSD", "TUSD", "USDN", "CUSDT", "USDP"]
        self.shitcoins = ["SHIB", "DOGE", "XDC", "LEO"]

    def regex_coins(self, file):
        """
        Extracts crypto coins from a file using regex.

        :param file: The name of the file to extract coins from.
        :type file: str
        """

        with open(file, "r") as file1:
            lines = file1.readlines()

        cryptos = [line.strip() for line in lines if re.match(r"[A-Z]+[A-Z]+[A-Z]*[\s]+", line)]
        cryptos2 = [crypto for crypto in cryptos if " " not in crypto]

        self.coins = list(set(cryptos2))

    def get_prices_df(self):
        """
        Scrapes the historical price data of selected coins and creates a DataFrame.

        This function will save the prices DataFrame to a CSV file for future use.
        """

        self.coins = self.coins[:self._n_coins]  # cheating -->stupid patch for coinmarket rate limit

        cryptos_list = list()

        # scrap each coin of the coins list
        for i, coin in enumerate(self.coins):
            print(i)
            if i % 25 == 0 and i != 0:
                print("sleeping for 1 min...")
                time.sleep(60)
            df = algos.scrap_coin(coin, f"{coin}_all_time")  # scraps the selected coins
            cryptos_list.append(df["Close"])  # keep the closing value column
            self.market_cap.append(df["Market Cap"])  # append the historic data of MC for each coin

            # assign the BTC date column as the date column of the prices df (BTC is the oldest)
            if coin == "BTC":
                self.date = df["Date"]

        # =====================================================================
        # Post Pros
        # =====================================================================
        self.df_prices = pd.concat(cryptos_list, axis=1)  # create the prices df
        self.df_prices.columns = self.coins  # add the coin names
        self.df_prices["Date"] = self.date  # add the dates
        self.df_prices = self.df_prices.set_index(self.df_prices["Date"].values)  # set the date column as index
        self.df_prices.drop(columns=["Date"], axis=1, inplace=True)  # drop the Date column

        # df = self.df_prices.copy()
        # # make nan the ico of each coin check AAVE Update: not needed anymore
        # for i in df.columns:
        #     j = 0
        #     while j < 2:
        #         pos = df[i].last_valid_index()
        #         df.at[pos, i] = np.nan
        #         # df[i].loc[pos] = np.nan
        #         j += 1
        # self.df_prices = df.copy()

        cwd = os.getcwd()
        cd.move_files(cwd, os.path.join(cwd, "../scrapped_data"))

        self.df_prices.to_csv(f"{self.save_dir}/{self.csv_name}.csv")

    def get_market_cap_df(self):
        """
        Creates the DataFrame of all the coins" market cap.

        This function will save the market cap DataFrame to a CSV file for future use.
        """
        self.df_market_cap = pd.concat(self.market_cap, axis=1)
        self.df_market_cap.columns = self.coins
        self.df_market_cap["Date"] = self.date
        self.df_market_cap = self.df_market_cap.set_index(self.df_market_cap["Date"].values)
        self.df_market_cap.drop(columns=["Date"], axis=1, inplace=True)

        self.df_market_cap.to_csv(f"{self.save_dir}/{self.csv_name}_market_cap.csv")

    def validate_from_past(self, _n_coins, _n_days, _mu_method, _cov_method, _obj_function, _drop, _scrap=False):
        """
        Performs portfolio optimization based on past data and validates the results.

        Parameters:
            :param _n_coins: Number of coins to consider for portfolio optimization.
            :type _n_coins: int

            :param _n_days: Number of days to consider for past data.
            :type _n_days: int

            :param _mu_method: Method for calculating expected returns. Possible values: "mean", "exp", "capm".
            :type _mu_method: str

            :param _cov_method: Method for calculating covariance. Possible values: "sample", "exp".
            :type _cov_method: str

            :param _obj_function: Objective function for optimization.
            Possible values: "quadratic", "sharpe", "min_volat".
            :type _obj_function: str

            :param _drop: Boolean flag indicating whether to drop missing values from the DataFrame. Default is False.
            :type _drop: bool

            :param _scrap: Boolean flag indicating whether to re-scrap data or use existing data.
            :type _scrap: bool
        """

        if not _scrap:
            self.df_prices = pd.read_csv(f"{self.save_dir}/{self.csv_name}.csv", index_col=0)

        df_mc = pd.read_csv(f"{self.save_dir}/{self.csv_name}_market_cap.csv", index_col=0)
        df_mc = df_mc.iloc[_n_days:, :]  # see the market cap of the coins from the specific day
        df_365 = df_mc.iloc[0, :].T  # take the market cap of only that day
        df_365.dropna(inplace=True)  
        coins = df_365.nlargest(_n_coins, )  # keep the n largest coins in terms of market cap
        self.selected_coins_of_past = list(coins.index)  # store the names in a list

        # remove the stable coins, the shitty coins and the ones that you cannot buy
        self.selected_coins_of_past = algos.remove_coins(self.stablecoins, self.selected_coins_of_past)
        self.selected_coins_of_past = algos.remove_coins(self.shitcoins, self.selected_coins_of_past)
        
        coin_list = self.df_prices.columns.tolist()
        coins = list(set(coin_list).intersection(self.selected_coins_of_past))

        self.df_prices = self.df_prices[coins]
        
        if self.hodl:
            # if you hodl check the prices of today
            prices_now = self.df_prices.iloc[0, :]
        else:
            # if you trade check the prices after one year of the investment
            prices_now = self.df_prices.iloc[_n_days - 365, :]

        # take the prices up to n_day
        self.df_prices_past = self.df_prices.iloc[_n_days:, :]
        # take the prices of the n_day
        prices_past = self.df_prices.iloc[_n_days, :]

        # portfolio optimization
        self.portfolio_from_past, mu, weights = algos.portfolio_optimization(self.df_prices_past, coins, self.budget,
                                                                             _mu_method, _cov_method, _obj_function,
                                                                             _drop)

        # get profit_loss
        self.portfolio_from_past, self.p_l = algos.get_p_l(self.portfolio_from_past, prices_past, prices_now)

    def optimize_portfolio(self, _n_coins, _mu_method, _cov_method, _obj_function, _drop=False, _scrap=False):
        """
        Performs portfolio optimization and creates the optimized portfolio DataFrame.

        :param _n_coins: Number of coins to consider for portfolio optimization.
        :type _n_coins: int

        :param _mu_method: Method for calculating expected returns. Possible values: "mean", "exp", "capm".
        :type _mu_method: str

        :param _cov_method: Method for calculating covariance. Possible values: "sample", "exp".
        :type _cov_method: str

        :param _obj_function: Objective function for optimization. Possible values: "quadratic", "sharpe", "min_volat".
        :type _obj_function: str

        :param _drop: Boolean flag indicating whether to drop missing values from the DataFrame. Default is False.
        :type _drop: bool

        :param _scrap: Boolean flag indicating whether to re-scrap data or use existing data.
        :type _scrap: bool
        """

        df_mc = pd.read_csv(f"{self.save_dir}/{self.csv_name}_market_cap.csv", index_col=0)
        if not _scrap:
            self.df_prices = pd.read_csv(f"{self.save_dir}/{self.csv_name}.csv", index_col=0)

        self.coins = self.df_prices.columns

        # take the n coins of the largest market cap
        df_365 = df_mc.iloc[0, :].T
        coins = df_365.nlargest(_n_coins, )
        df_365.dropna(inplace=True)
        self.selected_coins = list(coins.index)

        # remove the stable coins, the shitty coins and the ones that you cannot buy
        self.selected_coins = algos.remove_coins(self.stablecoins, self.selected_coins)
        self.selected_coins = algos.remove_coins(self.shitcoins, self.selected_coins)

        coin_list = self.df_prices.columns.tolist()
        coins = list(set(coin_list).intersection(self.selected_coins))
        self.selected_coins = coins

        portfolio, mu, weights = algos.portfolio_optimization(self.df_prices, self.selected_coins, self.budget,
                                                              _mu_method, _cov_method, _obj_function, _drop)

        coins_list = list()
        amount_list = list()
        n_coins_list = list()
        for coin, amount in portfolio.items():
            price = self.df_prices[coin].iloc[0]
            n_coins_bought = amount / price
            coins_list.append(coin)
            amount_list.append(amount)
            n_coins_list.append(n_coins_bought)

        self.portfolio = pd.DataFrame({"Coin": coins_list, "Amount": amount_list, "n_coins": n_coins_list})
        self.portfolio.sort_values(by=["Amount"], ascending=False, inplace=True)


if __name__ == "__main__":
    top_100 = True
    n_coins = 5
    n_days = 365 * 2
    mu_method = "capm"
    cov_method = "exp"
    obj_function = "sharpe"
    drop = False
    budget = 100
    hodl = True
    scrap = False
    save_to = ""
    crypto_class_20c = Cryptos(top_100, budget, n_coins, hodl, save_dir=save_to)

    crypto_class_20c.get_prices_df()
    crypto_class_20c.get_market_cap_df()
    crypto_class_20c.validate_from_past(n_coins, n_days, mu_method, cov_method, obj_function, drop, scrap)
    crypto_class_20c.optimize_portfolio(n_coins, mu_method, cov_method, obj_function, drop, scrap)
    print(f"\nn_coins={n_coins}\n")
    print(crypto_class_20c.portfolio)

    # n_coins = 10
    # crypto_class_10c = Cryptos(top_100, budget, n_coins, hodl)
    # crypto_class_10c.optimize_portfolio(n_coins, mu_method, cov_method, obj_function, drop, scrap)
    # print(f"\nn_coins={n_coins}\n")
    # print(crypto_class_10c.portfolio)
