#!/usr/bin/env python

import asyncio
import configparser
import sys

from datetime import date
from termcolor import colored
from telegram import ForceReply, Update
from telegram.constants import ChatMemberStatus
from telegram.ext import Application, CommandHandler, ContextTypes, MessageHandler, filters

from telethon.sync import TelegramClient


DRY_RUN = False
CONFIG = None
BOT = None
TELETHON_CLIENT = None
MONTHS = ['Enero', 'Febrero', 'Marzo', 'Abril', 'Mayo', 'Junio', 'Julio', 'Agosto', 'Septiembre', 'Octubre', 'Noviembre', 'Diciembre']

def configure_bot_mode():
    global DRY_RUN
    DRY_RUN = not(CONFIG.has_option('config', 'mode') and get_config_value('mode') == 'live')
    if(DRY_RUN):
        print(colored("Running in [DRY_RUN] mode, actions will be simulated.", 'green', attrs=['bold', 'underline']))
    else:
        print(colored("Running in live mode.", 'red', attrs=['bold', 'underline']))
        wait_for_confirmation()

def wait_for_confirmation():
    while True:
        user_input = input("Enter 'accept' to continue or type 'exit' to quit: ")
        if user_input == 'accept':
            break
        elif user_input == 'exit':
            sys.exit()
        print("Incorrect command: " + user_input)

def get_config_value(key):
    return CONFIG.get('config', key)

def initialize_config():
    global CONFIG 
    CONFIG = configparser.ConfigParser()
    CONFIG.read('config.ini')

def initialize_bot():
    global BOT
    BOT = Application.builder().token(get_config_value('bot_token')).build().bot

def initialize_telethon_client():
    global TELETHON_CLIENT
    TELETHON_CLIENT = TelegramClient('bot', get_config_value('api_id'), get_config_value('api_hash'))   
    TELETHON_CLIENT.start()
    TELETHON_CLIENT.connect()

def get_updated_invite_link(channel_id):
    invite_link = None
    if(DRY_RUN):
        print(colored('New channel invite will be generated, old one will be invalidated.', 'cyan'))
        invite_link = 'https://t.me/+newchannel'
    else:
        invite_link = asyncio.get_event_loop().run_until_complete(BOT.export_chat_invite_link(chat_id=channel_id))
    print('New channel invite: ' + colored(invite_link, 'yellow'))

def kick_member(channel_id, member):
    if(DRY_RUN):
        print("Member: " + colored("@" + member.user.username, 'red') + " will be removed from chat.")
    else:
        asyncio.get_event_loop().run_until_complete(BOT.ban_chat_member(chat_id=channel_id, user_id=member.user.id, until_date=31))
        print("Member: " + colored("@" + member.user.username, 'red') + " was removed from chat")

def get_config_channels():
    return get_config_value('channels').split()

async def get_users(client, channel_id):
    users = []
    async for user in client.iter_participants(channel_id):
      if not user.deleted:
        users.append(user)
    return users

def get_users_in_channel(channel_id):
    return asyncio.get_event_loop().run_until_complete(get_users(TELETHON_CLIENT, int(channel_id)))

def get_member_in_channel(channel_id, user_id):
    return asyncio.get_event_loop().run_until_complete(BOT.get_chat_member(chat_id=channel_id, user_id=user_id))

def should_kick_member(member):
    return member.status != ChatMemberStatus.ADMINISTRATOR and member.status != ChatMemberStatus.OWNER

def get_actual_channel_name(channel_id):
    return asyncio.get_event_loop().run_until_complete(BOT.get_chat(channel_id)).title

def update_channel_title(channel_id):
    updated_title = get_update_channel_title(channel_id)
    if(DRY_RUN):
        print('New channel title will be: ' + colored(updated_title, 'green'))
    else:
        asyncio.get_event_loop().run_until_complete(BOT.set_chat_title(channel_id, updated_title))

def get_update_channel_title(channel_id):
    today = date.today()
    title = get_actual_channel_name(channel_id).split()
    title[len(title) - 2] = MONTHS[int(today.month) - 1]
    title[len(title) - 1] = "\'" + str(today.year % 100)
    updated_title = ' '.join(title)
    print(colored('Configure new channel title', 'light_blue'))
    user_title = input('Press ENTER to confirm default title (' + colored(updated_title, 'light_green') + '):')
    if user_title != '':
         updated_title = user_title
    return updated_title

def kick_users(channel_id, users):
    counter = 0
    for user in users:
        member = get_member_in_channel(channel_id, user.id)
        if(should_kick_member(member)):
            kick_member(channel_id, member)
            counter += 1
    print(colored('A total of (' + str(counter) + ') users has been kicked out of the channel.', 'yellow'))

def main() -> None:

    initialize_config()
    initialize_bot()
    initialize_telethon_client()
    configure_bot_mode()

    for channel_id in get_config_channels():
        print(colored('The following actions will be performed on channel: [' + get_actual_channel_name(channel_id) + ']', 'yellow', attrs=['bold', 'underline']))
        users = get_users_in_channel(channel_id)
        kick_users(channel_id, users)
        update_channel_title(channel_id)
        get_updated_invite_link(channel_id)

if __name__ == "__main__":
    main()