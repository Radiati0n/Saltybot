import urllib2
import re
import requests
import random
import json
import pymysql
import math
import time

class SaltyBot:
    ##Class constants
    #K value used in calculating elo
    K = 32
    #Initial elo for characters not seen yet
    initialElo = 1200

    ##Class variables
    #opener
    #playerOneName
    #playerTwoName
    #db
    #gameStatus
    #money
    
    def __init__(self):
        self.opener = urllib2.build_opener()
        self.opener.addheaders = [('User-agent', 'Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/42.0.2311.152 Safari/537.36')]
        self.opener.addheaders.append(('Cookie', 'PHPSESSID=og52g9k5j4gprcvmeeu5foe0u1'))
        self.opener.addheaders.append(('Cookie', '__cfduid=d5866a182ac994d0d7fe5268086e20e2e1446683623'))
        self.opener.addheaders.append(('Cookie', '_ga=GA1.2.1188374362.1447004664'))
        self.opener.addheaders.append(('Cookie', '_gat=1'))
        self.opener.addheaders.append(('Cookie', 'GED_PLAYLIST_ACTIVITY=W3sidSI6IjI1bWwiLCJ0IjoxNDQ3MTk3ODk0LCJlZCI6eyJpIjp7InciOnsidHQiOjU1NiwicGQiOjU1NiwiYnMiOjEwfX0sImEiOlt7Imt2Ijp7fX0seyJrdiI6e319LHsia3YiOnt9fSx7Imt2Ijp7fX0seyJrdiI6e319LHsia3YiOnt9fV19LCJudiI6MCwicGwiOjU1Nn1d'))
        self.dbConnect()
        
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

        print "Betting " + str(int(amount)) + " on " + chosenPlayer
        
        url = "http://www.saltybet.com/ajax_place_bet.php"
        params = { 'selectedplayer' : chosenPlayer, 'wager' : str(int(amount)) }

        headers = {
            "Connection" : "keep-alive",
            "Accept" : "application/json, text/javascript, */*; q=0.01",
            "X-Requested-With" : "XMLHttpRequest",
            "User-Agent" : "Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/42.0.2311.152 Safari/537.36",
            "Content-Type" : "application/x-www-form-urlencoded; charset=UTF-8",
            "Referer" : "http://www.saltybet.com/",        
            "Accept-Encoding" : "gzip, deflate",
            "Accept-Language" : "en-US,en;q=0.8",
            "Cookie" : "__cfduid=d5866a182ac994d0d7fe5268086e20e2e1446683623; PHPSESSID=og52g9k5j4gprcvmeeu5foe0u1; _ga=GA1.2.1188374362.1447004664; GED_PLAYLIST_ACTIVITY=W3sidSI6IjI1bWwiLCJ0IjoxNDQ3MTk4OTMxLCJlZCI6eyJpIjp7InciOnsidHQiOjI5NCwicGQiOjI5NCwiYnMiOjEwLCJlcyI6MH19LCJhIjpbeyJrdiI6eyJtIjo0MDJ9fSx7Imt2Ijp7Im0iOjI2MTIsImMiOjJ9fSx7Imt2Ijp7fX0seyJrdiI6e319LHsia3YiOnt9fSx7Imt2Ijp7Im0iOjE1NDl9fV19LCJudiI6MSwicGwiOjI5NH1d",
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
        sqlQuery = "SELECT * FROM characters WHERE name = \"" + chosenPlayer + "\";"
        cursor.execute(sqlQuery)
        queryResult = cursor.fetchone()
        if "None" in str(queryResult):
            return self.initialElo
        else:
            return queryResult[1]

    
    def eloWinProb(self, player1Elo, player2Elo):
       return 1/(1+math.pow(10,(float(player2Elo)-float(player1Elo))/400))

            
bot = SaltyBot()
while True:
    try:
        bot.getMatchData()

        if bot.gameStatus == "open":
            print "Money: " + bot.money
            print bot.playerOneName + " vs " + bot.playerTwoName
            
            player1Elo = bot.getElo(0)
            player2Elo = bot.getElo(1)
            print "Player One Elo: " + str(player1Elo)
            print "Player Two Elo: " + str(player2Elo)

            print "P(P1win): " + str(bot.eloWinProb(player1Elo, player2Elo))
            print "P(P2win): " + str(bot.eloWinProb(player2Elo, player1Elo))

            if(bot.eloWinProb(player1Elo, player2Elo) > 0.5):
                bot.bet(0, float(bot.money)*0.10)
            else:
                bot.bet(1, float(bot.money)*0.10)

            while bot.gameStatus == "open" or bot.gameStatus == "locked":
                bot.getMatchData()
                time.sleep(3)

            if bot.gameStatus == "1":
                print bot.playerOneName + " wins!"
                s = 1
            elif bot.gameStatus == "2":
                print bot.playerTwoName + " wins!"
                s = 0
            
        time.sleep(5)
    except:
        print "Error - Trying again."

