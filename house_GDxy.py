import pandas as pd
import requests
import json
import re

# 封装1：输入文件路径，读取小区名称，挨个返回高德坐标
def get_house_xy(file):
    with open(file, "r", encoding = "utf-8") as f:
        house_xy = {}
        i = 1
        for house in f.readlines():
            my_params = {
                "key": my_key,
                "keywords": house,
                "city": "杭州",
                "citylimit": "true"
            }
            house_search = house.replace("\n", "").replace("\t", " ")
            house_name = re.findall(r"\s.+", house_search)[0]
            try:
                r = requests.get(root_url, params = my_params)
                # 读取高德返回的json信息
                r1 = json.loads(r.text)
                house_xy[house_name] = r1["pois"][0]["location"]
                print(f"{i}. 已记录{house_name} 高德坐标: {house_xy[house_name]}")
                i += 1
            except:
                print(f"{i}.{house_name} 记录失败！")
                house_xy[house_name] = "失败"
                i += 1
                continue

    table = pd.DataFrame.from_dict(house_xy, orient = "index")
    table.to_excel("house_xy.xlsx")


# 运行代码：
if __name__ == "__main__":
    my_key = "你申请的高德KEY"
    # 你需要爬取的数据类型，这个可以在高德的官网文件里找到
    root_url = "https://restapi.amap.com/v5/place/text?"
    file = "你自己的路径\house_poi_name.txt"
    # 运行程序
    get_house_xy(file)