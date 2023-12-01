from typing import Union, List, Dict
import yfinance as yf


from typing import Union, Dict, List

from typing import Union, Dict, List


def getStockData(ticker: dict[str, str], period: dict[str, str]):
    """
    Fetches historical stock data for the given ticker symbol and time period.

    Parameters:
    ticker (str): The stock ticker symbol.
    period (str): The time period for which historical data is requested (e.g., '1y' for 1 year).

    Returns:
    Union[Dict, Dict]: A dictionary containing either historical data or an error message.
    """
    try:
        # Fetch historical data for the given ticker symbol and period
        stock = yf.Ticker(ticker)
        history_data = stock.history(period=period)

        return {"history_data": history_data}
    except Exception as e:
        # Log the specific error
        return {"error": f"Error fetching historical data for {ticker} with period {period}"}


def getStockPrice(ticker: dict[str, str]) -> dict[str, Union[float, str]]:
    """
    Fetches the latest closing stock price for the given ticker symbol.

    Parameters:
    ticker (str): The stock ticker symbol.

    Returns:
    dict: A dictionary containing either the price or an error message.
    """
    try:
        # Fetch data for the given ticker symbol
        stock = yf.Ticker(ticker)

        # Get the latest closing price
        hist = stock.history(period="1d")
        latest_price = hist['Close'].iloc[-1]
        return {"price": latest_price}
    except Exception as e:
        # Log the specific error
        return {"error": f"Error fetching price for {ticker}"}
