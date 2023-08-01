from datetime import datetime


import numpy as np
import pandas as pd


from pypfopt import risk_models
from pypfopt import expected_returns
from pypfopt.efficient_frontier import EfficientFrontier


from cryptocmd import CmcScraper


def convert_to_datetime(date_str):
    """
    Converts a date string to a datetime object.

    Parameters:
        :param date_str: The input date string in the format "%Y-%m-%d".
        :type date_str: str

    Returns:
        :return: A datetime object representing the input date.
        :rtype: datetime.datetime
    """
    return datetime.strptime(date_str, "%Y-%m-%d")


def remove_coins(to_remove, selected_coins):
    """
    Removes specified coins from the selected coins list.

    Parameters:
        :param to_remove: A list of coins to be removed from the selected coins list.
        :type to_remove: list

        :param selected_coins: The list of selected coins.
        :type selected_coins: list

    Returns:
        :return: The updated list of selected coins after removal.
        :rtype: list
    """

    for coin in to_remove:
        try:
            selected_coins.remove(coin)
        except ValueError:
            pass

    return selected_coins


def scrap_coin(coin, coin_csv_name):
    """
    Scrapes data for a specific coin from a data source (Coingecko or similar).

    Parameters:
        :param coin: The name or symbol of the coin to scrape data for.
        :type coin: str

        :param coin_csv_name: The name of the CSV file to export the scraped data.
        :type coin_csv_name: str

    Returns:
        :return: A pandas DataFrame containing the scraped data for the specified coin.
        :rtype: pandas.DataFrame
    """

    # TO DO check a lib for coingecko --> more reliable
    print(f"\n ===== {coin} ===== \n")
    # initialise scraper without time interval
    scraper = CmcScraper(coin)

    # export the data as csv file, you can also pass optional `name` parameter
    scraper.export("csv", name=coin_csv_name)

    # Pandas dataFrame for the same data
    df = scraper.get_dataframe()

    return df


def regularize(weights):
    """
    Regularizes the weights of a portfolio.

    The function takes a dictionary of weights as input, where the keys represent coin names or symbols,
    and the values represent the corresponding percentage weights. The function scales the weights to ensure
    that their sum equals 1, making it a valid weight distribution for a portfolio.

    Parameters:
        :param weights: A dictionary containing coin names or symbols as keys and their corresponding percentage
                        weights as values.
        :type weights: dict

    Returns:
        :return: The updated weights dictionary with regularized values, where the sum of all weights equals 1.
        :rtype: dict
    """

    total_weight = sum(weights.values())

    if total_weight == 0:
        print("Cannot regularize the weights. All weights are zero.")
        return weights

    for coin, perc in weights.items():
        weights[coin] = perc / total_weight

    return weights


def filter_columns_by_data_span(data, min_data_span_days=60):
    """
    Filters columns in a DataFrame based on the time span of available data.

    The function iterates through each column in the DataFrame and checks the time span
    between the first and last valid index of each column. If the time span is less than
    the specified minimum data span (in days), the column is marked for removal. After
    processing all columns, the marked columns are dropped from the DataFrame.

    Parameters:
        :param data: The DataFrame containing the data to be filtered.
        :type data: pandas.DataFrame

        :param min_data_span_days: The minimum data span in days to retain a column. Default is 60.
        :type min_data_span_days: int

    Returns:
        :return: The DataFrame with columns filtered based on data span.
        :rtype: pandas.DataFrame
    """
    columns_to_drop = list()

    for token in data.columns:
        pos1 = data[token].last_valid_index()
        pos2 = data[token].first_valid_index()
        if pos1 is not None and pos2 is not None:
            start = convert_to_datetime(pos1)
            end = convert_to_datetime(pos2)
            delta = end - start
            if delta.days < min_data_span_days:
                columns_to_drop.append(token)
        else:
            columns_to_drop.append(token)

    data_filtered = data.drop(columns=columns_to_drop)

    return data_filtered


