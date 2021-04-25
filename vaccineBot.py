"""
Simple Bot to reply to Telegram messages.
First, a few handler functions are defined. Then, those functions are passed to
the Dispatcher and registered at their respective places.
Then, the bot is started and runs until we press Ctrl-C on the command line.
Usage:
Basic Echobot example, repeats messages.
Press Ctrl-C on the command line or send a signal to the process to stop the
bot.
"""
import logging, dataset, datetime, configparser
from collections import OrderedDict
from telegram import Update, ForceReply, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters, CallbackContext, CallbackQueryHandler, PicklePersistence

# Enable logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO
)


config = configparser.ConfigParser()
config.read('config.cfg')
TELEGRAM_TOKEN = config['Credentials'].get('telegram_token')
ADMIN_CONVERSATION_ID = config['Credentials'].get('admin_conversation_id')


logger = logging.getLogger(__name__)
logger.info("Starting bot.")
logger.info ("Admin ID = " + str(ADMIN_CONVERSATION_ID))


DB = dataset.connect("sqlite:///covid.db")
covid_table = DB['covid']
users_table = DB['users']
last_update_table = DB['last_update']


# Define a few command handlers. These usually take the two arguments update and
# context.
def start(update: Update, _: CallbackContext) -> None:
    """Send a message when the command /start is issued."""
    user = update.effective_user
    latest_day, previous_day = get_latest_stats_from_db()
    logger.info(latest_day['date'])
    _.bot_data.update({'date': str(latest_day['date'])})
    update.message.reply_markdown \
            (
            "*💉I'm the Irish Vaccine Data bot!💉* \n\n "
            "Try these commands\n\n"
            "✅ /daily - Subscribe for daily updates.\n\n"
            "📅 /latest - Get the latest vaccination stats.\n\n"
            "🗓 /week - Get the stats for the last 7 days.\n\n"
            "📈 /overall - Overall rollout statistics.\n\n"
            "❎ /unsubscribe - Unsubscribe from daily updates.\n\n"
        )

    logger.info("/start")


def help_command(update: Update, _: CallbackContext) -> None:
    """Send a message when the command /help is issued."""
    update.message.reply_text('Help!')

def return_daily_figure(date_object):
    day_str = str(date_object.day) + "/" + "{:02d}".format(date_object.month) + "/" + str(date_object.year)
    match = covid_table.find(date=day_str)
    result = match.next()
    return result['dailyVaccinations']


def week(update: Update, _: CallbackContext) -> None:
    """Send a message when the command /week is issued."""
    today = datetime.datetime.now()

    while 1:
        try:
            today_str = str(today.day) + "/" + "{:02d}".format(today.month) + "/" + str(today.year)
            match = covid_table.find(date=today_str)
            match.next()
            running_total = 0
            for i in range(6):
                running_total += return_daily_figure(today)
                today = today - datetime.timedelta(days=1)
            update.message.reply_markdown(
                "*Total doses in last 7 days*\n\n"
                + str('{:,}'.format(running_total)))
            logger.info("/week")

            break
        except:
            today = today - datetime.timedelta(days=1)


def get_latest_stats_from_db():

    #Start scanning back from todays date
    search_day = datetime.datetime.now()
    previous_day = search_day - datetime.timedelta(days=1)
    while 1:
        try:
            search_day_string = str(search_day.day) + "/" + "{:02d}".format(search_day.month) + "/" + str(search_day.year)
            logger.debug("Searching for %s", search_day_string)
            search_day_match = covid_table.find(date=search_day_string)
            search_day_data = search_day_match.next()

            # If we get here, it means we found a match.
            previous_day_string = str(previous_day.day) + "/" + "{:02d}".format(previous_day.month) + "/" + str(
                previous_day.year)
            previous_day_match = covid_table.find(date=previous_day_string)
            previous_day_data = previous_day_match.next()

            break
        except:
            search_day = search_day - datetime.timedelta(days=1)
            previous_day = search_day - datetime.timedelta(days=1)
    
    return (search_day_data, previous_day_data)


