import requests
from bs4 import BeautifulSoup

# aapl_url = "https://finance.yahoo.com/quote/AAPL?p=AAPL&.tsrc=fin-srch"
# amzn_url= "https://finance.yahoo.com/quote/AMZN?p=AMZN&.tsrc=fin-srch"

def real_time_price(url):
    result = requests.get(url)
    soup = BeautifulSoup(result.text, 'html.parser')
    stock_price = soup.find('fin-streamer', class_="Fw(b) Fz(36px) Mb(-4px) D(ib)")
    stock_changes = soup.find_all('fin-streamer', class_ ="Fw(500) Pstart(8px) Fz(24px)")
    qsp_price, qsp_price_change = [changes.get_text() for changes in stock_changes] # qsp-price and qsp-price-change

    return stock_price.get_text(), qsp_price, qsp_price_change
    # return f'Price is {stock_price.get_text()} and the regular Market Price / regular Market Change is {qsp_price} / {qsp_price_change}' 
