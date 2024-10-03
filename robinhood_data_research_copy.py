# -*- coding: utf-8 -*-

import robin_stocks.robinhood as r
# from r.globals import LOGGED_IN, SESSION, OUTPUT
import pyotp
import time
import requests
import json
import pandas as pd
from datetime import datetime
import yfinance as yf

#  add logging so there's more information about what's happening, esp when there's an error
import logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')


def symbol_for_stock(url, max_retries=3, retry_delay=2):
    """Fetch the stock symbol from a given URL with retry logic.

    Args:
        url (str): The URL to fetch the stock symbol from.
        max_retries (int): Maximum number of retries in case of a request failure.
        retry_delay (int): Delay in seconds between retries.

    Returns:
        str or None: The stock symbol if fetched successfully, None otherwise.
    """
    for attempt in range(max_retries):
        try:
            response = requests.get(url)
            if response.status_code == 200:
                json_data = response.json()
                return json_data.get('symbol')
            else:
                logging.warning(f"Attempt {attempt+1}: Failed to fetch symbol from {url}, status code {response.status_code}")
        except requests.RequestException as e:
            logging.warning(f"Attempt {attempt+1}: Request to {url} resulted in an exception: {e}")
        except ValueError as e:
            logging.warning(f"Attempt {attempt+1}: Decoding JSON for URL {url} failed: {e}")

        # Wait for retry_delay seconds before the next retry
        time.sleep(retry_delay)

    logging.error(f"Failed to fetch symbol from {url} after {max_retries} attempts")
    return None


# function to convert a dollar value to currency format
def format_currency(value):
    return "${:,.2f}".format(value)


# Function to get raw dataset with all filled orders
def get_all_orders():

  filled_orders = []
  filled_orders.append(['symbol','latest_price', 'order_type','quantity','unit_price','total_price','fees','timestamp'])

  stocks_etf = r.orders.get_all_stock_orders()
  stock_prices = {}
  for order in stocks_etf:
    if order['executions'] != []:
      order_details = []

      # Fetch the stock symbol from the URL
      sym = symbol_for_stock(order['instrument'])
      if sym is None:
        order_details.append('Symbol Unavailable')
      else:
        order_details.append(sym)

      # Fetch the latest price for the stock
      try:
        price = stock_prices[symbol_for_stock(order['instrument'])]
      except:
        try:
          price = r.stocks.get_latest_price(symbol_for_stock(order['instrument']), includeExtendedHours=True)[0]
        except:
          price = 0
        stock_prices[symbol_for_stock(order['instrument'])] = price
      
      # Append the stock details to the order
      order_details.append(price)
      order_details.append(order['side'])
      order_details.append(order['cumulative_quantity'])
      order_details.append(order['average_price'])
      order_details.append(order['executed_notional']['amount'])
      order_details.append(order['fees'])
      order_details.append(order['updated_at'])
      filled_orders.append(order_details)

  crypto = r.orders.get_all_crypto_orders()
  crypto_prices = {}
  for order in crypto:
    if order['executions'] != []:
      order_details = []
      order_details.append(order['currency_code'])
      try:
        price = crypto_prices[order['currency_code']]
      except:
        price = r.crypto.get_crypto_quote(order['currency_code'])['mark_price']
        crypto_prices[order['currency_code']] = price
      order_details.append(price)
      order_details.append(order['side'])
      order_details.append(order['cumulative_quantity'])
      order_details.append(order['average_price'])
      order_details.append(order['rounded_executed_notional'])
      order_details.append(0)
      order_details.append(order['updated_at'])
      filled_orders.append(order_details)

  # Converting to dataframe for analysis
  order_data = pd.DataFrame(filled_orders[1:], columns=filled_orders[0])

  # Ensure data types are correct
  order_data['timestamp'] = pd.to_datetime(order_data['timestamp'],utc=True)
  order_data = order_data.sort_values(by='timestamp', ascending=True)
  order_data[['quantity', 'unit_price', 'total_price', 'fees', 'latest_price']] = order_data[['quantity', 'unit_price', 'total_price', 'fees', 'latest_price']].astype(float)

  return order_data

