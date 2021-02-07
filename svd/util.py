import svd.constant as const
import json
import os


def pickup(index, prefix):
    current = None
    min = const.INTEGER_MAX
    layer = None
    for filename in os.listdir(const.MODEL_PATH):
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
    return min, current, layer
