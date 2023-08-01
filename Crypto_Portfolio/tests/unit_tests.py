import pytest
import itertools
from datetime import datetime

import pandas as pd
import numpy as np

from generic_algorithms import remove_coins, convert_to_datetime, scrap_coin, regularize, \
    portfolio_optimization, get_p_l, filter_columns_by_data_span


@pytest.fixture
def crypto_df():
    df = pd.read_csv("tests/data/sample_dataset.csv")
    df.set_index("Date", inplace=True)

    return df


@pytest.fixture
def mock_df():

    date_range = pd.date_range(start="2023-01-01", periods=5, freq="D")
    data = {
        "Token1": [10, 15, 20, None, 25],
        "Token2": [5, 8, 10, None, None],
        "Token3": [None, 7, None, 9, None],
        "Token4": [100, 120, 150, 180, 200]
    }
    df = pd.DataFrame(data, index=date_range)
    df.sort_index(ascending=False, inplace=True)
    df.index = df.index.strftime("%Y-%m-%d")
    return df


def test_datetime_conversion():
    # Test case 1: Valid date string
    date_str1 = "2023-07-27"
    expected_date1 = datetime(2023, 7, 27)
    assert convert_to_datetime(date_str1) == expected_date1

    # Test case 2: Another valid date string
    date_str2 = "2021-09-15"
    expected_date2 = datetime(2021, 9, 15)
    assert convert_to_datetime(date_str2) == expected_date2

    # Test case 3: Invalid date string format (should raise ValueError)
    date_str3 = "2023/07/27"
    with pytest.raises(ValueError):
        convert_to_datetime(date_str3)

    # Test case 4: Invalid date (day 32, should raise ValueError)
    date_str4 = "2023-07-32"
    with pytest.raises(ValueError):
        convert_to_datetime(date_str4)


def test_remove_coins():
    def remove_existing_coin():
        coins_list = ["BTC", "ETH", "LTC", "XRP"]
        coins_to_remove = ["LTC", "ETH"]
        updated_list = remove_coins(coins_to_remove, coins_list)
        expected_list = ["BTC", "XRP"]
        assert updated_list == expected_list

    def remove_non_existing_coin():
        coins_list = ["BTC", "ETH", "LTC", "XRP"]
        coins_to_remove = ["XLM", "ADA"]
        updated_list = remove_coins(coins_to_remove, coins_list)
        expected_list = ["BTC", "ETH", "LTC", "XRP"]
        assert updated_list == expected_list

    def remove_empty_list():
        coins_list = ["BTC", "ETH", "LTC", "XRP"]
        coins_to_remove = []
        updated_list = remove_coins(coins_to_remove, coins_list)
        expected_list = ["BTC", "ETH", "LTC", "XRP"]
        assert updated_list == expected_list

    remove_existing_coin()
    remove_non_existing_coin()
    remove_empty_list()


def test_scrap_coin():
    # Replace "YOUR_COIN_NAME" with the actual coin name you want to test
    coin_name = "BTC"
    coin_csv_name = f"{coin_name}_all_time"

    # Call the function to scrape the coin data
    df = scrap_coin(coin_name, coin_csv_name)

    # Check if the returned value is a DataFrame
    assert isinstance(df, pd.DataFrame)

    # Check if the DataFrame contains data (not empty)
    assert not df.empty

    # Check if the DataFrame has the expected columns (e.g., "Date", "Close", etc.)
    expected_columns = ["Date", "Close", "Open", "High", "Low", "Volume", "Market Cap"]
    assert all(col in df.columns for col in expected_columns)

    # Additional checks can be added based on the specific data or requirements


