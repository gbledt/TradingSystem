"""
============================ Trade Strategy ============================

 A class that holds information pertaining to the trade strategy and 
 makes use of the given CryptoSignals

 Author: Gerardo Bledt
 GitHub: gbledt
 Version: 0.1
 
 TODO:
	- All of it


"""

import numpy as np
import datetime
from TextColors import TextColors
import pandas as pd


NOMINAL_BUY = 0.01
NOMINAL_SELL = 0.01
NOMINAL_USD_PER_TRADE = 25

TRADE_ACTIVE = False#True
TRADE_ACTIVE_CRYPTO = False#True

class TradeStrategy:
	
	def __init__(self, *args, **kwargs):
		# The index of the strategy being used in the object
		if 'strategy' in kwargs:
			self.strategy = kwargs.get('strategy')

	def LinkAccount(self, account):
		""" Links an account to the TradingStrategy object
		"""
		self.account = account


	def CancelOrder(order):
		
		open_orders.remove(order)


	def TradeSignalStrategy(self, auth_client, coin):
		""" Decides which trading strategy is used to generate buy or 
		sell trade signals.
		"""
		
		# Choose the correct strategy to use
		if (self.strategy == 0):
			# SMA Golden Cross strategy
			print('\n SMA Golden Cross Strategy:')
			strategy_results = self.SMAGoldenCross(coin)
			
		elif (self.strategy == 1):
			print('\n Derivative Prediction Strategy:')
			strategy_results = self.DerivativePrediction(coin)
			
		elif (self.strategy == 2):
			# Variance Anomaly Trigger strategy
			print('\n Variance Anomaly Trigger Strategy:')
			strategy_results = self.VarianceAnomalyTrigger(coin)
			
		elif (self.strategy == 3):
			# Volume Anomaly Trigger strategy
			print('\n Volume Weighted Variance Anomaly Trigger Strategy:')
			strategy_results = self.VolumeWeightedVarianceAnomalyTrigger(coin)
			
		else:
			print(TextColors.Red + '\n Invalid Strategy!' + TextColors.RESET)
			strategy_results = {'buy_signal': False, 'sell_signal': False, 'buy_price': 0, 'sell_price': 0, 'buy_size': 0, 'sell_size': 0}
		
		# Post the Orders
		resp_post = self.PostOrders(auth_client, coin, strategy_results)

	
	def PostOrders(self, auth_client, coin, strategy_results):
		""" Given the results of the strategy, post the buy and sell 
		orders from the signals
		"""
		if strategy_results.get('buy_signal'):
			# Parse the results
			buy_size = str(round(strategy_results.get('buy_size'),6))
			buy_price = str(min(coin.price-0.10, round(strategy_results.get('buy_price'),2)))
			
			# Print the results of the trading strategy
			print(TextColors.GREEN + '   Buy: ' + TextColors.RESET + buy_size + ' at $' + buy_price)
			
			# Post the buy order
			if (TRADE_ACTIVE_CRYPTO):
				resp = auth_client.buy(price=buy_price, # USD
					size=buy_size, # Coin
					product_id=(coin.currency_wallet + '-USD'))
				
				# Print the result
				if 'message' in resp:
					print(TextColors.RED + '   ERROR: Failed to post\n    ' + 
						resp.get(u'message') + TextColors.RESET);
				else:
					print(TextColors.GREEN + '   SUCCESS!' + TextColors.RESET)
			else:
				resp = {'message': 'No trade was posted'}
				print(TextColors.YELLOW + '   Trading for ' + coin.currency_wallet + ' is inactive' + TextColors.RESET)
				
		if strategy_results.get('sell_signal'):
			# Parse the results
			sell_size = str(round(strategy_results.get('sell_size'),6))
			sell_price = str(max(coin.price+0.10, round(strategy_results.get('sell_price'),2)))
			
			# Print the results of the trading strategy
			print(TextColors.RED + '   Sell: ' + TextColors.RESET + sell_size + ' at $' + sell_price)
			
			# Post orders for active cryptos
			if (TRADE_ACTIVE_CRYPTO):
				# Post the sell order
				resp = auth_client.sell(price=sell_price, #USD
					size=sell_size, #BTC
					product_id=(coin.currency_wallet + '-USD'))
					
				# Print the result
				if 'message' in resp:
					print(TextColors.RED + '   ERROR: Failed to post\n    ' + 
						resp.get(u'message') + TextColors.RESET);
				else:
					print(TextColors.GREEN + '   SUCCESS!' + TextColors.RESET)
			else:
				resp = {'message': 'No trade was posted'}
				print(TextColors.YELLOW + '   Trading for ' + coin.currency_wallet + ' is inactive' + TextColors.RESET)
				
		if not strategy_results.get('buy_signal') and not strategy_results.get('sell_signal'):
			# Manufacture a response 
			resp = {'message': 'No trade was posted'}
			
			# Print that no signal will be posted
			print(TextColors.YELLOW + '   No trade signals calculated' + TextColors.RESET)
		
		return resp


	"""
	========================= Trade Strategies =========================
	"""
	def SMAGoldenCross(self, coin):
		# Timestep
		t = 1
		
		buy_sig = False
		sell_sig = False
		buy_size = NOMINAL_BUY
		sell_size = NOMINAL_SELL
		
		# Find the current values of the SMAs
		fast_SMA = coin.SMA_vec[0][-1]
		medium_SMA = coin.SMA_vec[1][-1]
		slow_SMA = coin.SMA_vec[2][-1]
		
		# Buy signal when shorter period SMAs are greater
		if (fast_SMA > medium_SMA and medium_SMA > slow_SMA):
			buy_sig = True
		else:
			buy_sign = False
				
		# Sell signal when shorter period SMAs are greater
		if (fast_SMA <= medium_SMA and medium_SMA <= slow_SMA):
			sell_sig = True
		else:
			sell_sig = False
		
		# Use the current dynamics to predict a price
		predicted_close = coin.price #+ t*coin.dSMAdt_vec[0][-1] + t**2/2*coin.ddSMAddt_vec[0][-1]/2
		
		# Price to set the buy bids
		buy_price = medium_SMA
		
		# Price to set the sell bids
		sell_price = medium_SMA
		
		buy_size = NOMINAL_USD_PER_TRADE/buy_price
		sell_size = NOMINAL_USD_PER_TRADE/sell_price
		
		# return the boolean signaling if you should buy or sell the crypto	
		return{'buy_signal': buy_sig, 'sell_signal': sell_sig, 'buy_price': buy_price, 'sell_price': sell_price, 'buy_size': buy_size, 'sell_size': sell_size}
	

	def DerivativePrediction(self, coin):
		buy_sig = False
		sell_sig = False
		buy_size = 0
		sell_size = 0
		buy_price = 0
		sell_price = 0
		
		# return the boolean signaling if you should buy or sell the crypto
		return {'buy_signal': buy_sig, 'sell_signal': sell_sig, 'buy_price': buy_price, 'sell_price': sell_price, 'buy_size': buy_size, 'sell_size': sell_size}	
	
	
	def VarianceAnomalyTrigger(self, coin):
		# Timestep
		t = 1
		
		# Constantly place buy and sell bids hoping to catch random price fluctuations
		buy_sig = True
		sell_sig = True
		buy_size = NOMINAL_BUY
		sell_size = NOMINAL_SELL
		
		# Find the current values of the SMAs
		sigma = np.std(np.array(coin.H_vec)-np.array(coin.L_vec))
		
		# Use the current dynamics to predict a price
		predicted_close = coin.price #+ t*coin.dSMAdt_vec[0][-1] + t**2/2*coin.ddSMAddt_vec[0][-1]/2
		
		# Price to set the buy bids
		buy_price = predicted_close - 3*sigma
		
		# Price to set the sell bids
		sell_price = predicted_close + 3*sigma
		
		buy_size = NOMINAL_USD_PER_TRADE/buy_price
		sell_size = NOMINAL_USD_PER_TRADE/sell_price
		
		# return the boolean signaling if you should buy or sell the crypto		
		return{'buy_signal': buy_sig, 'sell_signal': sell_sig, 'buy_price': buy_price, 'sell_price': sell_price, 'buy_size': buy_size, 'sell_size': sell_size}
		
		
	def VolumeWeightedVarianceAnomalyTrigger(self, coin):
		# Timestep
		t = 1
		
		# Constantly place buy and sell bids hoping to catch random price fluctuations
		buy_sig = True
		sell_sig = True
		buy_size = 10*NOMINAL_BUY
		sell_size = 10*NOMINAL_SELL
		
		# Find the current values of the SMAs
		sigma = np.std(np.multiply(np.array(coin.H_vec)-np.array(coin.L_vec),coin.V_vec/np.mean(coin.V_vec))) 
		
		# Use the current dynamics to predict a price
		predicted_close = coin.SMA_vec[0][-1]#+ t*coin.dSMAdt_vec[0][-1] + t**2/2*coin.ddSMAddt_vec[0][-1]/2
		
		# Price to set the buy bids
		buy_price = predicted_close - 3*sigma
		
		# Price to set the sell bids
		sell_price = predicted_close + 3*sigma
		
		buy_size = 3*NOMINAL_USD_PER_TRADE/buy_price
		sell_size = 3*NOMINAL_USD_PER_TRADE/sell_price
		
		# return the boolean signaling if you should buy or sell the crypto		
		return {'buy_signal': buy_sig, 'sell_signal': sell_sig, 'buy_price': buy_price, 'sell_price': sell_price, 'buy_size': buy_size, 'sell_size': sell_size}
