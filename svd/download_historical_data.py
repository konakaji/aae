import svd.finance.context as c

if __name__ == '__main__':
    history_repository = c.Context().get_history_repository()
    ticker_repository = c.Context().get_ticker_repository()
    no_cache = True
    for tick in ticker_repository.find_all_ticks():
        if no_cache or not history_repository.is_history_exist(tick, True):
            if not history_repository.download_daily(tick):
                continue
        if no_cache or not history_repository.is_history_exist(tick):
            history_repository.build_monthly_data(tick)
