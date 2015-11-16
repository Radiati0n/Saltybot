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
        self.opener.addheaders.append(('Cookie', 'PHPSESSID=phugqk1j1aqp210i0epcr5h6r6'))
        self.opener.addheaders.append(('Cookie', '__cfduid=d5866a182ac994d0d7fe5268086e20e2e1446683623'))
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
        sqlQuery = "SELECT * FROM characters WHERE name = \"" + chosenPlayer + "\";"
        cursor.execute(sqlQuery)
        queryResult = cursor.fetchone()
        if "None" in str(queryResult):
            return self.initialElo
        else:
            return queryResult[1]

    def updateDatabase(self, playerOneElo, playerTwoElo):
        cursor = self.db.cursor()
        sqlQuery = "SELECT * FROM characters WHERE name = \"" + self.playerOneName + "\";"
        cursor.execute(sqlQuery)
        queryResult = cursor.fetchone()
        if "None" in str(queryResult):
            self.insertNewCharacter(self.playerOneName, cursor)
        sqlQuery = "SELECT * FROM characters WHERE name = \"" + self.playerTwoName + "\";"
        cursor.execute(sqlQuery)
        queryResult = cursor.fetchone()
        if "None" in str(queryResult):
            self.insertNewCharacter(self.playerTwoName, cursor)
        sqlQuery = "UPDATE characters SET elo = " + str(playerOneElo) + ", matches = matches + 1 WHERE name = \"" + self.playerOneName + "\";"
        cursor.execute(sqlQuery)
        self.db.commit()
        sqlQuery = "UPDATE characters SET elo = " + str(playerTwoElo) + ", matches = matches + 1 WHERE name = \"" + self.playerTwoName + "\";"
        cursor.execute(sqlQuery)
        self.db.commit()

    def insertNewCharacter(self, characterName, cursor):
        sqlQuery = "INSERT INTO characters(name, elo, matches) \r\nVALUES (\"" + characterName + "\", " + str(self.initialElo) + ", 0);"
        cursor.execute(sqlQuery)
        self.db.commit()
    
    
    def eloWinProb(self, player1Elo, player2Elo):
       return 1/(1+math.pow(10,(float(player2Elo)-float(player1Elo))/400))

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
while True:
    try:
        bot.getMatchData()

        if bot.gameStatus == "open":
            print bot.playerOneName + " vs " + bot.playerTwoName
            
            player1Elo = bot.getElo(0)
            player2Elo = bot.getElo(1)
            print bot.playerOneName + " Elo: " + str(player1Elo)
            print bot.playerTwoName + " Elo: " + str(player2Elo)

            print "P(P1win): " + str(bot.eloWinProb(player1Elo, player2Elo))
            print "P(P2win): " + str(bot.eloWinProb(player2Elo, player1Elo))

            while bot.gameStatus == "open" or bot.gameStatus == "locked":
                bot.getMatchData()
                time.sleep(3)

            if bot.gameStatus == "1":
                print bot.playerOneName + " wins!"
                s = 1
            elif bot.gameStatus == "2":
                print bot.playerTwoName + " wins!"
                s = 0
            (player1NewElo, player2NewElo) = bot.calculateNewElos(player1Elo, player2Elo, s)
            bot.updateDatabase(player1NewElo, player2NewElo)
            
        time.sleep(5)
    except:
        print "Error - Trying again."
