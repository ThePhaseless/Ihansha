from dataclasses import dataclass
import argparse
import os
import time
import dotenv
import platform
import requests
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.wait import WebDriverWait
from yt_dlp import YoutubeDL
from selenium.webdriver.chrome.options import Options as ChromeOptions
from selenium.webdriver.chrome.service import Service
from chromedriver_py import binary_path
from selenium.webdriver.support import expected_conditions as EC
import configparser
import logging

logging.basicConfig(level=logging.INFO,
                    format='%(asctime)s %(levelname)s %(message)s')
logging.info('Starting the program...')

config = configparser.ConfigParser()
config.read('config.ini')


parser = argparse.ArgumentParser(
    prog="main.py", description="Download anime from shinden.pl")
parser.add_argument(
    "-s", "--silent", help="Run without opening a browser (Linux only)", action='store_true')
parser.add_argument("-l", "--link", help="Link to anime from shinden.pl")
parser.add_argument("-p", "--path", help="Download path")
parser.add_argument("-f", "--file", help="File with links to anime")
parser.add_argument(
    "-a", "--all", help="Download all episodes", action='store_true')
args = parser.parse_args()

envs = dotenv.load_dotenv("./secrets.env")
if os.getenv("LOGIN") == None or os.getenv("PASSWORD") == None:
    logging.critical(
        "Setup LOGIN and PASSWORD envs in system or in secrets.env file!")
    exit()

xbfbInstalled = False  # set to true if installed with this script
chromeInstalled = False  # set to true if installed with this script

start = 0
end = 0

dlPath = "./Downloads"
linkFile = None
silent = False

if config['config']['path'] == None:
    if args.path != None:
        dlPath = args.path
else:
    dlPath = config['config']['path']

if config['config']['links'] == None:
    linkFile = args.file
else:
    linkFile = config['config']['links']

if config['config']['silent'] == None:
    silent = args.silent
else:
    silent = config['config']['silent']


def downloadExtention(zipLink, filename):
    logging.info("Downloading extention...")
    try:
        open(filename, "wb").write(requests.get(
            zipLink, allow_redirects=True).content)
    except any as e:
        logging.error("Error while downloading extention: " + str(e))
        logging.error("Using downloaded extention...")


class HostingLink:
    def __init__(self, service: str, quality: str, voice: str, subtitles: str, added: str, link: str):
        self.service = service
        self.quality = quality
        self.voice = voice
        self.subtitles = subtitles
        self.added = added
        self.link = link


class Episode:
    def __init__(self, num: int, title: str, online: bool, PL: bool, watched: bool, link: str, hostingLinks: list):
        self.num = num
        self.title = title
        self.online = online
        self.PL = PL
        self.watched = watched
        self.link = link
        self.hostingLinks = hostingLinks


def searchForFiles(path):
    existingFiles = []
    tempPath = dlPath + "/" + path
    try:
        os.chdir(tempPath)
    except:
        return {}
    for file in os.listdir():
        if "E" in file and ".mp4" in file and not "part" in file:
            existingFiles += [int(file.replace(".mp4", "").replace("E", ""))]
    logging.info("Found " + str(len(existingFiles)) + " downloaded episodes")
    return existingFiles


