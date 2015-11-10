try:
    import urllib.request as urllib2
except ImportError:
    import urllib2
import re
import requests
import random
import json
import pymysql
import math
import time

class SaltyBot:
    #K value used in elo calculation, lower values will cause smaller flucuations in elo with a win or loss
    K = 32

    #Init method sets up opener to retrieve web data and the connection to the database
    def __init__(self):
        self.opener = urllib2.build_opener()
        self.opener.addheaders = [('User-agent', 'Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/42.0.2311.152 Safari/537.36')]
        self.opener.addheaders.append(('Cookie', 'PHPSESSID=phugqk1j1aqp210i0epcr5h6r6'))
        self.opener.addheaders.append(('Cookie', '__cfduid=d5866a182ac994d0d7fe5268086e20e2e1446683623'))
        self.dbConnect()

    #Retrieves the data for the current match
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

    #Sends the packet to post the bet on the selected player
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

    def dbConnect(self):
        self.db = pymysql.connect(host='raspimumble.no-ip.org',port=3306,user='saltybot',passwd='salty-pass',db='saltydata')

    def getElo(self, player):
        if player == 0:
            chosenPlayer = self.playerOneName
        else:
            chosenPlayer = self.playerTwoName
        cursor = self.db.cursor()
        sqlQuery = "select * from characters where name = \"" + chosenPlayer + "\";"
        cursor.execute(sqlQuery)
        queryResult = cursor.fetchone()
        if "None" in str(queryResult):
            return 1200
        else:
            return queryResult[1]

    ##
    # Given the elos of both characters and the s value, calculates and returns the new elos
    # Params:
    #   elo1 - elo of player1 before the match
    #   elo2 - elo of player2 before the match
    #   s - 1 if player1 won, .5 if a draw, 0 if player2 won
    # Return: (newElo1, newElo2) - tuple with the new elo for both players
    ##
    def calculateNewElos(self, elo1, elo2, s):
        transformedElo1 = math.pow(10, elo1/400)
        transformedElo2 = math.pow(10, elo2/400)
        expectedScore1 = transformedElo1/(transformedElo1+transformedElo2)
        expectedScore2 = transformedElo2/(transformedElo1+transformedElo2)
        newElo1 = elo1 + self.K*(s - expectedScore1)
        newElo2 = elo2 + self.K*(1 - s - expectedScore2)
        return (int(round(newElo1)), int(round(newElo2)))

        
bot = SaltyBot()
bot.getMatchData()

print "Money: " + bot.money
print "Game Status: " + bot.gameStatus
print bot.playerOneName + " vs " + bot.playerTwoName

print "Player One Elo: " + str(bot.getElo(0))
print "Player Two Elo: " + str(bot.getElo(1))

bot.bet(0, 1)
