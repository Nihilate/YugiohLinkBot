from YugiohLinkBot import YugiohLinkBot
import Config

bot = YugiohLinkBot(Config.subredditlist)

try:
    bot.run()
except BaseException as e:
    print("Shutting down bot: " + str(e))
    try:
        raise e
    except KeyboardInterrupt:
        exit(0)
