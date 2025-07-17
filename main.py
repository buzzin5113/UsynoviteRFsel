# Импорт модулей
from bs4 import BeautifulSoup
import logging
import os
import requests
import sqlite3
import telegram
import time

from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

import secret


def telegram_send_text(msg, secret_id, secret_token):
    """
    Отправка сообщения в телеграм
    """
    print(">>> telegram_send_text")

    bot = telegram.Bot(secret_token)
    try:
        bot.sendMessage(secret_id, text=msg, parse_mode=telegram.ParseMode.HTML)
        time.sleep(2)  # Чтобы не попасть в спам
        return True
    except telegram.TelegramError as error_text:
        logging.error('Ошибка отправки текстового сообщения в телеграм')
        logging.error(error_text)
        return False


def telegram_send_image(url, anketa_id, secret_id, secret_token):
    """
    Отправка фотов телеграм по ULR
    """
    print(">>> telegram_send_image")

    bot = telegram.Bot(secret_token)
    try:
        logging.info("Photo path: " + url)
        photo_path = "./photo/" + anketa_id + ".jpg";
        logging.info('Local photo path: ' + photo_path)
        
        headers = {'User-Agent' : 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_9_3) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/35.0.1916.47 Safari/537.36'}
           
        response = requests.get(url, headers=headers)
        open(photo_path, 'wb').write(response.content)

        bot.send_photo(secret_id, photo=open(photo_path, 'rb'))
        time.sleep(2)
        return True
    except telegram.TelegramError as error_text:
        logging.error('Ошибка отправки изображения в телеграм')
        logging.error(error_text)
        # msg = "Фотография не найдена"
        # telegram_send_text(msg)
        return False


def select_anketa(db, anketa_id):
    """
    Проверка наличия в БД номера анкеты
    """
    print(">>> select_anketa")

    c = db.cursor()
    c.execute("select count(*) from anketa where anketa_id = '{0}'".format(anketa_id))
    count = c.fetchone()

    if count[0] > 0:
        return 1
    else:
        return 0


def insert_anketa(db, anketa_id):
    """
    Вставка номера анкеты в БД
    """
    print(">>> insert_anketa")

    c = db.cursor()
    c.execute("INSERT INTO anketa(anketa_id) VALUES ('{0}')".format(anketa_id))
    db.commit()


def logging_set():
    """
    Настройка логгирования
    """
    print(">>> logging_set")

    handlers = [logging.FileHandler('./logs/post{0}.log'.format(time.strftime("%Y%m%d-%H%M%S")), 'a', 'utf-8'),
                logging.StreamHandler()]
    logging.basicConfig(format='%(asctime)s:%(levelname)s:%(message)s',
                        level=logging.INFO,
                        datefmt='%Y%m%d %H%M%S',
                        handlers=handlers)


def db_connect():
    """
    Подключение к БД
    Если БД не существует - создаём
    """
    print(">>> db_connect")

    file_path = './data/usynovite.db'

    if os.path.exists(file_path):
        conn = sqlite3.connect(file_path)
    else:
        conn = sqlite3.connect(file_path)
        c = conn.cursor()
        c.execute('''CREATE TABLE anketa (anketa_id text, age int)''')

    return conn


def db_close(db):
    """
    Закрытие БД
    """
    print(">>> db_close")


    db.close()


def get_render_page(url):
    """
    render
    """
    print(">>> get_render_page")

    print("r = session.get(url)"); r = session.get(url)
    print("r.html.render()"); r.html.render()
    html = r.html.html

    #timestamp = str(int(time.time()))

    #filename = url[34:]
    #filename = filename.replace("=", "_")
    #filename = filename.replace("&", "_")
    #filename = filename.replace("?", "_")

    #with open("./html/{0}-{1}.html".format(timestamp, filename), "w") as file:
    #    file.write(html)
    return html


