import pandas as pd
import requests
from bs4 import BeautifulSoup
import re
import time
import random
from tools import find_key #我自己写的"根据value找key"函数

import fake_useragent #随机生成UA
ua = fake_useragent.UserAgent()

# 目标：最新中心城区：西湖、余杭、拱墅、上城、滨江、临平、钱塘、萧山
# 房天下，杭州，小区
# 小区首页url访问次数过多会产生验证码，需要绕开


# 因为传入的都是字典，所以这里写个读取文件，转成字典的工具
# 这样的话可以控制每次爬取的内容和url，不用重复爬取
def txt_to_dict(fileroot): # 注：这里的fileroot需要是完整的路径
    info_total = {} # 空字典，储存读入的名称与url
    with open(fileroot, "r", encoding = "utf-8") as f:
        lines = f.readlines() # 把每行作为列表元素返回，包括\t和\n字符串
        for i in range(0, len(lines)): # 遍历每行的元素，应该形如："xxx名\t链接\n"，形式为字符串
            line_key = re.findall(r"^.+\t", lines[i])
            line_value = re.findall(r"http.+$", lines[i])
            line_key = "".join(line_key).replace("\t", "")
            line_value = "".join(line_value)
            info_total[line_key] = line_value
    return info_total #返回字典


# 封装1，获取街道真实页面。输入的是字典
def from_city_to_district(root_url): # 封装1，获得区链接。输入的是url
    # 0.获得路径后的"?rfss="内容，绕开验证码
    my_ua = {"User-Agent": ua.random}
    t = requests.get(root_url, headers = my_ua)
    print(f"杭州根：{t.status_code}") #监测
    t2 = BeautifulSoup(t.text, "html.parser") #分析源码，发现真正的杭州url包含了验证码查询参数
    t3 = t2.find_all("script")[3].text #查找第4个script元素，包含了真正的url
    pattern = re.compile(r"var t\d='(r.*)';")
    city_url = f"{root_url}?{pattern.search(t3).group(1)}" #获得真正的杭州url，绕过验证码！
    print(f"杭州真实页面：{city_url}") #监测

    # 1.遍历每个区，记录每个区的url
    search_district = r"^/housing/\d+__0_3_0_0_1_0_0_0/$" #先写好正则表达式，匹配区的url
    district_root_urls = {} #空字典，储存区的根url（注！此时还不是真正的区访问链接）
    district_urls = {} #空字典，储存区真正的访问url

    # 1.1获得每个区的根url
    r = requests.get(city_url, headers = my_ua)
    print(f"杭州真实访问：{r.status_code}") #监测
    r2 = BeautifulSoup(r.text, "html.parser")
    r3 = r2.find_all("a")
    for r3_1 in r3:
        if r3_1.get("href") != None and re.match(search_district, r3_1.get("href")):
            # 测试爬取：淳安160。共93个小区
            # 原区代码："152", "149", "151", "155", "154", "17367", "16704", "156"
            aim_district = ["152", "149", "151", "155", "154", "17367", "16704", "156"] # 匹配区代码
            if any(district in r3_1.get("href") for district in aim_district): #any逻辑判断
                district_root_urls[r3_1.string] = f"https://hz.esf.fang.com{r3_1.get('href')}"

    # 1.2获得每个区的真实访问url(获取"?rfss="内容)
    with open("district_urls.txt", "a", encoding = "utf-8") as f:
        for district_root_url in district_root_urls.values():
            t_key_district = find_key.get_key(district_root_urls, district_root_url) #根据url返回key(区名)
            t = requests.get(district_root_url, headers = my_ua)
            print(f"{t_key_district}根页面：{t.status_code}")  # 检查根页面url
            t2 = BeautifulSoup(t.text, "html.parser")  # 分析源码，发现真正的杭州url包含了验证码查询参数
            t3 = t2.find_all("script")[3].text  # 查找第4个script元素，包含了真正的url
            pattern = re.compile(r"var t\d='(r.*)';")
            district_urls[t_key_district] = f"{district_root_url}?{pattern.search(t3).group(1)}"  # 获得真正的杭州url，绕过验证码！
            f.write(f"{t_key_district}\t{district_urls[t_key_district]}\n") # 写入文件
            f.flush() #不等下一轮循环，立即写入
        print(f"区真实页面{len(district_urls)}个：{district_urls.items()}\n") #检查区链接

