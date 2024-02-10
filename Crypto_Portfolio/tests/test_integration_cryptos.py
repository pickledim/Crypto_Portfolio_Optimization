import pytest


import pandas as pd


from cryptorama import CryptoPortfolio


# Use tmpdir fixture to create a temporary directory
@pytest.fixture
def tmpdir(tmpdir_factory):
    # Create a temporary directory
    temp_dir = tmpdir_factory.mktemp("test_data")
    return str(temp_dir)


# Fixture to create an instance of the Cryptos class before each test function
@pytest.fixture
def cryptos_instance(tmpdir):
    return CryptoPortfolio(top_hundred=True, _budget=10000, _n_coins=5, remove_shitcoins=True, save_dir=tmpdir)


# Test case for the __init__ method
def test_cryptos_init(cryptos_instance):
    assert cryptos_instance.budget == 10000
    assert cryptos_instance._n_coins == 5
    assert isinstance(cryptos_instance.coins, list)


# Test case for the regex_coins method
def test_regex_coins(cryptos_instance):
    cryptos_instance.regex_coins("tests/data/cryptos_sample.txt")
    assert isinstance(cryptos_instance.coins, list)


# Test case for the get_prices_df method
def test_get_prices_df(cryptos_instance):
    cryptos_instance.get_prices_df()
    assert isinstance(cryptos_instance.df_prices, pd.DataFrame)


# Test case for the get_market_cap_df method
def test_get_market_cap_df(cryptos_instance):
    cryptos_instance.get_prices_df()
    cryptos_instance.get_market_cap_df()
    assert isinstance(cryptos_instance.df_market_cap, pd.DataFrame)


# Test case for the validate_from_past method
def test_validate_from_past(cryptos_instance):
    cryptos_instance.get_prices_df()
    cryptos_instance.get_market_cap_df()
    cryptos_instance.validate_from_past(_n_coins=5, _n_days=365, _mu_method="mean",
                                        _cov_method="sample", _obj_function="sharpe", _compounding=False, _scrap=False)
    assert isinstance(cryptos_instance.portfolio_from_past, pd.DataFrame)
    assert isinstance(cryptos_instance.p_l, float)


# Test case for the optimize_portfolio method
def test_optimize_portfolio(cryptos_instance):
    cryptos_instance.get_prices_df()
    cryptos_instance.get_market_cap_df()
    cryptos_instance.optimize_portfolio(_n_coins=5, _mu_method="mean",
                                        _cov_method="sample", _obj_function="sharpe", _compounding=False, _scrap=False)
    assert isinstance(cryptos_instance.portfolio, pd.DataFrame)


def test_specific_dates(cryptos_instance):
    cryptos_instance.get_prices_df()
    cryptos_instance.get_market_cap_df()
    cryptos_instance.validate_from_past_specific_dates(_n_coins=5, buy_date=365*3, sell_date=365, _mu_method="mean",
                                                       _cov_method="sample", _obj_function="sharpe", _compounding=False,
                                                       _scrap=False)
    assert isinstance(cryptos_instance.portfolio_from_past_specific, pd.DataFrame)
    assert isinstance(cryptos_instance.p_l_specific, float)


def test_run_all(cryptos_instance):
    cryptos_instance.run_all(file="tests/data/cryptos_sample.txt", _n_coins=5, _n_days=365*3, sell_date=365,
                             _mu_method="mean", _cov_method="sample", _obj_function="sharpe", _compounding=True,
                             _scrap=False)

    # Add assertions to validate the entire pipeline functionality
    assert cryptos_instance.df_prices is not None
    assert isinstance(cryptos_instance.df_prices, pd.DataFrame)
    assert not cryptos_instance.df_prices.empty

    assert cryptos_instance.df_market_cap is not None
    assert isinstance(cryptos_instance.df_market_cap, pd.DataFrame)
    assert not cryptos_instance.df_market_cap.empty

    assert cryptos_instance.portfolio is not None
    assert isinstance(cryptos_instance.portfolio, pd.DataFrame)
    assert not cryptos_instance.portfolio.empty

    assert cryptos_instance.portfolio_from_past is not None
    assert isinstance(cryptos_instance.portfolio_from_past, pd.DataFrame)
    assert not cryptos_instance.portfolio_from_past.empty


def test_data_pipeline(cryptos_instance):
    cryptos_instance.data_pipeline()

    # Assert that the data has been scraped and saved to CSV files
    assert cryptos_instance.df_prices is not None
    assert isinstance(cryptos_instance.df_prices, pd.DataFrame)
    assert not cryptos_instance.df_prices.empty
    assert cryptos_instance.df_market_cap is not None
    assert isinstance(cryptos_instance.df_market_cap, pd.DataFrame)
    assert not cryptos_instance.df_market_cap.empty


def test_post_pros_pipeline():
    _n_coins = 5
    _n_days = 365
    _mu_method = "mean"
    _cov_method = "sample"
    _obj_function = "sharpe"
    _compounding = True

    cryptos_instance = CryptoPortfolio(top_hundred=True, _budget=10000, _n_coins=5, remove_shitcoins=False,
                                       save_dir="tests/data")
    cryptos_instance.post_pros_pipeline(_n_coins, _n_days, _mu_method, _cov_method, _obj_function, _compounding)

    # Add assertions to check if the 'portfolio_from_past' and 'portfolio' DataFrames are not empty
    assert cryptos_instance.portfolio_from_past is not None
    assert isinstance(cryptos_instance.portfolio_from_past, pd.DataFrame)
    assert not cryptos_instance.portfolio_from_past.empty

    assert cryptos_instance.portfolio is not None
    assert isinstance(cryptos_instance.portfolio, pd.DataFrame)
    assert not cryptos_instance.portfolio.empty
