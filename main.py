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

parser = argparse.ArgumentParser(
    prog="main.py", description="Download anime from shinden.pl")
parser.add_argument("-s", "--silent", help="Run without opening a browser (only Linux)", action='store_true')
parser.add_argument("-l", "--link", help="Link to anime from shinden.pl")
parser.add_argument("-p", "--path", help="Download path")
parser.add_argument("-f", "--file", help="File with links to anime")
parser.add_argument(
    "-a", "--all", help="Download all episodes", action='store_true')
args = parser.parse_args()

envs = dotenv.load_dotenv("./secrets.env")
if os.getenv("LOGIN") == None or os.getenv("PASSWORD") == None:
    print("Setup LOGIN and PASSWORD envs in system or in secrets.env file!")
    exit()

start = 0
end = 0


def downloadExtention(zipLink):
    print("Downloading extention...")
    link = requests.get(zipLink)
    file = link.url.replace(
        "https://github.com/gorhill/uBlock/releases/download/", "").replace("/", "")
    open("UBOL.zip", "wb").write(
        requests.get(zipLink + file + ".chromium.mv3.zip", allow_redirects=True).content)


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


def searchForFiles(path):
    existingFiles = []
    tempPath = (args.path or "./Downloads") + "/" + path
    try:
        os.chdir(tempPath)
    except:
        return {}
    for file in os.listdir():
        if "E" in file and ".mp4" in file and not "part" in file:
            existingFiles += [int(file.replace(".mp4", "").replace("E", ""))]
    print("Found " + str(len(existingFiles)) + " downloaded episodes")
    return existingFiles


def download(num, link):
    link.replace("preview", "view")
    ydl_opts = {
        'outtmpl': (args.path or './Downloads') + "/" + animeName + '/' 'E' + str(num) + '.mp4'
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


def installChrome():
    try:
        if platform.system() == 'Windows':
            print("Installing via winget...")
            directories = os.system("winget install Hibbiki.Chromium")
            print(directories)
        elif platform.system() == 'Linux':
            print("Installing via apt...")
            directories = os.system("wget -O - https://raw.githubusercontent.com/scheib/chromium-latest-linux/master/update.sh | bash")
            System.setProperty("webdriver.chrome.driver", "./latest/chrome");
            print(directories)
        else:
            print("Unsupported OS, please install manually")
            exit()
    except:
        print("Error occured. Please install manually")
        exit()

def emailLogin():
    driver.get("https://shinden.pl/main/login")
    form = driver.find_element(By.CLASS_NAME, 'l-main-contantainer')
    try:
        #Cookies accept
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
        driver.save_screenshot('error.png')
        print("Something went wrong, please check error.png file or browser window")


animeLinks = [args.link]

if args.file == None:
    if args.link == None:
        animeLinks += [input("Enter link to the anime: ")]
else:
    f = open(args.file, "r")
    for animeLink in f:
        animeLinks += [animeLink]

if platform.system() != 'Windows':
    if(os.getenv('DISPLAY') == None):
        if args.silent or input("No display detected. Do you want to start virtual display? (Y/n)").lower() != "n":
            try:
                from xvfbwrapper import Xvfb
                print("Starting virtual display")
                vdisplay = Xvfb(width=1920, height=1080, colordepth=16)
                vdisplay.start()
            except:
                if input("Couldn't start virtual display. Do you want to install Xvfb? (Y/n)").lower() != "n":
                    global xvfbInstalled
                    xbfbInstalled = True
                    print("Installing via apt...")
                    directories = os.system("sudo apt -y install xvfb")
                    print(directories)
                    from xvfbwrapper import Xvfb
                    print("Starting virtual display")
                    vdisplay = Xvfb(width=1920, height=1080, colordepth=16)
                    vdisplay.start()
                else:
                    print("Running without virtual display...")

downloadExtention(
    "https://github.com/gorhill/uBlock/releases/latest/download/")

options = ChromeOptions()
options.add_extension("./UBOL.zip")
chromeInstalled: bool = False
try:
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--no-sandbox")
    service_object = Service(binary_path)
    driver = webdriver.Chrome(service=service_object, options=options)
    
except:
    chromeInstalled = input("Couldn't open Chrome nor Chromium. This script requires any of these to work. Do you want to install Chromium? (Y/n)").lower != "n"
    if chromeInstalled:
        installChrome();
        print("Chrome/Chromium installed")
        options.add_argument("--disable-dev-shm-usage")
        options.add_argument("--no-sandbox")
        service_object = Service(binary_path)
        driver = webdriver.Chrome(service=service_object, options=options)
        
driver.maximize_window()
print("Singing in...")
emailLogin()


for animeLink in animeLinks:
    showLink = animeLink
    try:
        if "all-episodes" not in showLink:
            showLink = showLink + "/all-episodes"
    except:
        continue
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
        break
    else:
        print("Found " + str(len(episodes)) + " episodes")
        end = len(episodes)
        print("Searching for links...")

    if not args.all:
        start = input("Start episode: ")
        end = input("End episode: ")

    skipEpisodes = searchForFiles(animeName)

    episodes.reverse()
    for episode in episodes:
        if args.all:
            if episode.num not in range(int(start), int(end)):
                continue
            elif episode.num in skipEpisodes:
                print("Skipping episode " + str(episode.num) +
                      " because it's already downloaded")
                continue

        searchLinks(episode)

driver.quit()
if platform.system() != 'Windows':
    vdisplay.stop()

if chromeInstalled:
    if input("Do you want to remove Chromium? (y/N)").lower == "y":
        if platform.system() == 'Windows':
            os.system("winget uninstall Hibbiki.Chromium")
        elif platform.system() == 'Linux':
            os.system("sudo apt remove chromium -y")
        else:
            print("Unsupported OS, please remove manually")
            exit()
    else:
        if platform.system() == 'Windows':
            print("You can remove it by typing 'winget uninstall Hibbiki.Chromium' in cmd")
        elif platform.system() == 'Linux':
            print("You can remove it by typing 'sudo apt remove chromium -y' in terminal")

if xbfbInstalled:
    if input("Do you want to remove Xvfb? (y/N)").lower == "y":
        if platform.system() == 'Linux':
            os.system("sudo apt remove xvfb -y")
        else:
            print("Unsupported OS, please remove manually")
            exit()
    else:
        if platform.system() == 'Linux':
            print("You can remove it by typing 'sudo apt remove xvfb -y' in terminal")