def get_pages_count():
    """
    Находим кол-во страниц с анкетами и возвращаем его
    """
    print(">>> get_pages_count")

    pages_count_str = ""

    try:

        url = "https://xn--b1agisfqlc7e.xn--p1ai/children?ageFrom=0&ageTo=17&page=0&limit=6"
        html = get_html(url)

        start_position = html.find('"children":"')

        while True:
            symbol = html[start_position+12]
            if symbol.isdigit():
                pages_count_str = pages_count_str + symbol
            else:
                if symbol != " ":
                    break
            start_position += 1

        print("Анкет: " + pages_count_str)
        pages_count = int(pages_count_str)
        pages_count = int((pages_count/6) + 2)
        logging.info("Количество страниц с анкетами: " + str(pages_count))
    except Exception as error:
        print(error)
        pages_count = 0

    return pages_count


def parser_page(html, db, a_count):
    """
    Парсим страницу со списком анкет
    Если анкеты нет в БД, то загружаем страницу с этой анкетой и вызываем функцию обработки
    """
    print(">>> parser_page")

    soup = BeautifulSoup(html, features="html.parser")
    div = soup('div', class_="ChildCard_buttons_block__7yJte")

    for k in div:
        string = str(k)

        start = string.find('/children/')
        anketa_id = ""
        while True:
            symbol = string[start+10]
            if symbol != '"':
                anketa_id = anketa_id + symbol
            else:
                break
            start += 1
        a_count += 1
        logging.info("Найдена анкета - {0}: порядковый номер {1}".format(anketa_id, a_count))

        if len(anketa_id) > 15:
            logging.info("Неверный ID анкеты, пропускаем")
            continue

        # Если анкеты нет, то грузим страницу
        if select_anketa(db, anketa_id) == 0:
            logging.info("Анкеты {0} нет в БД".format(anketa_id))
            parser_anketa(anketa_id)
            insert_anketa(db, anketa_id)
        else:
            logging.info("Анкета {0} уже есть в БД".format(anketa_id))

    return a_count


def parser_anketa(anketa_id,):
    """
    Обрабатываем страницу анкеты
    Собираем данные и отправляемв телеграм в формате:
        Имя:
        Номер анкеты:
        Пол:
        Регион:
        Возраст:
        Группа здоровья:
        Цвет глаз:
        Цвет волос:
        Возможные формы устройства:
        Братья или сестры:
        Причина отсутствия родительского попечения отца:
        Причина отсутствия родительского попечения матери:
        Характеристика:
        Ссылка на анкету:
        Видеоанкета:
        Куда обращаться:
    Также находим ссылку на фото
    """
    print(">>> paser_anketa")
    
    html = get_html('https://усыновите.рф/children/' + anketa_id)
    
    msg = ''

    start = html.find('"name":"') + 8
    end = html.find('"', start)
    msg = msg + 'Имя: ' + html[start:end] + '\n'

    start = html.find('"data":{"id":"') + 14
    end = html.find('"', start)
    msg = msg + 'Номер анкеты: ' + anketa_id + '\n'

    start = html.find('"gender":"') + 10
    end = html.find('"', start)
    msg = msg + 'Пол: ' + html[start:end] + '\n'

    start = html.find('"region":"') + 10
    end = html.find('"', start)
    msg = msg + 'Регион: ' + html[start:end] + '\n'

    start = html.find('"age":"') + 7
    end = html.find('"', start)
    msg = msg + 'Возраст: ' + html[start:end] + '\n'

    #start = html.find('"birthday":"') + 12
    #end = html.find('"', start)
    #msg = msg + 'Дата рождения: ' + html[start:end] + '\n'

    start = html.find('"healthGroup":"') + 15
    end = html.find('"', start)
    msg = msg + 'Группа здоровья: ' + html[start:end] + '\n'

    start = html.find('"eye":"') + 7
    end = html.find('"', start)
    msg = msg + 'Цвет глаз: ' + html[start:end] + '\n'

    start = html.find('"hair":"') + 8
    end = html.find('"', start)
    msg = msg + 'Цвет волос: ' + html[start:end] + '\n'

    start = html.find('"custodyForm":"') + 15
    end = html.find('"', start)
    msg = msg + 'Возможные формы устройства: ' + html[start:end] + '\n'

    start = html.find('"isSibling":"') + 13
    end = html.find('"', start)
    msg = msg + 'Братья или сестры: ' + html[start:end] + '\n'

    start = html.find('"fatherLack":"') + 14
    end = html.find('"', start)
    msg = msg + 'Причина отсутствия родительского попечения отца: ' + html[start:end] + '\n'

    start = html.find('"motherLack":"') + 14
    end = html.find('"', start)
    msg = msg + 'Причина отсутствия родительского попечения матери: ' + html[start:end] + '\n'

    start = html.find('"character":"') + 13
    end = html.find('"', start)
    msg = msg + 'Характеристика: ' + html[start:end] + '\n'

    msg = BeautifulSoup(msg, "lxml").text

    msg = msg + 'Ссылка на анкету: https://усыновите.рф/children/' + anketa_id + '\n'

    start = html.find('https://changeonelife.ru/videoprofiles')
    end = html.find('"', start)
    if start > 1:
        msg = msg + 'Видеоанкета: ' + html[start:end] + '\n'

    logging.info(msg)

    start = html.find('"photoPath":"') + 14
    end = html.find('"', start)
    photo_path = 'https://усыновите.рф/' + html[start:end]

    #Отправляем в усыновите_рф
    telegram_send_image(photo_path, anketa_id, secret.chat_id, secret.token)
    telegram_send_text(msg, secret.chat_id, secret.token)
    #Отправляем в usynovite.ru
    telegram_send_image(photo_path, anketa_id, secret.chat_id2, secret.token2)
    telegram_send_text(msg, secret.chat_id2, secret.token2)


