#Script to check nvidia's website for changes in the URL of the FE cards and try to add to cart on nbb
from typing import final
import requests
from datetime import datetime
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from fake_useragent import UserAgent
import time
import yaml
from fake_useragent import UserAgent
import os
import undetected_chromedriver.v2 as uc
import sys
from bs4 import BeautifulSoup
import re
import asyncio


def get_bavarnoldurl(url):
    r = requests.get(url)
    soup = BeautifulSoup(r.content, "html.parser")
    urls = []
    for a in soup.find_all('a', href=True):
        if 'https://www.awin1.com' in a['href']:
            urls.append(a['href'])
    return urls


url = "https://cutt.ly/QnEoXla"

print(get_bavarnoldurl(url))