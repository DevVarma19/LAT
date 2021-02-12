from flask import Flask, render_template, request, session, redirect, url_for
import json

# from flask_sqlalchemy import SQLAlchemy

from webdriver_manager.chrome import ChromeDriverManager

from selenium import webdriver
from selenium.webdriver.common.keys import Keys
import time
import datetime

import logging
logging.basicConfig(filename='log.txt', filemode='w')

with open('config.json', 'r') as c:
    params = json.load(c)["params"]

app = Flask(__name__)
app.secret_key = 'super secret key'
app.config.update()

# if params["local_server"]:
#     app.config['SQLALCHEMY_DATABASE_URI'] = params["local_uri"]
# else:
#     app.config['SQLALCHEMY_DATABASE_URI'] = params["prod_uri"]
#
# db = SQLAlchemy(app)


# class Log(db.Model):
#     '''
#         sno, date, time, content
#     '''
#     sno = db.Column(db.Integer, primary_key=True)
#     content = db.Column(db.Text(), nullable=False)
#     date = db.Column(db.String(12), nullable=False)
#     time = db.Column(db.String(12), nullable=False)

driver = None


@app.route('/', methods = ['GET', 'POST'])
def home():
    # check if user is already logged in
    if 'user' in session and session['user'] == params['admin_username']:
        return render_template('dashboard.html')

    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')

        if username == params['admin_username'] and password == params['admin_password']:
            #set session variable
            session['user'] = username
            return render_template('dashboard.html')
    else:
        #if the user is not logged in.
        return render_template('login.html')