# Function to adjust for stock splits
def adjust_for_stock_splits(data):
  adjusted_data = data.copy()
  symbols = adjusted_data['symbol'].unique()

  try:
    for symbol in symbols:
      stock = yf.Ticker(symbol)
      splits = stock.splits

      if splits.empty:
         continue
      
      for split_date, split_ratio in splits.items():
          # Transactions before the split date are adjusted
          transactions_to_adjust = adjusted_data[(adjusted_data['symbol'] == symbol) & (adjusted_data['timestamp'] < split_date)]
          # transactions_after = adjusted_data[(adjusted_data['symbol'] == symbol) & (adjusted_data['timestamp'] >= split_date)]
          adjusted_data.loc[transactions_to_adjust.index, 'quantity'] *= split_ratio
          adjusted_data.loc[transactions_to_adjust.index, 'unit_price'] /= split_ratio

    return adjusted_data
  except AttributeError as e:
    logging.error(f"AttributeError with {symbol}: {e}")
  except Exception as e:
    logging.error(f"Unexpected error with {symbol}: {e}", exc_info=True)
    raise


# Function to filter transactions by user-defined period
# def filter_transactions_by_period(data, start_date, end_date):
#   # Convert strings to datetime
#   start_date = pd.to_datetime(start_date,utc=True)
#   end_date = pd.to_datetime(end_date,utc=True)

#   # Filter data
#   filtered_data = data[(data['timestamp'] >= start_date) & (data['timestamp'] <= end_date)]
#   return filtered_data

