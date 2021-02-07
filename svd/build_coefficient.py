from svd.finance.context import Context

if __name__ == '__main__':
    c = Context()
    usecase = c.get_coefficient_usecase()
    usecase.build(["XOM", "WMT", "PG", "MSFT"], 5, 1)