def get_day_of_week_string(date_string):
    
    """ Get the day of the week based on the date string from the database """

    # Split on / string, and feed to a datetime object, to use weekday function
    date_strings = date_string.split("/")
    update_date = datetime.datetime(int(date_strings[2]), int(date_strings[1]), int(date_strings[0]))
    weekDays = ("Mon", "Tue", "Wed", "Thur", "Fri", "Sat", "Sun")
    day_of_week = str(weekDays[update_date.weekday()])
    return day_of_week

def today(update: Update, _: CallbackContext) -> None:
    
    """ Return the most recent vaccination numbers """
    
    logging.info("Getting latest update for " + str(update.message.chat_id))
    
    # Get latest day from db
    today, previous_day = get_latest_stats_from_db()
    
    # Get latest update string
    update_string = get_update_string(today, previous_day)
   
    # Send update
    update.message.reply_markdown(update_string)

    
   

def overall(update: Update, context: CallbackContext) -> None:
    """ Returns stats on overall rollout """

    today, _ = get_latest_stats_from_db()
    
    logging.info("Getting overall stats for " + str(update.message.chat_id))
    
    text =  \
    (
                "*Overall stats as of " + today['date'] + "*\n\n"
                + "Overall Total - " + str('{:,}'.format(today['totalVaccinations']))
                + "\nPfizer - " + str('{:,}'.format(today['pfizer']))
                + "\nAZ - " + str('{:,}'.format(today['astraZeneca']))
                + "\nModerna - " + str('{:,}'.format(today['moderna'])) + "\n\n"
                + "*% of adult (16+) pop. vaccinated*\n\n"
                + "First dose - " + str('{0:.2%}'.format(today['firstDose']/3863147)) + "\n"
                + "Second dose - " + str('{0:.2%}'.format(today['secondDose']/3863147))
    )

    update.message.reply_markdown(text)


def unset_response(update: Update, context: CallbackContext) -> None:
    """ Set users update to False """
    context.bot_data.update({str(update.message.chat_id) : 'False'})
    user_data = OrderedDict(user=str(update.message.chat_id),subscribed='False')   
    users_table.upsert(user_data, ['user'])
    logging.info("Unsubscribing user " + str(update.message.chat_id))
    text = "No worries, you've been unsubscribed.\n\n" \
            "To subscribe to daily updates again, just press /daily"
    update.message.reply_text(text)
   

def set_respond(update: Update, context: CallbackContext) -> None:
    """ Add this user to the list of subscribers """
    context.bot_data.update({str(update.message.chat_id) : 'True'})
    user_data = OrderedDict(user=str(update.message.chat_id),subscribed='True')
    users_table.upsert(user_data, ['user'])
    try:
        
        # Get current jobs and remove them from the queue.
        jq = context.job_queue
        jlist = jq.jobs()
        for job in jlist:
            job.schedule_removal()
        #except:
        #    logging.info("Got no jobs from the list, continue")

        # Recreate the job. 
        context.job_queue.run_repeating(schedule_response, 200, context="Daily")
        text = "I'll message you every day, as soon as the vaccine stats update.\n\n" \
                "To unsubscribe, just press /unsubscribe. \n\n" \
                "To see the latest stats, press /latest."
        update.message.reply_text(text)

    except (IndexError, ValueError):
        update.message.reply_text('Usage: /daily')

def users(update: Update, context: CallbackContext) -> None:
    """ Allow admin to query subscribed users """
    if str(update.message.chat_id) == str(ADMIN_CONVERSATION_ID):
        logger.info("Admin queried users")
        users_list = users_table.all()
        for user in users_list:
            update_string = "User - " + str(user['user']) + " Sub - " + str(user['subscribed'])
            context.bot.send_message(ADMIN_CONVERSATION_ID, parse_mode='HTML', text=update_string)
           
