import numpy as np
import requests
import json
import time
import sys
from requests.auth import AuthBase
import coinbasepro as cbp
import sqlite3


coinbase_key = ""
coinbase_passphrase = ""
coinbase_secret = ""

client = cbp.AuthenticatedClient(key = coinbase_key, secret = coinbase_secret, passphrase = coinbase_passphrase)

#Function receives price of Ethereum

def getPrice( ):

        newData = client.get_product_ticker(product_id='ETH-USD')
        currentPrice=newData['price']
        return float(currentPrice)

 #Function receives Ethereum balance

def getETHbalance( ):
        
        accountData =client.get_accounts()

        #Parses accounts for Ethereum account

        for a in accountData:
            if(a["currency"]=="ETH"):
                accountData = a["available"]
        accountBalanceETH = accountData

        return accountBalanceETH

#Function receives US balance

def getUSbalance():

        accountData = client.get_accounts()

        #Parses accounts for USD account

        for a in accountData:
            if(a["currency"]=="USD"):
                accountData = a["available"]
        accountBalanceUS = accountData

        return accountBalanceUS

#Buys Ethereum
def buyETH(a):

    a =float(a)
    a = round(a,2)
    buy = client.place_market_order(side='buy',product_id = 'ETH-USD', funds = a)

    return "bought"
        
#sells Ethereum
def sellETH(a):

    a =float(a)
    a = round(a,2)
    sell = client.place_market_order(side='sell',product_id = 'ETH-USD', funds=a)

    return "sold"    
   

#Decides whether to sell or buy Ethereum
def trade():

        USD = getUSbalance()
        if (USD==0):
           return sellETH(getUSbalance())
        else:
           return buyETH(getETHbalance())
            
#Function gets historic rates and calculates Coppock Curve to decide when to sell or buy     
def historic():

        #Gets historic data from 12 hours of Ethereum prices
        historicData = client.get_product_historic_rates('ETH-USD', granularity=21600)
        price = np.squeeze(np.asarray(np.matrix(historicData)))
        time.sleep(1)
        newData = client.get_product_ticker(product_id='ETH-USD')
        currentPrice=newData['price']   
        
        ROC11 = np.zeros(13)
        ROC14 = np.zeros(13)
        ROCSUM = np.zeros(13)

        #Calculate the rate of change of 11 and 14 periods 

        for ii in range(0,13):
            ROC11[ii] = (100*(price[ii]['close']-price[ii+11]['close']) / (price[ii+11]['close']))
            ROC14[ii] = (100*(price[ii]['close']-price[ii+14]['close']) / (price[ii+14]['close']))
            ROCSUM[ii] = ( ROC11[ii] + ROC14[ii] )

        coppock = np.zeros(4)

        #Calculate the slope of the curve

        for ll in range(0,4):
            coppock[ll] = (((1*ROCSUM[ll+9]) + (2*ROCSUM[ll+8]) + (3*ROCSUM[ll+7]) + (4*ROCSUM[ll+6]) + (5*ROCSUM[ll+5]) + (6*ROCSUM[ll+4]) + (7*ROCSUM[ll+3]) + (8*ROCSUM[ll+2]) + (9*ROCSUM[ll+1]) + (10*ROCSUM[ll])) / float(55))
        coppockD1 = np.zeros(3)

        for mm in range(3):
            coppockD1[mm] = coppock[mm] - coppock[mm+1]

        #return whether there was a positive or negative change

        if((coppockD1[1]) != 0):
            if (((coppockD1[0]/abs(coppockD1[0])) == 1.0) and ((coppockD1[1]/abs(coppockD1[1])) == -1.0)):
                return True
            else:
                return False
        

def main(argv):
        
    #creates ledger to record actions from program
        conn = sqlite3.connect('ledger.db')
        c = conn.cursor()
        c.execute("""CREATE TABLE IF NOT EXISTS ledgerETHtransaction(action TEXT, profit LONG,time TEXT PRIMARY KEY,Ethereum DOUBLE, USD DOUBLE);""")

        #runs forever

        while True:

            #Calculates difference in 12 hours
            trd = False
            yesterday = getPrice()
            time.sleep(21600)
            today = getPrice()

            USBalance = getUSbalance
            ETHBalance = getETHbalance
            
            trd = historic()
            action = ""

            if trd == True:
               action = trade()

            #calculates difference in 12 hour periods
             
            profit=str(today - yesterday)

            #inputs transcation in ledger
            c.execute(("""INSERT INTO ledgerETHtransaction VALUES(?,?,?,?,?);"""),(action,profit,"DATE('now')",ETHBalance,USBalance))
            conn.commit()

        con.close

if __name__ == "__main__":

    main(sys.argv[1:])

        