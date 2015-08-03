# YugiohLinkBot
YugiohLinkBot is a Reddit bot which creates comments displaying Yugioh card information when requested (Yugioh is a collectable card game). YugiohLinkBot can be found [here](https://www.reddit.com/user/YugiohLinkBot).

## Technical info
YGOLB is written in Python for use with Python 2.7. There's a requirements.txt if you want to test it out yourself, but you'll need to create YGOConfig.py with your own information. Please don't just run it right out of the box - you'll end up replying in all the same places the live bot does. If you do want to test it out yourself, make sure to change the subreddits it looks in to a private one that just you and the bot have access to.

## How it works
YGOLB uses PRAW (a Python library) to interface with Reddit through the /u/YugiohLinkBot account. It will then look through the new 50 or so comments once every minute or so, looking for the appropriate symbols. Once it's found one, it takes what's between the symbols and searches for it on various databases. If it finds it it makes a comment.

##To-do
- Refactor the code to work with Reddit's new OAuth requirements
- Refactor the code to use comment/submission streams as provided by PRAW
- Change database from SQLite to PostgreSQL
- Add stat-tracking function (similar to /u/Roboragi)
- Add archetype linking?