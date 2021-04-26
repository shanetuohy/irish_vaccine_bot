# Irish Vaccine Telegram Bot

This is the source code for a telegram bot which periodically updates the user about Irish vaccine data. 

The bot is running at https://t.me/irish_vaccine_bot


## Supported Commands

/daily - Adds the users coversation id to a db table of conversations to update when there is a database update
/week - Counts up the last 7 days of doses given
/overall - Gives some overall stats about the rollouy
/latest - Queries the db for the most recent data
/unsubscribe - Sets subscribed to false against the users coversation id


## Updates

The bot queries a local SQLite database every ~3 minutes to see has the date changed since the last time the bot updated everyone. 

The bot doesn't query the APIs itself. The 'updateDB.py' script does this. 

Data queried is from the Irish governments official data APIs, that are also used to update the official HSE site - https://covid-19.geohive.ie/pages/vaccinations
