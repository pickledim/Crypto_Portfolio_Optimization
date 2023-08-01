from src.cryptorama import CryptoPortfolio
from coincost_scrapping import top_coins


def run_from_json(inputs_dict):
    """
    Run the crypto market analysis and portfolio optimization using inputs from a dictionary.

    This function initializes a `CryptoPortfolio` instance based on the provided inputs and performs the following steps:
    1. If `scrap` is True, it scrapes the data for the top coins based on `n_coins` and saves it in the specified directory.
    2. Initializes a `CryptoPortfolio` instance with the relevant inputs.
    3. If `scrap` is True, it gets historical price data and market cap data for the selected coins.
    4. Validates the optimized portfolio from `n_days` before the current date using the specified optimization parameters.
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

    print(f"\nValidation of optimzed portfolio from {inputs_dict['n_days']} days before\n")

    cyrptos_instance.validate_from_past(_n_coins=inputs_dict["n_coins"],
                                        _n_days=inputs_dict["n_days"],
                                        _mu_method=inputs_dict["mu_method"],
                                        _cov_method=inputs_dict["cov_method"],
                                        _obj_function=inputs_dict["obj_function"],
                                        _compounding=inputs_dict["compounding"],
                                        _scrap=False)

    print(cyrptos_instance.portfolio_from_past)

    print(f"\nCurrent optimzed portfolio \n")

    cyrptos_instance.optimize_portfolio(_n_coins=inputs_dict["n_coins"],
                                        _mu_method=inputs_dict["mu_method"],
                                        _cov_method=inputs_dict["cov_method"],
                                        _obj_function=inputs_dict["obj_function"],
                                        _compounding=inputs_dict["compounding"],
                                        _scrap=False)

    print(f"\n{cyrptos_instance.portfolio}")

    return cyrptos_instance


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

    portfolios_1c = run_from_json(inputs_1coins)
