import urllib3
import csv
import datetime
import numpy as np
from scipy.stats import stats

###############################
# Getting and Parsing data:
###############################

# The following dictionary contains the list of all stocks I considered.
# Information taken from http://etfdb.com/etfdb-category/leveraged-bonds/
# and http://etfdb.com/etfdb-category/emerging-markets-bonds/

symbol_dict= {'US_bond': ['TBT',
                          'TTT',
                          'TMF',
                          'UST',
                          'UBT',
                          'SBND',
                          'BUNT',
                          'LBND',
                          'LBND',
                          'JGBT',
                          'IGU',
                          'TPS'],

              'emerging_market': ['EMB',
                                  'PCY',
                                  'EMLC',
                                  'VWOB',
                                  'LEMB',
                                  'ELD',
                                  'DSUM',
                                  'EMCB',
                                  'EBND',
                                  'CHNB',
                                  'KCNY',
                                  'CEMB',
                                  'CBON',
                                  'EMAG',
                                  'EMCD',
                                  'EMIH',
                                  'FEMB',
                                  'PFEM',
                                  'EMBH']}



# All value data taken from Yahoo! finance
base_url = "http://ichart.finance.yahoo.com/table.csv?s="

def make_url(ticker_symbol):
    return base_url + ticker_symbol


def make_filename(ticker_symbol):
    return "./" + ticker_symbol + ".csv"


def pull_historical_data(ticker_symbol, fund_type):

    # Here I get each of the .csv files of historical
    # value data and add it to the appropriate folder
    # (it is assumed that the directories 'US_bond' and
    # 'emerging market' have already been created)

    url = make_url(ticker_symbol)
    manager = urllib3.PoolManager()
    response = manager.request('GET', url)
    data = response.read()
    with open(fund_type +'/'+ticker_symbol+'.csv', 'wb') as f:
        f.write(data)


def parse_csv(ticker_symbol, fund_type):

    # For each fund, I take the date column and the adjusted value
    # column. The date is reformulated as days from the (somewhat
    # arbitrary) cutoff of five years ago. The list is then cast as
    # a NumPy array for ease of calculations.
    
    data = []
#    print(ticker_symbol)
    with open(fund_type+'/'+ticker_symbol+'.csv') as csvfile:
        reader = csv.DictReader(csvfile)
        ts=[]
        for row in reader:
            date = row['Date'].split('-')
            date_obj = datetime.date(int(date[0]),
                                     int(date[1]),
                                     int(date[2]))

            t = date_obj -datetime.date(2011, 2, 9)
            ts.append(t)
            if t.days > 0:
                data.append([t.days, float(row['Adj Close'])])
    data= np.flipud(np.array(data))
#    max_value=max(data[:,1])
#    data[:,1]=data[:,1]/max_value
    return data


###########################
# Analysis:
###########################



def get_slopes(symbol_list, fund_type):

    # For each fund, I perform a simple least-squares linear regression
    # to get the value as a function of time.

    # Here, I also restrict the analysis to only those funds which have
    # gained value over the past five years (i.e. have a positive slope).
    # The logic behind this is that, if we're only adding one fund to the
    # portfolio, we can limit ourselves to choosing one that has
    # historically done well. The question is then whether the US bonds
    # that have done well have done better than the emerging market funds
    # that have done well.
    
    slopes=[]
    for symbol in symbol_list:
        slope = stats.linregress(parse_csv(symbol,fund_type))[0]
        if slope >0.0:
            slopes.append(slope)
#    print(len(slopes))
    return slopes






def main(symbol_dict):

    # Here's where I put it all together. Once the slope of each fund
    # have been calculated, I run a two-tailed independent t-test
    # comparing the sets of slopes for the two types of funds. The
    # test returns a tuple of the form (test statistic, p-value)

    # The results require us to set a statistical significance level (alpha).
    # (when I was analyzing astroparticle physics data, we used
    # alpha = 5.7x10^(-5), but for this, alpha = 0.05 or 0.01 should be
    # sufficient.) The results can be interpreted as follows:

    # p > alpha/2: There is insufficient evidence to reject the claim
    # that the two samples have the same mean (i.e. there is no difference
    # between the leveraged bonds and the emerging market stocks)

    # p < alpha/2 and t < 0: the average increase in value of an emerging
    # market fund is likely greater than that of a leveraged bond fund over the
    # same period

    # p < alpha/2 and t > 0: the average increase in value of an emerging
    # market fund is likely less than that of a leveraged bond fund over the
    # same period

    # Note: I am running a Welch's t-test rather than a Student's t-test
    # because there is no reason to assume that the two populations have equal
    # variances.
    
    
    slopes = {}
    for key in symbol_dict:
        for bond in symbol_dict[key]:
            pull_historical_data(bond, key)
        slopes[key]=get_slopes(symbol_dict[key], key)
    return stats.ttest_ind(slopes['US_bond'],
                           slopes['emerging_market'],
                           equal_var=False)


# Running this code at 6:22 PM EST on February 9th 2016 yielded a test
# statistic of 4.21 and a p value of 0.001. Therefore, even with the more
# rigorous alpha bound of 0.01, the leveraged bond funds ourperform the
# emerging market funds.