# 封装2，获取街道真实页面。输入的是字典
def from_district_to_street(district_urls):
# 2.遍历区里每个街道，记录每个街道的url
    street_root_urls = {} #空字典，储存街道根url
    street_urls = {} #空字典，储存街道真实访问url

    # 2.1获取街道的根url
    for district_url in district_urls.values():
        t_key_district = find_key.get_key(district_urls, district_url) #根据url返回key(区名)
        my_ua = {"User-Agent": ua.random}
        r = requests.get(district_url, headers = my_ua)
        print(f"{find_key.get_key(district_urls, district_url)}街道根：{r.status_code}") #监测，根据value返回key
        r2 = BeautifulSoup(r.text, "html.parser")
        r3 = r2.find("p", id="shangQuancontain")
        r4 = r3.find_all("a")
        for r4_1 in r4:
            if "不限" not in r4_1.get_text():
                street_root_urls[f"{t_key_district}>{r4_1.string}"] = f"https://hz.esf.fang.com{r4_1.get('href')}"
    print(f"街道根页面链接{len(street_root_urls)}个：{street_root_urls.items()}\n") #检查所有区的街道链接

    # 2.2获取街道的真实访问url
    with open("street_urls.txt", "a", encoding = "utf-8") as f:
        for street_root_url in street_root_urls.values():
            t_key_street = find_key.get_key(street_root_urls, street_root_url) #根据url返回key(区名>街道名)
            my_ua = {"User-Agent": ua.random}
            t = requests.get(street_root_url, headers = my_ua)
            print(f"{t_key_street}街道根页面：{t.status_code}")  # 检查根页面url
            t2 = BeautifulSoup(t.text, "html.parser")  # 分析源码，发现真正的杭州url包含了验证码查询参数
            t3 = t2.find_all("script")[3].text  # 查找第4个script元素，包含了真正的url
            pattern = re.compile(r"var t\d='(r.*)';")
            street_urls[t_key_street] = f"{street_root_url}?{pattern.search(t3).group(1)}"  # 获得真正的杭州url，绕过验证码！
            f.write(f"{t_key_street}\t{street_urls[t_key_street]}\n") #写入文件
            f.flush() #不等下一轮循环，立即写入
        print(f"街道真实页面{len(street_urls)}个：{street_urls.items()}\n") #检查区链接

# 封装3：获取小区的访问页面并记录。输入的是字典。
def from_street_to_house(street_urls):
    ############# 创建文件，储存结果 ##############
    with open("house_link.txt", "a", encoding = "utf-8") as f_link:

        # 3.遍历街道下每个小区的url，注意翻页。【小区url写入文件】
        house = {} #字典。储存所有小区名及链接
        for street_url in street_urls.values():
            t_key_street = find_key.get_key(street_urls, street_url) #根据url返回key(区名>街道名)

            # 3.1获取页码，实现翻页
            my_ua = {"User-Agent": ua.random}
            r = requests.get(street_url, headers = my_ua)
            print(f"\n{find_key.get_key(street_urls, street_url)}真实访问:{r.status_code}") #监测
            r1 = BeautifulSoup(r.text, "html.parser")
            pages = r1.find("span", class_ = "fy_text").get_text()[2:] #页码是"1/xx"，故取两位后
            search_page = re.compile(r"\d+_0_0_0/")
            for i in range(1, int(pages)+1): #从第1页翻到最后一页
                street_url_page = re.sub(search_page, f"{i}_0_0_0/", street_url) #获得每页的链接
                print(f"{find_key.get_key(street_urls, street_url)}共{pages}页，第{i}页:{street_url_page}") #监测：翻页

                # 3.2遍历所有小区，url写入文件
                my_ua = {"User-Agent": ua.random}
                s = requests.get(street_url_page, headers = my_ua)
                s1 = BeautifulSoup(s.text, "html.parser")
                s2 = s1.find_all("a", class_ = "plotTit")
                for s2_1 in s2:
                    house_urls = f"https://hz.esf.fang.com{s2_1['href']}"
                    house[f"{t_key_street}>{s2_1.get_text()}"] = house_urls #用字典储存每个小区url
                    f_link.write(f"{find_key.get_key(house, house_urls)}\t{house_urls}\n") #每页小区url写入文件
                    f_link.flush() #立即写入

