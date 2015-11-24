from SaltyBot import SaltyBot
import time
import sys

bot = SaltyBot()
print "SaltyBot initialized...\n"
while True:
    try:
        bot.getMatchData()

        if bot.gameStatus == "open":
            print "Money: " + bot.money
            print bot.playerOneName + " vs " + bot.playerTwoName
            
            if(bot.gameMode != "exhibition"):
                player1Elo = bot.getElo(0)
                player2Elo = bot.getElo(1)
                print bot.playerOneName + " Elo: " + str(player1Elo)
                print bot.playerTwoName + " Elo: " + str(player2Elo)

                print "P(" + bot.playerOneName + " win): " + str(bot.eloWinProb(player1Elo, player2Elo))
                print "P(" + bot.playerTwoName + " win): " + str(bot.eloWinProb(player2Elo, player1Elo))
                if(bot.eloWinProb(player1Elo, player2Elo) > 0.5):
                    bot.bet(0, float(bot.money)*0.10)
                else:
                    bot.bet(1, float(bot.money)*0.10)
            else:
                print "No bets are made during exhibition mode"

            while bot.gameStatus == "open" or bot.gameStatus == "locked":
                bot.getMatchData()
                time.sleep(3)

            if bot.gameStatus == "1":
                print bot.playerOneName + " wins!"
                s = 1
            elif bot.gameStatus == "2":
                print bot.playerTwoName + " wins!"
                s = 0
            print ""
        time.sleep(5)
    except:
        e = sys.exc_info()[0]
        print "Error: ", e
        time.sleep(5)

