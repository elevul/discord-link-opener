'''
Script to monitor links sent to discord channels and opening them in a new browser tab.
Adapted to monitor links sent by https://partalert.net/join-discord

by https://github.com/Smidelis
based on https://github.com/clearyy/discord-link-opener and https://github.com/Vincentt1705/partalert-link-opener

'''

import webbrowser
import asyncio
from discord.ext.commands import Bot
import re
import winsound
from datetime import datetime
import urllib.parse as urlparse
from urllib.parse import parse_qs
import yaml
from azure.servicebus import ServiceBusClient, ServiceBusMessage
from datetime import datetime
from bs4 import BeautifulSoup
import requests

#pylint: disable=anomalous-backslash-in-string

client = Bot('KarlaKolumna')
client.remove_command('help')

#Pulling configuration from yaml file
with open("config.yml", "r") as ymlfile:
    cfg = yaml.load(ymlfile, Loader=yaml.FullLoader)

#Registering the browsers and preparing the choice
webbrowser.register('chrome', None, webbrowser.BackgroundBrowser(cfg['browsers']['chrome']['path']))
webbrowser.register('edgechromium', None, webbrowser.BackgroundBrowser(cfg['browsers']['edgechromium']['path']))
webbrowser.register('firefox', None, webbrowser.BackgroundBrowser(cfg['browsers']['firefox']['path']))
browserchoice = cfg['browsers']['user_choice']

# Pulling keywords from yml config file
keywords = cfg['filters']['keywords']

#Pulling Service Bus from config file
CONNECTION_STR = cfg['servicebus']['CONNECTION_STR']
TOPIC_NAME = cfg['servicebus']['TOPIC_NAME']
date = datetime.now().strftime("%d_%m_%Y")

# Pulling blacklist from yml file and accounting for it being null
black = cfg['filters']['blacklist']
if black == [None]:
    blacklist = ''
else:
    blacklist = black
print(blacklist)

# Pulling channels from yml file
channels = cfg['channels']

# Pulling token from the yml file
token = cfg['token']

global start_count
start_count = 0

# Decide whether you want to hear a bell sound when a link is opened (True/False)
playBellSound = cfg['various']['playBellSound']

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

# Function to build the amazon url, where partalert is redirecting to
def get_amazon_url(url):
    r = requests.get(url)
    soup = BeautifulSoup(r.content, "html.parser")
    urls = []
    for a in soup.find_all('a', href=True):
        if 'partalert.net' not in a['href']:
            urls.append(a['href'])
    return urls

def get_bavarnoldurl(url):
    r = requests.get(url)
    soup = BeautifulSoup(r.content, "html.parser")
    urls = []
    for a in soup.find_all('a', href=True):
        if 'https://www.awin1.com' in a['href']:
            urls.append(a['href'])
    return urls

# Check for keywords and blacklisted words in message urls and open browser if conditions are met
async def check_urls(urls, channel_name):
    for url in urls:
        if any(x in url.lower() for x in keywords) and all(x not in url.lower() for x in blacklist):
            # Check if url contains partalert.net. If true, direct amazon link will be built.
            if "partalert.net" in url:
                amazon_urls = get_amazon_url(url)
                for amazon_url in amazon_urls:
                    webbrowser.open_new_tab(amazon_url)
                    print_time(f'Link opened from #{channel_name}: {amazon_url}')
            elif "cutt.ly" in url:
                bavarnold_urls = get_bavarnoldurl(url)
                for bavarnold_url in bavarnold_urls:
                    webbrowser.open_new_tab(bavarnold_url)
                    print_time(f'Link opened from #{channel_name}: {bavarnold_url}')
            else: 
                # Enter path to your browser
                webbrowser.get(browserchoice).open_new_tab(url)
                print_time(f'Link opened from #{channel_name}: {url}')
            if playBellSound:
                winsound.PlaySound('bell.wav', winsound.SND_FILENAME)

async def get_last_msg(channelid):
    msg = await client.get_channel(channelid).history(limit=1).flatten()
    return msg[0]

async def send_single_message(message):
    servicebus_client = ServiceBusClient.from_connection_string(conn_str=CONNECTION_STR, logging_enable=True)
    with servicebus_client:
        # get a Queue Sender object to send messages to the queue
        sender = servicebus_client.get_topic_sender(topic_name=TOPIC_NAME)
        with sender:
            # send one message
            sender.send_messages(message)
    print_time("Sent a single message")

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
        urls = re.findall('(http[s]?:\/\/(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*(),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+)', last_msg.content)
        ldlcidentifiers = re.findall('http[s]?:\/\/www\.ldlc\.com.*(PB\d*.html)', last_msg.content)
        print(str(ldlcidentifiers))
        try:
            if ldlcidentifiers:
                url = 'https://www.ldlc.com/fiche/' + ldlcidentifiers[0]
                cardfull = re.findall('NVIDIA RTX (.* [Tt]?[Ii]?)\(?\w*\)?',last_msg.content)[0]
                cardname = re.sub('\s+','',cardfull).lower()
                print_time('Sending ' + cardname + ' - ' + url)
                messageservicebus = ServiceBusMessage(
                    url,
                    message_id=cardname
                )
                asyncio.ensure_future(send_single_message(messageservicebus))
        except:
            print('Message is malformed. Ignoring for the purpose of sending a message to the queue')
        asyncio.ensure_future(check_urls(urls, message.channel.name))
client.run(token,bot=False)
