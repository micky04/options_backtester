import pandas as pd
from datetime import datetime
import itertools
import os

def main_backtest(profile):
    """
    Function: The main program responsible for executing the backtest

    Parameters:
        profile.
            entry_dates (dict) -- {'BAC':[Timestamp('2009-07-10 00:00:00'), ...], 'AMAT':[...]}
            exit_dates (list) -- ['BAC','AMAT']
            DTE_range (dict) --
            List of max and min DTE for each trade, arranged according to preference
            Example: {'BAC':[[Timestamp('2009-07-10 00:00:00'), ...],[..., ...]], 'AMAT':[...]}
            symbols (list) -- ['AAPL','BAC'...]
            strategy (string) -- 'earnings'/'calendar'
            exec_params (dict) -- Generic execution parameters
            strat_params (dict) -- Strategy specific parameters
                (Example for both params are at the bottom)

    """
    pf = portfolio(profile)
    main_dir = 'Users/Michael/Desktop/Options/options_data'
    tradingdays_stamp, tradingdays_dir = tools.getTradingDays()

    ## ---- START TIME LOOP ----
    for date_dir, date_stamp in zip(tradingdays_dir, tradingdays_stamp):
        ## If there are positions open or the date is an entry date, file will be opened.
        entry_symbols, open_pos = pf.check_event(date_stamp)
        if entry_symbols == [] and open_pos == False: ## If there are no events
            continue
        data = tools.getOptions('hdf5', profile.main_dir, date_dir)
        if entry_symbols != []: ## If there are symbols to enter positions
            pf.open_pos(data, entry_symbols, date_stamp)

class portfolio:
    """
    Function: The main handler of portfolio execution and storing positions
    """
    def __init__(self,profile):
        self.profile = profile
        self.open_positions = dict(zip(self.profile.symbols, [[] for sym in self.profile.symbols]))
        self.closed_positions = dict(zip(self.profile.symbols, [[] for sym in self.profile.symbols]))

    def check_event(self,date):
        """
        Function: Check for entry dates and open positions
        Parameters:
            date (Timestamp) -- Example: Timestamp('2016-07-06 00:00:00')
        Returns:
            entry_symbols (list) -- List of symbols to trade on that day
            open_pos (Boolean) -- True if there are open positions on that day
        """
        ## Check for entry dates
        entry_symbols = []
        for symbol,dates in self.profile.entry_dates.items():
            if date in dates:
                entry_symbols.append(symbol)
        ## Check for open positions
        if self.open_positions != {}:
            open_pos = False ## MUST CHANGE !!!!!!!!!!!!!!!!!!!!!!!
        else:
            open_pos = False

        return entry_symbols,open_pos

    def open_pos(self, data, entry_symbols, exec_date):
        """
        Function: Opens new positions.
        Parameters:
            all_data (Pandas df) --- the options data of that day
            entry_symbols (list) --- the symbols to use to add positions
            exec_date (Timestamp) --- Date to open position
        """
        if self.profile.strategy == 'earnings': ## Execution based on earnings parameters
            for sym in entry_symbols:
                symbol_df = data.loc[data['UnderlyingSymbol'] == sym]

                for date_range in self.profile.DTE_range[sym]: ## Get DTE range
                    if date_range[0] > exec_date:
                        exp_range = date_range
                        break
                sym_exp = list(dict.fromkeys(symbol_df['Expiration'].tolist()))
                sym_datetime_exp = [datetime.strptime(str_date, '%m/%d/%Y') for str_date in sym_exp]

                ## Get options contract expiration (pos_exp)
                pos_exp = False
                for option_exp in sym_datetime_exp:
                    if exp_range[0] < option_exp < exp_range[1]:
                        pos_exp = option_exp
                if not pos_exp: ## No suitable options expiration date has been found
                    print('No option contracts with expirations between '+str(exp_range[0])+' and '+str(exp_range[1])+'.')
                print(pos_exp)

                ## Get exact options contract (the more ATM the better)
                symbol_df = symbol_df.loc[symbol_df['Expiration'] == pos_exp.strftime('%m/%d/%Y')]
                sym_price = symbol_df['UnderlyingPrice'].tolist()[0]
                sym_strikes = list(dict.fromkeys(symbol_df['Strike'].tolist())) ## all strike prices of given exp date
                pos_strike = min(sym_strikes, key=lambda x:abs(x - sym_price)) ## Get strike closest to symbol price

                ## Saving data
                strike_df = symbol_df.loc[symbol_df['Strike'] == pos_strike]
                self.open_positions[sym].append(strike_df)

    def log(self,info):
        ## Save data (entry/exit info, portfolio value changes)
        pass

class tools:
    def getTradingDays():
        """
        Function: Get list of trading days from tradingdays.txt
        Returns:
            Timestamp -- [Timestamp('2016-07-06 00:00:00'), Timestamp('2016-07-07 00:00:00'), ...]
            Directory -- ['/2016/201607/20160706_edited.h5', '/2016/201607/20160707_edited.h5', ...]
        """
        ## Get all trading days
        os.chdir('C:\\Users\\Michael\\Desktop\\Options\\programs\\backtester')
        tradingdays = open('tradingdays.txt', 'r')
        tradingdays = [line.split(',') for line in tradingdays.readlines()]

        tradingdays = tradingdays[-600:] ## TEMPORARY
        ## Convert to directory
        tradingdays_dir = [tools.url(day[0][:8]) for day in tradingdays]
        ## Convert to Timestamp
        tradingdays_timestamp = [pd.to_datetime(day[0][:8],format='%Y%m%d') for day in tradingdays]
        return tradingdays_timestamp,tradingdays_dir

    def url(date):
        """
        Function: convert date to file dir of date
        Parameters:
            date (string, must be h5 format) -- '20190104' (Example)
        Returns: '/2019/201901/20190104_edited.h5' (Example)
        """
        url = r'\\'+date[:4]+r'\\'+date[:6]+r'\\'+date+'_edited.h5'
        return url

    def getOptions(format,main_dir,date_dir):
        if format == 'csv':
            return pd.read_csv(r'C:/'+main_dir+date_dir)
        elif format == 'hdf5':
            print(main_dir+date_dir)
            return pd.read_hdf(main_dir+date_dir)
