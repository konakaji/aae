from svd.finance.context import Context
import svd.constant as const

if __name__ == '__main__':
    c = Context()
    usecase = c.get_coefficient_usecase()
    usecase.build(const.DEFAULT_STOCKS, 5, 1)