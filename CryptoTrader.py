#!/usr/bin/env python
"""
================ GDAX Algorithmic Cryptocurrency Trader ================

 An algorithmic trader for the GDAX Cryptocurrency exchange. 

 Author: Gerardo Bledt
 GitHub: gbledt
 Version: 0.1
 
 TODO:
	- Create the trade signal analyzer algorithm
	- Make the main loop modular
	- Fully integrate the CryptoCoin Class


"""
__version__ = '0.1'
__author__ = 'Gerardo Bledt'

# The required imports
import gdax
import sys, os
import time
import datetime
import os
import numpy as np
import pylab as pl
import matplotlib.dates as mdates
import matplotlib.pyplot as plt
from matplotlib.finance import candlestick2_ohlc as ohlc
from matplotlib.finance import candlestick_ohlc
import matplotlib.ticker as mticker
from TextColors import TextColors
from CryptoCoin import CryptoCoin
import pandas as pd

# Global variables

# Name of the file containing the API key
FILE_NAME = "gdax_api_keys";  

# Index numbers for the different account wallets
i_USD = 0;
i_BTC = 1;
i_LTC = 2;
i_ETH = 3;
i_BCH = 4;

# List holding the indices of active accounts
TRADE_ACTIVE = False#True
TRADE_ACTIVE_CRYPTO = [True,True,True,True]#[False,False,False]
ACTIVE_CRYPTOCURRENCIES = [i_BTC,i_LTC,i_ETH,i_BCH];
NUM_ACTIVE_CRYPTO = len(ACTIVE_CRYPTOCURRENCIES)
ACTIVE_STRATEGIES = [0,2,3]

# Loop control parameters
LOOP_FREQUENCY = 1/float(300);
LOOP_RATE = 1/LOOP_FREQUENCY;
LOOP_ITERATIONS = 100;
fail_loop_counter = 0

# Candlestick parameters 
TIME_SLICE = 3600#86400#3600;#86400;  # in seconds
CANDLE_WINDOW = 100;
PLOT_WINDOW = [[] for i in range(NUM_ACTIVE_CRYPTO)];

print(PLOT_WINDOW)

# Simple Moving average parameters
SMA = [5,10,20]
PLOT_SMA = True
COLORS_SMA = ['white','yellow','orange','red']

# Exponential Moving average parameters
EMA = [2,3,12,26]
PLOT_EMA = False
COLORS_EMA = ['white','yellow','orange','red']

# Order tracking
buy_order_id = [[] for i in range(NUM_ACTIVE_CRYPTO)];
sell_order_id = [[] for i in range(NUM_ACTIVE_CRYPTO)];

# Derivative plot parameters
COLORS_DERIV = ['red','red','red']

# Plotting 
INITIALIZE_CANDLE_PLOT = [False,False,False]
INITIALIZE_DERIV_PLOT = [False,False,False]
COLOR_SCHEME = 1
PLOT_COLOR_SCHEME = ['white','black']
PLOT_COLOR_SCHEME_SECONDARY = ['black','white']

"""
=============================== Methods ================================
"""
def PrintHeader():
	""" Prints a header during initialization with overall information 
	about the software.
	"""
	# Clear the terminal
	os.system('clear')
	
	# Basic information print out during initialization
	print ('\n\n' + TextColors.GREEN + 
	'%% ==================================================== %%'
	'\n\n' + '          GDAX Algorithmic Cryptocurrency Trader'
	'\n\n' + '                     Author: gbledt'
	'\n' +   '                      Version: 0.1'
	'\n' +   '            Date: ' + 
	datetime.datetime.now().isoformat() + '\n\n'
	'%% ==================================================== %%\n\n'
	+ TextColors.RESET)


def InstantiateAuthClient(f_name):
	""" Creates an instance of the 
	"""
	print (TextColors.GREEN + 'Parsing GDAX API key information...\n\n')
	
	# Get the account API key info from the stored file
	with open(f_name) as f:
		api_info = f.readlines();
	api_info = [x.strip() for x in api_info] 
		
	# Parse the account info
	key = api_info[0];
	b64secret = api_info[1];
	passphrase = api_info[2];
	
	# Print account API info 
	print ('Initializing an Auth Client from ' + f_name + 
		' with key:\n    ' + key + '\n\n' + TextColors.RESET)
		
	# Instantiate the authenticated client to the account
	return gdax.AuthenticatedClient(key, b64secret, passphrase)


