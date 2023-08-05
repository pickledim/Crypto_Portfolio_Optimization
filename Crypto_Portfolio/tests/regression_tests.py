import pytest


import numpy as np
import pandas as pd


from cryptorama import CryptoPortfolio
from generic_algorithms import portfolio_optimization, get_p_l


@pytest.fixture
def crypto_df():
    df = pd.read_csv("tests/data/sample_dataset.csv")
    df.set_index("Date", inplace=True)

    return df


@pytest.fixture
def cryptos_instance():
    return CryptoPortfolio(top_hundred=True, _budget=10000, _n_coins=10, save_dir="./tests/data")


def test_portfolio_optimization(crypto_df):

    selected_coins = ["BTC", "ETH", "SOL"]
    budget = 10e3
    mu_method = "mean"
    cov_method = "exp"
    obj_function = "sharpe"

    sample_portfolio, mu, weights = portfolio_optimization(crypto_df, selected_coins, budget, mu_method, cov_method,
                                                           obj_function, _compounding=True)

    assert list(sample_portfolio.keys()) == ["ETH", "SOL"]
    assert sample_portfolio["ETH"] == 9737.9
    assert sample_portfolio["SOL"] == 262.1

    assert np.all(np.isclose(mu.values, [0.69843989, 1.26172862, 1.69948962]))

    assert list(weights.keys()) == ["BTC", "ETH", "SOL"]
    assert np.all(np.isclose(np.fromiter(weights.values(), dtype=float), [0., 0.97379, 0.02621]))

    obj_function = "min_volat"
    sample_portfolio, mu, weights = portfolio_optimization(crypto_df, selected_coins, budget, mu_method, cov_method,
                                                           obj_function, _compounding=True)

    assert list(sample_portfolio.keys()) == ["BTC", "ETH"]
    assert sample_portfolio["BTC"] == 9809.5
    assert sample_portfolio["ETH"] == 190.5

    assert np.all(np.isclose(mu.values, [0.69843989, 1.26172862, 1.69948962]))

    assert list(weights.keys()) == ["BTC", "ETH", "SOL"]
    assert np.all(np.isclose(np.fromiter(weights.values(), dtype=float), [0.98095, 0.01905, 0.]))
    

def test_get_p_l(crypto_df):
    # Sample data for testing
    portfolio = {"BTC": 2000, "ETH": 1000, "SOL": 500}
    coins = ["BTC", "ETH", "SOL"]
    # buy date
    in_price_coins = crypto_df.loc["2020-07-25", coins]
    final_price_coins = crypto_df.loc["2023-07-25", coins]

    # Test the get_p_l function
    result_portfolio, p_l = get_p_l(portfolio, in_price_coins, final_price_coins)

    # Check the DataFrame values
    assert result_portfolio["Coin"].tolist() == ["BTC", "ETH", "SOL"]
    assert result_portfolio["Amount"].tolist() == [2000, 1000, 500]
    assert all(result_portfolio["n_coins"] >= 0)

    # Check the calculated profit-loss (p_l)
    # p_l_calc = portfolio["BTC"] / in_price_coins["BTC"] * (final_price_coins["BTC"] - in_price_coins["BTC"]) \
    #            + portfolio["ETH"] / in_price_coins["ETH"] * (final_price_coins["ETH"] - in_price_coins["ETH"]) \
    #            + portfolio["SOL"] / in_price_coins["SOL"] * (final_price_coins["SOL"] - in_price_coins["SOL"])

    assert p_l == pytest.approx(17945.570001069253)


