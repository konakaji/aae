from svd.finance.context import Context
from svd.util import date_format
import svd.constant as const

if __name__ == '__main__':
    c = Context()
    usecase = c.get_coefficient_usecase()
    repository = c.get_history_repository()
    ticks = const.DEFAULT_STOCKS
    start = 0
    end = 12
    dates = []
    with open(const.DATE_PATH) as f:
        for l in f.readlines():
            id, date = l.rstrip().split("\t")
            date = date_format(date)
            if start <= int(id) < end:
                dates.append(date)
    with open(const.PRICE_PATH, "w") as f:
        result = {}
        f.write("\t{}\n".format("\t".join(dates)))
        for tick in ticks:
            histories = repository.find_history_by_tick(tick)[start: end]
            prices = []
            for h in histories:
                prices.append(str(h.open_price))
            f.write("{}\t{}\n".format(tick, "\t".join(prices)))