def download(num, link):
    link.replace("preview", "view")
    ydl_opts = {
        'outtmpl': dlPath + "/" + animeName + '/' 'E' + str(num) + '.mp4'
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
                    logging.info("Waiting for iframe...")
                    time.sleep(6)
                    dlLink = driver.find_element(By.CLASS_NAME, "player-online").find_element(By.TAG_NAME,
                                                                                              'iframe').get_attribute(
                        "src")
                    if "captcha" in dlLink:
                        logging.error("Wrong url, trying another mirror...")
                        continue
                    break
                except:
                    logging.error("Captcha error, trying again")
                    time.sleep(1)
                    continue

            time.sleep(1)
            download(ep.num, dlLink)
            break


def installChrome():
    try:
        if platform.system() == 'Windows':
            logging.info("Installing via winget...")
            directories = os.system("winget install Hibbiki.Chromium")
            logging.info(directories)
        elif platform.system() == 'Linux':
            logging.info(
                "Installing via script from https://github.com/scheib/chromium-latest-linux...")
            directories = os.system(
                "wget -O - https://raw.githubusercontent.com/scheib/chromium-latest-linux/master/update.sh | bash")
            chromeInstalled = True
            logging.info(directories)
        else:
            logging.error("Unsupported OS, please install manually")
            exit()
    except:
        logging.info("Couldn't install Chromium. Please install manually.")
        exit()
    logging.info("Chrome/Chromium installed")


def acceptPrivacyPoilcy():
    wait = WebDriverWait(driver, 10)
    wait.until(EC.element_to_be_clickable(
        (By.XPATH, "/html/body/div[11]/div[1]/div[2]/div/div[2]/button[2]")))
    driver.find_element(
        By.XPATH, "/html/body/div[11]/div[1]/div[2]/div/div[2]/button[2]").click()


def emailLogin():
    driver.get("https://shinden.pl/main/login")
    acceptPrivacyPoilcy()
    form = driver.find_element(By.CLASS_NAME, 'l-main-contantainer')
    try:
        # Cookies accept
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
            logging.critical("Wrong credentials!")
    except any as e:
        driver.save_screenshot('error.png')
        logging.critical(
            "Something went wrong, please check error.png file or browser window, error: " + str(e))


def virtualDisplay():
    if platform.system() != 'Windows':
        if os.getenv('DISPLAY') == None:
            logging.info("No display detected, starting virtual display...")
        elif not silent:
            if input("No display detected. Do you want to start virtual display? (Y/n)").lower() == "n":
                return
        try:
            from xvfbwrapper import Xvfb
            logging.info("Starting virtual display")
            vdisplay = Xvfb(width=1920, height=1080, colordepth=16)
            vdisplay.start()
        except:
            if input("Couldn't start virtual display. Do you want to install Xvfb? (Y/n)").lower() != "n":
                global xvfbInstalled
                xbfbInstalled = True
                logging.info("Installing via apt...")
                directories = os.system("sudo apt -y install xvfb")
                logging.info(directories)
                from xvfbwrapper import Xvfb
                logging.info("Starting virtual display")
                vdisplay = Xvfb(width=1920, height=1080, colordepth=16)
                vdisplay.start()
            else:
                logging.info("Running without virtual display...")
                return
        return vdisplay
    return


animeLinks = []
if args.link != None:
    animeLinks += [args.link]

# Get links from file and from user input
if linkFile == '' or linkFile == None:
    if args.link == None:
        animeLinks += [input("Enter link to the anime: ")]
elif linkFile != '' and linkFile != None:
    try:
        f = open(linkFile, "r")
        for animeLink in f:
            animeLinks += [animeLink]
    except:
        logging.critical("Couldn't open file with links")
        exit()


vdisplay = virtualDisplay()

downloadExtention(
    "https://github.com/gorhill/uBlock/releases/download/uBOLite_0.1.23.4076/uBOLite_0.1.23.4076.chromium.mv3.zip", "UBOL.zip")

# start Chromium
options = ChromeOptions()
options.add_extension("./UBOL.zip")
chromeInstalled: bool = False
options.add_argument("--disable-dev-shm-usage")
options.add_argument("--no-sandbox")
options.add_argument("--lang=pl")
try:
    service_object = Service(binary_path)
    driver = webdriver.Chrome(service=service_object, options=options)

except any as e:
    logging.exception("Chrome/Chromium error: " + str(e))
    chromeInstalled = input(
        "Do you want to try installing Chromium? (Y/n)").lower() != "n"
    if chromeInstalled:
        installChrome()
        if platform.system() == 'linux' and chromeInstalled:
            options.binary_location = "./latest/chrome"
        options.add_argument("--disable-dev-shm-usage")
        options.add_argument("--no-sandbox")
        service_object = Service(binary_path)
        driver = webdriver.Chrome(service=service_object, options=options)
    else:
        logging.exception("Chrome/Chromium not installed. Exiting...")
        exit()

logging.info("Waiting for privacy policy...")


logging.info("Singing in...")
emailLogin()

# Begin scraping
for animeLink in animeLinks:
    showLink = animeLink

    if "all-episodes" not in showLink:
        showLink = showLink + "/all-episodes"

    try:
        driver.get(showLink)
    except:
        continue
    animeName = driver.find_element(By.CLASS_NAME, "title").text
    WebDriverWait(driver, timeout=5).until(
        lambda d: d.find_element(By.CLASS_NAME, "list-episode-checkboxes"))
    logging.debug(driver.current_url)

    unavailable = []
    episodes = []

    episodesRaw = driver.find_element(
        By.CLASS_NAME, "list-episode-checkboxes").find_elements(By.TAG_NAME, "tr")

    for episode in episodesRaw:
        listTemp = episode.find_elements(By.XPATH, "./*")
        temp = Episode(int(listTemp[0].text), str(listTemp[1]), False, False, False,
                       listTemp[5].find_element(By.TAG_NAME, "a").get_attribute("href"), [])
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
        logging.info("Episodes not available: ")
        logging.info(unavailable)
    if len(episodes) == 0:
        logging.info("No available episodes!")
        break
    else:
        logging.info("Found " + str(len(episodes)) + " episodes")
        end = len(episodes)
        logging.info("Searching for links...")

    if not args.all:
        start = input("Start episode: ")
        end = input("End episode: ")

    skipEpisodes = searchForFiles(animeName)

    episodes.reverse()
    for episode in episodes:
        # print type of episode
        if args.all:
            if episode.num not in range(int(start), int(end)):
                continue
            elif episode.num in skipEpisodes:
                logging.info("Skipping episode " + str(episode.num) +
                             " because it's already downloaded")
                continue

        searchLinks(episode)

driver.quit()
if vdisplay != None:
    vdisplay.stop()

if chromeInstalled:
    if input("Do you want to remove Chromium? (y/N)").lower() == "y":
        if platform.system() == 'Windows':
            os.system("winget uninstall Hibbiki.Chromium")
        elif platform.system() == 'Linux':
            os.system("sudo apt remove chromium -y")
        else:
            logging.exception("Unsupported OS, please remove manually")
            exit()
    else:
        if platform.system() == 'Windows':
            logging.info(
                "You can remove it by typing in cmd: \n winget uninstall Hibbiki.Chromium")
        elif platform.system() == 'Linux':
            print(
                "You can remove it by typing in terminal: \n ls \n sudo rm -R ./<folder-with-random-numbers>")

if xbfbInstalled and platform.system() != 'Windows':
    if input("Do you want to remove Xvfb? (y/N)").lower() == "y":
        if platform.system() == 'Linux':
            os.system("sudo apt remove xvfb -y")
        else:
            logging.info("Unsupported OS, please remove manually")
    else:
        if platform.system() == 'Linux':
            print("You can remove it by typing in terminal: \n sudo apt remove xvfb -y")
