from svd.finance.context import Context
from svd.util import date_format
import svd.constant as const
import matplotlib.pyplot as p


def plot(tick, dates, start, end, index):
    marker = ["s", "x", "o", "D"][index]
    histories = repository.find_history_by_tick(tick)[start: end + 1]
    prices = []
    for h in histories:
        prices.append(h.open_price)
    p.plot(dates, prices, label=tick, linewidth=2, marker=marker)

if __name__ == '__main__':
    c = Context()
    usecase = c.get_coefficient_usecase()
    repository = c.get_history_repository()
    ticks = const.DEFAULT_STOCKS
    start = 0
    end = 11
    dates = []
    with open(const.DATE_PATH) as f:
        for l in f.readlines():
            id, date = l.rstrip().split("\t")
            date = date_format(date)
            if start <= int(id) < end + 1:
                dates.append(date)
    with open(const.PRICE_PATH, "w") as f:
        result = {}
        f.write("\t{}\n".format("\t".join(dates)))
        for tick in ticks:
            histories = repository.find_history_by_tick(tick)[start: end + 1]
            prices = []
            for h in histories:
                prices.append(str(h.open_price))
            f.write("{}\t{}\n".format(tick, "\t".join(prices)))
    p.figure(facecolor="white", edgecolor="black", linewidth=1, figsize=[10, 6])
    p.grid(which='major', color='gray', linestyle='-')
    p.tick_params(labelsize=16)
    p.xlabel("date", fontsize=16)
    p.ylabel("price ($)", fontsize=16)
    for i, tick in enumerate(ticks):
        plot(tick, dates, start, end, i)
    p.legend(fontsize=16)
    p.savefig(const.PRICE_FIGURE_PATH)


