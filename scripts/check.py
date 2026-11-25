#!/usr/bin/env python3
"""夜市小吃 LLM Wiki 的檢查器（graph 中的「檢查」節點）。

用法：
    python3 scripts/check.py wiki     # 只檢查 wiki（ingest 之後跑）
    python3 scripts/check.py slides   # 只檢查簡報（產生簡報之後跑）
    python3 scripts/check.py          # 全部

規則：
  W1 wiki 的每一條事實（條列 / 表格列）都要有 [S#] 來源標籤
  W2 引用的 [S#] 必須在 raw/ 找得到
  D1 每張投影片都要宣告 data-wiki（依據哪些 wiki 頁）與 data-src（來源）
  D2 投影片上的每個數字，都要能在它宣告的 wiki 頁裡找到
  D3 投影片寫到「發明 / 由來 / 起源」，同一張要有「一說 / 爭議 / 傳說」
  D4 引用 S5（只讀到摘要）的投影片，必須顯示「待驗證」
  D5 爭議與待查.md 判定不採用的寫法，不可出現在簡報
"""
import html
import pathlib
import re
import sys

ROOT = pathlib.Path(__file__).resolve().parent.parent
WIKI = ROOT / "wiki"
RAW = ROOT / "raw"
SLIDES = ROOT / "slides" / "index.html"

NAV_PAGES = {"index.md", "log.md", "爭議與待查.md"}
REJECTED = ["1899", "30～40 萬", "30-40萬", "invented in Taichung", "台中發明"]
UNVERIFIED_SRC = "S5"

errors, warns = [], []


def raw_ids():
    return {p.name.split("-")[0] for p in RAW.glob("S*.md")}


def check_wiki():
    ids = raw_ids()
    for page in sorted(WIKI.glob("*.md")):
        if page.name in NAV_PAGES:
            continue
        for n, line in enumerate(page.read_text(encoding="utf-8").splitlines(), 1):
            s = line.strip()
            is_fact = re.match(r"^(- |\d+\. |\| )", s)
            if not is_fact or set(s) <= set("|- :") or s.startswith("| 時間") \
               or s.startswith("| 小吃") or s.startswith("| 主張") or s.startswith("相關"):
                continue
            tags = re.findall(r"S\d", s)
            if not tags:
                errors.append(f"W1 {page.name}:{n} 沒有來源標籤 → {s[:40]}")
            for t in tags:
                if t not in ids:
                    errors.append(f"W2 {page.name}:{n} 引用不存在的來源 {t}")


def slide_sections(src):
    pat = re.compile(r'<section class="slide[^"]*"([^>]*)>(.*?)</section>', re.S)
    for i, m in enumerate(pat.finditer(src), 1):
        attrs, body = m.group(1), m.group(2)
        wiki = re.search(r'data-wiki="([^"]*)"', attrs)
        srcs = re.search(r'data-src="([^"]*)"', attrs)
        text = html.unescape(re.sub(r"<[^>]+>", " ", body))
        text = re.sub(r"\s+", " ", text)
        yield i, (wiki.group(1) if wiki else None), (srcs.group(1) if srcs else None), text


def check_slides():
    src = SLIDES.read_text(encoding="utf-8")
    ids = raw_ids()
    count = 0
    for i, wiki, srcs, text in slide_sections(src):
        count += 1
        if wiki is None or srcs is None:
            errors.append(f"D1 第 {i} 張沒有 data-wiki / data-src")
            continue
        pages = [p.strip() for p in wiki.split(",") if p.strip()]
        corpus = ""
        for p in pages:
            f = WIKI / p
            if not f.exists():
                errors.append(f"D1 第 {i} 張宣告的 wiki 頁不存在：{p}")
            else:
                corpus += f.read_text(encoding="utf-8")
        for s in srcs.split():
            if s not in ids:
                errors.append(f"D1 第 {i} 張宣告不存在的來源 {s}")
        # D2 數字都要找得到出處（忽略 1–2 位數的序號）
        if pages:
            for num in sorted(set(re.findall(r"\d{3,4}", text))):
                if num not in corpus:
                    errors.append(f"D2 第 {i} 張的數字 {num} 在 {wiki} 找不到")
        # D3 起源類敘述要有保留語氣
        if re.search(r"發明|由來|起源", text) and not re.search(r"一說|爭議|傳說", text):
            errors.append(f"D3 第 {i} 張談起源，卻沒有「一說 / 爭議 / 傳說」")
        # D4 用到 wiki 中「⚠️待驗證」那幾行的內容，投影片就必須顯示「待驗證」
        #    （v1 只看 data-src 有沒有 S5，誤擋了引用 S5「原文」的第 3 張 → v2 改成逐行比對）
        #    v3：只算「只出現在待驗證行」的詞；蚵仔、番薯粉這類在已驗證行也有的詞不算
        verified = "\n".join(l for l in corpus.splitlines() if "⚠️" not in l)
        if "待驗證" not in text:
            for line in corpus.splitlines():
                if "⚠️待驗證" not in line:
                    continue
                body = line.split("⚠️待驗證", 1)[1]
                terms = [w for w in re.split(r"[\s、，。：；|（）()\[\]S\d⚠️*]+", body) if 2 <= len(w) <= 6]
                hit = [w for w in terms if w in text and w not in verified]
                if len(hit) >= 2:
                    errors.append(f"D4 第 {i} 張用到待驗證內容（{'、'.join(hit[:3])}），但沒有顯示「待驗證」")
                    break
        # D5 被排除的寫法
        for bad in REJECTED:
            if bad in text:
                errors.append(f"D5 第 {i} 張出現已判定不採用的寫法：{bad}")
    if count == 0:
        errors.append("D1 找不到任何投影片")
    return count


def main():
    mode = sys.argv[1] if len(sys.argv) > 1 else "all"
    n = 0
    if mode in ("all", "wiki"):
        check_wiki()
    if mode in ("all", "slides"):
        n = check_slides()
    for w in warns:
        print("WARN ", w)
    for e in errors:
        print("ERROR", e)
    print(f"--- 檢查完成：{len(errors)} 個錯誤、{len(warns)} 個警告" + (f"、投影片 {n} 張" if n else ""))
    sys.exit(1 if errors else 0)


if __name__ == "__main__":
    main()
