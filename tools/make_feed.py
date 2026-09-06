# -*- coding: utf-8 -*-
"""RSS 2.0 フィード生成（発見経路の補強）。blog/articles.json から feed.xml をルートに出力。
アグリゲーター・一部AIクローラー・フィードリーダーが新着を拾える標準シグナル。blog_sync から実行。"""
import json
from datetime import datetime, timezone, timedelta
from pathlib import Path
from xml.sax.saxutils import escape

REPO = Path(__file__).resolve().parents[1]
SITE = "https://ai-benri-lab.github.io"
JST = timezone(timedelta(hours=9))
WD = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]
MO = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]


def rfc822(d: str) -> str:
    try:
        dt = datetime.strptime(d, "%Y-%m-%d").replace(tzinfo=JST)
    except Exception:  # noqa: BLE001
        dt = datetime.now(JST)
    return f"{WD[dt.weekday()]}, {dt.day:02d} {MO[dt.month-1]} {dt.year} {dt:%H:%M:%S} +0900"


def build() -> int:
    arts = json.loads((REPO / "blog" / "articles.json").read_text(encoding="utf-8"))
    items = sorted(arts.values(), key=lambda a: a.get("date", ""), reverse=True)
    now = f"{WD[datetime.now(JST).weekday()]}, {datetime.now(JST):%d} {MO[datetime.now(JST).month-1]} {datetime.now(JST).year} {datetime.now(JST):%H:%M:%S} +0900"
    parts = ['<?xml version="1.0" encoding="UTF-8"?>',
             '<rss version="2.0" xmlns:atom="http://www.w3.org/2005/Atom">', '<channel>',
             '<title>AIべんりラボ 便利ガジェットレビュー</title>',
             f'<link>{SITE}/blog/</link>',
             f'<atom:link href="{SITE}/feed.xml" rel="self" type="application/rss+xml" />',
             '<description>AIが運営する便利ガジェットのレビュー・比較メディア。公開仕様と検証動画に基づく客観レビュー。</description>',
             '<language>ja</language>', f'<lastBuildDate>{now}</lastBuildDate>']
    for a in items:
        slug = a.get("slug", "")
        url = f"{SITE}/blog/{slug}.html"
        title = escape(str(a.get("title", slug)))
        cat = escape(str(a.get("category", "")))
        parts += ['<item>', f'<title>{title}</title>', f'<link>{url}</link>',
                  f'<guid isPermaLink="true">{url}</guid>',
                  f'<category>{cat}</category>', f'<pubDate>{rfc822(a.get("date",""))}</pubDate>',
                  f'<description>{title}</description>', '</item>']
    parts += ['</channel>', '</rss>']
    (REPO / "feed.xml").write_text("\n".join(parts), encoding="utf-8")
    print(f"feed.xml: {len(items)} items")
    return len(items)


if __name__ == "__main__":
    build()
