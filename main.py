from ast import arg
from asyncio.windows_events import NULL
from dataclasses import dataclass
import argparse
import os
import time
from traceback import print_tb
import dotenv
import platform
import requests
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.wait import WebDriverWait
from yt_dlp import YoutubeDL
from selenium.webdriver.edge.options import Options as EdgeOptions
from selenium.webdriver.edge.service import Service as EdgeService
from webdriver_manager.microsoft import EdgeChromiumDriverManager

parser = argparse.ArgumentParser(
    prog="main.py", description="Download anime from shinden.pl")
parser.add_argument("-l", "--link", help="Link to anime from shinden.pl")
parser.add_argument("-p", "--path", help="Download path")
parser.add_argument(
    "-a", "--all", help="Download all episodes", action='store_true')
args = parser.parse_args()

envs = dotenv.load_dotenv("./secrets.env")
if os.getenv("LOGIN") == NULL or os.getenv("PASSWORD") == NULL:
    print("Setup LOGIN and PASSWORD envs in system or in secrets.env file!")
    exit()

animeLink = args.link or input("Shinden Link: ")

start = 0
end = 0


def downloadExtention(zipLink):
    print("Downloading extention...")
    link = requests.get(zipLink)
    file = link.url.replace(
        "https://github.com/gorhill/uBlock/releases/download/", "").replace("/", "")
    open("UBOL.zip", "wb").write(
        requests.get(zipLink + file + ".mv3.zip", allow_redirects=True).content)


@dataclass
class HostingLink:
    service: str
    quality: str
    voice: str
    subtitles: str
    added: str
    link: str


@dataclass
class Episode:
    num: int
    title: str
    online: bool
    PL: bool
    watched: bool
    link: str
    hostingLinks = []


def searchForFiles(seriesName):
    existingFiles = {}
    path = (vars.path or "./Downloads") + "/" + seriesName
    os.getcwd(path)
    for file in os.listdir():
        if "E" in file:
            existingFiles += {file.replace(".mp4", "").replace("E", "")}
    print("Found at least " + len(existingFiles) + " files")
    return existingFiles


def download(num, link):
    link.replace("preview", "view")
    ydl_opts = {
        'outtmpl': (args.path or 'Downloads') + "/" + animeName + '/' 'E' + str(num) + '.mp4'
    }
    with YoutubeDL(ydl_opts) as ydl:
        ydl.download(link)


def searchLinks(ep: Episode):
    supportedHostings = ['Gdrive', 'Cda', 'Vk', 'Dailymotion', 'Sibnet']
    driver.get(ep.link)
    listTemp = driver.find_element(By.CLASS_NAME, "table-responsive").find_element(By.TAG_NAME, "tbody").find_elements(
        By.TAG_NAME, "tr")
    driver.find_element(By.CLASS_NAME, "mobile-close").click()
    for link in listTemp:
        dlLink = ""
        time.sleep(1)
        if (link.find_element(By.CLASS_NAME, 'ep-pl-name').text in supportedHostings):
            while True:
                button = link.find_element(
                    By.CLASS_NAME, "ep-buttons").find_element(By.TAG_NAME, "a")
                button.click()

                try:
                    print("Waiting for iframe...")
                    time.sleep(6)
                    dlLink = driver.find_element(By.CLASS_NAME, "player-online").find_element(By.TAG_NAME,
                                                                                              'iframe').get_attribute(
                        "src")
                    if "captcha" in dlLink:
                        print("Wrong url, trying another mirror...")
                        continue
                    break
                except:
                    print("Captcha error, trying again")
                    time.sleep(1)
                    continue
            # try:
            time.sleep(1)
            download(ep.num, dlLink)
            break
            # except:
            #   print("Download failed, trying next hosting...")


def emailLogin():
    driver.get("https://shinden.pl/main/login")
    form = driver.find_element(By.CLASS_NAME, 'l-main-contantainer')
    try:
        WebDriverWait(driver, timeout=3).until(
            lambda d: d.find_element(By.CLASS_NAME, "details_save--3nDG7"))
        driver.find_element(By.CLASS_NAME, "details_save--3nDG7").click()
    except:
        print()
    try:
        WebDriverWait(driver, timeout=3).until(
            lambda d: d.find_element(By.CLASS_NAME, "cb-enable"))
        driver.find_element(By.CLASS_NAME, "cb-enable").click()

        while True:
            form.find_element(
                By.CSS_SELECTOR, '[name="username"]').send_keys(os.getenv('LOGIN'))
            form.find_element(
                By.CSS_SELECTOR, '[name="password"]').send_keys(os.getenv('PASSWORD'))
            form.find_element(By.CSS_SELECTOR, '[type="submit"]').click()
            if driver.current_url != "https://shinden.pl/main/login":
                break
            print("Wrong credentials")
    except:
        print("Wrong credentials")


options = EdgeOptions()
options.headless = False

if platform.system() != 'Windows':
    from xvfbwrapper import Xvfb

    options.headless = False
    print("Starting virtual display")
    vdisplay = Xvfb(width=1920, height=1080, colordepth=16)
    vdisplay.start()

downloadExtention(
    "https://github.com/gorhill/uBlock/releases/latest/download/")
options.add_extension("./UBOL.zip")

try:
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--no-sandbox")
    driver = webdriver.Edge(service=EdgeService(
        EdgeChromiumDriverManager().install()), options=options)

except:
    print("Couldn't open Edge, make sure to install it before running this script")
    exit()

print("Singing in...")
emailLogin()
driver.maximize_window()

showLink = animeLink
if "all-episodes" not in showLink:
    showLink = showLink + "/all-episodes"
try:
    driver.get(showLink)
    animeName = driver.find_element(By.CLASS_NAME, "title").text
    WebDriverWait(driver, timeout=5).until(
        lambda d: d.find_element(By.CLASS_NAME, "list-episode-checkboxes"))
    print(driver.current_url)
except:
    exit()

unavailable = []
episodes = []

episodesRaw = driver.find_element(
    By.CLASS_NAME, "list-episode-checkboxes").find_elements(By.TAG_NAME, "tr")

for episode in episodesRaw:
    listTemp = episode.find_elements(By.XPATH, "./*")
    temp = Episode(int(listTemp[0].text), str(listTemp[1]), False, False, False,
                   listTemp[5].find_element(By.TAG_NAME, "a").get_attribute("href"))
    if listTemp[2].find_element(By.TAG_NAME, "i").get_attribute("class") == "fa fa-fw fa-check":
        temp.online = True
    else:
        unavailable += [int(listTemp[0].text)]
        continue
    if listTemp[3].find_element(By.TAG_NAME, "span").get_attribute("title") == "Polski":
        temp.PL = True
    else:
        unavailable += [int(listTemp[0].text)]
        continue
    if listTemp[6].find_element(By.TAG_NAME, "i").get_attribute("class") == "fa fa-fw fa-check-square-o":
        temp.watched = True
    episodes += [temp]


if len(unavailable) > 0:
    print("Episodes not available: ")
    print(unavailable)
if len(episodes) == 0:
    print("No available episodes!")
else:
    print("Found " + str(len(episodes)) + " episodes")
    print("Searching for links...")

if not args.all:
    start = input("Start episode: ")
    end = input("End episode: ")

episodes.reverse()
for episode in episodes:
    if args.all:
        if episode.num not in range(int(start), int(end)):
            continue
        elif episode.num not in searchForFiles(animeName):
            print("Skipping episode " + episode.num +
                  " because it's already downloaded")

    searchLinks(episode)

driver.quit()
if platform.system() != 'Windows':
    vdisplay.stop()
