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
import datetime
import logging, dataset

from telegram import Update, ForceReply, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters, CallbackContext, CallbackQueryHandler

# Enable logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO
)

logger = logging.getLogger(__name__)

DB = dataset.connect("sqlite:///covid.db")
covid_table = DB['covid']


# Define a few command handlers. These usually take the two arguments update and
# context.
def start(update: Update, _: CallbackContext) -> None:
    """Send a message when the command /start is issued."""
    user = update.effective_user
    # update.message.reply_markdown_v2(
    #    fr'Hi {user.mention_markdown_v2()}\!',
    #    reply_markup=ForceReply(selective=True),
    # )
    update.message.reply_markdown \
            (
            "*💉I'm the Irish Vaccine Data bot!💉* \n\n "
            "Try these commands\n"
            "📅 /latest - Get the latest vaccination stats.\n\n"
            "🗓 /week - Get the stats for the last 7 days.\n\n"
        )


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
            break
        except:
            today = today - datetime.timedelta(days=1)


def today(update: Update, _: CallbackContext) -> None:
    """ Return the most recent vaccination numbers """
    covid_table = DB['covid']
    logging.info("Getting latest update")
    #Start scanning back from todays date
    search_day = datetime.datetime.now()
    previous_day = search_day - datetime.timedelta(days=1)
    while 1:
        try:
            search_day_string = str(search_day.day) + "/" + "{:02d}".format(search_day.month) + "/" + str(search_day.year)
            logger.info("Searching for %s", search_day_string)
            search_day_match = covid_table.find(date=search_day_string)
            search_day_data = search_day_match.next()

            # If we get here, it means we found a match.
            previous_day_string = str(previous_day.day) + "/" + "{:02d}".format(previous_day.month) + "/" + str(
                previous_day.year)
            previous_day_match = covid_table.find(date=previous_day_string)
            previous_day_data = previous_day_match.next()


            logger.info("Calculating previous day data")
            pfizer = search_day_data['pfizer'] - previous_day_data['pfizer']
            az = search_day_data['astraZeneca'] - previous_day_data['astraZeneca']
            moderna = search_day_data['moderna'] - previous_day_data['moderna']


            update.message.reply_markdown\
            (
                "*" + search_day_string + "*\n"
                + "\nDaily Total - " + str('{:,}'.format(search_day_data['dailyVaccinations']))
                + "\n\nPfizer - " + str('{:,}'.format(pfizer))
                + "\nAZ - " + str('{:,}'.format(az))
                + "\nModerna - " + str('{:,}'.format(moderna))
            )


            break
        except:
            search_day = search_day - datetime.timedelta(days=1)
            previous_day = search_day - datetime.timedelta(days=1)


def echo(update: Update, _: CallbackContext) -> None:
    """Echo the user message."""
    update.message.reply_text(update.message.text)


def main() -> None:
    """Start the bot."""
    # Create the Updater and pass it your bot's token.
    updater = Updater("1653123514:AAGFi2oLMPIky2BcsuCTQGbQS5vhCY6nFsQ")

    # Get the dispatcher to register handlers
    dispatcher = updater.dispatcher

    # on different commands - answer in Telegram
    dispatcher.add_handler(CommandHandler("start", start))
    dispatcher.add_handler(CommandHandler("help", help_command))
    dispatcher.add_handler(CommandHandler("latest", today))
    dispatcher.add_handler(CommandHandler("week", week))
    # on non command i.e message - echo the message on Telegram
    dispatcher.add_handler(MessageHandler(Filters.text & ~Filters.command, echo))

    # Start the Bot
    updater.start_polling()

    # Run the bot until you press Ctrl-C or the process receives SIGINT,
    # SIGTERM or SIGABRT. This should be used most of the time, since
    # start_polling() is non-blocking and will stop the bot gracefully.
    updater.idle()


if __name__ == '__main__':
    main()
