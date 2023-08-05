import pandas as pd
from datetime import datetime

from src.cryptorama import CryptoPortfolio
from coincost_scrapping import top_coins


def run_app(inputs_dict):
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
        "save_dir": inputs_dict["save_dir"]

    }
    if inputs_dict["scrap"]:
        top_coins(inputs_dict["n_coins"], inputs_dict["save_dir"])

    cyrptos_instance = CryptoPortfolio(**class_inputs)

    if inputs_dict["scrap"]:
        cyrptos_instance.get_prices_df()
        cyrptos_instance.get_market_cap_df()

    print(f"\nValidation of optimized portfolio from {inputs_dict['n_days']} days before\n")

    cyrptos_instance.validate_from_past(_n_coins=inputs_dict["n_coins"],
                                        _n_days=inputs_dict["n_days"],
                                        _mu_method=inputs_dict["mu_method"],
                                        _cov_method=inputs_dict["cov_method"],
                                        _obj_function=inputs_dict["obj_function"],
                                        _compounding=inputs_dict["compounding"],
                                        _scrap=False)

    print(cyrptos_instance.portfolio_from_past)

    print(f"\nCurrent optimized portfolio \n")

    cyrptos_instance.optimize_portfolio(_n_coins=inputs_dict["n_coins"],
                                        _mu_method=inputs_dict["mu_method"],
                                        _cov_method=inputs_dict["cov_method"],
                                        _obj_function=inputs_dict["obj_function"],
                                        _compounding=inputs_dict["compounding"],
                                        _scrap=False)

    print(f"\n{cyrptos_instance.portfolio}")

    return cyrptos_instance


def calculate_profit(inputs):
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

    Returns:
        :return: A tuple containing the total profit, a dictionary of profits on different validation days, and a
                 dictionary of optimized portfolios on different validation days.
        :rtype: Tuple[float, Dict[str, float], Dict[str, pandas.DataFrame]]
    """
    df = inputs["data"]
    _top_100 = inputs["top_100"]
    _n_coins = inputs["n_coins"]
    _mu_method = inputs["mu_method"]
    _cov_method = inputs["cov_method"]
    _obj_function = inputs["obj_function"]
    _budget = inputs["budget"]
    _n_days_vector = inputs["days_vector"]
    sell_day = inputs["sell_day"]
    compounding = inputs["compounding"]
    _save_dir = inputs["save_dir"]

    crypto_class = CryptoPortfolio(_top_100, _budget, _n_coins, _save_dir)
    results = {}
    portf = {}

    for n_days in _n_days_vector:
        try:
            crypto_class.validate_from_past_specific_dates(_n_coins, int(n_days), sell_day, _mu_method, _cov_method,
                                                           _obj_function, compounding)
            date = df.iloc[n_days].name

            results[date] = crypto_class.p_l_specific
            portf[date] = crypto_class.portfolio_from_past_specific
        except Exception as e:
            pass

    p_l = sum(results.values())

    return p_l, results, portf


def check_coins(portfolio):
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


def convert_date_to_number(date_latest_update, wanted_date):
    """
    Convert date strings to a time delta in days.

    This function takes two date strings in the format "%d/%m/%Y" and calculates the time delta between them. The result
    is returned as an integer representing the number of days between the two dates.

    Parameters:
        :param date_latest_update: The latest date in the format "%d/%m/%Y".
        :type date_latest_update: str
        :param wanted_date: The desired date in the format "%d/%m/%Y".
        :type wanted_date: str

    Returns:
        :return: The time delta between the two dates in days.
        :rtype: int

    Example:
     convert_date_to_number("11/05/2019", "30/06/2019")
    50
     convert_date_to_number("01/01/2020", "15/02/2020")
    45
    """
    # Convert the date strings to datetime objects
    date_latest_update = datetime.strptime(date_latest_update, "%d/%m/%Y")
    wanted_date = datetime.strptime(wanted_date, "%d/%m/%Y")

    # Calculate the time delta
    delta_buy = date_latest_update - wanted_date

    # Convert the time delta to a float representing the number of days
    delta = int(delta_buy.total_seconds() / (24 * 60 * 60))
    return delta


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
        "n_coins": 1,
        "budget": 100,
        "scrap": False,
        "hodl": True,
        "compounding": False,
        "n_days": 180,
        "mu_method": 'mean',
        "cov_method": 'exp',
        "obj_function": 'quadratic',
        "save_dir": "./new_data"
    }

    portfolios_1c = run_app(inputs_1coins)
