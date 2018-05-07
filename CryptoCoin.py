"""
============================= Crypto Coin ==============================

 A class that holds the gathered candlestick data. Contains methods for 
 analyzing the signals and determining trade signals based on various
 strategies. 

 Author: Gerardo Bledt
 GitHub: gbledt
 Version: 0.1
 
 TODO:
	- Port over the plotting to this class


"""

import numpy as np
import datetime
from TradeStrategy import TradeStrategy
from TextColors import TextColors
import matplotlib.dates as mdates
import matplotlib.pyplot as plt
from matplotlib.finance import candlestick2_ohlc as ohlc
from matplotlib.finance import candlestick_ohlc
import matplotlib.ticker as mticker
import pandas as pd


NUM_ACTIVE_CRYPTO = 4
NOMINAL_BUY = 0.01
NOMINAL_SELL = 0.01
NOMINAL_USD_PER_TRADE = 25

PLOT_SMA = True
PLOT_EMA = False
COLORS_SMA = ['white','yellow','orange','red']
COLORS_EMA = ['white','yellow','orange','red']
# Plotting 
INITIALIZE_CANDLE_PLOT = False
INITIALIZE_DERIV_PLOT = False
COLOR_SCHEME = 1
PLOT_COLOR_SCHEME = ['white','black']
PLOT_COLOR_SCHEME_SECONDARY = ['black','white']
i_BOLL = 2

