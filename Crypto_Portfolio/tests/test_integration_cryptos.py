import pytest
import pandas as pd
from Crypto_class import Cryptos  # Assuming the class is defined in the cryptos.py file


# Use tmpdir fixture to create a temporary directory
@pytest.fixture
def tmpdir(tmpdir_factory):
    # Create a temporary directory
    temp_dir = tmpdir_factory.mktemp("test_data")
    return str(temp_dir)


# Fixture to create an instance of the Cryptos class before each test function
@pytest.fixture
def cryptos_instance(tmpdir):
    return Cryptos(top_hundred=True, _budget=10000, _n_coins=5, _hodl=True, save_dir=tmpdir)


# Test case for the __init__ method
def test_cryptos_init(cryptos_instance):
    assert cryptos_instance.budget == 10000
    assert cryptos_instance.hodl is True
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
                                        _cov_method="sample", _obj_function="sharpe", _drop=False, _scrap=False)
    assert isinstance(cryptos_instance.portfolio_from_past, pd.DataFrame)
    assert isinstance(cryptos_instance.p_l, float)


# Test case for the optimize_portfolio method
def test_optimize_portfolio(cryptos_instance):
    cryptos_instance.get_prices_df()
    cryptos_instance.get_market_cap_df()
    cryptos_instance.optimize_portfolio(_n_coins=5, _mu_method="mean",
                                        _cov_method="sample", _obj_function="sharpe", _drop=False, _scrap=False)
    assert isinstance(cryptos_instance.portfolio, pd.DataFrame)

# Run the tests with the following command:
# pytest test_integration_cryptos.py