def test_post_pros_pipeline(cryptos_instance):
    n_coins = 10
    n_days = 365 * 3
    mu_method = "mean"
    cov_method = "exp"
    obj_function = "sharpe"
    compounding = False,
    scrap = False

    cryptos_instance.post_pros_pipeline(n_coins, n_days, mu_method, cov_method, obj_function, compounding, scrap)

    assert cryptos_instance.portfolio["Coin"][0] == "BNB"
    assert cryptos_instance.portfolio["Amount"][0] == 10e3
    assert np.isclose(cryptos_instance.portfolio["n_coins"][0], 41.580251)

    assert cryptos_instance.portfolio_from_past["Coin"][0] == "BNB"
    assert cryptos_instance.portfolio_from_past["Amount"][0] == 10e3
    assert np.isclose(cryptos_instance.portfolio_from_past["n_coins"][0], 509.67548)

    assert np.isclose(cryptos_instance.p_l, 112576.335)

    obj_function = "min_volat"
    cryptos_instance.post_pros_pipeline(n_coins, n_days, mu_method, cov_method, obj_function, compounding, scrap)

    assert np.all(cryptos_instance.portfolio["Coin"].values == ['TRX', 'BTC', 'BNB'])
    assert np.all(np.isclose(cryptos_instance.portfolio["Amount"].values,
                             np.array([4327.1, 4230.6, 1442.3000000000002])))
    assert np.all(np.isclose(cryptos_instance.portfolio["n_coins"].values,
                             np.array([52415.93983180336, 0.1448305433614756, 5.997119643646173])))

    assert np.all(cryptos_instance.portfolio_from_past["Coin"].values == ['XRP', 'BTC', 'XLM'])
    assert np.all(
        np.isclose(cryptos_instance.portfolio_from_past["Amount"].values,
                   np.array([5270.8, 4582.1, 147.10000000000002])))
    assert np.all(np.isclose(cryptos_instance.portfolio_from_past["n_coins"].values,
                             np.array([23564.904765840012, 0.416900443970483761, 1555.944040521383])))

    assert np.isclose(cryptos_instance.p_l, 19242.428690850073)

    obj_function = "quadratic"
    cryptos_instance.post_pros_pipeline(n_coins, n_days, mu_method, cov_method, obj_function, compounding, scrap)

    assert cryptos_instance.portfolio["Coin"][0] == "BNB"
    assert cryptos_instance.portfolio["Amount"][0] == 10e3
    assert np.isclose(cryptos_instance.portfolio["n_coins"][0], 41.580251)

    assert cryptos_instance.portfolio_from_past["Coin"][0] == "BNB"
    assert cryptos_instance.portfolio_from_past["Amount"][0] == 10e3
    assert np.isclose(cryptos_instance.portfolio_from_past["n_coins"][0], 509.67548)

    assert np.isclose(cryptos_instance.p_l, 112576.335)


def test_specific_dates(cryptos_instance):
    n_coins = 10
    buy_date = 365 * 3
    sell_date = 365 * 2
    mu_method = "mean"
    cov_method = "exp"
    obj_function = "sharpe"
    compounding = True,

    cryptos_instance.validate_from_past_specific_dates(n_coins, buy_date, sell_date, mu_method, cov_method,
                                                       obj_function, compounding, _scrap=False)

    assert np.all(cryptos_instance.portfolio_from_past_specific["Coin"].values == ['BNB'])
    assert np.all(
        np.isclose(cryptos_instance.portfolio_from_past_specific["Amount"].values,
                   np.array([10e3])))
    assert np.all(np.isclose(cryptos_instance.portfolio_from_past_specific["n_coins"].values,
                             np.array([509.67548028694387])))

    assert np.isclose(cryptos_instance.p_l_specific, 149835.55794035515)

    obj_function = "min_volat"
    cryptos_instance.validate_from_past_specific_dates(n_coins, buy_date, sell_date, mu_method, cov_method,
                                                       obj_function, compounding, _scrap=False)

    assert np.all(cryptos_instance.portfolio_from_past_specific["Coin"].values == ['XRP', 'BTC', 'XLM'])
    assert np.all(
        np.all(np.isclose(cryptos_instance.portfolio_from_past_specific["Amount"].values,
                          np.array([5270.8, 4582.1, 147.10000000000002]))))
    assert np.all(np.isclose(cryptos_instance.portfolio_from_past_specific["n_coins"].values,
                             np.array([23564.904765840012, 0.41690044397048376, 1555.944040521383])))

    assert np.isclose(cryptos_instance.p_l_specific, 22028.210521246423)

    obj_function = "quadratic"
    cryptos_instance.validate_from_past_specific_dates(n_coins, buy_date, sell_date, mu_method, cov_method,
                                                       obj_function, compounding, _scrap=False)

    assert np.all(cryptos_instance.portfolio_from_past_specific["Coin"].values == ['BNB'])
    assert np.all(
        np.isclose(cryptos_instance.portfolio_from_past_specific["Amount"].values,
                   np.array([10e3])))
    assert np.all(np.isclose(cryptos_instance.portfolio_from_past_specific["n_coins"].values,
                             np.array([509.67548028694387])))

    assert np.isclose(cryptos_instance.p_l_specific, 149835.55794035515)
