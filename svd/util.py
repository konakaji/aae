import svd.constant as const
import json
import os


def pickup(index, prefix):
    current = None
    min = const.INTEGER_MAX
    layer = None
    count = 0
    files = os.listdir(const.MODEL_PATH)
    files.sort()
    for filename in files:
        if not filename.startswith(prefix + "-"):
            continue
        if filename.__contains__("-" + str(index) + "-"):
            with open(const.MODEL_PATH + "/" + filename) as f:
                r = f.read()
                json_txt = json.loads(r)
                e = float(json_txt["extra"][const.ENERGY_KEY])
                l = json_txt["extra"][const.LAYER_KEY]
                if min > e:
                    min = e
                    layer = l
                    current = filename
            count = count + 1
            # if count == 5:
            #     break
    return min, current, layer

def date_format(date_str):
    day_month, year = date_str.split(",")
    month, day = day_month.split(" ")
    return "{} {}".format(month, year[3:5])