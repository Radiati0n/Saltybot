import urllib2
import re
import requests
import random
import json
import pymysql
import math
import time

class SaltyBot:
    def __init__(self):
        self.opener = urllib2.build_opener()
        self.opener.addheaders = [('User-agent', 'Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/42.0.2311.152 Safari/537.36')]
        self.opener.addheaders.append(('Cookie', 'PHPSESSID=phugqk1j1aqp210i0epcr5h6r6'))
        self.opener.addheaders.append(('Cookie', '__cfduid=d5866a182ac994d0d7fe5268086e20e2e1446683623'))
        
    def getMatchData(self):
        mainPage = self.opener.open('http://www.saltybet.com/')
        stateJson = self.opener.open('http://www.saltybet.com/state.json')
        mainPageData = mainPage.read()
        jsonData = stateJson.read()
        jsonData = json.loads(jsonData)
        mainPageData = mainPageData.replace(',','')
        
        moneySearch = re.search('(?<=<span class="dollar" id="balance">)\w+', mainPageData)
        self.money = moneySearch.group(0)
        self.gameStatus = jsonData["status"]                                        
        self.playerOneName = jsonData["p1name"]
        self.playerTwoName = jsonData["p2name"]

    def bet(self, player, amount):
        if player == 0:
            chosenPlayer = "player1"
        else:
            chosenPlayer = "player2"
        url = "http://www.saltybet.com/ajax_place_bet.php"
        params = { 'selectedplayer' : chosenPlayer, 'wager' : str(amount) }

        headers = {
            "Connection" : "keep-alive",
            "Accept" : "*/*",
            "Origin" : "http://www.saltybet.com",
            "X-Requested-With" : "XMLHttpRequest",
            "User-Agent" : "Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/42.0.2311.152 Safari/537.36",
            "Content-Type" : "application/x-www-form-urlencoded; charset=UTF-8",
            "Referer" : "http://www.saltybet.com/",        
            "Accept-Encoding" : "gzip, deflate",
            "Accept-Language" : "en-US,en;q=0.8",
            "Cookie" : "__cfduid=d5866a182ac994d0d7fe5268086e20e2e1446683623; PHPSESSID=phugqk1j1aqp210i0epcr5h6r6",
        }
                         
        requests.post(url, data=params, headers=headers)
                                                
            
bot = SaltyBot()
bot.getMatchData()

print "Money: " + bot.money
print "Game Status: " + bot.gameStatus
print bot.playerOneName + " vs " + bot.playerTwoName


bot.bet(0, 1)
