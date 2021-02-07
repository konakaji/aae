from svd.finance.entity import History, StateCoefficient
from svd.finance.api import HistoryApi, TickerAPI
import os, svd.finance.context as c, numpy, math


class HistoryRepository:
    def __init__(self, history_api: HistoryApi):
        self.history_api = history_api

    def download_daily(self, tick):
        return self.history_api.download(tick)

    def build_monthly_data(self, tick):
        prev_month = None
        with open(c.DOW_JONES_HISTORICAL_DATA_FORMAT.format(tick)) as f, open(
                c.DOW_JONES_HISTORICAL_MONTHLY_DATA_FORMAT.format(tick), "w") as w:
            for l in f.readlines():
                date, open_price, close_price = l.rstrip().split("\t")
                month = date.split(" ")[0]
                if prev_month is not None and prev_month != month:
                    w.write("{}\t{}\t{}\n".format(prev_date, prev_open_price, prev_close_price))
                prev_month = month
                prev_date = date
                prev_open_price = open_price
                prev_close_price = close_price
            w.write(l)

    def find_history_by_tick(self, tick, daily=False):
        results = []
        file = c.DOW_JONES_HISTORICAL_MONTHLY_DATA_FORMAT.format(tick)
        if daily:
            file = c.DOW_JONES_HISTORICAL_DATA_FORMAT.format(tick)
        with open(file) as f:
            for l in f.readlines():
                date, open_price, close_price = l.rstrip().split("\t")
                results.append(History(date, float(open_price), float(close_price)))
        results.reverse()
        return results

    def find_history_by_tick_and_span(self, tick, span, from_index):
        results = []
        for index, history in enumerate(self.find_history_by_tick(tick)):
            if index < from_index:
                continue
            elif index >= from_index + span:
                continue
            results.append(history)
        return results

    def is_history_exist(self, tick, daily=False):
        file = c.DOW_JONES_HISTORICAL_MONTHLY_DATA_FORMAT.format(tick)
        if daily:
            file = c.DOW_JONES_HISTORICAL_DATA_FORMAT.format(tick)
        if not os.path.exists(file):
            return False
        if len(self.find_history_by_tick(tick, daily)) == 0:
            return False
        return True


class TickerRepository:
    def __init__(self, ticker_api: TickerAPI):
        self.ticker_api = ticker_api
        self.tick_map = {"DWDP": "DD"}

    def download_tickers(self):
        self.ticker_api.download()

    def find_all_ticks(self):
        results = []
        with open(c.DOW_JONES_COMPONENTS_FILE) as f:
            for i, l in enumerate(f.readlines()):
                name, tick = l.rstrip().split(",")
                if tick in self.tick_map:
                    tick = self.tick_map[tick]
                results.append(tick)
        return results


class CoefficientRepository:
    def save(self, matrix: StateCoefficient, span, date_from_index):
        numpy.save(c.COEFFICIENT_FILE_FORMAT.format(span, date_from_index), matrix.data)
        with open(c.VISUALIZE_COEFFICIENT_FORMAT.format(span, date_from_index), "w") as f:
            for vector in matrix.data:
                f.write("{}\n".format("\t".join([str(v) for v in vector])))

    def save_dates(self, dates: [str]):
        with open(c.DATES_FILE, "w") as f:
            for i, d in enumerate(dates):
                f.write("{}\t{}\n".format(i, d))

    def save_tickers(self, tickers: [str]):
        with open(c.TICKS_FILE, "w") as f:
            for i, d in enumerate(tickers):
                f.write("{}\t{}\n".format(i, d))

    def load(self, span, date_from_index) -> StateCoefficient:
        data = numpy.load(c.COEFFICIENT_FILE_FORMAT.format(span, date_from_index))
        return StateCoefficient(data)

    def load_sub(self, sub, span, date_from_index) -> StateCoefficient:
        data = numpy.load(c.COEFFICIENT_FILE_FORMAT.format(span, date_from_index))
        return StateCoefficient(data[0: sub] * math.sqrt(len(data)) / math.sqrt(sub))