def get_pages(pages_count, db):
    """
    Цикл скачивания страниц
    """

    a_count = 0
    err_count = 0
    count = 0

    while count <= pages_count:
        url = 'https://xn--b1agisfqlc7e.xn--p1ai/children?ageFrom=0&ageTo=17&page=' + str(count) + '&limit=6'
        logging.info(url)

        html = get_html(url)

        # Иногда возвращается пустая страница, она размером ~29Kb
        # Перезапрашиваем 60 раз с паузой в 10 секунд
        if len(html) < 35000 and err_count < 60:
            logging.info("Получена пустая страница, попытка получения {0}".format(err_count))
            err_count += 1
            time.sleep(3)
            continue

        a_count = parser_page(html, db, a_count)
        count += 1
        err_count = 0


    logging.info("Всего обработано {0} анкет.".format(a_count))
    logging.info("Новых - {0} анкет.".format(a_count))


def get_html(url):
    """
    Получение содержимого страницы
    Взято с Stackoverflow
    """
    chrome_options = Options()
    chrome_options.add_argument("--headless")  # Run Chrome in headless mode (no GUI)
    chrome_options.add_argument("--disable-gpu")  # Disable GPU acceleration (recommended for headless)

    driver = webdriver.Remote(command_executor="http://127.0.0.1:4444/wd/hub",options=chrome_options)

    try:
        driver.get(url)
        # Wait for the page to fully load and JS to execute (adjust timeout as needed)
        WebDriverWait(driver, 20).until(
            EC.presence_of_element_located((By.TAG_NAME, "body"))
        )
        page_source = driver.page_source

        #timestamp = str(int(time.time()))

        #filename = url[34:]
        #filename = filename.replace("=", "_")
        #filename = filename.replace("&", "_")
        #filename = filename.replace("?", "_")
        #output_filename = timestamp + filename

        #with open("./html/"+output_filename, "w", encoding="utf-8") as file:
        #    file.write(page_source)
        #print(f"Page source saved to {output_filename}")

        time.sleep(2)

        return page_source

    except Exception as e:
        print(f"An error occurred: {e}")
    finally:
        driver.quit()


# Основной цикл
def main():

    # Настройка логирования
    logging_set()
    logging.info("========== Start ==========")

    # Подключение БД
    db = db_connect()

    # Получение страниц
    # ищем общее количество страниц
    pages_count = get_pages_count()
    if pages_count > 0:
        get_pages(pages_count, db)

    # Закроем БД
    db_close(db)

    logging.info("========== Stop ==========")


# Вход в программу
if __name__ == "__main__":
    main()

