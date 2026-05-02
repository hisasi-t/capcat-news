import feedparser
import datetime
import html as html_lib
from feeds import FEEDS
from keywords import CATEGORIES, EXCLUDE_KEYWORDS

JST = datetime.timezone(datetime.timedelta(hours=9))
WEEKDAY = ["月", "火", "水", "木", "金", "土", "日"]


def fetch_all():
    articles = []
    for url in FEEDS:
        try:
            d = feedparser.parse(url, request_headers={"User-Agent": "Mozilla/5.0"})
            source = d.feed.get("title", url)
            for e in d.entries[:20]:
                articles.append({
                    "title": e.get("title", "").strip(),
                    "link": e.get("link", ""),
                    "summary": e.get("summary", ""),
                    "source": source,
                })
        except Exception as ex:
            print(f"skip {url}: {ex}")
    return articles


def categorize(articles):
    # 除外キーワードにひっかかる記事を先に弾く
    filtered = [
        a for a in articles
        if not any(kw in a["title"] + a["summary"] for kw in EXCLUDE_KEYWORDS)
    ]

    buckets = {cat: [] for cat in CATEGORIES}
    used = set()

    for cat, keywords in CATEGORIES.items():
        if not keywords:
            continue
        for a in filtered:
            aid = id(a)
            if aid in used:
                continue
            text = a["title"] + " " + a["summary"]
            if any(kw in text for kw in keywords):
                buckets[cat].append(a)
                used.add(aid)

    # キャッチオール（最後のカテゴリ）
    catch = list(CATEGORIES.keys())[-1]
    for a in filtered:
        if id(a) not in used:
            buckets[catch].append(a)
            used.add(id(a))

    return buckets


def render(buckets):
    now = datetime.datetime.now(JST)
    dow = WEEKDAY[now.weekday()]
    date_str = now.strftime(f"%Y年%m月%d日（{dow}）")

    active = [(cat, items) for cat, items in buckets.items() if items]

    # 目次
    toc_items = ""
    for i, (cat, _) in enumerate(active):
        label = html_lib.escape(cat)
        toc_items += f'<a class="toc-link" href="#s{i}">{label}</a>'

    # セクション
    sections = ""
    for i, (cat, items) in enumerate(active):
        cards = ""
        for a in items[:6]:
            title = html_lib.escape(a["title"])
            source = html_lib.escape(a["source"])
            link = html_lib.escape(a["link"])
            cards += f"""
        <a class="card" href="{link}" target="_blank" rel="noopener">
          <span class="card-source">{source}</span>
          <span class="card-title">{title}</span>
        </a>"""
        sections += f"""
    <section id="s{i}">
      <h2>{html_lib.escape(cat)}</h2>
      <div class="cards">{cards}
      </div>
    </section>"""

    return f"""<!DOCTYPE html>
<html lang="ja">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<meta name="theme-color" content="#111111">
<title>朝刊 {date_str}</title>
<style>
  * {{ box-sizing: border-box; margin: 0; padding: 0; }}
  body {{
    background: #f4f4f4;
    color: #111;
    font-family: -apple-system, 'Hiragino Sans', 'Noto Sans JP', sans-serif;
    padding-bottom: 3rem;
  }}
  header {{
    background: #111;
    color: #fff;
    padding: 1.1rem 1rem 0.9rem;
  }}
  header h1 {{
    font-size: 1.1rem;
    font-weight: bold;
    letter-spacing: 0.04em;
  }}
  header .date {{
    font-size: 0.75rem;
    color: #aaa;
    margin-top: 0.2rem;
  }}
  nav {{
    background: #fff;
    border-bottom: 1px solid #ddd;
    padding: 0.6rem 0.75rem;
    display: flex;
    flex-wrap: wrap;
    gap: 0.4rem;
  }}
  .toc-link {{
    font-size: 0.72rem;
    color: #444;
    text-decoration: none;
    background: #f0f0f0;
    border-radius: 4px;
    padding: 0.2rem 0.5rem;
    white-space: nowrap;
  }}
  .toc-link:active {{ background: #ddd; }}
  section {{
    margin: 1rem 0.75rem 0;
  }}
  h2 {{
    font-size: 0.88rem;
    font-weight: bold;
    color: #111;
    border-left: 3px solid #111;
    padding-left: 0.55rem;
    margin-bottom: 0.55rem;
  }}
  .cards {{
    display: flex;
    flex-direction: column;
    gap: 1px;
    background: #ddd;
    border: 1px solid #ddd;
    border-radius: 8px;
    overflow: hidden;
  }}
  .card {{
    background: #fff;
    padding: 0.75rem 0.9rem;
    text-decoration: none;
    color: inherit;
    display: flex;
    flex-direction: column;
    gap: 0.2rem;
  }}
  .card:active {{ background: #f0f0f0; }}
  .card-source {{
    font-size: 0.65rem;
    color: #888;
  }}
  .card-title {{
    font-size: 0.9rem;
    line-height: 1.5;
    color: #111;
  }}
  footer {{
    text-align: center;
    font-size: 0.68rem;
    color: #aaa;
    margin-top: 2rem;
  }}
</style>
</head>
<body>
<header>
  <h1>朝刊</h1>
  <div class="date">{date_str}</div>
</header>
<nav>{toc_items}</nav>
{sections}
<footer>{now.strftime("%H:%M")} JST · 自動生成</footer>
</body>
</html>"""


if __name__ == "__main__":
    arts = fetch_all()
    buckets = categorize(arts)
    page = render(buckets)
    with open("index.html", "w", encoding="utf-8") as f:
        f.write(page)
    total = sum(len(v) for v in buckets.values())
    print(f"完了: {total} 件")