@app.route('/data', methods=['POST'])
def data():
    logs = ''

    #getting the data from the form
    SEARCH_URL = request.form.get('url')
    MSG = request.form.get('message')
    PAGES = int(request.form.get('pages'))

    # starting chrome automation
    chrome_options = webdriver.ChromeOptions()
    driver = webdriver.Chrome(ChromeDriverManager().install())

    driver.get(params['linkedin'])
    EMAIL = params['linkedin_email']
    PASSWORD = params['linkedin_password']
    email = driver.find_element_by_id('username')
    password = driver.find_element_by_id('password')
    try:
        email.send_keys(EMAIL)
        time.sleep(2)
        password.send_keys(PASSWORD)
        time.sleep(2)
        driver.find_element_by_class_name("from__button--floating").click()
    except Exception as e:
        return "Authentication Failed"

    for i in range(PAGES):
        if i == 1:
            SEARCH_URL = SEARCH_URL + f'&page={i + 1}'
        elif i > 1:
            SEARCH_URL = SEARCH_URL.replace(f'&page={i}', f'&page={i + 1}')
        print(SEARCH_URL)
        driver.get(SEARCH_URL)
        time.sleep(2)
        try:
            result_sec = driver.find_element_by_tag_name("tbody")
            results = result_sec.find_elements_by_tag_name("tr")
            print(len(results))
        except Exception as e:
            print(e)
            logging.error("Could not find results sections")
        ins = []

        try:
            for result in results:
                columns = result.find_elements_by_tag_name("td")
                name_tag, activity = columns[0], columns[4].text
                if 'No activity' not in activity:
                    continue
                ins.append(name_tag)
        except Exception as e:
            logging.error("Could not find (name tag)")
            logging.exception(e)

        hrefs = []
        for ind in ins:
            try:
                a = ind.find_elements_by_tag_name("a")
                href = a[1].get_attribute("href")
                hrefs.append(href)
            except:
                continue
        logging.debug(f"Found {len(hrefs)} hrefs")
        with open("work.txt", 'w') as file:
            file.write('The URLs scraped: ')
            file.write('\n')
            file.write("\n".join(hrefs))
            file.write('\n----------\n')

        for profile in hrefs:
            if profile.startswith("https://www.linkedin.com/sales/people/"):
                SENT = False
                driver.get(profile)
                time.sleep(3)

                ##        try:
                ####            premium = driver.find_element_by_css_selector("artdeco-modal")
                ####            logging.error("premium")
                ##            close_btn = driver.find_element_by_xpath("/html/body/div[4]/div/div/button")
                ##            close_btn.click()
                ##            logging.error("premium closed")
                ##        except Exception as e:
                ##            logging.error("No premium")

                try:
                    name = driver.find_element_by_xpath(
                        '/html/body/main/div[1]/div[2]/div/div[1]/div[1]/div/dl/dt/span').text
                except Exception as e:
                    name = " "
                    logging.error("Could not find name")
                    logging.exception(e)
                name = name.split(" ")
                blacklist = ["dr.", "esq", "mr"]
                if any([x in name[0].lower() for x in blacklist]):
                    fname = ' '.join(name[:2])
                # if len(name)<=2:
                else:
                    fname = name[0]
                #         else:
                #             fname = ' '.join(name[:2])

                ##        try:
                ####            premium = driver.find_element_by_css_selector("artdeco-modal")
                ####            logging.error("premium")
                ##            close_btn = driver.find_element_by_xpath("/html/body/div[4]/div/div/button")
                ##            close_btn.click()
                ##            logging.error("premium closed")
                ##        except Exception as e:
                ##            logging.error("No premium")

                try:
                    time.sleep(2)
                    drop_btn = driver.find_element_by_xpath(
                        "/html/body/main/div[1]/div[2]/div/div[2]/div[1]/div[3]/button")
                    drop_btn.click()
                    connect_btn = driver.find_element_by_xpath(
                        "/html/body/main/div[1]/div[2]/div/div[2]/div[1]/div[3]/div/div/div[1]/div/ul/li[1]/div/div[1]")
                    connect_btn.click()
                    print("clicked")
                    SENT = True
                    time.sleep(3)
                except Exception as e:
                    logging.error("Could not connect")
                    logging.exception(e)

                ##        try:
                ####            premium = driver.find_element_by_css_selector("artdeco-modal")
                ####            logging.error("premium")
                ##            close_btn = driver.find_element_by_xpath("/html/body/div[4]/div/div/button")
                ##            close_btn.click()
                ##            logging.error("premium closed")
                ##        except Exception as e:
                ##            logging.error("No premium")

                try:
                    # send note
                    time.sleep(2)
                    text_box = driver.find_element_by_xpath("/html/body/div[3]/div/div/div[2]/div/textarea")
                    text_box.click()
                    time.sleep(2)
                    text_box.send_keys(f'Hi {fname},\n{MSG}')

                    ##            input("Msg typed")

                    time.sleep(3)

                    send_btn = driver.find_element_by_xpath("/html/body/div[3]/div/div/div[3]/div/button[2]")
                    send_btn.click()
                    time.sleep(2)
                except Exception as e:
                    print(f"{profile} Could not send message")
                    logging.error("Could not send message")
                    logging.exception(e)

                print(f'SENT - {SENT}: {profile}')
                with open("work.txt", 'a+') as file:
                    file.write(f'SENT - {SENT}: {profile}')
                    file.write('\n')
                print("Sleeping for 5 seconds")
                time.sleep(5)

    return redirect(url_for('logs'))


@app.route('/logs')
def logs():
    if 'user' not in session and session['user'] is not params['admin_username']:
        return redirect('/')
    try:
        log = open("log.txt", 'r')
        log = log.readlines()

        url = open("work.txt", 'r')
        url = url.readlines()

        date = datetime.datetime.now()
        return render_template('log.html', logs=log, date=date, urls=url)
    except Exception as e:
        return e


@app.route('/stop', methods=['GET'])
def stop():
    if 'user' not in session:
        return redirect('/')
    # print(driver)
    if driver is not None:
        driver.close()
    else:
        return "Script is not running currently"
    return redirect(url_for('/'))


@app.route('/logout')
def logout():
    if 'user' in session:
        session['user'] = None
    return redirect('/')


app.run(debug=True)