import datetime
from typing import Tuple, Dict

import pandas as pd
from dateutil.relativedelta import relativedelta

import Crypto_Portfolio.coincost_scrapping as cs
import Crypto_Portfolio.src.generic_algorithms as algos
from Crypto_Portfolio.src.cryptorama import CryptoPortfolio, remove_unwanted_coins


def run_app(inputs_dict: dict) -> CryptoPortfolio:
    """
    Run the crypto market analysis and portfolio optimization using inputs from a dictionary.

    This function initializes a `CryptoPortfolio` instance based on the provided inputs and performs the following
    steps:
    1. If `scrap` is True, it scrapes the data for the top coins based on `n_coins` and saves it in the specified
    directory.
    2. Initializes a `CryptoPortfolio` instance with the relevant inputs.
    3. If `scrap` is True, it gets historical price data and market cap data for the selected coins.
    4. Validates the optimized portfolio from `n_days` before the current date using the specified optimization
    parameters.
    5. Prints the optimized portfolio based on past data.
    6. Optimizes the portfolio for the current date using the specified optimization parameters.
    7. Prints the current optimized portfolio.

    Parameters:
        :param inputs_dict: A dictionary containing input parameters for the analysis and optimization.
        :type inputs_dict: dict

    Returns:
        :return: A `CryptoPortfolio` instance with the analysis results and optimized portfolios.
        :rtype: CryptoPortfolio
    """

    class_inputs = {
        "top_hundred": inputs_dict["top_100"],
        "_budget": inputs_dict["budget"],
        "_n_coins": inputs_dict["n_coins"],
        "remove_shitcoins": inputs_dict["remove_shitcoins"],
        "save_dir": inputs_dict["save_dir"]

    }
    if inputs_dict["scrap"]:
        cs.top_coins(inputs_dict["n_coins"], inputs_dict["save_dir"])

    cyrptos_instance = CryptoPortfolio(**class_inputs)

    if inputs_dict["scrap"]:
        cyrptos_instance.get_prices_df()
        cyrptos_instance.get_market_cap_df()

    cyrptos_instance.validate_from_past(_n_coins=inputs_dict["n_coins"],
                                        _n_days=inputs_dict["n_days"],
                                        _mu_method=inputs_dict["mu_method"],
                                        _cov_method=inputs_dict["cov_method"],
                                        _obj_function=inputs_dict["obj_function"],
                                        _compounding=inputs_dict["compounding"],
                                        _scrap=inputs_dict["scrap"])

    cyrptos_instance.optimize_portfolio(_n_coins=inputs_dict["n_coins"],
                                        _mu_method=inputs_dict["mu_method"],
                                        _cov_method=inputs_dict["cov_method"],
                                        _obj_function=inputs_dict["obj_function"],
                                        _compounding=inputs_dict["compounding"],
                                        _scrap=inputs_dict["scrap"])

    return cyrptos_instance


def run_app_patch(inputs_coins: dict) -> pd.DataFrame:

    _budget = inputs_coins["budget"]
    _mu_method = inputs_coins["mu_method"]
    _cov_method = inputs_coins["cov_method"]
    _obj_function = inputs_coins["obj_function"]
    compounding = inputs_coins["compounding"]

    coins = cs.top_coins(inputs_coins["n_coins"], inputs_coins["save_dir"])

    remove_shitcoins = inputs_coins["remove_shitcoins"]

    # remove the stable coins, the shitty coins and the ones that you cannot buy
    wanted_coins = remove_unwanted_coins(coins, remove_shitcoins)
    wanted_coins = wanted_coins[:inputs_coins["n_coins"]]
    legacy_data = pd.read_csv(f"./legacy_data/All_cryptos.csv", index_col=0)
    legacy_data_subset = legacy_data[wanted_coins]

    end_date = datetime.datetime.now()
    start_date = algos.convert_to_datetime(legacy_data_subset.index.max())
    delta = end_date - start_date
    days = delta.days
    if days <= 90:
        legacy_data = pd.read_csv(f"./legacy_data/All_cryptos_only_cmc.csv", index_col=0)
        legacy_data_subset = legacy_data[wanted_coins]
        start_date = algos.convert_to_datetime(legacy_data_subset.index.max())

    legacy_data_subset.index = pd.to_datetime(legacy_data_subset.index, format="%Y-%m-%d")
    legacy_data_subset.index = legacy_data_subset.index.strftime("%d-%m-%Y")

    processor = cs.CoinGeckoDataProcessor(wanted_coins, start_date, end_date)
    processor.fetch_and_process_all()
    new_data = processor.df_prices
    new_data.index = new_data.index.strftime("%d-%m-%Y")

    data = pd.concat([new_data, legacy_data_subset])
    data.index = pd.to_datetime(data.index, format="%d-%m-%Y")
    data = data.sort_index(ascending=False)

    portfolio, mu, weights = algos.portfolio_optimization(data,
                                                          wanted_coins,
                                                          _budget,
                                                          _mu_method,
                                                          _cov_method,
                                                          _obj_function,
                                                          _compounding=compounding)

    coins_list = list()
    amount_list = list()
    n_coins_list = list()
    for coin, amount in portfolio.items():
        price = data[coin].iloc[0]
        n_coins_bought = amount / price
        coins_list.append(coin)
        amount_list.append(amount)
        n_coins_list.append(n_coins_bought)

    portfolio = pd.DataFrame({"Coin": coins_list, "Amount": amount_list, "n_coins": n_coins_list})
    portfolio.sort_values(by=["Amount"], ascending=False, inplace=True)

    return portfolio


