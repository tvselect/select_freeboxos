import json
import logging
import sys

from subprocess import Popen, PIPE
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo
from time import sleep
from selenium import webdriver
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.common.exceptions import NoSuchElementException

from channels_free import CHANNELS_FREE

cmd = "echo $USER"
echo = Popen(cmd, stdout=PIPE, stderr=PIPE, shell=True)
stdout, stderr = echo.communicate()
user = stdout.decode("utf-8")[:-1]

sys.path.append("/home/" + user + "/.config/select_freeboxos")

from config import (
    ADMIN_PASSWORD,
    FREEBOX_SERVER_IP,
    IPTV_SELECT_TITLES,
    MAX_SIM_RECORDINGS,
)


logging.basicConfig(
    filename="/var/tmp/freeboxos.log",
    format="%(asctime)s %(levelname)s: %(message)s",
    level=logging.INFO,
)


def exito():
    cmd = "killall cheese"
    Popen(cmd, stdout=PIPE, stderr=PIPE, shell=True)
    exit()


try:
    with open(
        "/home/" + user + "/.local/share/select_freeboxos" "/info_progs.json", "r"
    ) as jsonfile:
        data = json.load(jsonfile)
except FileNotFoundError:
    logging.error(
        "No info_progs.json file. Need to check curl command or "
        "internet connection. Exit programme."
    )
    exit()

if len(data) == 0:
    cmd = (
        "cp /home/" + user + "/.local/share/select_freeboxos"
        "/info_progs.json /home/" + user + "/.local/share/select"
        "_freeboxos/info_progs_last.json"
    )
    Popen(cmd, stdout=PIPE, stderr=PIPE, shell=True)
    logging.info("No data to record programmes. Exit programme.")
    exit()

service = Service(executable_path="./geckodriver")
options = webdriver.FirefoxOptions()
options.add_argument("start-maximized")
options.add_argument("disable-infobars")
options.add_argument("--disable-extensions")
options.add_argument("--headless")

driver = webdriver.Firefox(service=service, options=options)

driver.get("http://" + FREEBOX_SERVER_IP + "/login.php#Fbx.os.app.pvr.app")
sleep(8)

login = driver.find_element("id", "fbx-password")
sleep(1)
login.click()
sleep(1)
login.send_keys(ADMIN_PASSWORD)
sleep(1)
login.send_keys(Keys.RETURN)
sleep(10)

try:
    with open(
        "/home/" + user + "/.local/share/select_freeboxos" "/info_progs_last.json", "r"
    ) as jsonfile:
        data_last = json.load(jsonfile)
except FileNotFoundError:
    data_last = []

starting = []

for video in data_last:
    start = datetime.strptime(video["start"], "%Y%m%d%H%M").astimezone(
        ZoneInfo("Europe/Paris")
    )
    end = start + timedelta(seconds=video["duration"])

    starting.append((start, end))

day_next = datetime.now().astimezone(ZoneInfo("Europe/Paris")) + timedelta(1)
day_next_mid = datetime.strptime(
    day_next.strftime("%Y%m%d") + "0000", "%Y%m%d%H%M"
).astimezone(ZoneInfo("Europe/Paris"))

n = 0
last_channel = "x/x"

