# 三民書局暢銷總榜 → MariaDB
# 題目和提示見 README.md
# 執行前先設定帳密（DB_HOST 請改成你 VM 的 IP；程式在 VM 裡跑就用 localhost）：
#   export DB_HOST=192.168.x.x DB_USER=ricky DB_PASS=ricky DB_NAME=rickycrawer
# 執行：python crawler.py

import datetime
import os
import time
from dotenv import load_dotenv
from urllib.robotparser import RobotFileParser

import mariadb
import requests
from bs4 import BeautifulSoup

from pathlib import Path

ok = load_dotenv(Path(__file__).parent / ".env")
print(".env 讀到了嗎？", ok)

BASE = "https://www.sanmin.com.tw"
URL = "https://www.sanmin.com.tw/promote/top"
HEADERS = {"User-Agent": "course-crawler/1.0 (Ricky)"}

# 1. 先看 robots.txt 允不允許（提示 2）
# 把結果（True 或 False）存在 allowed
r = requests.get(BASE + "/robots.txt", headers=HEADERS, timeout=10)
robots = RobotFileParser()
robots.parse(r.text.splitlines())
allowed = robots.can_fetch(HEADERS["User-Agent"], URL)
print("robots.txt 允許嗎？", allowed)

books = []

if allowed:
    rank = 0  # 排名放在頁數迴圈外面，第 2 頁才會接著第 41 名

    # 延伸題：3 頁，用 for 迴圈抓完
    for page in range(1, 4):
        time.sleep(1)  # 每次請求之間等 1 秒

        # 2. 抓排行榜頁面
        page_url = URL + "?id=wbyy&pi=" + str(page)
        r = requests.get(page_url, headers=HEADERS, timeout=10)
        print("狀態碼：", r.status_code)

        # 3. 用 BeautifulSoup 找出每一本書（提示 3、4）
        soup = BeautifulSoup(r.text, "html.parser")
        items = soup.select("div.sProduct")

        for item in items:
            rank = rank + 1

            title = item.select_one("h3").get_text(strip=True)

            author_tag = item.select_one("span.Author")
            author = ""
            if author_tag:
                author = author_tag.get_text(strip=True).replace("作者：", "")

            publisher_tag = item.select_one("span.Publisher")
            publisher = ""
            if publisher_tag:
                publisher = publisher_tag.get_text(strip=True).replace("出版社：", "")

            a = item.select_one("div.Title a") or item.select_one("a")
            link = BASE + a["href"]

            books.append([rank, title, author, publisher, link])

        print("第", page, "頁：", len(items), "本")

print("抓到", len(books), "本")

if len(books) > 0:
    today = datetime.date.today()

    # 4. 存進 MariaDB，同一天跑兩次不能重複（提示 5）
    
    conn = mariadb.connect(
        host=os.environ.get("DB_HOST", "localhost"),
        user=os.environ["DB_USER"],
        password=os.environ["DB_PASS"],
        database=os.environ["DB_NAME"],
    )
    cur = conn.cursor()

    # (rank_date, rank_no) 是唯一鍵：同一天同名次已存在 → 改成更新，不會多一列
    sql = (
        "INSERT INTO books (rank_date, rank_no, title, author, publisher, url) "
        "VALUES (?, ?, ?, ?, ?, ?) "
        "ON DUPLICATE KEY UPDATE "
        "title = VALUES(title), author = VALUES(author), "
        "publisher = VALUES(publisher), url = VALUES(url)"
    )
    for b in books:
        cur.execute(sql, (today, b[0], b[1], b[2], b[3], b[4]))
    conn.commit()  # 沒有 commit，資料不會真的存進去

    # 5. 從資料庫查回來，印出共幾本、前 10 名（提示 6）
    cur.execute("SELECT COUNT(*) FROM books WHERE rank_date = ?", (today,))
    print("資料庫裡", today, "共", cur.fetchone()[0], "本")

    cur.execute(
        "SELECT rank_no, title FROM books WHERE rank_date = ? ORDER BY rank_no LIMIT 10",
        (today,),
    )
    for rank_no, title in cur.fetchall():
        print(rank_no, title)

    conn.close()
else:
    print("一本都沒抓到，不寫資料庫")