# 封装4：获取小区信息。输入的是字典
def get_house_info(house):
# 4.从小区url进入小区详情/攻略/成交，爬取信息，写入表格
# 4.1通过小区总urls，爬取小区详情，输出表格
    num = 0
    with open("house_recorded.txt", "a", encoding = "utf-8") as f: # 记录已经爬取过的小区
        for house_url in house.values():
            num += 1
            # 读取目前已爬取的信息，读取excel
            # 字典储存小区详情信息，注意：每次循环要读取一遍！不然上一个小区会留到下一个小区
            house_info = pd.read_excel('house_info.xlsx', index_col = [0])
            house_info_now = {}

            # 4.1.1爬取小区详情信息
            house_detail = house_url.replace(".htm", "/housedetail.htm") # 替换url，进入详情页面
            my_ua = {"User-Agent": ua.random}
            r = requests.get(house_detail, headers = my_ua)
            r1 = BeautifulSoup(r.text, "html.parser")

            # 如果小区详情页不存在，则进入下一个小区
            r_test = r1.title
            if "杭州二手房-房天下" in r_test.string:
                continue
            # print(f"{find_key.get_key(house, house_url)}  详情页访问：{r.status_code}")  # 监测访问成功

            # 获得小区名，与小区详情
            house_info_now["小区名"] = r1.find("h3").get_text()
            info_all = r1.find("ul", class_ = "clearfix").find_all("li")
            for info in info_all:
                try: # 遇到一些没资料的楼盘，这条语句总是报错。使之跳出
                    house_info_now[info.span.get_text().replace(" ","")] = info.p.get_text(strip = True).replace(" ","").replace("\n","")
                except:
                    continue

            # 4.1.2爬取小区时间线、周边设施配套信息
            # 此部分要注意：部分小区不具备某类设施，find返回的是None，不排除的话后续程序会报错！
            house_strategy = house_url.replace(".htm", "/strategy.htm")
            my_ua = {"User-Agent": ua.random}
            r = requests.get(house_strategy, headers=my_ua)
            r1 = BeautifulSoup(r.text, "html.parser")
            # 以下这段命令是防止攻略信息不存在或页面不存在。报错即跳出
            try:
                r_test = r1.title
                if "杭州二手房-房天下" in r_test.string:
                    continue
            except:
                continue

            # print(f"{find_key.get_key(house, house_url)}  攻略页访问：{r.status_code}")  # 监测

            # 时间线：完工时间、交盘时间等..
            timeevents = r1.find_all("div", class_ = "t")
            if timeevents != None: #防止该小区没有时间线，排除None
                for timeevent in timeevents:
                    time_point = timeevent.find_previous_sibling("div", class_ = "time").string
                    house_info_now[timeevent.string] = time_point
            # 小区设施：如有的话赋值1
            facilitys = r1.find("div", class_ = "facilities")
            if facilitys != None: # 防止该小区没有任何设施，排除None
                for facility in facilitys.find_all("li"):
                    if "none_ss" not in facility["class"]:
                        house_info_now[facility.span.get_text()] = 1 # 设施标记1
            # 周边设施
            indexs = r1.find_all("h3") #先搜索“便利指数”标签，再往上找父级
            for index in indexs:
                if "交通配置" in index.string:
                    trans_text = index.find_parent().find_next_sibling().get_text().replace("\n","") #上个父级下个兄弟，定位到设施的描述文字
                    trans_round = re.findall(r"\d+个..", trans_text) #提取符合正则表达式的字符串
                    house_info_now["周边2km交通"] = "|".join(trans_round)
                elif "教育配置" in index.string:
                    edu_text = index.find_parent().find_next_sibling().get_text().replace("\n","") #上个父级下个兄弟，定位到设施的描述文字
                    edu_round = re.findall(r"\d+个..", edu_text) #提取符合正则表达式的字符串
                    house_info_now["周边3km教育"] = "|".join(edu_round)
                elif "医疗配套" in index.string:
                    med_text = index.find_parent().find_next_sibling().get_text().replace("\n","") #上个父级下个兄弟，定位到设施的描述文字
                    med_round = re.findall(r"\d+个..", med_text) #提取符合正则表达式的字符串
                    house_info_now["周边3km医疗"] = "|".join(med_round)
                elif "购物配套" in index.string:
                    shop_text = index.find_parent().find_next_sibling().get_text().replace("\n","") #上个父级下个兄弟，定位到设施的描述文字
                    shop_round = re.findall(r"\d+个..", shop_text) #提取符合正则表达式的字符串
                    house_info_now["周边3km购物"] = "|".join(shop_round)
                elif "休闲配套" in index.string:
                    lei_text = index.find_parent().find_next_sibling().get_text().replace("\n","") #上个父级下个兄弟，定位到设施的描述文字
                    lei_round = re.findall(r"\d+个..", lei_text) #提取符合正则表达式的字符串
                    house_info_now["周边3km休闲"] = "|".join(lei_round)

            # 把上述信息合并进一个数据框，第一行第一列为小区名
            info_table_now = pd.DataFrame(house_info_now, index = [0]) #将一个小区信息转成数据框
            info_table_total = pd.concat([house_info, info_table_now]) #把这个小区数据框合并到大表里
            info_table_total.to_excel("house_info.xlsx")  # 以防万一程序中途退出，每次都输出一个表
            f.write(f"{house_info_now['小区名']}\t{house_url}\t已爬取\n") # 当前小区已爬取，记录成功
            f.flush() # 立即写入
            print(f"{num}.{find_key.get_key(house, house_url)}  信息爬取√")
            # time.sleep(random.uniform(1, 2)) # 每次爬取等待1秒-2秒，避免被网站反爬检测到

