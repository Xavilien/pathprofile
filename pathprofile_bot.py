from telegram.ext import Updater, CommandHandler, ConversationHandler, CallbackQueryHandler, MessageHandler, Filters
from telegram import ChatAction, InlineKeyboardMarkup, InlineKeyboardButton, Bot
import os
from math import log10
from functools import wraps
from main import get_distance, get_azimuth, check_freq, calculate_effective_obstacle

TOKEN = os.environ.get('PATHPROFILE_TOKEN')
PORT = int(os.environ.get('PORT', 5000))
ME = os.environ.get('TELEGRAM_ID')

VERSION = 1.5
VERSION_INTRO = "Updates owner's chat when someone runs a command"

chats = {}
logs = []


def typing(func):
    """Sends typing action while processing func command."""

    @wraps(func)
    def command_func(update, context, *args, **kwargs):
        context.bot.send_chat_action(chat_id=update.effective_message.chat_id, action=ChatAction.TYPING)
        return func(update, context,  *args, **kwargs)

    return command_func


# /version
@typing
def version(update, _):
    update.message.reply_text(f"Version {VERSION}\n"
                              f"{VERSION_INTRO}")
    return -1


def log(update, command):
    username = update.message.chat.username
    message = f"{username} ran {command}"
    print(message)
    logs.append(message + "\n")

    if ME:
        bot = Bot(TOKEN)
        bot.send_message(ME, message)


@typing
def send_logs(update, _):
    if len(logs) > 0:
        update.message.reply_text("".join(logs))
    else:
        update.message.reply_text("No logs.")


# Bot replies "Hello World!" when the /start command is activated for the Bot
@typing
def start(update, _):
    log(update, "/start")
    welcome_message = "I can help you calculate path profile, azimuth, and distance between two MGRs.\n\n" \
                      "You can control me by sending these commands:\n\n" \
                      "/pathprofile - calculate path profile\n" \
                      "/distance - calculate distance (in km) between 2 MGRs\n" \
                      "/azimuth - calculate azimuth (in mils) from MGR 1 to MGR 2\n" \
                      "/cancel - cancel current operation (e.g. in case of incorrect entry)\n" \
                      "/help - show this message\n\n" \
                      "Any feedback can be directed to @xavilien"
    update.message.reply_text(welcome_message)
    return -1


@typing
def cancel(update, _):
    update.message.reply_text("Operation cancelled.")
    return -1


def get_mgr(text):
    """
    :param text: str of the following form:
    100 100
    200 200
    :return: [10.0, 10.0], [20.0, 20.0]
    """
    text = text.split()
    mgr = list(map(lambda x: float(x) / 10, text))
    return mgr[:2], mgr[2:]


@typing
def azimuth(update, context):
    r"""
    Calculates azimuth between 2 MGRs
    Matches (\d+ \d+\n\d+ \d+)
    """
    text = update.message.text
    if text == '/azimuth':
        log(update, "/azimuth")
        update.message.reply_text("Please enter the two MGRs as such:\n100 100\n200 200")
        return "azimuth"
    else:
        text = context.matches[0].group(0)  # We use the regex match in case of bad input
        mgr1, mgr2 = get_mgr(text)  # Convert raw text to the 2 mgrs
        azi = get_azimuth(mgr1, mgr2)  # Calculate azimuth
        update.message.reply_text(f"MGR 1: {text[0]} {text[1]}\nMGR 2: {text[2]} {text[3]}\nAzimuth: {azi:.0f}mils")
        return -1


@typing
def distance(update, context):
    r"""
    Calculates distance between 2 MGRs
    Matches (\d+ \d+\n\d+ \d+)
    """
    text = update.message.text
    if text == '/distance':
        log(update, "/distance")
        update.message.reply_text("Please enter the two MGRs as such:\n100 100\n200 200")
        return "distance"
    else:
        text = context.matches[0].group(0)
        mgr1, mgr2 = get_mgr(text)  # Convert raw text to the 2 mgrs
        dist = get_distance(mgr1, mgr2)  # Calculate distance
        text = text.split()
        update.message.reply_text(f"MGR 1: {text[0]} {text[1]}\nMGR 2: {text[2]} {text[3]}\nDistance: {dist:.3f}km")
        return -1


