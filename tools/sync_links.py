# -*- coding: utf-8 -*-
"""links.html の商品カード欄を prodesk の queue.yaml から自動再生成して push する。

開発機のタスクスケジューラ（links-sync、毎日10:50）から呼ばれる。人の介在なし。
- queue.yaml を prodesk から scp（affiliate_links がある商品だけカード化）
- links.html の AUTO-CARDS マーカー間を差し替え
- 差分があれば git commit + push（GitHub Pages が数分で反映）

安全策（queue.yaml 由来テキストはLLM/外部データを含むため信頼しない）:
- name/blurb は HTML エスケープ + 長さ制限（injectionでタグ/スクリプトを入れられない）
- リンク URL は a.r10.to 直リンク、または もしも経由リンク（現金化・媒体固定パラメータ+item.rakuten）のみ採用
  （それ以外は「準備中」表示）
"""
import html
import re
import subprocess
import sys
from pathlib import Path

import yaml

REPO = Path(__file__).resolve().parents[1]
LINKS = REPO / "links.html"
import os as _os
KEY = _os.environ.get("PRODESK_KEY", str(Path.home() / ".ssh" / "id_ed25519_claude_win"))
REMOTE = _os.environ.get("PRODESK_HOST", "claude@192.168.11.30") + ":C:/Users/claude/shorts-factory/data/queue.yaml"
START, END = "<!-- AUTO-CARDS START -->", "<!-- AUTO-CARDS END -->"
# 楽天リンクの許可形式（injection対策）: 旧 a.r10.to 直リンク、または
# もしも経由リンク（現金化。媒体固定パラメータ + url= は item.rakuten.co.jp のみ）。
RAKUTEN_RE = re.compile(
    r"^https://a\.r10\.to/[A-Za-z0-9]+$"
    r"|^https://af\.moshimo\.com/af/c/click\?a_id=5781682&p_id=54&pc_id=54&pl_id=27059"
    r"&url=https%3A%2F%2Fitem\.rakuten\.co\.jp%2F[A-Za-z0-9%_./-]+$")


def fetch_queue() -> dict:
    tmp = REPO / "tools" / "queue_snapshot.yaml"
    subprocess.run(["scp", "-q", "-o", "BatchMode=yes", "-i", KEY, REMOTE, str(tmp)],
                   check=True, timeout=60)
    return yaml.safe_load(tmp.read_text(encoding="utf-8")) or {}


def card(item: dict) -> str:
    name = html.escape(str(item.get("name", item["slug"]))[:48])
    blurb = html.escape(str(item.get("blurb", ""))[:60])
    url = ""
    for l in item.get("affiliate_links") or []:
        u = str(l.get("url", ""))
        if RAKUTEN_RE.match(u):
            url = u
            break
    if not url:
        return ""  # リンクの無い商品はページに載せない
    sub = f'\n    <p class="sub">{blurb}</p>' if blurb else ""
    href = html.escape(url, quote=True)  # もしもURLの & を &amp; に（HTML属性として正しく）
    return f"""  <div class="card">
    <h2>{name}</h2>{sub}
    <div class="btns">
      <a class="btn rk" href="{href}" rel="sponsored noopener" target="_blank">楽天で見る</a>
      <span class="btn soon">Amazon準備中</span>
    </div>
  </div>
"""


def main() -> int:
    cfg = fetch_queue()
    cards = "".join(card(it) for it in cfg.get("items", []))
    s = LINKS.read_text(encoding="utf-8")
    if START not in s or END not in s:
        print("markers missing in links.html — abort", file=sys.stderr)
        return 1
    new = s[: s.index(START) + len(START)] + "\n" + cards + s[s.index(END):]
    if new == s:
        print("no change")
        return 0
    LINKS.write_text(new, encoding="utf-8")
    subprocess.run(["git", "-C", str(REPO), "add", "links.html"], check=True)
    subprocess.run(["git", "-C", str(REPO), "commit", "-q", "-m",
                    "links: auto-sync product cards from queue.yaml\n\n"
                    "Co-Authored-By: Claude Fable 5 <noreply@anthropic.com>"], check=True)
    subprocess.run(["git", "-C", str(REPO), "push", "-q"], check=True, timeout=120)
    print("pushed")
    return 0


if __name__ == "__main__":
    sys.exit(main())
