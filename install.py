import readline
import random
import getpass
import logging

from time import sleep
from selenium import webdriver
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By

from subprocess import Popen, PIPE

logging.basicConfig(
    filename="/var/tmp/select_freeboxos.log",
    format="%(asctime)s %(levelname)s: %(message)s",
    level=logging.INFO,
)

answers = ["oui", "non"]

service = Service(executable_path="./geckodriver")
options = webdriver.FirefoxOptions()
options.add_argument("start-maximized")
options.add_argument("disable-infobars")
options.add_argument("--disable-extensions")
options.add_argument("--headless")

print("Veuillez patienter\n")

driver = webdriver.Firefox(service=service, options=options)
driver.get("http://mafreebox.freebox.fr/login.php")

print("Connexion à la Freebox:\n")

go_on = True
not_connected = True
answer_hide = "maybe"
n = 0

while not_connected:
    if answer_hide.lower() == "oui":
        freebox_os_password = input(
            "\nVeuillez saisir votre mot de passe " "admin de la Freebox: "
        )
    else:
        freebox_os_password = getpass.getpass(
            "\nVeuillez saisir votre mot " "de passe admin de la Freebox: "
        )
    print(
        "Veuillez patienter pendant la tentative de connexion à "
        "Freebox OS avec votre mot de passe."
    )
    sleep(4)
    login = driver.find_element("id", "fbx-password")
    sleep(1)
    login.clear()
    sleep(1)
    login.click()
    sleep(1)
    login.send_keys(freebox_os_password)
    sleep(1)
    login.send_keys(Keys.RETURN)
    sleep(6)

    try:
        login = driver.find_element("id", "fbx-password")
        try_again = input(
            "\nLe programme install.py n'a pas pu se connecter à Freebox OS car "
            "le mot de passe ne correspond pas à celui enregistré dans "
            "la Freebox.\nVoulez-vous essayer de nouveau?(oui ou non): "
        )
        if try_again.lower() == "oui":
            if answer_hide.lower() != "oui":
                while answer_hide.lower() not in answers:
                    answer_hide = input(
                        "\nVoulez-vous afficher le mot de passe que vous saisissez "
                        "pour que cela soit plus facile? (répondre par oui ou non): "
                    )
            n += 1
            if n > 6:
                print(
                    "\nImpossible de se connecter à Freebox OS avec ce mot de passe. "
                    "Veuillez vérifier votre mot de passe de connexion admin en vous "
                    "connectant à l'adresse http://mafreebox.freebox.fr/login.php puis "
                    "relancez le programme install.py. "
                )
                driver.quit()
                go_on = False
                break
        else:
            driver.quit()
            go_on = False
            break
    except:
        print("Le mot de passe correspond bien à votre compte admin Freebox OS")
        not_connected = False
        sleep(2)
        driver.quit()

title_answer = "no_se"