@typing
def pathprofile(update, context):
    r"""
    Initial state for the path profile calculator. Gets user to input MGR.
    Matches (\d+ \d+\n\d+ \d+)
    :return: "pathprofile" if MGR has not be inputted, "get_radio" otherwise
    """
    text = update.message.text
    chat = chats.get(update.message.chat_id)  # Keep track of variables the user has inputted

    if text == "/pathprofile":
        log(update, "/pathprofile")
        chats[update.message.chat_id] = {}
        update.message.reply_text("Please enter the two MGRs as such:\n100 100\n200 200")
        return "pathprofile"
    else:
        text = context.matches[0].group(0)
        mgr1, mgr2 = get_mgr(text)
        text = text.split()
        chat["mgr1"] = f"{text[0]} {text[1]}"
        chat["mgr2"] = f"{text[2]} {text[3]}"
        chat["distance"] = get_distance(mgr1, mgr2)

        update.message.reply_text(f"MGR 1: {chat['mgr1']}\n"
                                  f"MGR 2: {chat['mgr1']}\n"
                                  f"Distance: {get_distance(mgr1, mgr2):.1f}km")

        # Generate keyboard to ask whether the user wants to calculate for 406 or 408 radio
        options = [406, 408]
        keyboard = [[InlineKeyboardButton(str(option), callback_data=option) for option in options]]
        reply_markup = InlineKeyboardMarkup(keyboard)

        update.message.reply_text("Radio type", reply_markup=reply_markup)

        return "get_radio"


@typing
def get_radio(update, _):
    """
    Processes radio choice and asks for frequency.
    :return: get_frequency
    """
    query = update.callback_query
    chat = chats[query.message.chat.id]
    chat["radio"] = int(query.data)
    query.message.edit_text(f"Radio: {query.data}")  # Take away the inlinekeyboard to show the option picked

    query.message.reply_text("Please enter transmitting frequency to 2 decimal places.")

    return "get_freq"


@typing
def get_freq(update, context):
    r"""
    Processes frequency choice, including checks to make sure that it is valid and asks for transmitting height
    Matches (\d+\.\d+)
    :return: get_height
    """
    freq = float(context.matches[0].group(0))
    chat = chats[update.message.chat_id]
    radio = chat["radio"]

    if check_freq(radio, freq):
        chat["freq"] = freq
        update.message.reply_text(f"Transmitting frequency: {freq}MHz")
        update.message.reply_text("Please enter height of transmitting and receiving node to the nearest metre "
                                  "as such:\n"
                                  "30 40")
        return "get_height"
    else:
        update.message.reply_text("Invalid frequency, please enter again.")
        return "get_freq"


@typing
def get_height(update, context):
    r"""
    Processes transmitting and receiving height and asks for the number of obstacles between the two nodes
    Matches (\d+) (\d+)
    :return: get_obstacles
    """
    heights = context.matches[0].group(1, 2)
    chat = chats[update.message.chat_id]

    chat["ht"] = int(heights[0])
    chat["hr"] = int(heights[1])
    update.message.reply_text(f"Transmitting height: {heights[0]}m\nReceiving height: {heights[1]}m")
    update.message.reply_text("Please enter number of obstacles between the two nodes.")
    return "get_number_of_obstacles"


