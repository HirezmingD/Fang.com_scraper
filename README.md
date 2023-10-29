### 爬取房天下网站的房价交易及小区数据（Fang_com_hangzhou.py）

自己写的shit山代码

网址（杭州房天下）：https://hz.fang.com/

爬取范围，最新中心城区：西湖、余杭、拱墅、上城、滨江、临平、钱塘、萧山

网页访问顺序：房天下-杭州-小区 

爬取逻辑：

1. 爬取城区链接，输出区url文件
2. 爬取街道链接，输出街道url文件
3. 爬取街道所有的小区url
4. 爬取小区信息，记录文件
5. 爬取交易信息，小区名匹配交易信息，输出xlsx

爬取结果：
![123](https://github.com/HirezmingD/Fang.com_scraper/assets/48850493/b37108c6-bf15-4777-a34e-c9b2c03f7846)


### 调用高德API获取小区高德坐标（house_GDxy.py）
* 输入文件路径，读取小区名称，挨个返回高德坐标
* 使用的是高德地图web服务，官方开发指南:https://lbs.amap.com/api/webservice/guide/api/search
