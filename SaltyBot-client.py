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

    
    def eloWinProb(self, player1Elo, player2Elo):
       return 1/(1+math.pow(10,(float(player2Elo)-float(player1Elo))/400))

            
bot = SaltyBot()
while True:
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
            time.sleep(5)

        if bot.gameStatus == "1":
            print bot.playerOneName + " wins!"
            s = 1
        elif bot.gameStatus == "2":
            print bot.playerTwoName + " wins!"
            s = 0
        
    time.sleep(10)
