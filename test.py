books = []
error = []
for rank, item in enumerate(items, start=1):
    title_tag = item.select_one(".Title h3")
    link_tag = item.select_one(".Title a")
    author_tag = item.select_one("span.Author")
    publisher_tag = item.select_one("span.Publisher")

    if not all((title_tag, link_tag, author_tag, publisher_tag)):
       
        error.append({
            "rank": rank,
            "reason": "資料不完整"

        })
        print(f"第 {rank} 本資料不完整")
        continue