if go_on:
    while title_answer.lower() not in answers:
        title_answer = input(
            "\nVoulez-vous utiliser le nommage de TV-select "
            "pour nommer les titres des programmes? Si vous répondez oui, alors "
            "les titres seront composés du titre du programme, de son numéro "
            "d'idendification dans IPTV-select puis de la recherche "
            "correspondante. Si vous répondez non, le nommage de Freebox OS "
            "sera utilisé (dans ce cas des erreurs peuvent apparaitre si la "
            "différence de temps (marge avant le début du film) est trop "
            "grande): "
        )

    cmd = "echo $USER"
    echo = Popen(cmd, stdout=PIPE, stderr=PIPE, shell=True)
    stdout, stderr = echo.communicate()
    user = stdout.decode("utf-8")[:-1]

    try:
        with open(
            "/home/" + user + "/.config/select_freeboxos/" "config.py", "r"
        ) as conf:
            params = conf.read().splitlines()
    except FileNotFoundError:
        cmd = (
            "cp /opt/select_freeboxos/config_template.py /home/"
            + user
            + "/.config/select_freeboxos/config.py"
        )
        cp_conf = Popen(cmd, stdout=PIPE, stderr=PIPE, shell=True)
        cp_conf.wait()
        cmd = (
            "chmod o-r /home/" + user + "/.config/select_freeboxos/config.py"
        )
        chmod = Popen(cmd, stdout=PIPE, stderr=PIPE, shell=True)
        chmod.wait()

    try:
        with open(
            "/home/" + user + "/.config/select_freeboxos/" "config.py", "r"
        ) as conf:
            params = conf.read().splitlines()
    except FileNotFoundError:
        logging.error(
            "Impossible to copy config.py file in home/$USER/"
            ".config/select_freeboxos. Please check if the file is "
            "in /opt/select_freeboxos directory"
        )

    with open("/home/" + user + "/.config/select_freeboxos/" "config.py", "w") as conf:
        for param in params:
            if "ADMIN_PASSWORD" in param:
                conf.write("ADMIN_PASSWORD = " + '"' + freebox_os_password + '"\n')
            elif "IPTV_SELECT_TITLES" in param:
                if title_answer.lower() == "oui":
                    conf.write("IPTV_SELECT_TITLES = True\n")
                else:
                    conf.write("IPTV_SELECT_TITLES = False\n")
            else:
                conf.write(param + "\n")

    print("\nConfiguration des tâches cron du programme IPTV-select:\n")

    cmd = 'curl -I https://iptv-select.fr | grep HTTP | tail -1 | cut -d " " -f 2'
    http = Popen(cmd, stdout=PIPE, stderr=PIPE, shell=True)
    stdout, stderr = http.communicate()
    http_response = stdout.decode("ascii")[:-1]

    if http_response != "200":
        print(
            "\nLa box IPTV-select n'est pas connectée à internet. Veuillez "
            "vérifier votre connection internet et relancer le programme "
            "d'installation.\n\n"
        )
        go_on = False

    if go_on:
        username = input(
            "Veuillez saisir votre identifiant de connexion (adresse "
            "email) sur IPTV-select.fr: "
        )
        password_iptvrecord = getpass.getpass(
            "Veuillez saisir votre mot de passe sur IPTV-select.fr: "
        )

        cmd = "ls -a ~ | grep ^.netrc$"
        output = Popen(cmd, stdout=PIPE, stderr=PIPE, shell=True)
        stdout, stderr = output.communicate()
        ls_netrc = stdout.decode("utf-8")[:-1]

        if ls_netrc == "":
            cmd = "touch ~/.netrc"
            touch = Popen(cmd, stdout=PIPE, stderr=PIPE, shell=True)
            touch.wait()
            cmd = "chmod go= ~/.netrc"
            chmod = Popen(cmd, stdout=PIPE, stderr=PIPE, shell=True)

        authprog_response = "403"

        with open("/home/" + user + "/.netrc", "r") as file:
            lines_origin = file.read().splitlines()

        while authprog_response != "200":
            with open("/home/" + user + "/.netrc", "r") as file:
                lines = file.read().splitlines()

            try:
                position = lines.index("machine www.iptv-select.fr")
                lines[position + 1] = "  login {username}".format(username=username)
                lines[position + 2] = "  password {password_iptvrecord}".format(
                    password_iptvrecord=password_iptvrecord
                )
            except ValueError:
                lines.append("machine www.iptv-select.fr")
                lines.append("  login {username}".format(username=username))
                lines.append(
                    "  password {password_iptvrecord}".format(
                        password_iptvrecord=password_iptvrecord
                    )
                )

            with open("/home/" + user + "/.netrc", "w") as file:
                for line in lines:
                    file.write(line + "\n")

            cmd = 'curl -iSn https://www.iptv-select.fr/api/v1/prog | grep HTTP | cut -d " " -f 2'

            authprog = Popen(cmd, stdout=PIPE, stderr=PIPE, shell=True)
            stdout, stderr = authprog.communicate()
            authprog_response = stdout.decode("ascii")[:-1]

            if authprog_response != "200":
                try_again = input(
                    "Le couple identifiant de connexion et mot de passe "
                    "est incorrect.\nVoulez-vous essayer de nouveau?(oui ou non): "
                )
                answer_hide = "maybe"
                if try_again.lower() == "oui":
                    username = input(
                        "Veuillez saisir de nouveau votre identifiant de connexion (adresse email) sur IPTV-select.fr: "
                    )
                    while answer_hide.lower() not in answers:
                        answer_hide = input(
                            "Voulez-vous afficher le mot de passe que vous saisissez "
                            "pour que cela soit plus facile? (répondre par oui ou non): "
                        )
                    if answer_hide.lower() == "oui":
                        password_iptvrecord = input(
                            "Veuillez saisir de nouveau votre mot de passe sur IPTV-select.fr: "
                        )
                    else:
                        password_iptvrecord = getpass.getpass(
                            "Veuillez saisir de nouveau votre mot de passe sur IPTV-select.fr: "
                        )
                else:
                    go_on = False
                    with open("/home/" + user + "/.netrc", "w") as file:
                        for line in lines_origin:
                            file.write(line + "\n")
                    break
        if go_on:
            heure = random.randint(6, 23)
            minute = random.randint(0, 58)
            minute_2 = minute + 1

            cmd = (
                "crontab -u "
                + user
                + " -l >  /home/"
                + user
                + "/.local/share/select_freeboxos/cron_tasks.sh"
            )
            crontab_init = Popen(cmd, stdout=PIPE, stderr=PIPE, shell=True)
            crontab_init.wait()

            with open(
                "/home/" + user + "/.local/share/select_freeboxos/cron" "_tasks.sh", "r"
            ) as crontab_file:
                cron_lines = crontab_file.readlines()

            curl = (
                "{minute} {heure} * * * export USER='{user}' && "
                "curl -H 'Accept: application/json;"
                "indent=4' -n "
                "https://www.iptv-select.fr/api/v1/prog > /home/$USER/.local/share/select_freeboxos/info_"
                "progs.json 2>> /var/tmp/cron_curl.log\n".format(
                    user=user,
                    minute=minute,
                    heure=heure,
                )
            )

            cron_launch = (
                "{minute_2} {heure} * * * export USER='{user}' && "
                "cd /opt/select_freeboxos && bash cron_freeboxos_app"
                ".sh\n".format(user=user, minute_2=minute_2, heure=heure)
            )

            cron_lines = [
                curl if "select_freeboxos/info_progs.json" in cron else cron
                for cron in cron_lines
            ]
            cron_lines = [
                cron_launch if "select_freeboxos &&" in cron else cron
                for cron in cron_lines
            ]

            cron_lines_join = "".join(cron_lines)

            if "select_freeboxos/info_progs.json" not in cron_lines_join:
                cron_lines.append(curl)
            if "cd /opt/select_freeboxos &&" not in cron_lines_join:
                cron_lines.append(cron_launch)

            with open(
                "/home/" + user + "/.local/share/select_freeboxos" "/cron_tasks.sh", "w"
            ) as crontab_file:
                for cron_task in cron_lines:
                    crontab_file.write(cron_task)

            cmd = (
                "crontab -u "
                + user
                + " /home/"
                + user
                + "/.local/share/select_freeboxos/cron_tasks.sh"
            )
            cron = Popen(cmd, stdout=PIPE, stderr=PIPE, shell=True)
            cron.wait()
            cmd = "rm /home/" + user + "/.local/share/select_freeboxos" "/cron_tasks.sh"
            rm = Popen(cmd, stdout=PIPE, stderr=PIPE, shell=True)

            print(
                "\nLes tâches cron de votre box IPTV-select sont maintenant configurés!\n"
            )
