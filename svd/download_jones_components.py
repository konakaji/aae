import svd.finance.context as c

if __name__ == '__main__':
    repository = c.Context().get_ticker_repository()
    repository.download_tickers()
