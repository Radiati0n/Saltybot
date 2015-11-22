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
    ##Login variables
    #Ubuntu USER_AGENT
    USER_AGENT = 'Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:42.0) Gecko/20100101 Firefox/42.0'
    #Windows USER_AGENT
    #USER_AGENT = 'Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/42.0.2311.152 Safari/537.36'
    ACCEPT_HTML = 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8'
    ACCEPT_JSON = 'application/json, text/javascript, */*; q=0.01'
    ACCEPT_LANGUAGE = 'en-US,en;q=0.5'
    ACCEPT_ENCODING = 'gzip, deflate'
    CONNECTION = 'keep-alive'
    CONTENT_TYPE = 'application/x-www-form-urlencoded; charset=UTF-8'
    #Enter login details for account to use here
    EMAIL = ''
    PASSWORD = ''

    ##Class variables
    #opener
    #playerOneName
    #playerTwoName
    #db
    #gameStatus
    #money

    def buildCookieString(self, cookieDict):
        cookies = ''
        for key in cookieDict:
            cookies += key+'='+cookieDict[key]+'; '
        return cookies

    def signin(self):
        s = requests.Session()
        url = 'http://www.saltybet.com'
        response = s.get(url)
        cookie = self.buildCookieString(response.cookies.get_dict())

        url = 'http://www.saltybet.com/authenticate?signin=1'
        data = {
            'email':self.EMAIL,
            'pword':self.PASSWORD,
            'authenticate':'signin'
        }
        headers = {
            'User-Agent':self.USER_AGENT,
            'Accept':self.ACCEPT_HTML,
            'Accept-Language':self.ACCEPT_LANGUAGE,
            'Accept-Encoding':self.ACCEPT_ENCODING,
            'Cookie':cookie,
            'Referer':'http://www.saltybet.com/authenticate?signin=1',
            'Connection':self.CONNECTION,
            'Content-Type':self.CONTENT_TYPE,
            'Content-Length':'56'
        }
        
        response = s.post(url, data=data, headers=headers)
        cookies = self.buildCookieString(s.cookies.get_dict())
        return cookies

    def __init__(self):
        self.cookie = self.signin()
        self.opener = urllib2.build_opener()
        self.opener.addheaders = [('User-agent', self.USER_AGENT)]
        self.opener.addheaders.append(('Cookie', self.cookie))
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
        if "bracket" in jsonData["remaining"] or "FINAL ROUND!" in jsonData["remaining"]:
            self.gameMode = "tournament"
        elif "exhibition matches" in jsonData["remaining"]:
            # Using just "exhibition" would match the final tournament round
            self.gameMode = "exhibition"
        else:
            self.gameMode = "match"
        self.playerOneName = jsonData["p1name"]
        self.playerTwoName = jsonData["p2name"]
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
            "Connection" : self.CONNECTION,
            "Accept" : self.ACCEPT_JSON,
            "X-Requested-With" : "XMLHttpRequest",
            "User-Agent" : self.USER_AGENT,
            "Content-Type" : self.CONTENT_TYPE,
            "Referer" : "http://www.saltybet.com/",        
            "Accept-Encoding" : self.ACCEPT_ENCODING,
            "Accept-Language" : self.ACCEPT_LANGUAGE,
            "Cookie" : self.cookie
            }
                         
        response = requests.post(url, data=params, headers=headers)

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

                                                                                                   
