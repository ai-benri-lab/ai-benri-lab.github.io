# -*- coding: utf-8 -*-
"""公開済み記事のアフィリエイトリンクを queue.yaml の最新状態に合わせる。

なぜ要るか: gen_blog は記事を一度しか作らない（既に .html があれば飛ばす）。
そのため「記事を書いた時点でリンクが無かった」商品は、あとで queue.yaml に
リンクが付いても記事は空のまま＝完全な行き止まりになる。2026-10-04 時点で
商品記事 10 本がこの状態だった。同じ理由で、9/23 に もしも経由（現金化）へ
変えたリンクも、記事側は楽天直リンクのまま取り残されている。

やること（記事本文には触らない）:
  - まとめ末尾の「楽天で価格を見る」ボタンが無く queue にリンクがあれば挿す
  - ボタンはあるが URL が queue と違えば貼り替える（楽天直 -> もしも経由など）

queue.yaml に同じ slug が 2 つある商品は、どちらのリンクか決められないので触らない。

  python tools/sync_blog_links.py [--dry]
"""
from __future__ import annotations
import html, re, sys, tempfile
from pathlib import Path

import yaml

sys.path.insert(0, str(Path(__file__).resolve().parent))
from gen_blog import BLOG, RAKUTEN_RE, RROOT, fetch  # noqa: E402

HUB = '<a href="../links.html" style="display:block;text-align:center;border:2px solid #2f8f3a;'
CTA_RE = re.compile(r'<a href="([^"]+)" rel="sponsored noopener"[^>]*>楽天で価格を見る</a>')


def cta_html(url: str) -> str:
    return (f'<a href="{html.escape(url, quote=True)}" rel="sponsored noopener" target="_blank" '
            f'style="display:block;text-align:center;background:#bf0000;color:#fff;font-weight:700;'
            f'text-decoration:none;border-radius:10px;padding:13px;margin:14px 0">楽天で価格を見る</a>')


def wanted_url(item: dict) -> str:
    """queue.yaml から、形式検証を通った楽天リンクを1本選ぶ（もしも経由を優先）。"""
    ls = item.get("affiliate_links") or (
        [{"url": item["affiliate_url"]}] if item.get("affiliate_url") else [])
    urls = [str(l.get("url", "")) for l in ls]
    ok = [u for u in urls if RAKUTEN_RE.match(u)]
    return next((u for u in ok if "af.moshimo.com" in u), ok[0] if ok else "")


def main(dry: bool = False) -> int:
    tmp = Path(tempfile.mkdtemp())
    if not fetch(f"{RROOT}/data/queue.yaml", tmp / "queue.yaml"):
        print("queue.yaml を取得できない（prodesk が寝ている？）")
        return 1
    cfg = yaml.safe_load((tmp / "queue.yaml").read_text(encoding="utf-8")) or {}
    seen: dict[str, int] = {}
    for it in cfg.get("items", []):
        seen[it["slug"]] = seen.get(it["slug"], 0) + 1
    items = {it["slug"]: it for it in cfg.get("items", []) if seen[it["slug"]] == 1}

    added = changed = 0
    for f in sorted(BLOG.glob("*.html")):
        slug = f.stem
        it = items.get(slug)
        if it is None:
            continue
        want = wanted_url(it)
        if not want:
            continue
        s = f.read_text(encoding="utf-8")
        m = CTA_RE.search(s)
        if m:
            if html.unescape(m.group(1)) == want:
                continue
            new = s[:m.start()] + cta_html(want) + s[m.end():]
            changed += 1
            what = "貼り替え"
        else:
            i = s.find(HUB)
            if i < 0:
                print(f"  {slug}: まとめのボタンが見つからないので触らない")
                continue
            new = s[:i] + cta_html(want) + s[i:]
            added += 1
            what = "追加"
        print(f"  {slug}: {what} -> {want[:72]}")
        if not dry:
            f.write_text(new, encoding="utf-8")
    print(f"{'(dry) ' if dry else ''}リンク追加 {added} 本 / 貼り替え {changed} 本")
    return 0


if __name__ == "__main__":
    sys.exit(main(dry="--dry" in sys.argv))
