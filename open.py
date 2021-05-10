'''
Script to monitor links sent to discord channels and opening them in a new browser tab.
Generalized version
by https://github.com/Smidelis
based on https://github.com/clearyy/discord-link-opener and https://github.com/Vincentt1705/partalert-link-opener
'''

import webbrowser
import asyncio
import discord
from discord.ext.commands import Bot
from discord.ext import commands
import re
import winsound
from datetime import datetime

#pylint: disable=anomalous-backslash-in-string

client = Bot('KarlaKolumna')
client.remove_command('help')

# Prompt users for keywords to search for in the links.
keywords = list(map(str,input("Enter keywords to search for, seperated by space: ").split()))

# Prompt user to enter negative keywords that will prevent a browser window from opening. To have no blacklisted words, press enter right away
blacklist = list(map(str,input("Enter blacklisted keywords, seperated by space: ").split()))

# Enter channel id(s) where links would be picked up (monitor channel id) seperated by commas. these should be ints
channels = []

# Enter token of discord account that has access to watch specified channels
token = ''

global start_count
start_count = 0

# Decide whether you want to hear a bell sound when a link is opened (True/False)
playBellSound = True

# Based on https://github.com/Vincentt1705/partalert-link-opener
# Function to print the current time before the information about the link.
def print_time(*content):
    """
    Can be used as a normal print function but includes the current date and time
    enclosed in brackets in front of the printed content.
    :param content: The content you would normally put in a print() function
    """
    now = datetime.now()
    date_time = now.strftime("%d/%m/%Y %H:%M:%S")
    print(f"[{date_time}] - [INFO] ", *content)

# Check for keywords and blacklisted words in message urls and open browser if conditions are met
async def check_urls(urls, channel_name):
    for url in urls:
        if any(x in url.lower() for x in keywords) and all(x not in url.lower() for x in blacklist):
            # Enter path to your browser
            webbrowser.get("C:/Program Files (x86)/Microsoft/Edge/Application/msedge.exe %s").open(url)
            print_time(f'Link opened from #{channel_name}: {url}')
            if playBellSound:
                winsound.PlaySound('bell.wav', winsound.SND_FILENAME)

async def get_last_msg(channelid):
    msg = await client.get_channel(channelid).history(limit=1).flatten()
    return msg[0]

@client.event
async def on_ready():
    print_time('{} is ready to watch for links.'.format(str(client.user)))
    if len(keywords) >= 1 and keywords[0] != '':
        print_time('Watching for keywords {}.'.format(', '.join(keywords)))
    else:
        print_time('No keywords have been provided.')
    if len(blacklist) > 0:
        print_time('Ignoring keywords {}.'.format(', '.join(blacklist)))
    else:
        print_time('No keywords currently blacklisted.')

# Fixed discordpy not able to read embeds anymore. Thanks to dubble#0001 on Discord.
@client.event
async def on_message(message):
    if message.channel.id in channels:
        await asyncio.sleep(0.3)
        last_msg = await get_last_msg(message.channel.id)
        try:
            fields = last_msg.embeds[0].fields
            linkembed = next(x for x in fields if x.name == "Link")
            urls = re.findall('http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*(),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+', linkembed.value if linkembed else "")
            for url in urls:
                await check_urls(urls, message.channel.name)
        except:
            if last_msg.content != '':
                urls = re.findall("(?:(?:https?|ftp):\/\/)?[\w/\-?=%.#&+]+\.[\w/\-?=%.#&+]+",last_msg.content)
                if urls:
                    await check_urls(urls, message.channel.name)

client.run(token,bot=False)