# Main analysis function
def perform_investment_analysis(data, start_date=None, end_date=None):

  try: 
    # Initialize the summary table
    summary_table = pd.DataFrame(columns=['symbol', 'quantity_purchased', 'investment_amount', 'quantity_sold', 'return_amount', 'realized_gain_loss', 'unrealized_gain_loss', 'current_position_size'])

    # Adjust data for stock splits
    data = adjust_for_stock_splits(data)

    # If end date, filter dataframe for transactions before the end date
    if end_date:
        data = data[data['timestamp'] <= pd.to_datetime(end_date, utc=True)]
    

    # If start date, create two dataframes: one for transactions before the start date and one for transactions after the start date
    if start_date:
      before_start_date = data[data['timestamp'] < pd.to_datetime(start_date, utc=True)]
      after_start_date = data[data['timestamp'] >= pd.to_datetime(start_date, utc=True)]
    
    # run analysis if both before and after start date dataframes exist and are not empty
    if 'before_start_date' in locals() and 'after_start_date' in locals() and not before_start_date.empty and not after_start_date.empty:
      #  iterate over after_start_date data symbols and identify if there are buy orders, sell orders or both for each symbol
      for symbol in after_start_date['symbol'].unique():
        # Track realized gains/losses separately for each year
        realized_gains_losses = {}

        after_symbol_data = after_start_date[after_start_date['symbol'] == symbol]
        after_buy_orders = after_symbol_data[after_symbol_data['order_type'] == 'buy'].copy()
        after_sell_orders = after_symbol_data[after_symbol_data['order_type'] == 'sell'].copy()
        
        #  set the quantity purchased, investment amount, quantity sold and return amount to sum for each respective column minus fees (for investment amount and return amount)
        total_quantity_purchased = after_buy_orders['quantity'].sum()
        total_investment_amount = after_buy_orders['total_price'].sum() - after_buy_orders['fees'].sum()
        total_quantity_sold = after_sell_orders['quantity'].sum()
        total_return_amount = after_sell_orders['total_price'].sum() - after_sell_orders['fees'].sum()
        realized_gain_loss = 0

        # if there are sell orders after the start date, run FIFO calculation
        if not after_sell_orders.empty:
          before_symbol_data = before_start_date[before_start_date['symbol'] == symbol]
          before_buy_orders = before_symbol_data[before_symbol_data['order_type'] == 'buy'].copy()
          before_sell_orders = before_symbol_data[before_symbol_data['order_type'] == 'sell'].copy()

          # Run FIFO calculation for before start date orders
          for index, before_sell_order in before_sell_orders.iterrows():
            before_sell_quantity = before_sell_order['quantity']

            while before_sell_quantity > 0 and not before_buy_orders[before_buy_orders['quantity'] > 0].empty:
              before_buy_order = before_buy_orders[before_buy_orders['quantity'] > 0].iloc[0]
              before_buy_quantity = before_buy_order['quantity']
              before_quantity_to_sell = min(before_sell_quantity, before_buy_quantity)
              before_sell_quantity -= before_quantity_to_sell
              before_buy_orders.at[before_buy_order.name, 'quantity'] -= before_quantity_to_sell
          
          #  Run FIFO calculation with updated before transaction data and after transaction data to determine realized gains/losses
          for index, sell_order in after_sell_orders.iterrows():
            fiscal_year = sell_order['timestamp'].year
            sell_quantity = sell_order['quantity']

            while sell_quantity > 0 and (not before_buy_orders[before_buy_orders['quantity'] > 0].empty or not after_buy_orders[after_buy_orders['quantity'] > 0].empty):
                # update realized gains/losses for each fiscal year by first checking for before buy orders and then after buy orders
                if not before_buy_orders[before_buy_orders['quantity'] > 0].empty:
                  buy_order = before_buy_orders[before_buy_orders['quantity'] > 0].iloc[0]
                else:
                  buy_order = after_buy_orders[after_buy_orders['quantity'] > 0].iloc[0]

                buy_quantity = buy_order['quantity']
                quantity_to_sell = min(sell_quantity, buy_quantity)
                realized_gain_loss = (sell_order['unit_price'] - buy_order['unit_price']) * quantity_to_sell

                # Update realized gains/losses by fiscal year
                if fiscal_year not in realized_gains_losses:
                    realized_gains_losses[fiscal_year] = realized_gain_loss
                else:
                    realized_gains_losses[fiscal_year] += realized_gain_loss

                sell_quantity -= quantity_to_sell

                # Update the quantity in the original DataFrame
                if not before_buy_orders[before_buy_orders['quantity'] > 0].empty:
                  before_buy_orders.at[buy_order.name, 'quantity'] -= quantity_to_sell
                else:
                  after_buy_orders.at[buy_order.name, 'quantity'] -= quantity_to_sell
          

        # Calculate unrealized returns only for those symbols that were bought in the user defined period
        unrealized_gain_loss = 0
        current_position_size = 0
        for index, after_buy_order in after_buy_orders.iterrows():
            if after_buy_order['quantity'] > 0:  # Only unsold shares are considered
                current_price_per_unit = after_symbol_data.iloc[-1]['latest_price']
                buy_price_per_unit = after_buy_order['unit_price']
                unrealized_gain_loss += (current_price_per_unit - buy_price_per_unit) * after_buy_order['quantity']
                current_position_size += current_price_per_unit * after_buy_order['quantity']
    
        # Append corrected data to the summary table
        summary_table = pd.concat([summary_table, pd.DataFrame({
            'symbol': [symbol],
            'quantity_purchased': [total_quantity_purchased],
            'investment_amount': [total_investment_amount],
            'quantity_sold': [total_quantity_sold],
            'return_amount': [total_return_amount],
            'realized_gain_loss': [realized_gains_losses],
            'unrealized_gain_loss': [unrealized_gain_loss],
            'current_position_size': [current_position_size]
        })], ignore_index=True)
    
    else:
    # Filter data for the user-defined period
    # if not start_date: start_date = '2013-04-18'
    # if not end_date: end_date = datetime.now()
    # data = filter_transactions_by_period(data, start_date, end_date)

    # Re-process each symbol with corrected logic
      for symbol in data['symbol'].unique():

        # Track realized gains/losses separately for each year
        realized_gains_losses = {}

        symbol_data = data[data['symbol'] == symbol]
        buy_orders = symbol_data[symbol_data['order_type'] == 'buy'].copy()
        sell_orders = symbol_data[symbol_data['order_type'] == 'sell'].copy()

        # Reset trackers for summary data
        total_quantity_purchased = buy_orders['quantity'].sum()
        total_investment_amount = buy_orders['total_price'].sum() - buy_orders['fees'].sum()
        total_quantity_sold = sell_orders['quantity'].sum()
        total_return_amount = sell_orders['total_price'].sum() - sell_orders['fees'].sum()
        realized_gain_loss = 0


        # Adjust FIFO calculation for realized gains/losses to handle no corresponding buy orders
        for index, sell_order in sell_orders.iterrows():
            fiscal_year = sell_order['timestamp'].year
            sell_quantity = sell_order['quantity']

            while sell_quantity > 0 and not buy_orders[buy_orders['quantity'] > 0].empty:
                buy_order = buy_orders[buy_orders['quantity'] > 0].iloc[0]
                buy_quantity = buy_order['quantity']

                quantity_to_sell = min(sell_quantity, buy_quantity)
                realized_gain_loss = (sell_order['unit_price'] - buy_order['unit_price']) * quantity_to_sell

                # Update realized gains/losses by fiscal year
                if fiscal_year not in realized_gains_losses:
                    realized_gains_losses[fiscal_year] = realized_gain_loss
                else:
                    realized_gains_losses[fiscal_year] += realized_gain_loss

                sell_quantity -= quantity_to_sell
                buy_orders.at[buy_order.name, 'quantity'] -= quantity_to_sell

        # Adjust calculation for unrealized gains/losses
        unrealized_gain_loss = 0
        current_position_size = 0
        for index, buy_order in buy_orders.iterrows():
            if buy_order['quantity'] > 0:  # Only unsold shares are considered
                current_price_per_unit = symbol_data.iloc[-1]['latest_price']
                buy_price_per_unit = buy_order['unit_price']
                unrealized_gain_loss += (current_price_per_unit - buy_price_per_unit) * buy_order['quantity']
                current_position_size += current_price_per_unit * after_buy_order['quantity']

        # Append corrected data to the summary table
        summary_table = pd.concat([summary_table, pd.DataFrame({
            'symbol': [symbol],
            'quantity_purchased': [total_quantity_purchased],
            'investment_amount': [total_investment_amount],
            'quantity_sold': [total_quantity_sold],
            'return_amount': [total_return_amount],
            'realized_gain_loss': [realized_gains_losses],
            'unrealized_gain_loss': [unrealized_gain_loss],
            'current_position_size': [current_position_size]
        })], ignore_index=True)

    # Initialize total portfolio value
    total_portfolio_value = 0

    # Calculate total portfolio value
    total_portfolio_value = summary_table['current_position_size'].sum()

    # Add position size percentage column
    summary_table['position_size_percentage'] = summary_table['current_position_size'] / total_portfolio_value * 100

    
    return summary_table
  
  except Exception as e:
    logging.error("Error in get_all_orders: %s", e, exc_info=True)
    raise


