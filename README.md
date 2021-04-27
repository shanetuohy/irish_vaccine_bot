# Irish Vaccine Telegram Bot

This is the source code for a telegram bot which periodically updates the user about Irish vaccine data. 

A live version of this bot is running at https://t.me/irish_vaccine_bot, try it out. 


## Supported Commands

/daily - Adds the users coversation id to a db table of conversations to update when there is a database update

/week - Counts up the last 7 days of doses given

/overall - Gives some overall stats about the rollout

/latest - Queries the db for the most recent data

/unsubscribe - Sets subscribed to false against the users coversation id

### Admin Only Commands

/users - Respond with a list of users that are subscribed to updates

/broadcast - Broadcast a message, from that bot, to all subscribed users. Used for alerting about updates. 

## Updates

The bot queries a local SQLite database every ~3 minutes to see has the date changed since the last time the bot updated everyone. 

The bot doesn't query the APIs itself. The 'updateDB.py' script does this. 

Data queried is from the Irish governments official data APIs, that are also used to update the official HSE site - https://covid-19.geohive.ie/pages/vaccinations


## Deploy your own version

### Step 1 - Get a bot token

The Telegram botfather bot can be used to get a bot token. Once you have this, put the token into the config.cfg file. No need for quotes, just replace the sample token that is there. 

### Step 2 - Get your coversation ID

You will also need to know your conversation id, so that you can interact with the bot as the admin. To get this, use the "GetIDs Bot". Use the string of numbers that it returns. Add this to the config.cfg file too. 

### Step 3 - Set up the database

Rename the sample database file (sample_database.db) to covid.db. 

### Step 4 - Install the requirements into a virtual environment

Create a venv for the bot and enable the virtual environment.  
```bash
python3 -m venv vaccineBot
source vaccineBot/bin/activate
```

Now install the requirements from the requirements.txt folder

```bash
pip install -r requirements.txt
```

### Step 5 - Run the updateDB.py script

The APIs do not provide historical data for the vaccine rollout unfortunately, so the database needs to be manually kept up to date with the updateDB.py script. This script will periodically query the APIs and when there is an update, it will add the latest days stats to the database so the bot can access the data.

Whem you run the script for the first time, you should see it add the latest days data to the database.

```bash
> python updateDB.py
```

### Step 6 - Start the bot

Now that your database is set up and the corrent tokens are configured, you can start the bot. It will immediately be ready to respond to your commands. 

```bash
> python vaccineBot.py
```

Once the bot is running, it logs details of the commands that people run against it. 
