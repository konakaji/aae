import sys, warnings

sys.path.append("../")
warnings.filterwarnings('ignore')

from ibmq.base import find_key

if __name__ == '__main__':
    print("api_key:", find_key())
