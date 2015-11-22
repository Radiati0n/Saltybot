from SaltyBot import SaltyBot
import time
import sys

bot = SaltyBot()
while True:
    try:
        bot.getMatchData()

        if bot.gameStatus == "open" and bot.gameMode != "exhibition":
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
        e = sys.exc_info()[0]
        print "Error: ", e
        time.sleep(5)