def calculate_profit(inputs: dict, verbosity=False) -> Tuple[float, Dict[str, float], Dict[str, pd.DataFrame]]:
    """
    Calculate the profit and optimized portfolios for a given DataFrame and parameters.

    This function calculates the profit and optimized portfolios based on a DataFrame of historical daily returns for
    selected tokens and various input parameters for portfolio optimization.

    Parameters:
        :param inputs: A dictionary containing the input parameters for portfolio optimization.
                       It should include the following keys:
                       - 'data': The DataFrame containing historical daily returns of selected tokens.
                       - 'top_100': Boolean flag indicating whether to consider only the top 100 tokens by market cap.
                       - 'n_coins': The number of tokens to be included in the portfolio.
                       - 'mu_method': The method to calculate the mean historical return of tokens
                                      (e.g., 'mean', 'exp', 'capm').
                       - 'cov_method': The method to calculate the covariance matrix of tokens' returns
                                       (e.g., 'sample', 'exp').
                       - 'obj_function': The objective function for portfolio optimization
                                         (e.g., 'sharpe', 'quadratic', 'min_volat').
                       - 'budget': The investment budget for the portfolio.
                       - 'days_vector': A list of integers representing the number of days to validate the optimized
                       portfolio.
                       - 'sell_day': The number of days from the latest date to consider for selling the tokens in the
                       portfolio.
                       - 'compounding': Boolean flag indicating whether to consider compounding returns.
                       - 'save_dir': The directory path to save the resulting data and figures.
        :type inputs: dict

        :param verbosity: A boolean that allows to print more info on the console.

        :type verbosity: bool

    Returns:
        :return: A tuple containing the total profit, a dictionary of profits on different validation days, and a
                 dictionary of optimized portfolios on different validation days.
        :rtype: Tuple[float, Dict[str, float], Dict[str, pandas.DataFrame]]
    """
    # df = inputs["data"]
    _top_100 = inputs["top_100"]
    _remove_shitcoins = inputs["remove_shitcoins"]
    _n_coins = inputs["n_coins"]
    _mu_method = inputs["mu_method"]
    _cov_method = inputs["cov_method"]
    _obj_function = inputs["obj_function"]
    _budget = inputs["budget"]
    buy_day = inputs["DCA"]
    start_date = algos.convert_date_format(inputs["start_date"])
    compounding = inputs["compounding"]
    _save_dir = inputs["save_dir"]

    crypto_class = CryptoPortfolio(_top_100, _budget, _n_coins, _remove_shitcoins, _save_dir)

    if "sell_at_last_date" in inputs:
        sell_at_last_date = inputs["sell_at_last_date"]
    else:
        sell_at_last_date = False

    if inputs["sell_date"] is None:
        df = pd.read_csv(f"{_save_dir}/{crypto_class.csv_name}.csv", nrows=1, index_col=0)
        sell_date = algos.convert_to_datetime(df.index.values[0])
    else:
        sell_date = algos.convert_date_format(inputs["sell_date"])

    pl_data = {}
    portf = {}

    specific_date = start_date.replace(day=buy_day)

    years = relativedelta(sell_date, specific_date).years
    months = years * 12 + relativedelta(sell_date, specific_date).months

    dates_of_months = [specific_date.strftime("%Y-%m-%d")]
    for i in range(months):
        date_of_month = specific_date + relativedelta(months=i+1)
        dates_of_months.append(date_of_month.strftime("%Y-%m-%d"))

    for day in dates_of_months:
        try:
            crypto_class.validate_from_past_specific_dates(_n_coins, day, sell_date, _mu_method, _cov_method,
                                                           _obj_function, compounding)
            date = crypto_class.df_market_cap.loc[day].name

            pl_data[date] = crypto_class.p_l_specific
            portf[date] = crypto_class.portfolio_from_past_specific
        except Exception as e:
            pass

    p_l = sum(pl_data.values())

    if sell_at_last_date and verbosity:
        inv = _budget * len(dates_of_months)
        print(f'\nInvestment: {inv} $')
        print(f'Final Profit: {round(p_l, 2)} $')  # + p_l_100
        print(f'Final Profit: {round(p_l / inv * 100, 2)} %\n')  # + p_l_100

    return p_l, pl_data, portf