def PrintPortfolioInfo(portfolio):
	""" Prints the basic account info for all of the user's active 
	accounts. Also finds the total value for the portfolio in USD.
	"""
	# Begin account printing
	print (TextColors.GREEN + 
		'\n%% ==================================================== %%\n\n'
		+ 'Retrieving all account information from GDAX...\n\n')
	
	# Find and print the current time of query
	current_time = auth_client.get_time().get('iso')
	print ('Account portfolio information at time: \n    ' + 
		current_time + '\n')
	
	# Initialize the total portfolio
	portfolio_value = 0;
	
	# Iterate over all accounts
	for a in portfolio:
		
		# Get the type of currency of the current account
		currency_wallet = a.get(u'currency')
		
		# Get the balance in the currency
		balance = float(a.get(u'balance'));
		
		# Get the amount in order holds
		holds = float(a.get(u'hold'));
		
		# Get the balance in the currency
		available_balance = balance - holds;
		
		# Get the current conversion rate to USD
		if currency_wallet != 'USD':
			currency_ticker = None;
			while (currency_ticker is None) or ('message' in currency_ticker):
				currency_ticker = auth_client.get_product_ticker(product_id=currency_wallet + '-USD');
			conversion_to_USD = float(currency_ticker.get(u'price'));
		else:
			conversion_to_USD = 1;
		
		# Convert the currency into USD
		value_USD = conversion_to_USD*balance
		
		# Sum the currency value to the portfolio
		portfolio_value += value_USD
		
		# Print the currency wallet information
		print (currency_wallet + ' wallet:\n' + 
		'    Balance: ' + str(balance) + '\n' + 
		'    Order Holds: ' + str(holds) + '\n' + 
		'    Available: ' + str(available_balance) + '\n' + 
		'    Price: ' + str(conversion_to_USD) + '\n' + 
		'    USD Conversion:' + str(value_USD) + '\n\n')
	
	# Print the total portfolio value in USD
	print ('Total portfolio value in USD: $' + str(portfolio_value) + '\n\n')
	
	# End account printing
	print (TextColors.RESET)
	
	
def PrintProgramInfo(portfolio):
	
	# Begin program printing
	print (TextColors.GREEN + 
		'%% ==================================================== %%\n\n'
		+ 'Program information:\n')
	print('Cryptocurrencies active for trading: ')
	for p in portfolio[1:]:
		print('    ' + p.get(u'currency'))
	
	print('\nLoop Iterations: ' + str(LOOP_ITERATIONS))
	print('Loop Frequency: ' + str(round(LOOP_FREQUENCY,4)) + 'Hz')
	print('Loop Rate: ' + str(LOOP_RATE) + 's')
	
	# End program printing
	print ('\nProgram will begin...' + TextColors.RESET)


def PrintIterStatistics():
	""" Prints statistics about the current iteration
	"""
	return True


def FailureCatch(fail_loop_count, err):		
	""" A failure has occurred, these happen likely due to API's 
	request to the database returning bad data
	"""
	print (TextColors.RED
		+ '\n\n'
		+ '*********************************\n' 
		+ '*             ERROR             *\n'
		+ '*********************************\n')
	print('Error: '+ err[0].message + '\n'
		+ str(err[1])
		+ '\nIn file ' + str(err[2]) 
		+ ' on line ' + str(err[3])
		+ '\n\n')
	print(TextColors.RESET)
		
	# Break out of the program if error persists
	if (fail_loop_count >= 10):
		print (TextColors.RED
			+ '\n\n'
			+ '********************************\n' 
			+ '*      EXCEEDED FAIL LIMIT      *\n'
			+ '*       EXITTING PROGRAM!       *\n'
			+ '*********************************\n\n' + TextColors.RESET)
		return True
	else:
		# Sleep for 5s to give time for database to update
		time.sleep(5)
		return False
	
	
def CalcSMA(values,window):
	""" Calculates a Simple Moving Average over the given window
	"""
	weigths = np.repeat(1.0, window)/window
	smas = np.convolve(values, weigths, 'valid')
	smas = np.insert(smas,0,np.repeat(smas[0], len(values)-len(smas)))
	return smas # as a numpy array
    
    
def CalcEMA(values, window):
	""" Calculates an Exponantial Moving Average over the given window
	"""
	weights = np.exp(np.linspace(-1., 0., window))
	weights /= weights.sum()
	a = np.convolve(values, weights, mode='full')[:len(values)]
	a[:window] = a[window]
	return a
	
	
def CalcDerivativeFixedX(x, y, filter_length=1):
	for k in range(0,filter_length):
		dydx = np.diff(y)/x
		dydx0 = 5;
	return np.insert(dydx,0,dydx[0])
	
		
	