for video in data:
    n += 1

    start = datetime.strptime(video["start"], "%Y%m%d%H%M").astimezone(
        ZoneInfo("Europe/Paris")
    )
    start_day = start.strftime("%d")
    start_month = start.strftime("%m")
    start_year = start.strftime("%y")
    start_hour = start.strftime("%H")
    start_minute = start.strftime("%M")

    end = start + timedelta(seconds=video["duration"])
    end_hour = end.strftime("%H")
    end_minute = end.strftime("%M")

    """
        Max simultaneous recording to adapt according to internet speed.
        Set to 2 but to adapt after tests.
        Seem that it is limited to 2 simultaneous recordings:
        https://assistance.free.fr/articles/gerer-et-visionner-mes-enregistrements-72
        but fiber optic internet connection can handle more.
    """

    try:
        channel_number = CHANNELS_FREE[video["channel"]]
    except KeyError:
        logging.error(
            "La chaine " + video["channel"] + " n'est pas "
            "présente dans le fichier channels_free.py"
        )
        continue

    if len(starting) < MAX_SIM_RECORDINGS:
        starting.append((start, end))
        to_record = True
    else:
        if starting[-MAX_SIM_RECORDINGS][1] < start:
            starting.append((start, end))
            to_record = True
        else:
            to_record = False

    if to_record:
        text_to_click = "Programmer un enregistrement"
        xpath = f"//span[text()='{text_to_click}']"
        programmer_enregistrements = driver.find_element(By.XPATH, xpath)
        sleep(1)
        programmer_enregistrements.click()
        sleep(4)
        channel_uuid = driver.find_element("name", "channel_uuid")
        sleep(1)
        n = 0
        follow_record = True
        while channel_uuid.get_attribute("value").split("/")[0] != channel_number:
            channel_uuid.clear()
            sleep(1)
            if last_channel.split("/")[0] != channel_number:
                channel_uuid.send_keys(channel_number)
            else:
                channel_uuid.click()
                sleep(1)
                channel_uuid.clear()
                sleep(3)
                channel_uuid.send_keys(last_channel)
                sleep(1)
                channel_uuid.click()
            sleep(1)
            channel_uuid.send_keys(Keys.RETURN)
            sleep(1)
            last_channel = channel_uuid.get_attribute("value")
            n += 1
            if n > 10:
                logging.error(
                    "Impossible de sélectionner la chaîne. Merci de "
                    "vérifier si la chaine n°" + channel_number + " qui "
                    "correspond à la chaine " + video["channel"] + " "
                    "d'IPTV-select est bien présente dans la liste des "
                    "chaines Freebox. "
                )
                follow_record = False
                break
        if follow_record:
            if start >= day_next_mid:
                date = driver.find_element("name", "date")
                date.click()
                sleep(1)
                text_to_click = "Demain"
                xpath = f"//li[text()='{text_to_click}']"
                demain = driver.find_element(By.XPATH, xpath)
                demain.click()
                sleep(1)

            start_time = driver.find_element("name", "start_time")
            start_time.clear()
            sleep(1)
            start_time.send_keys(start_hour + ":" + start_minute)
            sleep(1)
            start_time.send_keys(Keys.RETURN)
            sleep(1)
            end_time = driver.find_element("name", "end_time")
            end_time.clear()
            sleep(1)
            end_time.send_keys(end_hour + ":" + end_minute)
            sleep(1)
            end_time.send_keys(Keys.RETURN)
            sleep(1)
            if IPTV_SELECT_TITLES:
                name_prog = driver.find_element("name", "name")
                name_prog.clear()
                sleep(1)
                name_prog.send_keys(video["title"])
                sleep(1)
            text_to_click = "Sauvegarder"
            xpath = f"//span[text()='{text_to_click}']"
            sauvegarder = driver.find_element(By.XPATH, xpath)
            sauvegarder.click()
            sleep(5)
            try:
                internal_error = driver.find_element(
                    By.XPATH, "//div[contains(text(), 'Erreur interne')]"
                )
                logging.error(
                    "Une erreur interne de la Freebox est survenue. "
                    "La programmation des enregistrements n'a pas "
                    "pu être réalisée. Merci de vérifier si le disque "
                    "dur n'est pas plein."
                )
                break
            except NoSuchElementException:
                pass
        else:
            text_to_click = "Annuler"
            xpath = f"//span[text()='{text_to_click}']"
            sauvegarder = driver.find_element(By.XPATH, xpath)
            sauvegarder.click()
            sleep(5)

sleep(6)
driver.quit()

cmd = (
    "cp /home/" + user + "/.local/share/select_freeboxos/"
    "info_progs.json /home/" + user + "/.local/share/"
    "select_freeboxos/info_progs_last.json"
)
Popen(cmd, stdout=PIPE, stderr=PIPE, shell=True)
