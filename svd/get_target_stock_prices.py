from svd.finance.context import Context

if __name__ == '__main__':
    c = Context()
    usecase = c.get_coefficient_usecase()
    repository = c.get_history_repository()
    ticks = usecase.get_ticks()[0]
    ticks = ticks[0:4]
    start = 99
    end = 111
    dates = []
    with open("input/dates.txt") as f:
        for l in f.readlines():
            id, date = l.rstrip().split("\t")
            date = date.split(",")[0]
            if start <= int(id) < end:
                dates.append(date)
    with open("output/prices", "w") as f:
        result = {}
        f.write("\t{}\n".format("\t".join(dates)))
        for id, tick in enumerate(ticks):
            histories = repository.find_history_by_tick(tick)[start: end]
            prices = []
            result[id] = {}
            for h in histories:
                prices.append(str(h.close_price))
            f.write("{}\t{}\n".format(tick, "\t".join(prices)))
            usecase.fill(result, id, 4, histories)
        for id, tick in enumerate(ticks):
            cs = []
            for k, v in result[id].items():
                cs.append(str(v))
            f.write("{}\t{}\n".format(tick, "\t".join(cs)))