def check_coins(portfolio: dict):
    """
    Check the total number of coins for each cryptocurrency in the given portfolio.

    This function takes a portfolio dictionary containing DataFrames for different dates, each representing the
    distribution of coins and their quantities. It concatenates the DataFrames and calculates the total number of coins
    for each cryptocurrency.

    Parameters:
        :param portfolio: A dictionary containing DataFrames for different dates with cryptocurrency distribution.
        :type portfolio: Dict[str, pandas.DataFrame]

    Returns:
        This function does not return anything. It prints the cryptocurrency name and the total number of coins held for
        each cryptocurrency in the given portfolio.

    Example:
     check_coins({
            '2019-05-11': pd.DataFrame({
                'Coin': ['BNB'],
                'Amount': [100.0],
                'n_coins': [4.75072]
                }),
            '2019-06-10': pd.DataFrame({
                'Coin': ['BNB'],
                'Amount': [100.0],
                'n_coins': [3.118692]
            }),
            # ...
            })
    Output:
        BNB 7.869412
    """
    # Convert the dictionary to a list of DataFrames
    dfs = [pd.DataFrame(portfolio[date]) for date in portfolio]

    # Concatenate the list of DataFrames into a single DataFrame
    result_df = pd.concat(dfs, keys=portfolio.keys())

    def get_total_coins(data):
        print(data["Coin"].iloc[0], data["n_coins"].sum())

    result_df.groupby("Coin").apply(get_total_coins)


def get_df_from_dict(data_dict):
    """
    Convert a dictionary of DataFrames to a single DataFrame.

    This function takes a dictionary of DataFrames and concatenates them into a single DataFrame, with the dictionary
    keys as the new index level for the resulting DataFrame. The resulting DataFrame will have a 'Date' column
    containing the original dictionary keys as dates.

    Parameters:
        :param data_dict: A dictionary containing DataFrames as values.
        :type data_dict: dict

    Returns:
        :return: A single DataFrame containing the data from the input dictionary.
        :rtype: pandas.DataFrame

    Example:
    data_dict = {
            '2019-05-11': pd.DataFrame({'Coin': ['BNB'], 'Amount': [100.0], 'n_coins': [4.75072]}),
            '2019-06-10': pd.DataFrame({'Coin': ['BNB'], 'Amount': [100.0], 'n_coins': [3.118692]})
        }
    df = get_df_from_dict(data_dict)
     print(df)
                  Date Coin  Amount   n_coins
    2019-05-11  BNB   100.0  4.75072
    2019-06-10  BNB   100.0  3.118692
    """
    # Concatenate the DataFrames from the dictionary values
    df = pd.concat(data_dict.values(), keys=data_dict.keys())

    # Reset the index to move the dates to a separate column
    df.reset_index(level=0, inplace=True)

    # Rename the index column to 'Date'
    df.rename(columns={'level_0': 'Date'}, inplace=True)

    return df


if __name__ == '__main__':

    # Inputs
    inputs_1coins = {
        "top_100": True,
        "n_coins": 20,
        "remove_shitcoins": True,
        "budget": 100,
        "scrap": False,
        "hodl": True,
        "compounding": False,
        "start_date": "19/04/2023",
        "DCA": 3,
        "sell_date": None,
        "mu_method": 'mean',
        "cov_method": 'exp',
        "obj_function": 'quadratic',
        "save_dir": "./tests/data"
    }
    df_sample = run_app_patch(inputs_1coins)
    # p_l, results, portf = calculate_profit(inputs_1coins)
