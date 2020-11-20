from flask import Flask, redirect, url_for, render_template, request
import requests
import lxml
from bs4 import BeautifulSoup

app = Flask(__name__)

# # Step 1: Sending a HTTP request to a URL
# url = "https://money.cnn.com/data/hotstocks/"
# # Make a GET request to fetch the raw HTML content
# html_content = requests.get(url).text
# soup = BeautifulSoup(html_content, "lxml")
# #print(soup)


@app.route("/", methods=['GET', 'POST'])
def home():
    if request.method == 'POST':
        company = request.form['company']

        url = 'https://ca.finance.yahoo.com/most-active'
        header = {
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_11_2) AppleWebKit/601.3.9 (KHTML, like Gecko) Version/9.0.2 Safari/601.3.9'
        }
        count = 0
        symbols = []
        response = requests.get(url, headers=header)
        soup = BeautifulSoup(response.content, 'lxml')
        for item in soup.select('.simpTblRow'):
            symbols.append(item.select('[aria-label=Symbol]')[0].get_text())
            # print("Name =",item.select('[aria-label=Name]')[0].get_text())
            # print("Price =",item.select('[aria-label*=Price]')[0].get_text())
            # print("Change =",item.select('[aria-label=Change]')[0].get_text())
            # print("% change =",item.select('[aria-label="% change"]')[0].get_text())
            # print("Market cap =",item.select('[aria-label="Market cap"]')[0].get_text())
            # print("Avg vol (3-month) =",item.select('[aria-label*="Avg vol (3-month)"]')[0].get_text())
            # print("PE ratio (TTM) =",item.select('[aria-label*="PE ratio (TTM)"]')[0].get_text())
            # print('____________________________')
            if count == 4:
                break
            count += 1
        print(symbols)

        return redirect(url_for('stocks', company=company))
    return render_template("index.html")

@app.route("/stocks/<company>", methods=['GET', 'POST'])
def stocks(company):
    API_KEY = 'VKRIY5YHD1AYDELD'
    r = requests.get('https://www.alphavantage.co/query?function=TIME_SERIES_DAILY&symbol=' + company + '&apikey=' + API_KEY)
    if (r.status_code == 200):
        print(r.json())

    result = r.json()
    dataForAllDays = result['Time Series (Daily)']
    dataForSingleDate = dataForAllDays['2020-11-18']
    print(result)
    print(dataForSingleDate['1. open'])
    # print(dataForSingleDate['2. high'])
    # print(dataForSingleDate['3. low'])
    # print(dataForSingleDate['4. close'])
    # print(dataForSingleDate['5. volume'])
    #return render_template("age.html",age=age)
    return render_template("stocks.html", company=company,open=dataForSingleDate['1. open'])

if __name__ == "__main__":
    app.run(debug=True)