def broadcast(update: Update, context: CallbackContext) -> None:
    """ Allow admin to send out broadcasts to all subscribed users """
    
    if str(update.message.chat_id) == str(ADMIN_CONVERSATION_ID):
        update_string = update.message.text[11:]
        logger.info("Admin did a broadcast")
        users_list = users_table.all()
        for user in users_list:
            if user['subscribed'] == "True":
                context.bot.send_message(user['user'], parse_mode='HTML', text=update_string)
                logger.info("Broadcasted message " + str(update_string) + " to user " + str(user['user']))
                
                
def get_update_string(today, previous_day):   
    """ Get the string for daily updates """

    pfizer = today['pfizer'] - previous_day['pfizer']
    az = today['astraZeneca'] - previous_day['astraZeneca']
    moderna = today['moderna'] - previous_day['moderna']

    day_of_week = get_day_of_week_string(today['date'])

    l1 = "*" + day_of_week + " " + str(today['date']) + "*\n"
    l2 = "\nDaily Total - " + str('{:,}'.format(today['dailyVaccinations']))
    l3 = "\n\nPfizer - " + str('{:,}'.format(pfizer))
    l4 = "\nAZ - " + str('{:,}'.format(az))
    l5 = "\nModerna - " + str('{:,}'.format(moderna))
    l6 = "\n"
    l7 = "\nFirst dose - " + str('{0:.2%}'.format(today['firstDose']/3863147))
    l8 = "\nSecond dose - " + str('{0:.2%}'.format(today['secondDose']/3863147))
    
    update_string = l1 + l2 + l3 + l4 + l5 + l6 + l7 + l8
    return update_string


def schedule_response(context: CallbackContext) -> None:
    """ Send an update to the subscribed users """

    today, previous_day = get_latest_stats_from_db()
    update_string = get_update_string(today, previous_day)
    
    # From DB get the date of our last update
    last_update = last_update_table.find_one(id=1)
    
    # Get the list of users
    users_list = users_table.all()

    if last_update['date'] == today['date']:
        #If the dates are the same, skip updating
        return None

    #If we get this far, dates were different, so let's send an update
    logging.info("Dates were different, time for an update!")
    
    for user in users_list:
        if user['subscribed'] == 'True':
            logging.info("Sending update to user - " + user['user'])
            context.bot.send_message(user['user'], parse_mode='MarkdownV2', text=update_string)
    
    #Update the last updated date in the db
    last_update_data = OrderedDict(id=1,date=today['date'])
    last_update_table.upsert(last_update_data, ['id'])


def main() -> None:
    """Start the bot."""
    # Create the Updater and pass it your bot's token.
    #updater = Updater("***REMOVED***")
    persistence = PicklePersistence(filename='conv_persistence')
    updater = Updater(TELEGRAM_TOKEN, persistence=persistence, use_context=True)

    # Get the dispatcher to register handlers
    dispatcher = updater.dispatcher

    # on different commands - answer in Telegram
    dispatcher.add_handler(CommandHandler("start", start))
    dispatcher.add_handler(CommandHandler("help", help_command))
    dispatcher.add_handler(CommandHandler("latest", today))
    dispatcher.add_handler(CommandHandler("week", week))
    dispatcher.add_handler(CommandHandler("daily", set_respond))
    dispatcher.add_handler(CommandHandler("unsubscribe", unset_response))
    dispatcher.add_handler(CommandHandler("overall", overall)),
    dispatcher.add_handler(CommandHandler("broadcast", broadcast))
    dispatcher.add_handler(CommandHandler("users", users))
    

    # Start the Bot
    updater.start_polling()

    # Run the bot until you press Ctrl-C or the process receives SIGINT,
    # SIGTERM or SIGABRT. This should be used most of the time, since
    # start_polling() is non-blocking and will stop the bot gracefully.
    updater.idle()


if __name__ == '__main__':
    main()
