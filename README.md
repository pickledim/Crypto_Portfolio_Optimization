# Cryptos Portfolio Management and Optimization

The Crypto Portfolio Optimization is a tool designed for cryptocurrency data analysis and portfolio optimization. It provides functionalities for scraping historical price and market cap data of cryptocurrencies, performing portfolio optimization, and validating the results.

## Getting Started

To use the CryptoPortfolio, follow the steps below:

1. **Install Dependencies**: Ensure that you have the required Python libraries installed. The class depends on pandas, numpy, and requests. If you don't have these libraries, install them using pip:

```
pip install -r requirements.txt
```

2. **Import the CryptoPortdolio**: Import the `CryptoPortfolio` class from the script that contains the class.

```python
from Crypto_portfolio.src.cryptorama import CryptoPortfolio
```

3. **Initialize the CryptoPortfolio Object**: Create an instance of the CryptoPortfolio class by providing the necessary parameters.

```python
top_hundred = True  # Set to True to consider the top 100 coins, False to consider all cryptocurrencies.
budget = 1000  # Total budget for the portfolio.
n_coins = 10  # Number of coins to consider for portfolio optimization.
save_dir = "/path/to/save/data"  # Directory to save the scraped data.
crypto_portfolio = CryptoPortfolio(top_hundred, budget, n_coins, save_dir)
```

## Functionality

### 1. Scraping Data

#### 1.1 Scrape Historical Price Data

The `get_prices_df()` method scrapes the historical price data of selected coins and creates a DataFrame. This function will save the prices DataFrame to a CSV file for future use.

```python
crypto_portfolio.get_prices_df()
```

#### 1.2 Scrape Market Cap Data

The `get_market_cap_df()` method creates the DataFrame of all the coins' market cap. This function will save the market cap DataFrame to a CSV file for future use.

```python
crypto_portfolio.get_market_cap_df()
```

### 2. Portfolio Optimization

#### 2.1 Validate Portfolio From Past Data

The `validate_from_past()` method performs portfolio optimization based on past data and validates the results. It takes the following parameters:

- `_n_coins`: Number of coins to consider for portfolio optimization.
- `_n_days`: Number of days to consider for past data.
- `_mu_method`: Method for calculating expected returns. Possible values: "mean", "exp", "capm".
- `_cov_method`: Method for calculating covariance. Possible values: "sample", "exp".
- `_obj_function`: Objective function for optimization. Possible values: "quadratic", "sharpe", "min_volat".
- `_compounding`: Boolean flag indicating whether to compound the mean.
- `_scrap`: Boolean flag indicating whether to re-scrape data or use existing data. Default is False.

```python
crypto_portfolio.validate_from_past(_n_coins, _n_days, _mu_method, _cov_method, _obj_function, _compounding, _scrap=False)
```

#### 2.2 Optimize Current Portfolio

The `optimize_portfolio()` method performs portfolio optimization and creates the optimized portfolio DataFrame. It takes the following parameters:

- `_n_coins`: Number of coins to consider for portfolio optimization.
- `_mu_method`: Method for calculating expected returns. Possible values: "mean", "exp", "capm".
- `_cov_method`: Method for calculating covariance. Possible values: "sample", "exp".
- `_obj_function`: Objective function for optimization. Possible values: "quadratic", "sharpe", "min_volat".
- `_compounding`: Boolean flag indicating whether to compound the mean.
- `_scrap`: Boolean flag indicating whether to re-scrape data or use existing data. Default is False.

```python
crypto_portfolio.optimize_portfolio(_n_coins, _mu_method, _cov_method, _obj_function, _compounding=False, _scrap=False)
```

## Example Usage

Here is an example of how to use the Cryptos class:

```python
from Crypto_portfolio.src.cryptorama import CryptoPortfolio

top_hundred = True
budget = 1000
n_coins = 10
save_dir = "/path/to/save/data"
crypto_portfolio = CryptoPortfolio(top_hundred, budget, n_coins, save_dir)

# Scrape historical price and market cap data
crypto_portfolio.get_prices_df()
crypto_portfolio.get_market_cap_df()

# Validate portfolio from past data
n_days = 365
mu_method = "exp"
cov_method = "sample"
obj_function = "quadratic"
compounding = True
crypto_portfolio.validate_from_past(n_coins, n_days, mu_method, cov_method, obj_function, compounding)

# Optimize current portfolio
crypto_portfolio.optimize_portfolio(n_coins, mu_method, cov_method, obj_function, compounding)
```

The Cryptos class simplifies cryptocurrency data analysis and portfolio optimization, making it easier to manage your crypto investments effectively. Happy investing!