#Import the required modules
from flask import Flask, redirect, url_for, render_template, request, Response, session
import requests
from pandas import DataFrame
from bs4 import BeautifulSoup
import numpy as np
import scipy.stats
import matplotlib.pyplot as plt
from flask_mail import Mail,  Message
import os

#Configuring flask and flask_mail
app = Flask(__name__)
app.config['SECRET_KEY'] = os.urandom(24)
app.config.update(
    MAIL_SERVER='smtp.gmail.com',
    MAIL_PORT=465,
    MAIL_USE_SSL=True,
    MAIL_USERNAME = 'stocksminiapplication@gmail.com',
    MAIL_PASSWORD = 'moektykgjvbibben'
)

mail = Mail(app)

#Home route of the application
@app.route("/", methods=['GET', 'POST'])
def home():
    if request.method == 'POST':
        company = request.form['company'] #gets the company symbol that user searched
        return redirect(url_for('stocks', company=company))

    url = 'https://ca.finance.yahoo.com/most-active' #URL to get the top most-active companies
    header = {
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_11_2) AppleWebKit/601.3.9 (KHTML, like Gecko) Version/9.0.2 Safari/601.3.9'
    }
    count = 0
    most_active = []

    #Creation of table on the home page
    table_header=["Name", "Price", "Change", "%change", "Market cap", "Avg vol (3-month)"]
    response = requests.get(url, headers=header)
    soup = BeautifulSoup(response.content, 'lxml')
    for item in soup.select('.simpTblRow'):
        most_active.append(item.select('[aria-label=Name]')[0].get_text())
        most_active.append(item.select('[aria-label*=Price]')[0].get_text())
        most_active.append(item.select('[aria-label=Change]')[0].get_text())
        most_active.append(item.select('[aria-label="% Change"]')[0].get_text())
        most_active.append(item.select('[aria-label="Market Cap"]')[0].get_text())
        most_active.append(item.select('[aria-label="Avg Vol (3 month)"]')[0].get_text())
        if count == 9:
            break
        count += 1
    return render_template("index.html", table_header=table_header, most_active=most_active) #renders index.html page when accessed

#Company route of the application
@app.route("/<company>", methods=['GET', 'POST'])
def stocks(company):

    API_KEY1 = 'VKRIY5YHD1AYDELD'
    r = requests.get('https://www.alphavantage.co/query?function=TIME_SERIES_DAILY&symbol=' + company + '&apikey=' + API_KEY1) #API endpoint to hit using the key

    result = r.json()
    dataForAllDays = result['Time Series (Daily)']
    dataForSingleDate = dataForAllDays[result['Meta Data']['3. Last Refreshed']]

    #saving the data into the session
    session['company']=company
    session['open']=dataForSingleDate['1. open']
    session['high']=dataForSingleDate['2. high']
    session['low']=dataForSingleDate['3. low']
    session['close']=dataForSingleDate['4. close']
    session['volume']=dataForSingleDate['5. volume']

    keys = list(dataForAllDays.keys())
    openValues=[]
    for x in keys:
        openValues.append(float(dataForAllDays[x]['1. open']))

    pdopenValues = DataFrame(openValues)
    pdopenValues = pdopenValues[0]

    #Plotting the graph using matplotlib
    plt.figure()
    plt.plot(openValues)
    plt.title(company)
    plt.xlabel("Trading Days")
    plt.ylabel("Stock Price")
    plt.savefig('static/fig1.png')

    log_returns = np.log(1 + pdopenValues.pct_change())
    plt.figure()
    plt.plot(log_returns)
    plt.title(company)
    plt.xlabel("Trading Days")
    plt.ylabel("Log Returns")
    plt.savefig('static/fig2.png')

    # properties
    u = log_returns.mean()
    var = log_returns.var()
    stdev = log_returns.std()

    t_intervals = 252
    iterations = 100

    plt.figure()

    #predicting the future values of the stock
    for i in range(iterations):
        drift = u - (0.5 * var)
        Z = scipy.stats.norm.ppf(np.random.rand(t_intervals))
        daily_returns = np.exp(drift + stdev * Z)

        price_list = np.zeros(t_intervals)
        S0 = pdopenValues.iloc[-1]
        price_list[0] = S0

        for t in range(1, t_intervals):
            price_list[t] = price_list[t - 1] * daily_returns[t]

        plt.plot(price_list)
        plt.title(company)
        plt.xlabel("Trading Days")
        plt.ylabel("Projected Prices")
        plt.savefig('static/fig3.png')

    return render_template("stocks.html", company=company, open=dataForSingleDate['1. open'], high=dataForSingleDate['2. high'], low=dataForSingleDate['3. low'], close=dataForSingleDate['4. close'], volume=dataForSingleDate['5. volume']) #renders stocks.html when accessed

#Email route of the application helps in configuring and sending the email to user
@app.route("/email", methods=['GET', 'POST'])
def email():
    if request.method == 'POST':
        email = request.form['email']
        with app.app_context():
            msg = Message(subject="Stocks-MiniApplication",
                          sender=app.config.get("MAIL_USERNAME"),
                          recipients=[email],
                          body=("Hello\n\nThe details you have requested regarding "+session.get('company')+" is given below: \n\nCompany - "+session.get('company')+"\n"+"Open - "+session.get('open')+"\n"+"Close - "+session.get('close')+"\n"+"High - "+session.get('high')+"\n"+"Low - "+session.get('low')+"\n"+"Volume - "+session.get('volume')+"\n\nThank you for using Stocks-MiniApplication, Please visit again!!!\n\nHappy Trading!!!\n\nRegards,\nTeam Stocks-MiniApplication"))
            #Attaching the plots as images to the email
            with app.open_resource("static/fig1.png") as fp:
                msg.attach("fig1.png", "fig1/png", fp.read())
            with app.open_resource("static/fig2.png") as fp:
                msg.attach("fig2.png", "fig2/png", fp.read())
            with app.open_resource("static/fig3.png") as fp:
                msg.attach("fig3.png", "fig3/png", fp.read())
            mail.send(msg)
        return render_template("email.html", email=email) #renders email.html when accessed

#Following code helps in refreshing the CSS styles every time the page is refreshed
@app.context_processor
def override_url_for():
    """
    Generate a new token on every request to prevent the browser from caching static files.
    """
    return dict(url_for=dated_url_for)


def dated_url_for(endpoint, **values):
    if endpoint == 'static':
        filename = values.get('filename', None)
        if filename:
            file_path = os.path.join(app.root_path,
                                     endpoint, filename)
            values['q'] = int(os.stat(file_path).st_mtime)
    return url_for(endpoint, **values)

#Starting the flask application
if __name__ == "__main__":
    app.run(host='0.0.0.0',port=8080,debug=True)