# Function to pull annual realized gains and losses
def annual_realized_summary(df):
  try:
    summary_table = df.copy()

    # Extracting and normalizing the realized_gain_loss column
    realized_gains = pd.json_normalize(summary_table['realized_gain_loss'])

    # Merging the normalized realized gains with the original symbol column
    realized_gains['symbol'] = summary_table['symbol']

    # Melting the DataFrame to have one row per symbol-year pair
    melted_gains = realized_gains.melt(id_vars=['symbol'], var_name='year', value_name='gain_loss').dropna()

    # Summarizing by year
    yearly_summary = melted_gains.groupby('year')['gain_loss'].agg(['sum', 'idxmax', 'idxmin'])
    yearly_summary = yearly_summary.reset_index()
    yearly_summary.columns = ['Year', 'Total Realized Gains', 'Top Gainer', 'Top Loser']

    # Adding symbol information to yearly summary
    yearly_summary['Top Gainer'] = melted_gains.loc[yearly_summary['Top Gainer'], 'symbol'].values
    yearly_summary['Top Loser'] = melted_gains.loc[yearly_summary['Top Loser'], 'symbol'].values

    # Group by year and apply a function to get top 5 gainers or losers
    grouped = melted_gains.groupby('year', as_index=False)

    # For gainers, sort in descending order
    yearly_top_5 = grouped.apply(lambda x: x[x['gain_loss'] > 0].nlargest(5, 'gain_loss')).reset_index(drop=True)
    yearly_top_5 = yearly_top_5.reindex(columns=['year', 'symbol', 'gain_loss'])

    # For losers, sort in ascending order
    yearly_bottom_5 = grouped.apply(lambda x: x[x['gain_loss'] <= 0].nsmallest(5, 'gain_loss')).reset_index(drop=True)
    yearly_bottom_5 = yearly_bottom_5.reindex(columns=['year', 'symbol', 'gain_loss'])

    # All-time metrics
    all_time_total_invested = summary_table['investment_amount'].sum()
    all_time_total_capital_returned = summary_table['return_amount'].sum()
    all_time_unrealized_gains_losses = summary_table['unrealized_gain_loss'].sum()
    all_time_realized_gains_losses = yearly_summary['Total Realized Gains'].sum()

    return yearly_summary, yearly_top_5, yearly_bottom_5, all_time_total_invested, all_time_total_capital_returned, all_time_unrealized_gains_losses, all_time_realized_gains_losses
  
  except Exception as e:
    logging.error("Error in get_all_orders: %s", e, exc_info=True)
    raise


