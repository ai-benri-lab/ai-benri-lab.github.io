# -*- coding: utf-8 -*-
"""IndexNow: notify Bing / Yandex / Seznam of our URLs for fast crawling & indexing.

被リンクの薄い新規サイトの「発見経路」を補うための無料の即時通知プロトコル（公式）。
Google は非対応だが Bing はこれで素早くクロールし、Bing の index は Copilot 等の AI 検索にも効く
（当サイトの AIO 狙いと相性が良い）。sitemap.xml（自前生成）の URL 一覧を api.indexnow.org へ POST する。

前提: キーファイル https://ai-benri-lab.github.io/<key>.txt が公開されていること（tools/.indexnow_key と一致）。
blog_sync から gen_blog の後に実行し、更新のたびに Bing へ通知する。
"""
import re, sys
from pathlib import Path
import requests

REPO = Path(__file__).resolve().parents[1]
HOST = "ai-benri-lab.github.io"
KEY = (REPO / "tools" / ".indexnow_key").read_text(encoding="utf-8").strip()
KEYLOC = f"https://{HOST}/{KEY}.txt"
ENDPOINT = "https://api.indexnow.org/indexnow"


def urls_from_sitemap() -> list[str]:
    t = (REPO / "sitemap.xml").read_text(encoding="utf-8")
    urls = re.findall(r"<loc>\s*(https://[^<\s]+?)\s*</loc>", t)
    # 自ホストのみ採用（injection/誤送信対策）
    return [u for u in dict.fromkeys(urls) if u.startswith(f"https://{HOST}/")]


def ping(urls: list[str]) -> int | None:
    if not urls:
        print("indexnow: no urls")
        return None
    body = {"host": HOST, "key": KEY, "keyLocation": KEYLOC, "urlList": urls[:10000]}
    r = requests.post(ENDPOINT, json=body,
                      headers={"Content-Type": "application/json; charset=utf-8"}, timeout=30)
    # 200=OK / 202=受理(検証待ち) / 400,403,422,429=要確認
    print(f"indexnow: submitted {len(urls)} urls -> HTTP {r.status_code} {r.text[:80]}")
    return r.status_code


if __name__ == "__main__":
    try:
        ping(urls_from_sitemap())
    except Exception as e:  # noqa: BLE001
        print(f"indexnow failed (non-fatal): {e}", file=sys.stderr)
