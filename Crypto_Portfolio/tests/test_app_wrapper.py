import pytest

import numpy as np
from Crypto_Portfolio.app_wrapper import *
from pandas.testing import assert_frame_equal


@pytest.fixture
def crypto_df():
    df = pd.read_csv("tests/data/sample_dataset.csv")
    df.set_index("Date", inplace=True)

    return df


@pytest.fixture
def sample_inputs():
    return {
        "top_100": True,
        "n_coins": 5,
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
def test_calculate_profit(sample_inputs):

    expected_pl_sample = np.array([2.7652964254775916, -2.325604860185444, -1.693885839726309, -4.859998663575225])
    expected_portfolio = pd.DataFrame({"Coin": "ETH",
                                       "Amount": 100.0,
                                       "n_coins": 0.052503},
                                      index=[0])
    total_pl_sample, pl_sample, portf_sample = calculate_profit(sample_inputs)

    assert isinstance(pl_sample, dict)
    assert isinstance(portf_sample, dict)
    assert np.isclose(np.array(list(pl_sample.values())), expected_pl_sample).all()
    assert_frame_equal(portf_sample[list(portf_sample.keys())[1]], expected_portfolio)


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
# def test_convert_date_to_number():
#     date_latest_update = "11/05/2019"
#     wanted_date = "30/06/2019"
#
#     result = convert_date_to_number(date_latest_update, wanted_date)
#
#     assert isinstance(result, int)
#     assert result == -50


# Test get_df_from_dict function
def test_get_df_from_dict():
    data_dict = {
        '2019-05-11': pd.DataFrame({'Coin': ['BNB'], 'Amount': [100.0], 'n_coins': [4.75072]}),
        '2019-06-10': pd.DataFrame({'Coin': ['BNB'], 'Amount': [100.0], 'n_coins': [3.118692]})
    }

    result = get_df_from_dict(data_dict)

    assert isinstance(result, pd.DataFrame)
    assert result.shape == (2, 4)