# function to log in to Robinhood
def login(username, password, mfa_code=None):
  try:
    r.authentication.login(username,password,mfa_code=mfa_code,expiresIn=5000, store_session=False)
    return {
        'status': 'success',
        'message': 'Logged in successfully'
    }
  except Exception as e:
    logging.error("Error in login function: %s", e, exc_info=True)
    return {
        'status': 'error',
        'message': str(e)
    }


# Function to log out of Robinhood
def logout():
  try:
    r.authentication.logout()
    return {
        'status': 'success',
        'message': 'Logged out successfully'
    }
  except Exception as e:
    logging.error("Error in logout function: %s", e, exc_info=True)
    return {
        'status': 'error',
        'message': str(e)
    }
  

# Function compiling all previous functions into one
def final_results(start_date=None, end_date=None):
  try:
    data = get_all_orders()
    summary = perform_investment_analysis(data, start_date, end_date)
    summary_annual, top_5, bottom_5, all_time_total_invested, all_time_total_capital_returned, all_time_unrealized_gains_losses, all_time_realized_gains_losses = annual_realized_summary(summary)
    
    # Formatting the data
    summary_annual['Total Realized Gains'] = summary_annual['Total Realized Gains'].apply(format_currency)
    top_5['gain_loss'] = top_5['gain_loss'].apply(format_currency)
    bottom_5['gain_loss'] = bottom_5['gain_loss'].apply(format_currency)
    total_invested = format_currency(all_time_total_invested)
    total_capital_returned = format_currency(all_time_total_capital_returned)
    unrealized_gains_losses = format_currency(all_time_unrealized_gains_losses)
    realized_gains_losses = format_currency(all_time_realized_gains_losses)

    return {
      'status': 'success',
      'message': {
          'summary': summary,
          'summary_annual': summary_annual.to_dict(orient='records'),
          'top_5': top_5.to_dict(orient='records'),
          'bottom_5': bottom_5.to_dict(orient='records'),
          'total_invested': total_invested,
          'total_capital_returned': total_capital_returned,
          'unrealized_gains_losses': unrealized_gains_losses,
          'realized_gains_losses': realized_gains_losses
      }
    }
  
  except Exception as e:
      logging.error("Error in final_results function: %s", e, exc_info=True)
      raise
      return {
          'status': 'error',
          'message': str(e)
      }