# 封装5：获取小区交易信息，读取小区名和交易表格，输出xlsx
def get_trades(house_urls):
    with open("trade_record.txt", "a", encoding = "utf-8") as f:
        num = 1
        time_start = time.time() #记录运行开始时间
        for house_url in house_urls.values():
            time.sleep(random.uniform(5, 8))  # 每次爬取等待几秒
            # 先读取首页，判断有无交易；有的话，有几页
            my_ua = {"User-Agent": ua.random}
            trade_url = house_url.replace(".htm", f"/chengjiao/")
            r = requests.get(trade_url, headers = my_ua) #读首页
            r1 = BeautifulSoup(r.text, "html.parser")

            # 如果有验证码，则陷入循环，提醒刷新！
            while "访问验证" in r1.find("title").get_text():
                print("#" * 10 + f"打开{find_key.get_key(house_urls, house_url)}遇到验证码，暂停10分钟" + "#" * 10)
                time_now = time.time()  # 记录当前时间
                print(f"程序已运行时间: {(time_now - time_start)/60 :.2f}分钟")
                time.sleep(600) # 暂停再继续爬取，测试验证码消失没
                r = requests.get(trade_url, headers=my_ua)  # 读首页
                r1 = BeautifulSoup(r.text, "html.parser")

            # 如果没有交易信息，跳出
            r2 = r1.find("table").get_text()
            if "市场信息" not in r2:
                print(f"{num}.{find_key.get_key(house_urls, house_url)}: 无交易")
                f.write(f"{find_key.get_key(house_urls, house_url)}\t{trade_url}\t无交易\n")
                f.flush()
                num += 1
                continue

            # 如果有交易信息，判断页数
            # 只1页的情况
            r3 = r1.find("a", {"id":"PageControl1_hlk_last"})
            if r3 is None:
                # 每次循环前打开excel，把本次爬到的表格合并进去
                trade_info_open = pd.read_excel('trade_info.xlsx', index_col=[0])

                # 原始的html，直接.text即可，不用bs4解析
                # pd把网页读取为数据框，取列表第一个元素(即我们要的交易表格)
                t = pd.read_html(r.text)[0]
                t_name = t.assign(house_Name=find_key.get_key(house_urls, house_url))  # 赋值小区名
                trade_info = pd.concat([trade_info_open, t_name])
                trade_info.to_excel("trade_info.xlsx")
                print(f"{num}.{find_key.get_key(house_urls, house_url)}: 1页 记录成功")
            # 有>1页的情况
            elif "末页" in r3.get_text():
                # 找页数思路："下一页"的父级的上一个兄弟标签，即最后页数的span标签
                page_url = re.findall(r"-p1\d+", r3["href"])
                page = "".join(page_url).replace("-p1", "")
                for i in range(1, int(page)+1):
                    time.sleep(random.uniform(5, 8)) # 每次爬取等待几秒
                    trade_info_open = pd.read_excel('trade_info.xlsx', index_col=[0])
                    trade_url2 = house_url.replace(".htm", f"/chengjiao/t11-a11-p1{i}/")
                    r = requests.get(trade_url2, headers = my_ua)
                    r1 = BeautifulSoup(r.text, "html.parser")

                    while "访问验证" in r1.find("title").get_text():
                        print("#" * 10 + f"{find_key.get_key(house_urls, house_url)}的第{i}页遇到验证码，暂停10分钟" + "#" * 10)
                        time_now = time.time()  # 记录当前时间
                        print(f"程序已运行时间: {(time_now - time_start)/60 :.2f}分钟")
                        time.sleep(600) # 暂停再继续爬取，测试验证码消失没
                        r = requests.get(trade_url2, headers = my_ua)
                        r1 = BeautifulSoup(r.text, "html.parser")

                    t = pd.read_html(r.text)[0]
                    t_name = t.assign(house_Name = find_key.get_key(house_urls, house_url))  # 赋值小区名
                    trade_info = pd.concat([trade_info_open, t_name])
                    trade_info.to_excel("trade_info.xlsx")
                print(f"{num}.{find_key.get_key(house_urls, house_url)}: 共{page}页 记录成功")

            f.write(f"{find_key.get_key(house_urls, house_url)}\t{trade_url}\t记录成功\n")
            f.flush()
            num += 1