def test_regularize():
    # Test case 1: All weights are non-zero
    weights = {"BTC": 0.4, "ETH": 0.3, "LTC": 0.3}
    updated_weights = regularize(weights)
    assert isinstance(updated_weights, dict)
    assert abs(sum(updated_weights.values()) - 1) < 1e-9

    # Test case 2: Some weights are zero
    weights = {"BTC": 0, "ETH": 0.5, "LTC": 0, "XRP": 0.0}
    updated_weights = regularize(weights)
    assert isinstance(updated_weights, dict)
    assert abs(sum(updated_weights.values()) - 1) < 1e-9

    # Test case 3: All weights are zero
    weights = {"BTC": 0, "ETH": 0, "LTC": 0}
    updated_weights = regularize(weights)
    assert isinstance(updated_weights, dict)
    assert abs(sum(updated_weights.values()) - 0) < 1e-9

    # Test case 4: Total weight < 1
    weights = {"BTC": 0.5, "ETH": 0.2, "LTC": 0}
    updated_weights = regularize(weights)
    assert isinstance(updated_weights, dict)
    assert abs(sum(updated_weights.values()) - 1) < 1e-9

    # Test case 5: Total weight > 1
    weights = {"BTC": 0.5, "ETH": 0.7, "LTC": 0}
    updated_weights = regularize(weights)
    assert isinstance(updated_weights, dict)
    assert abs(sum(updated_weights.values()) - 1) < 1e-9


def test_portfolio_optimization(crypto_df):
    # Other test parameters
    selected_coins = ["BTC", "ETH", "SOL"]
    budget = 100000

    possible_mu_methods = ["mean", "exp", "capm"]
    possible_cov_methods = ["sample", "exp"]
    possible_obj_functions = ["quadratic", "sharpe", "min_volat"]

    # Get all combinations of mu_method, cov_method, and obj_function
    all_combinations = list(itertools.product(possible_mu_methods, possible_cov_methods, possible_obj_functions))

    # Test the portfolio_optimization function with all combinations
    for mu_method, cov_method, obj_function in all_combinations:
        port, mu, clean_weights = portfolio_optimization(crypto_df, selected_coins, budget, mu_method, cov_method,
                                                         obj_function)
        # Check the return types
        assert isinstance(port, dict)
        assert isinstance(mu, pd.Series)
        assert isinstance(clean_weights, dict)

        # Check if the portfolio investment values are non-negative and sum to the budget
        assert all(value >= 0 for value in port.values())
        assert np.isclose(sum(port.values()), budget)

        # Check the expected returns series
        assert isinstance(mu, pd.Series)
        assert all(value >= 0 for value in mu)

        # Check the clean_weights dictionary
        assert isinstance(clean_weights, dict)
        assert np.isclose(sum(clean_weights.values()), 1)


def test_get_p_l():
    # Sample data for testing
    portfolio = {"BTC": 9667, "ETH": 304, "XRP": 0.21}
    in_price_coins = pd.Series({"BTC": 9667, "ETH": 304, "XRP": 0.21})
    final_price_coins = pd.Series({"BTC": 29227, "ETH": 1857, "XRP": 0.71})

    # Test the get_p_l function
    result_portfolio, p_l = get_p_l(portfolio, in_price_coins, final_price_coins)

    # Check the return types
    assert isinstance(result_portfolio, pd.DataFrame)
    assert isinstance(p_l, float)

    # Check the DataFrame columns
    assert all(col in result_portfolio.columns for col in ["Coin", "Amount", "n_coins"])


def test_filter_columns_by_data_span(mock_df):
    # Call the function being tested
    filtered_df = filter_columns_by_data_span(mock_df, min_data_span_days=3)

    # Check that the DataFrame columns have been filtered correctly
    assert "Token1" in filtered_df.columns
    assert "Token2" not in filtered_df.columns
    assert "Token3" not in filtered_df.columns
    assert "Token4" in filtered_df.columns

    # Check that the original DataFrame has not been modified
    assert "Token1" in mock_df.columns
    assert "Token2" in mock_df.columns
    assert "Token3" in mock_df.columns
    assert "Token4" in mock_df.columns

    # Test with an empty DataFrame
    empty_df = pd.DataFrame()
    filtered_empty_df = filter_columns_by_data_span(empty_df)
    assert filtered_empty_df.empty

    # Test with minimum data span greater than all columns (no columns should be dropped)
    df_all = mock_df.copy()
    filtered_df_all = filter_columns_by_data_span(df_all, min_data_span_days=0)
    assert df_all.equals(filtered_df_all)

    # Test with minimum data span equal to the time span of one column (no columns should be dropped)
    df_one_column = mock_df.copy()
    filtered_df_one_column = filter_columns_by_data_span(df_one_column, min_data_span_days=2)
    assert df_one_column.equals(filtered_df_one_column)