@typing
def get_number_of_obstacles(update, context):
    r"""
    Processes the number of obstacles between the two nodes and initialises some variables we will need for calculation.
    If there are no obstacles, calculate immediately. Otherwise, get all the obstacles by passing to get_obstacles.
    Matches (\d+)
    :return: "get_obstacles" or -1
    """
    chat = chats[update.message.chat_id]

    # Initialise some variables that we will need
    chat["number_of_obstacles"] = int(context.matches[0].group(0))
    chat["obstacles"] = []
    chat["largest_obstacle"] = (0.0, 0.0)

    if chat["number_of_obstacles"] == 0:
        return calculate(update)

    update.message.reply_text("Please enter distance between obstacle 1 and transmitting "
                              "node to the nearest km and height of obstacle 1 to the nearest metres as such:\n"
                              "5 30")
    return "get_obstacles"


@typing
def get_obstacles(update, context):
    r"""
    Processes the obstacles heights and distances between the two nodes before calling the calculate function
    that will send the results to the user. Final step of the pathprofile conversation.
    Matches (\d+) (\d+)
    """
    chat = chats[update.message.chat_id]
    d, h = list(map(float, context.matches[0].group(1, 2)))
    
    if d >= chat["distance"]:  # Make sure that the distance is valid
        update.message.reply_text("Obstacle must be between the two nodes. Please enter again.")
        return "get_obstacles"
    
    chat["obstacles"].append((d, h))
    if h > chat["largest_obstacle"][1]:
        chat["largest_obstacle"] = (d, h)

    if (count := len(chat["obstacles"])) == chat["number_of_obstacles"]:  # Check if we have details of all obstacles
        return calculate(update)

    update.message.reply_text(f"Please enter distance between obstacle {count+1} and transmitting node to the "
                              f"nearest km and height of obstacle {count+1} to the nearest metres as such:\n"
                              "5 30")
    return "get_obstacles"


def calculate(update):
    # Pull out all the relevant variables
    chat = chats[update.message.chat_id]
    mgr1 = chat["mgr1"]
    mgr2 = chat["mgr2"]
    dist = chat["distance"]
    radio = chat["radio"]
    freq = chat["freq"]
    ht = chat["ht"]
    hr = chat["hr"]

    obstacles = chat["obstacles"]
    largest_obstacle = chat["largest_obstacle"]

    message = f"MGR 1: {mgr1}\n" \
              f"MGR 2: {mgr2}\n" \
              f"Distance: {dist:.1f}km\n" \
              f"Radio: {radio}\n" \
              f"Frequency: {freq}MHz\n" \
              f"Transmitting height: {ht}m\n" \
              f"Receiving height: {hr}m\n\n"

    # Print details of all the obstacles
    for i, obstacle in enumerate(chat["obstacles"]):
        message += f"Obstacle {i + 1}\n" \
                   f"Distance: {obstacle[0]:.0f}km\n" \
                   f"Height: {obstacle[1]:.0f}m\n\n"

    # Step 2: calculate height and distance of final obstacle
    for i in range(len(obstacles)):
        for x in range(i + 1, len(obstacles)):
            obj = calculate_effective_obstacle(obstacles[i], obstacles[x], dist)
            if obj[1] > largest_obstacle[1]:
                largest_obstacle = obj

    d1 = largest_obstacle[0]
    d2 = dist - d1
    h = largest_obstacle[1]

    # Step 3: adjust height of final obstacles for earth curvature correction
    height_correction = d1 * d2 / 12.75 / 0.7
    h += height_correction

    message += f"The final calculated obstacle is {d1:.1f}km away from the transmitting node, " \
               f"with a height of {h:.1f}m\n\n"

    # Step 4: calculate height of LOS over the obstacle
    if hr > ht:
        los = (hr - ht) * d1 / dist + ht
    elif ht > hr:
        los = (ht - hr) * d2 / dist + hr
    else:
        los = ht

    message += f"The height of the LOS over the obstacle is {los:.1f}m\n\n"

    # Step 5: calculate height of 0.6 first fresnel zone
    radius = 0.6 * 548 * (d1 * d2 / freq / dist) ** 0.5
    ffz_height = los - radius

    message += f"0.6 of the first fresnel zone radius is {radius:.1f}m\n\n"

    # Step 6: find the relevant case and calculate EPL
    fsl = 20 * log10(41.87 * freq * dist)
    pel = 115.11 + 40 * log10(dist) - 20 * log10(ht * hr)

    if h < ffz_height:  # case 1/2 no obstruction within 0.6 of the first fresnel zone
        epl = fsl
        message += "Since the obstacle is not within 0.6 of the first fresnel zone, EPL = FSL\n\n"
    elif h > los:  # case 4
        if fsl > pel:
            sl_fs = 19.22 * log10(h) - 9.5 * log10(d1) + 10 * log10(freq) - 41.84
            epl = fsl + sl_fs
            message += "Since the obstacle blocks the LOS, EPL = FSL + SL\n\n"
        else:
            sl_pe = 20.3 * log10(h) - 20 * log10(d1) + 10 * log10(freq) - 40
            epl = pel + sl_pe
            message += "Since the obstacle blocks the LOS, EPL = PEL + SL\n\n"
    else:  # case 3
        epl = pel
        message += "Since the obstacle is within 0.6 of the first fresnel zone " \
                   "but does not block the LOS, EPL = PEL\n\n"

    message += f"EPL = {epl:.1f}dB\n"

    # Step 7: calculate APL, we assume receiver sensitivity using 2048MBps
    if radio == 408:
        apl = 36. + 2 * 20 - 2 * 2.4 - (-82)
    else:
        apl = 40. + 2 * 15 - 2 * 9 - (-82)
    message += f"APL = {apl}dB\n"

    # Step 8: calculate FM
    fm = apl - epl
    message += f"FM = {fm:.1f}dB\n\n"

    # Step 9: conclude if comms is through
    if fm > 20:
        message += "Comms through!!!"
    else:
        message += "No comms :("

    update.message.reply_text(message)
    return -1


