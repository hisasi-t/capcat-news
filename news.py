import feedparser
import datetime
import html as html_lib
from feeds import FEEDS
from keywords import CATEGORIES

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
    buckets = {cat: [] for cat in CATEGORIES}
    used = set()

    for cat, keywords in CATEGORIES.items():
        if not keywords:
            continue
        for a in articles:
            aid = id(a)
            if aid in used:
                continue
            text = a["title"] + " " + a["summary"]
            if any(kw in text for kw in keywords):
                buckets[cat].append(a)
                used.add(aid)

    # キャッチオール（最後のカテゴリ）
    catch = list(CATEGORIES.keys())[-1]
    for a in articles:
        if id(a) not in used:
            buckets[catch].append(a)
            used.add(id(a))

    return buckets


def render(buckets):
    now = datetime.datetime.now(JST)
    dow = WEEKDAY[now.weekday()]
    date_str = now.strftime(f"%Y年%m月%d日（{dow}）")

    sections = ""
    for cat, items in buckets.items():
        if not items:
            continue
        cards = ""
        for a in items[:6]:
            title = html_lib.escape(a["title"])
            source = html_lib.escape(a["source"])
            link = html_lib.escape(a["link"])
            cards += f"""
        <a class="card" href="{link}" target="_blank" rel="noopener">
          <div class="card-source">{source}</div>
          <div class="card-title">{title}</div>
        </a>"""
        sections += f"""
    <section>
      <h2>{cat}</h2>
      <div class="cards">{cards}
      </div>
    </section>"""

    return f"""<!DOCTYPE html>
<html lang="ja">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<meta name="theme-color" content="#c87941">
<title>🐱☕ 朝刊 {date_str}</title>
<style>
  :root {{
    --bg:      #fdf8f2;
    --card:    #ffffff;
    --accent:  #c87941;
    --accent2: #e8a87c;
    --text:    #3a2a1a;
    --sub:     #9a8070;
    --border:  #ead5bb;
  }}
  * {{ box-sizing: border-box; margin: 0; padding: 0; }}
  body {{
    background: var(--bg);
    color: var(--text);
    font-family: -apple-system, 'Hiragino Sans', 'Noto Sans JP', sans-serif;
    padding-bottom: 3rem;
    max-width: 640px;
    margin: 0 auto;
  }}
  header {{
    background: linear-gradient(135deg, #b06a30 0%, var(--accent2) 100%);
    color: #fff;
    padding: 1.4rem 1rem 1rem;
    text-align: center;
  }}
  header h1 {{
    font-size: 1.5rem;
    font-weight: bold;
    letter-spacing: 0.05em;
  }}
  header .date {{
    font-size: 0.82rem;
    opacity: 0.88;
    margin-top: 0.35rem;
  }}
  section {{
    margin: 1.1rem 0.75rem 0;
  }}
  h2 {{
    font-size: 0.97rem;
    font-weight: bold;
    color: var(--accent);
    border-left: 4px solid var(--accent);
    padding-left: 0.6rem;
    margin-bottom: 0.65rem;
  }}
  .cards {{
    display: flex;
    flex-direction: column;
    gap: 0.55rem;
  }}
  .card {{
    background: var(--card);
    border: 1px solid var(--border);
    border-radius: 12px;
    padding: 0.8rem 1rem;
    text-decoration: none;
    color: inherit;
    display: block;
    box-shadow: 0 1px 4px rgba(0,0,0,0.07);
    transition: background 0.15s;
  }}
  .card:active {{ background: #fdefd8; }}
  .card-source {{
    font-size: 0.68rem;
    color: var(--sub);
    margin-bottom: 0.25rem;
  }}
  .card-title {{
    font-size: 0.93rem;
    line-height: 1.5;
  }}
  footer {{
    text-align: center;
    font-size: 0.72rem;
    color: var(--sub);
    margin-top: 2.5rem;
    padding: 0 1rem;
  }}
</style>
</head>
<body>
<header>
  <h1>🐱 おはよう朝刊 ☕</h1>
  <div class="date">{date_str}</div>
</header>
{sections}
<footer>自動生成 · {now.strftime("%H:%M")} JST</footer>
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