def GetCandles(time_slice=60):
	""" Retrieves the candlestick data from the historical data over a 
	certain range. The width of the candle is in seconds and defaulted 
	to 60s, but can be overwritten.
	"""
	# Get a the ISO times for the window
	start_time = (datetime.datetime.utcnow() - datetime.timedelta(seconds=30*time_slice)).isoformat()
	current_time = datetime.datetime.utcnow().isoformat()
	
	# Get the candles for the window at every minute
	candle_data = []
	candle_try_count = 0
	while (len(candle_data) < CANDLE_WINDOW) or ('message' in candle_data):
		candle_try_count += 1
		candle_data = auth_client.get_product_historic_rates(product_id=coin.currency_wallet + 
			'-USD', start=start_time, end=current_time, granularity=time_slice)
			
		if (len(candle_data) < CANDLE_WINDOW) or ('message' in candle_data):
			if 'message' in candle_data:
				print(TextColors.RED + 'ERROR: ' + 
					candle_data.get(u'message') + TextColors.RESET);
			time.sleep(0.5)
		if candle_try_count >= 10:
			break
	
	# Output the length to plot if the data is less than the window
	if (len(candle_data) < CANDLE_WINDOW):
		plot_window = len(candle_data)
		active_crypto = False
		print(TextColors.RED + 'Error: recieved data incorrect length\n' 
			+ 'Inactivating trades for ' + coin.currency_wallet + TextColors.RESET)
	else:
		plot_window = CANDLE_WINDOW
		active_crypto = True
		
	return candle_data, plot_window, active_crypto
	
		
"""
============================= Trade Script =============================
"""
# Some initialization information printing
PrintHeader();

# Create an instance of the authenticated client with the API key
auth_client = InstantiateAuthClient(FILE_NAME);

# Get the account info from the client
accounts = auth_client.get_accounts()

# Print the current account info
PrintPortfolioInfo(accounts);

# Print Program info
PrintProgramInfo(accounts)

# Initialize CryptoSignal objects
crypto_coin_list = []
i_crypto = 0
for a in accounts:
	if a.get(u'currency') != 'USD':
		# Initialize a new coin
		coin = CryptoCoin(account=a, currency_wallet=a.get(u'currency'), i_crypto=i_crypto)
		
		# Initialize all of the trade strategies for the coin
		coin.InitializeTradeStrategies(ACTIVE_STRATEGIES)
	
		# Add the new coin object to the list
		crypto_coin_list.append(coin)
		i_crypto +=  1
	
# Iterate the script for as many iterations as required
for k in range(0,LOOP_ITERATIONS):
	try:
		# Print the current account info
		PrintPortfolioInfo(accounts);
		
		# Print loop iteration header 
		print('\n\n%% ==================================================== %%'
			'\n\nIteration ' + str(k) + ': ' + 
			auth_client.get_time().get('iso'))
		
		# Initialize all cryptos to actively trade
		TRADE_ACTIVE_CRYPTO = [True,True,True,True]
		
		# Clear all orders for the crypto first
		if TRADE_ACTIVE:
			resp_cancel = auth_client.cancel_all(product_id=coin.currency_wallet)
		
		# Iterate over all crypto wallets
		for coin in crypto_coin_list:
			
			# Print the current wallet
			print('\nAnalyzing ' + coin.currency_wallet + '...')
			
			# Get the current ticker for the wallet
			ticker_k = None;
			while (ticker_k is None) or ('message' in ticker_k):
				ticker_k = auth_client.get_product_ticker(product_id=coin.currency_wallet + '-USD');
			
			# Pack all of the signals
			coin.SetTicker(ticker=ticker_k)
			
			# Print the current price
			print('Current price of ' + coin.currency_wallet + ' in USD is $' + str(round(coin.price,2)))
			
			# Get the candles for the chosen time slice
			print('Retrieving candlestick data...')
			candles, PLOT_WINDOW[coin.i_crypto], TRADE_ACTIVE_CRYPTO[coin.i_crypto] = GetCandles(TIME_SLICE);
			
			# Pack all of the signals
			coin.SetCandleData(candles=candles)
			
			# Analyse the signals with SMA
			coin.AnalyzeSMA(SMA)
				
			# Calculate the trading signals
			print('Calculating trade signals...')
			coin.TradeSignalStrategy(auth_client)
			
			# Plot the candles if it is asked for
			coin.PlotCandles(TIME_SLICE)
			
			# Plot the derivatives if it is asked for
			coin.PlotDerivatives()
		
		# Prints statistics about the current iteration
		PrintIterStatistics()
		
		# Sleep at the given loop rate
		time.sleep(LOOP_RATE)
		
		# Reset the loop failure count after a successful run
		fail_loop_counter = 0;
		
	except Exception as e:  
	  
		# Grab the system info about the failure
		exc_type, exc_obj, exc_tb = sys.exc_info()
		fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
		e_list = [e, exc_type, fname, exc_tb.tb_lineno]
	
		# Increment the loop failure counter
		fail_loop_counter += 1
		
		# Run the failure catch method and exit if loop counter is high
		if FailureCatch(fail_loop_counter, e_list):
			break

# Wait for user to quit the program
RUNNING = True
while RUNNING:
	running_query = raw_input(TextColors.YELLOW + 
		'\nDone with the program (Y/N)?: ' + TextColors.RESET)
	if (running_query == 'Y' or running_query == 'y'):
		RUNNING = False

	