def get_conversation_handler():
    mgr_filter = Filters.regex(r"(\d+ \d+\n\d+ \d+)")

    conversation_handler = ConversationHandler(
        entry_points=[CommandHandler('distance', distance),
                      CommandHandler('azimuth', azimuth),
                      CommandHandler('pathprofile', pathprofile)],
        states={
            "distance": [MessageHandler(mgr_filter, distance)],
            "azimuth": [MessageHandler(mgr_filter, azimuth)],
            "pathprofile": [MessageHandler(mgr_filter, pathprofile)],
            "get_radio": [CallbackQueryHandler(get_radio)],
            "get_freq": [MessageHandler(Filters.regex(r"(\d+\.\d+)"), get_freq)],
            "get_height": [MessageHandler(Filters.regex(r"(\d+) (\d+)"), get_height)],
            "get_number_of_obstacles": [MessageHandler(Filters.regex(r"(\d+)"), get_number_of_obstacles)],
            "get_obstacles": [MessageHandler(Filters.regex(r"(\d+) (\d+)"), get_obstacles)]
        },
        fallbacks=[CommandHandler('cancel', cancel),
                   CommandHandler('pathprofile', pathprofile),
                   CommandHandler('azimuth', azimuth),
                   CommandHandler('distance', distance)],

    )

    return conversation_handler


def main():
    updater = Updater(TOKEN)
    dp = updater.dispatcher  # Registers handlers

    dp.add_handler(get_conversation_handler())
    dp.add_handler(CommandHandler("version", version))  # To keep track of bot updates
    dp.add_handler(CommandHandler("start", start))  # Run start function when /start command is used
    dp.add_handler(CommandHandler("help", start))
    dp.add_handler(CommandHandler("logs", send_logs))

    print("Starting bot...")
    updater.start_polling()  # Start the bot

    url = "https://pathprofile.herokuapp.com/" + TOKEN
    updater.start_webhook(listen="0.0.0.0", port=PORT, url_path=TOKEN, webhook_url=url)

    updater.idle()  # Not exactly sure why this has to be here to be honest


if __name__ == '__main__':
    main()
