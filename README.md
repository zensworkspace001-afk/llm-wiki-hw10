# 第十週作業：夜市小吃 LLM Wiki ＋ 教學 HTML 簡報

```
llm-wiki-hw10/
├── CLAUDE.md              ← Schema：Wiki 的規則（第三層）
├── raw/                   ← 第一層：6 篇來源的閱讀筆記（S1–S6，附網址）
├── wiki/                  ← 第二層：LLM 維護的知識頁
│   ├── index.md           ← 目錄（查詢從這裡開始）
│   ├── log.md             ← 時間紀錄（討論、ingest、lint、產生簡報）
│   ├── 爭議與待查.md       ← 來源矛盾與待驗證清單
│   └── 夜市與小吃.md、夜市歷史.md、士林夜市.md、蚵仔煎.md、臭豆腐.md、珍珠奶茶.md、其他常見小吃.md
├── slides/index.html      ← 教學 HTML 簡報（13 張，可用 ←/→ 或滑動翻頁）
├── scripts/check.py       ← 檢查器（Wiki Lint ＋ 簡報檢查）
├── workflow/
│   ├── graph.md           ← loop / graph 設計與流程圖
│   ├── run-log.md         ← 一次實際執行的檢查紀錄
│   └── reflection.md      ← 反思
└── SUBMISSION.md          ← 可直接貼到作業繳交欄的文字
```

使用：直接用瀏覽器打開 `slides/index.html`；檢查：`python3 scripts/check.py`
