from YugiohLinkBot import YugiohLinkBot
import Config

bot = YugiohLinkBot(Config.subredditlist)

try:
    while(1):
        bot.run()
except Exception as e:
    print("Shutting down bot: " + str(e))
    try:
        raise e
    except KeyboardInterrupt:
        exit(0)
