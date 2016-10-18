# loveliv
SIF 国服活动追踪器，可以每分钟爬取档线和**指定玩家的得分**，并支持微信提醒。

## 功能

本项目分为三个组件
- 爬虫 `Servant`：从SIFLive爬取档线和指定玩家的得分、排名、等级信息
- Web服务器 `Web`：实时展示档线、玩家分数、排名变化等数据和图表
- 微信机器人 `Bot`：当关注玩家等级提升、档位变化、分数变化时提醒

## 运行方法

#### 1. 首先，你要安装 Python 3.4 +

#### 2. `python3 -m pip install -r requirements.txt`

#### 3. 初始化数据库

```bash
$ python3 -i utils.py
>>> init_master()
>>> exit()
```

#### 4. 输入关注者列表

```sql
$ sqlite3 events.db
SQLite version 3.x.x 20xx-xx-xx xx:xx:xx
Enter ".help" for instructions
Enter SQL statements terminated with a ";"
sqlite> insert into follows (ind, id, name) values (1, xxx, 'xxx');

```

其中，`ind` 是玩家在本系统中的编号，要求 `isinstance(ind,int) and 1<=ind<=5`（更改代码可以放宽ind数量的限制）；
`id` 是玩家在 sifcn.loveliv.es 网站中的 ID；`name` 是昵称。

#### 5. 启动爬虫模块

`python3 servant.py`

使用 `-e EVENT_ID` 参数指定活动 ID，如留空将爬取最新的活动；
使用 `-b BUGGY_USERS,...` 来指定爬取时减少关注哪些人，当爬取这些人出错时将不会重试，也不会记录日志。

#### 6. 启动 Web 服务器

`python3 webserver.py`

使用 `LOVELIV_PORT` 参数指定端口，默认为`80`。

#### 7. 启动微信机器人

`python3 chatbot.py`

你需要事先创建一个用于通知的微信群，将群聊名称填入代码的 `CHAT_NAME` 常量中，然后用微信扫码登录。