# 实际运行代码：
if __name__ == "__main__":
    # root_url = "https://hz.esf.fang.com/housing/__0_3_0_0_1_0_0_0/"  # 城市根页面
    #
    # # 1.爬取区链接，输出区url文件
    # from_city_to_district(root_url)
    # district_urls = txt_to_dict("D:\BaiduSyncdisk\DATA\pystudy\scraper_project\hangzhou_house_price_202308\district_urls.txt")  # 区url的绝对路径
    #
    # # 2.爬取街道链接，输出街道url文件
    # from_district_to_street(district_urls)
    # street_urls = txt_to_dict("D:\BaiduSyncdisk\DATA\pystudy\scraper_project\hangzhou_house_price_202308\street_urls.txt")  # 街道url的绝对路径
    #
    # # 3.爬取街道所有的小区url
    # from_street_to_house(street_urls)
    # house_urls = txt_to_dict("D:\BaiduSyncdisk\DATA\pystudy\scraper_project\hangzhou_house_price_202308\house_link.txt")  # 小区url的绝对路径
    #
    # # 4. 爬取小区信息，记录文件
    # get_house_info(house_urls)

    # 5.爬取交易信息，小区名匹配交易信息，输出xlsx
    house_urls_recorded = txt_to_dict("D:\BaiduSyncdisk\DATA\pystudy\scraper_project\hangzhou_house_price\house_link.txt")
    get_trades(house_urls_recorded)