class CryptoCoin:
	
	def __init__(self, *args, **kwargs):
		""" Initialize the CryptoCoin object with the required 
		information for the account
		"""
		if 'account' in kwargs:
			self.account = kwargs.get('account')
		if 'currency_wallet' in kwargs:
			self.currency_wallet = kwargs.get('currency_wallet')
		if 'i_crypto' in kwargs:
			self.i_crypto = kwargs.get('i_crypto')
			
		self.INITIALIZE_CANDLE_PLOT = False
		self.INITIALIZE_DERIV_PLOT = False
	
	
	"""
	========================= Analysis Methods =========================
	"""
	def SetTicker(self, ticker):
		self.ticker = ticker
		self.price = float(ticker.get(u'price'))
	
	def SetCandleData(self, candles):
		""" Sets new candle data to the object
		"""
		# Set the new candle data
		self.candles = candles
		
		# Initialize all the vectors
		self.time_vec = []
		self.O_vec = []
		self.H_vec = []
		self.L_vec = []
		self.C_vec = []
		self.V_vec = []
		
		# Iterate over all the candles
		for c in reversed(candles):
			
			# Get the timestamps from the data
			self.time_vec.append(datetime.datetime.fromtimestamp(c[0]))
				
			# Parse the candles into OHLCV
			self.O_vec.append(c[3])
			self.H_vec.append(c[2])
			self.L_vec.append(c[1])
			self.C_vec.append(c[4])
			self.V_vec.append(c[5])
			
	
	def CalcSignalDerivatives(self, *args, **kwargs):
		""" Calculate the derivatives of the input signal
		"""
		if 'Open' in kwargs:
			self.dOdt = self.CalcDerivativeFixed(1,self.O_vec)
			self.ddOddt = self.CalcDerivativeFixed(1,self.dOdt)
			
		if 'High' in kwargs:
			self.dHdt = self.CalcDerivativeFixed(1,self.H_vec)
			self.ddHddt = self.CalcDerivativeFixed(1,self.dHdt)
			
		if 'Low' in kwargs:
			self.dLdt = self.CalcDerivativeFixed(1,self.L_vec)
			self.ddLddt = self.CalcDerivativeFixed(1,self.dLdt)
			
		if 'Close' in kwargs:
			self.dCdt = self.CalcDerivativeFixed(1,self.C_vec)
			self.ddCddt = self.CalcDerivativeFixed(1,self.dCdt)
		
		
	def CalcDerivativeFixed(self, x, y):
		""" Calculate a fixed step size derivative
		"""
		dydx = np.diff(y)/x
		return np.insert(dydx,0,dydx[0])
		
		
	def CalcSMA(self, values, window):
		""" Calculates a Simple Moving Average over the given window
		"""
		# Create an equally weighted vector of the correct length
		weigths = np.repeat(1.0, window)/window
		
		# Convolve the values and weigts to create the moving average
		smas = np.convolve(values, weigths, 'valid')
		
		# Repeat the first value to be the same length as the original vector
		smas = np.insert(smas,0, np.repeat(smas[0], len(values)-len(smas)))
		
		# Return the simple moving average
		return smas # as a numpy array
		
	
	def CalcEMA(self, values, window):
		""" Calculates an Exponential Moving Average over the given window
		"""
		weights = np.exp(np.linspace(-1., 0., window))
		weights /= weights.sum()
		a = np.convolve(values, weights, mode='full')[:len(values)]
		a[:window] = a[window]
		return a
			
	
	def CalcBoll(self, SMA, length=30, numsd=2):
		""" returns average, upper band, and lower band"""
		length = SMA[i_BOLL]
		px = pd.DataFrame(data=self.C_vec)
		price = px
		ave = price.rolling(length,center=False).mean()
		sd = price.rolling(length,center=False).std()
		upband = ave + (sd*numsd)
		dnband = ave - (sd*numsd)
		return np.round(ave,3), np.round(upband,3), np.round(dnband,3)
			
			
	def AnalyzeSMA(self, SMA):
		# Initialize the vectors holding the SMA and its derivatives
		SMA_vec = [[] for i in range(len(SMA))]
		dSMAdt_vec = [[] for i in range(len(SMA))]
		ddSMAddt_vec = [[] for i in range(len(SMA))]
		
		# Create simple moving averages for the currency (close data)
		for ma in range(0,len(SMA)):
			SMA_vec[ma] = self.CalcSMA(self.C_vec,SMA[ma])
			dSMAdt_vec[ma] = self.CalcDerivativeFixed(1,SMA_vec[ma])
			ddSMAddt_vec[ma] = self.CalcDerivativeFixed(1,dSMAdt_vec[ma])
		
		# Store the vectors
		self.SMA = SMA
		self.SMA_vec = SMA_vec
		self.dSMAdt_vec = dSMAdt_vec
		self.ddSMAddt_vec = ddSMAddt_vec
		
		# Calculate the Boll bands
		self.BOLL, self.uBOLL, self.lBOLL = self.CalcBoll(SMA)
		
		
	def AnalyzeEMA(self, EMA):
		# Initialize the vectors holding the SMA and its derivatives
		EMA_vec = [[] for i in range(len(EMA))]
		dEMAdt_vec = [[] for i in range(len(EMA))]
		ddEMAddt_vec = [[] for i in range(len(EMA))]
		
		# Create simple moving averages for the currency (close data)
		for ma in range(0,len(EMA)):
			EMA_vec[ma] = self.CalcEMA(self.C_vec,EMA[ma])
			dEMAdt_vec[ma] = self.CalcDerivativeFixed(1,EMA_vec[ma])
			ddEMAddt_vec[ma] = self.CalcDerivativeFixed(1,dEMAdt_vec[ma])
		
		# Store the vectors
		self.EMA = EMA
		self.EMA_vec = EMA_vec
		self.dEMAdt_vec = dEMAdt_vec
		self.ddEMAddt_vec = ddEMAddt_vec
	
	
	def InitializeTradeStrategies(self, ACTIVE_STRATEGIES):
		# Initialize the list of trade strategies
		self.strategy_list = []
		
		# Append all of the TradeStrategy objects
		for strat in ACTIVE_STRATEGIES:
			self.strategy_list.append(TradeStrategy(strategy=strat))
		
	
	def TradeSignalStrategy(self, auth_client):
		""" Decides which trading strategy is used to generate buy or 
		sell trade signals.
		"""
		# Run the all of the trade strategies
		for strategy in self.strategy_list:
			strategy.TradeSignalStrategy(auth_client, self)			
	
	
	"""
	============================= Plotting =============================
	"""
	def FormatPlot(self, fig, ax):
		""" Formats the coloring scheme of the plot. Will later support 
		multiple color schemes that can be chosen.
		"""
		
		# Color the figure with the chosen scheme
		if (COLOR_SCHEME == 0):
			# Light scheme
			ax.spines['bottom'].set_color("black")
			ax.spines['top'].set_color("black")
			ax.spines['left'].set_color("black")
			ax.spines['right'].set_color("black")
			ax.tick_params(axis='y', colors='black')
			ax.tick_params(axis='x', colors='black')
			ax.yaxis.label.set_color("black")
			ax.xaxis.label.set_color("black")
			fig.patch.set_facecolor('white')
		
		elif (COLOR_SCHEME == 1):
			# Dark scheme
			ax.spines['bottom'].set_color("w")
			ax.spines['top'].set_color("w")
			ax.spines['left'].set_color("w")
			ax.spines['right'].set_color("w")
			ax.tick_params(axis='y', colors='w')
			ax.tick_params(axis='x', colors='w')
			ax.yaxis.label.set_color("w")
			ax.xaxis.label.set_color("w")
			fig.patch.set_facecolor('black')
		
		# Format the Figure
		fig.tight_layout()
		
		# Set the initialized plot flag to true
		return True


	def PlotCandles(self, TIME_SLICE, PLOT_WINDOW_i=60):
		""" Plots the data from the candlesticks over the given window
		"""
		# Create the figure
		fig = plt.figure(num='Candlestick Real-Time Plot', figsize=(10, 12.5))
		
		# Set the current crypto to the appropriate subplot axis
		ax_candle = fig.add_subplot(411+self.i_crypto)
		
		# Clear the previous data
		ax_candle.clear()
		
		# Iterate through the available data to create candles
		x = 0
		candle_array = []
		while x < PLOT_WINDOW_i:
			# Set the OHLC candlestick data
			appendLine = mdates.date2num(self.time_vec[-PLOT_WINDOW_i+x]),self.O_vec[-PLOT_WINDOW_i+x],self.H_vec[-PLOT_WINDOW_i+x],self.L_vec[-PLOT_WINDOW_i+x],self.C_vec[-PLOT_WINDOW_i+x],self.V_vec[-PLOT_WINDOW_i+x]
			candle_array.append(appendLine)
			x+=1
		if TIME_SLICE == 3600:
			width = 0.025;
		elif TIME_SLICE == 60:
			width = 0.0005
		elif TIME_SLICE == 300:
			width = 0.0025
		else:
			width = 0.025
		candlestick_ohlc(ax_candle, candle_array, width, colorup='g', colordown='r')
		
		# Format the x axis with the dates
		x_time = self.time_vec[-PLOT_WINDOW_i:]
			
		# Plot the Simple Moving Average
		if (PLOT_SMA):
			for ma in range(0,len(self.SMA)):
				plt.plot(x_time[-len(self.SMA_vec[ma][-PLOT_WINDOW_i:]):], self.SMA_vec[ma][-PLOT_WINDOW_i:],
					COLORS_SMA[ma],linewidth=1)
				
				if (ma == i_BOLL):
					plt.plot(x_time[-len(self.SMA_vec[ma][-PLOT_WINDOW_i:]):], self.BOLL[-PLOT_WINDOW_i:],
						COLORS_SMA[ma],linewidth=1)
					plt.plot(x_time[-len(self.SMA_vec[ma][-PLOT_WINDOW_i:]):], self.uBOLL[-PLOT_WINDOW_i:],
						COLORS_SMA[ma],linewidth=1)
					plt.plot(x_time[-len(self.SMA_vec[ma][-PLOT_WINDOW_i:]):], self.lBOLL[-PLOT_WINDOW_i:],
						COLORS_SMA[ma],linewidth=1)
				
		
		# Plot the Exponential Moving Average
		if (PLOT_EMA):
			for ma in range(0,len(EMA)):
				plt.plot(x_time, self.EMA_vec[ma][-PLOT_WINDOW_i:],
					COLORS_EMA[ma],linewidth=1)	
			
		# Format the x axis tick markers
		ax_candle.xaxis.set_major_locator(mticker.MaxNLocator(20))
		ax_candle.xaxis.set_major_formatter(mdates.DateFormatter('%H:%M:%S'))
		fig.autofmt_xdate()
		
		# Format the plot on initial pass
		if (self.INITIALIZE_CANDLE_PLOT == False):
			self.INITIALIZE_CANDLE_PLOT = self.FormatPlot(fig, ax_candle)
			
		# Format the axes after clear
		ax_candle.grid(True)
		plt.ylabel(self.currency_wallet + ' Price in USD [$]')
		if (self.i_crypto == (NUM_ACTIVE_CRYPTO - 1)):
			plt.xlabel('Date and Time, EST')
		
		# Draw the figure
		ax_candle.patch.set_facecolor(PLOT_COLOR_SCHEME[COLOR_SCHEME])
		ax_candle.grid(color=PLOT_COLOR_SCHEME_SECONDARY[COLOR_SCHEME])
		fig.canvas.draw()
		plt.show(block=False)
			
	
	def PlotDerivatives(self, PLOT_WINDOW_i=60, color_plot='red'):
		""" Plots the close price and its first and second derivatives over 
		the time window
		"""
		fig = plt.figure(num='Price Derivatives',figsize=(10, 12.5))
		
		
		# Format the x axis with the dates
		x = self.time_vec[-PLOT_WINDOW_i:]
		y = self.C_vec
		
		for ma in range(0,len(self.SMA_vec)):
			
			y_filt = self.SMA_vec[ma]
			dydx = self.dSMAdt_vec[ma]
			ddyddx = self.ddSMAddt_vec[ma]
			
			ax = [[] for i in range(3)];
			ax[0] = fig.add_subplot(3,4,1+self.i_crypto)
		
			# Clear the previous data
			if (ma == 0):
				ax[0].clear()
				plt.title(self.currency_wallet + ' Price Data')
				plt.ylabel(self.currency_wallet + ' Price in USD [$]')
			
			ax[0].grid(color=PLOT_COLOR_SCHEME_SECONDARY[COLOR_SCHEME])	
			ax[0].patch.set_facecolor(PLOT_COLOR_SCHEME[COLOR_SCHEME])
			ax[0].grid(color=PLOT_COLOR_SCHEME_SECONDARY[COLOR_SCHEME])
			ax[0].xaxis.set_major_locator(mticker.MaxNLocator(5))
			ax[0].xaxis.set_major_formatter(mdates.DateFormatter('%H:%M:%S'))
			
			# Format the x axis with the dates
			plt.plot(x[-len(y_filt[-PLOT_WINDOW_i:]):], y_filt[-PLOT_WINDOW_i:],
				COLORS_SMA[ma],linewidth=0.5)
				
			if (ma == (len(self.SMA_vec) - 1)):
				plt.plot(x[-len(y[-PLOT_WINDOW_i:]):], y[-PLOT_WINDOW_i:],
					'grey',linewidth=0.5)
			ax[0].autoscale(enable=True, axis='x', tight=True)
			
			# 1st derivative plot
			ax[1] = fig.add_subplot(3,4,5+self.i_crypto)
			# Clear the previous data
			if (ma == 0):
				ax[1].clear()
			ax[1].grid(color=PLOT_COLOR_SCHEME_SECONDARY[COLOR_SCHEME])
			ax[1].grid(color=PLOT_COLOR_SCHEME_SECONDARY[COLOR_SCHEME])
			ax[1].patch.set_facecolor(PLOT_COLOR_SCHEME[COLOR_SCHEME])
			ax[1].grid(color=PLOT_COLOR_SCHEME_SECONDARY[COLOR_SCHEME])
			ax[1].xaxis.set_major_locator(mticker.MaxNLocator(5))
			ax[1].xaxis.set_major_formatter(mdates.DateFormatter('%H:%M:%S'))
			plt.ylabel(self.currency_wallet + ' Derivative in USD [$]')
				
			#x_time_dx = mdates.date2num(x_time[:-1] + x_time[1:]) / 2
			plt.plot(x[-len(dydx[-PLOT_WINDOW_i:]):], dydx[-PLOT_WINDOW_i:],
				COLORS_SMA[ma],linewidth=0.5)
			if (ma == (len(self.SMA_vec) - 1)):
				plt.plot([x[-len(dydx[-PLOT_WINDOW_i:])],x[-1]], [0,0],
					'grey',linewidth=1)
			ax[1].autoscale(enable=True, axis='x', tight=True)
				
			# 2nderivative plot
			ax[2] = fig.add_subplot(3,4,9+self.i_crypto)
			# Clear the previous data
			if (ma == 0):
				ax[2].clear()
			ax[2].grid(color=PLOT_COLOR_SCHEME_SECONDARY[COLOR_SCHEME])
			ax[2].grid(color=PLOT_COLOR_SCHEME_SECONDARY[COLOR_SCHEME])
			ax[2].patch.set_facecolor(PLOT_COLOR_SCHEME[COLOR_SCHEME])
			ax[2].grid(color=PLOT_COLOR_SCHEME_SECONDARY[COLOR_SCHEME])
			ax[2].xaxis.set_major_locator(mticker.MaxNLocator(5))
			ax[2].xaxis.set_major_formatter(mdates.DateFormatter('%H:%M:%S'))
			plt.ylabel(self.currency_wallet + ' Acceleration in USD [$]')
			plt.xlabel('Date and Time, EST')
				
			plt.plot(x[-len(ddyddx[-PLOT_WINDOW_i:]):], ddyddx[-PLOT_WINDOW_i:],
				COLORS_SMA[ma],linewidth=0.25)
			if (ma == (len(self.SMA_vec) - 1)):
				plt.plot([x[-len(ddyddx[-PLOT_WINDOW_i:])],x[-1]], [0,0],
					'grey',linewidth=1)
			ax[2].autoscale(enable=True, axis='x', tight=True)
				
		# Format the plot on initial pass
		if (self.INITIALIZE_DERIV_PLOT == False):
			self.INITIALIZE_DERIV_PLOT = self.FormatPlot(fig, ax[0])
			self.INITIALIZE_DERIV_PLOT = self.FormatPlot(fig, ax[1])
			self.INITIALIZE_DERIV_PLOT = self.FormatPlot(fig, ax[2])
			
		
		# Show the figure
		plt.tight_layout()
		fig.autofmt_xdate()
		fig.canvas.draw()
