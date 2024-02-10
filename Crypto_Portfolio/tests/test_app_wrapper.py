import pytest
from Crypto_Portfolio.app_wrapper import *


@pytest.fixture
def crypto_df():
    df = pd.read_csv("tests/data/sample_dataset.csv")
    df.set_index("Date", inplace=True)

    return df

# Test run_app function
def test_run_app():
    inputs_dict = {
        "top_100": True,
        "budget": 100,
        "n_coins": 10,
        "remove_shitcoins": False,
        "save_dir": "./tests/data",
        "scrap": False,
        "n_days": 180,
        "mu_method": "mean",
        "cov_method": "sample",
        "obj_function": "sharpe",
        "compounding": True
    }

    result = run_app(inputs_dict)

    assert isinstance(result, CryptoPortfolio)


# Test calculate_profit function
def test_calculate_profit(crypto_df):
    inputs = {
        "data": crypto_df,  # replace df_prices with your DataFrame containing historical daily returns
        "top_100": True,
        "n_coins": 10,
        "remove_shitcoins": False,
        "mu_method": "mean",
        "cov_method": "sample",
        "obj_function": "sharpe",
        "budget": 100,
        "days_vector": [180, 365],
        "sell_day": 180,
        "compounding": True,
        "save_dir": "./tests/data"
    }

    result = calculate_profit(inputs)

    assert isinstance(result, tuple)
    assert len(result) == 3


# Test check_coins function
def test_check_coins():
    portfolio = {
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
    }

    check_coins(portfolio)  # Simply check if it executes without any exceptions


# Test convert_date_to_number function
def test_convert_date_to_number():
    date_latest_update = "11/05/2019"
    wanted_date = "30/06/2019"

    result = convert_date_to_number(date_latest_update, wanted_date)

    assert isinstance(result, int)
    assert result == -50


# Test get_df_from_dict function
def test_get_df_from_dict():
    data_dict = {
        '2019-05-11': pd.DataFrame({'Coin': ['BNB'], 'Amount': [100.0], 'n_coins': [4.75072]}),
        '2019-06-10': pd.DataFrame({'Coin': ['BNB'], 'Amount': [100.0], 'n_coins': [3.118692]})
    }

    result = get_df_from_dict(data_dict)

    assert isinstance(result, pd.DataFrame)
    assert result.shape == (2, 4)

# Add more test cases as needed for each function