def portfolio_optimization(df, selected_coins, _budget, _mu_method, _cov_method, _obj_function, _compounding=False):
    """
    Perform portfolio optimization using the Efficient Frontier approach.

    The function takes historical price data (DataFrame) of selected coins, budget,
    method for calculating expected returns, method for calculating covariance, objective
    function for optimization, and a boolean flag for dropping missing values.

    Parameters:
        :param df: DataFrame containing historical price data of selected coins.
        :type df: pandas.DataFrame

        :param selected_coins: List of selected coin names or symbols from the DataFrame.
        :type selected_coins: list

        :param _budget: The total budget for the portfolio.
        :type _budget: float

        :param _mu_method: Method for calculating expected returns.
        Possible values: "mean", "exp", "capm".
        :type _mu_method: str

        :param _cov_method: Method for calculating covariance.
        Possible values: "sample", "exp".
        :type _cov_method: str

        :param _obj_function: Objective function for optimization.
        Possible values: "quadratic", "sharpe", "min_volat".
        :type _obj_function: str

        :param _compounding: Boolean flag indicating whether to compound the mean. Default is False.
        :type _drop: bool

    Returns:
        :return: A dictionary containing the optimized portfolio with coin names as keys and
        investment values as values, a pandas Series representing the calculated expected returns
        for the selected coins, a dictionary with cleaned and adjusted weights for the optimized portfolio.
        :rtype: tuple
    """

    mu_mapping = {
        "mean": expected_returns.mean_historical_return,
        "exp": expected_returns.ema_historical_return,
        "capm": expected_returns.capm_return
    }

    cov_mapping = {
        "sample": risk_models.sample_cov,
        "exp": risk_models.exp_cov
    }

    df = df[selected_coins]

    # keep the coins that are in the market for at least 2 months
    df = filter_columns_by_data_span(df, min_data_span_days=60)

    # if _drop:
    #     df.dropna(inplace=True)

    df = df.sort_index(ascending=True)

    # Calculate expected returns and sample covariance
    mu = mu_mapping[_mu_method](df, compounding=_compounding, frequency=365)
    mu.replace([np.inf, -np.inf], np.nan, inplace=True)
    mu.dropna(inplace=True)
    # print(mu)
    ind_list = mu.index
    df = df[ind_list]
    S = cov_mapping[_cov_method](df, frequency=365)

    # Optimize for maximal Sharpe ratio
    ef = EfficientFrontier(mu, S, weight_bounds=(0, 1))

    obj_f_mapping = {
        "quadratic": ef.max_quadratic_utility,
        "sharpe": ef.max_sharpe,
        "min_volat": ef.min_volatility
    }

    weights = obj_f_mapping[_obj_function]()
    clean_weights = ef.clean_weights()
    clean_weights = regularize(clean_weights)

    ef.portfolio_performance(verbose=True)

    port = {}
    for coin, perc in clean_weights.items():
        if perc > 0:
            port[coin] = perc * _budget

    print(f"Invest {np.array(list(port.values())).sum()}")

    return port, mu, clean_weights


def get_p_l(portfolio, in_price_coins, final_price_coins):
    """
    Calculate the profit-loss of the selected coins in the portfolio.

    The function takes an optimized portfolio dictionary, initial prices of the coins series,
    and final prices of the coins series as inputs.

    Parameters:
        :param portfolio: The optimized portfolio dictionary with coin names as keys and investment values as values.
        :type portfolio: dict

        :param in_price_coins: A Series containing the initial prices of the coins series, with coin names as keys
        and prices as values.
        :type in_price_coins: pd.Series

        :param final_price_coins: A Series containing the final prices of the coins series, with coin names as keys
        and prices as values.
        :type final_price_coins: pd.Series

    Returns:
        :return: A DataFrame representing the portfolio with columns "Coin", "Amount", and "n_coins",
                 and the calculated profit-loss (p_l) for the selected coins.
        :rtype: tuple
    """

    p_l = 0
    coins_list = list()
    amount_list = list()
    n_coins_list = list()

    for coin, amount in portfolio.items():
        in_price = in_price_coins[coin]
        fin_price = final_price_coins[coin]
        n_coins_bought = amount / in_price
        coins_list.append(coin)
        amount_list.append(amount)
        n_coins_list.append(n_coins_bought)
        p_l += n_coins_bought * (fin_price - in_price)

    print(f"\n Profit Loss: {p_l}e\n")

    portfolio = pd.DataFrame({"Coin": coins_list, "Amount": amount_list, "n_coins": n_coins_list})
    portfolio.sort_values(by=["Amount"], ascending=False, inplace=True)

    return portfolio, p_l
