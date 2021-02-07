from bs4 import BeautifulSoup
import urllib3, svd.finance.context as c

URL_FORMAT = "https://finance.yahoo.com/quote/{}/history?period1={}&period2={}&interval=1d&filter=history&frequency=1d"


class HistoryApi:
    def download(self, tick):
        total_min = 1207008000
        total_max = 1241136000
        step = 10000000
        min_timestamp = total_max - step
        max_timestamp = total_max
        all_success = True
        with open(c.DOW_JONES_HISTORICAL_DATA_FORMAT.format(tick), "w") as f:
            while (True):
                success = self.do_download(tick, min_timestamp, max_timestamp, f)
                if not success:
                    all_success = False
                if min_timestamp == total_min:
                    break
                max_timestamp = min_timestamp
                min_timestamp = max(total_min, min_timestamp - step)
        return all_success

    def do_download(self, tick, from_timestamp, to_timestamp, f):
        http = urllib3.PoolManager()
        url = URL_FORMAT.format(tick, from_timestamp, to_timestamp)
        response = http.request("GET", url)
        print(url)
        soup = BeautifulSoup(response.data, "html.parser")
        try:
            for tr in soup.find(id="Col1-1-HistoricalDataTable-Proxy").find("table").find_all("tr"):
                tds = tr.find_all("td")
                if len(tds) < 5:
                    continue
                date = tds[0].text
                open_price = tds[1].text
                close_price = tds[4].text
                f.write("{}\t{}\t{}\n".format(date, open_price, close_price))
            return True
        except:
            print("fail to parse: {}".format(tick))
            return False


class TickerAPI:
    def download(self):
        url = c.DOW_JONES_COMPONENTS_URL
        output = c.DOW_JONES_COMPONENTS_FILE

        http = urllib3.PoolManager()
        response = http.request('GET', url)
        soup = BeautifulSoup(response.data, "html.parser")
        results = []
        for trs in soup.find_all("tr"):
            tds = trs.find_all("td")
            name = tds[0].text
            ticker = tds[1].text
            if name == "Name":
                continue
            if name == "Walgreens Boots Alliance":
                name = "General Electric Company "
                ticker = "GE"
            results.append((name, ticker))
        with open(output, "w") as f:
            for r in results:
                f.write("{},{}\n".format(r[0], r[1]))
