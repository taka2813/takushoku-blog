#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
宅配食・ミールキット比較ナビ  静的サイトジェネレーター（標準ライブラリのみ）

Cowork セッションで使われていた元の build.py は取り出せなかったため、
2026-09-10 に、公開済み HTML（takushoku-blog-site-update11.zip / docs/）から
「同じ出力を再現できる」形で組み直したもの。

使い方:
    python build.py extract   # docs/*.html から content/ と templates/ を復元（初回のみ）
    python build.py build     # content/ + templates/ + config.json -> docs/
    python build.py verify    # build した結果が既存 docs/ と一致するか確認（差分表示）

設計:
    templates/page.html … 1ページ分の完全な雛形。可変部分だけを {{PLACEHOLDER}} にしてある。
        {{TITLE_FULL}}  <title> と og:title（記事は「… | サイト名」、トップはサイト名のみ）
        {{DESC}}        meta description と og:description
        {{CANONICAL}}   canonical と og:url
        {{OG_TYPE}}     website / article
        {{JSONLD}}      構造化データ（<script type="application/ld+json"> …）ページ固有・そのまま保持
        {{GA}}          Google Analytics タグ（config の google_analytics_id が空なら出力なし）
        {{BODY}}        <main> と </main> の間の中身（そのまま保持。編集はこのファイルで行う）
    content/<slug>.json       … ページのメタ情報（上記プレースホルダーの値）
    content/<slug>.body.html  … <main>…</main> の中身そのもの
    static/                   … そのまま docs/ にコピーするファイル（style.css, robots.txt）
    sitemap.xml は config の pages 順で build 時に生成する。
"""
import json
import os
import re
import sys
import hashlib
import shutil

ROOT = os.path.dirname(os.path.abspath(__file__))
DOCS = os.path.join(ROOT, "docs")
CONTENT = os.path.join(ROOT, "content")
TEMPLATES = os.path.join(ROOT, "templates")
STATIC = os.path.join(ROOT, "static")
CONFIG_PATH = os.path.join(ROOT, "config.json")
TEMPLATE_PATH = os.path.join(TEMPLATES, "page.html")

# extract の基準にするページ（可変部分が全種類そろっている記事ページ）
BASE_PAGE = "diet-takuhaibento.html"


def read(path):
    with open(path, encoding="utf-8") as f:
        return f.read()


def write(path, text):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8", newline="\n") as f:
        f.write(text)


def load_config():
    return json.loads(read(CONFIG_PATH))


# ---------------------------------------------------------------- extract ----
def extract():
    cfg = load_config()
    site = cfg["site_name"]
    gsv_line = (
        '<meta name="google-site-verification" content="%s">\n'
        % cfg["google_site_verification"]
    )

    def parse_page(fname):
        t = read(os.path.join(DOCS, fname))
        title = re.search(r"<title>(.*?)</title>", t, re.S).group(1)
        desc = re.search(r'<meta name="description" content="(.*?)">', t, re.S).group(1)
        canonical = re.search(r'<link rel="canonical" href="(.*?)">', t).group(1)
        og_type = re.search(r'<meta property="og:type" content="(.*?)">', t).group(1)
        a = t.index(gsv_line) + len(gsv_line)
        b = t.index("\n</head>", a)
        jsonld = t[a:b]
        mo = t.index("<main>") + len("<main>")
        mc = t.index("</main>")
        body = t[mo:mc]
        return title, desc, canonical, og_type, jsonld, body

    # --- テンプレートを基準ページから作る ---
    base_raw = read(os.path.join(DOCS, BASE_PAGE))
    title, desc, canonical, og_type, jsonld, body = parse_page(BASE_PAGE)
    tpl = base_raw
    tpl = tpl.replace("<main>" + body + "</main>", "<main>{{BODY}}</main>", 1)
    tpl = tpl.replace(jsonld, "{{JSONLD}}", 1)
    tpl = tpl.replace("<title>%s</title>" % title, "<title>{{TITLE_FULL}}</title>", 1)
    tpl = tpl.replace(
        '<meta property="og:title" content="%s">' % title,
        '<meta property="og:title" content="{{TITLE_FULL}}">',
        1,
    )
    tpl = tpl.replace(
        '<meta name="description" content="%s">' % desc,
        '<meta name="description" content="{{DESC}}">',
        1,
    )
    tpl = tpl.replace(
        '<meta property="og:description" content="%s">' % desc,
        '<meta property="og:description" content="{{DESC}}">',
        1,
    )
    tpl = tpl.replace(
        '<link rel="canonical" href="%s">' % canonical,
        '<link rel="canonical" href="{{CANONICAL}}">',
        1,
    )
    tpl = tpl.replace(
        '<meta property="og:url" content="%s">' % canonical,
        '<meta property="og:url" content="{{CANONICAL}}">',
        1,
    )
    tpl = tpl.replace(
        '<meta property="og:type" content="%s">' % og_type,
        '<meta property="og:type" content="{{OG_TYPE}}">',
        1,
    )
    # GA 差し込み位置（</head> の直前）。基準ページには GA が無いので目印を置くだけ。
    tpl = tpl.replace("\n</head>", "{{GA}}\n</head>", 1)
    write(TEMPLATE_PATH, tpl)

    # --- 各ページを content/ に書き出す ---
    pages = cfg["pages"]
    for p in pages:
        fname = p["slug"] + ".html"
        title, desc, canonical, og_type, jsonld, body = parse_page(fname)
        suffix = " | " + site
        meta = {
            "slug": p["slug"],
            "title": title[: -len(suffix)] if title.endswith(suffix) else title,
            "title_has_site_suffix": title.endswith(suffix),
            "description": desc,
            "canonical": canonical,
            "og_type": og_type,
            "jsonld": jsonld,
            "listed_on_index": p.get("listed_on_index", False),
            "in_sitemap": p.get("in_sitemap", True),
            "date": p.get("date", ""),
        }
        write(os.path.join(CONTENT, p["slug"] + ".json"),
              json.dumps(meta, ensure_ascii=False, indent=2) + "\n")
        write(os.path.join(CONTENT, p["slug"] + ".body.html"), body)

    # --- static/ に素通しファイルを退避 ---
    for name in ("style.css", "robots.txt"):
        src = os.path.join(DOCS, name)
        if os.path.exists(src):
            write(os.path.join(STATIC, name), read(src))
    print("extract 完了: templates/page.html, content/*, static/* を作成しました")


# ------------------------------------------------------------------ build ----
def render_page(meta, cfg):
    tpl = read(TEMPLATE_PATH)
    site = cfg["site_name"]
    title_full = meta["title"] + (" | " + site if meta["title_has_site_suffix"] else "")
    body = read(os.path.join(CONTENT, meta["slug"] + ".body.html"))
    ga = ""
    gid = cfg.get("google_analytics_id", "").strip()
    if gid:
        ga = (
            '\n<script async src="https://www.googletagmanager.com/gtag/js?id=%s"></script>\n'
            "<script>window.dataLayer=window.dataLayer||[];function gtag(){dataLayer.push(arguments);}"
            "gtag('js',new Date());gtag('config','%s');</script>" % (gid, gid)
        )
    out = tpl
    out = out.replace("{{TITLE_FULL}}", title_full)
    out = out.replace("{{DESC}}", meta["description"])
    out = out.replace("{{CANONICAL}}", meta["canonical"])
    out = out.replace("{{OG_TYPE}}", meta["og_type"])
    out = out.replace("{{JSONLD}}", meta["jsonld"])
    out = out.replace("{{GA}}", ga)
    out = out.replace("{{BODY}}", body)
    return out


def render_sitemap(cfg):
    lines = ['<?xml version="1.0" encoding="UTF-8"?>',
             '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">']
    site_updated = cfg.get("updated", "")
    for p in cfg["pages"]:
        if not p.get("in_sitemap", True):
            continue
        meta = json.loads(read(os.path.join(CONTENT, p["slug"] + ".json")))
        m = re.search(r'"dateModified":\s*"([0-9-]+)"', meta.get("jsonld", ""))
        lastmod = m.group(1) if m else site_updated
        if lastmod:
            lines.append("  <url><loc>%s</loc><lastmod>%s</lastmod></url>"
                         % (meta["canonical"], lastmod))
        else:
            lines.append("  <url><loc>%s</loc></url>" % meta["canonical"])
    lines.append("</urlset>")
    return "\n".join(lines) + "\n"


def build():
    cfg = load_config()
    os.makedirs(DOCS, exist_ok=True)
    for p in cfg["pages"]:
        meta = json.loads(read(os.path.join(CONTENT, p["slug"] + ".json")))
        write(os.path.join(DOCS, p["slug"] + ".html"), render_page(meta, cfg))
    for name in os.listdir(STATIC):
        shutil.copyfile(os.path.join(STATIC, name), os.path.join(DOCS, name))
    write(os.path.join(DOCS, "sitemap.xml"), render_sitemap(cfg))
    print("build 完了: docs/ を再生成しました（%d ページ）" % len(cfg["pages"]))


# ----------------------------------------------------------------- verify ----
def verify():
    cfg = load_config()
    ok = True
    for p in cfg["pages"]:
        fname = p["slug"] + ".html"
        cur = os.path.join(DOCS, fname)
        if not os.path.exists(cur):
            print("  欠落: docs/%s" % fname)
            ok = False
            continue
        meta = json.loads(read(os.path.join(CONTENT, p["slug"] + ".json")))
        gen = render_page(meta, cfg)
        old = read(cur)
        if gen != old:
            ok = False
            print("  差分: %s (gen %dB / docs %dB)" % (fname, len(gen), len(old)))
            g = gen.splitlines()
            o = old.splitlines()
            for i in range(min(len(g), len(o))):
                if g[i] != o[i]:
                    print("    L%d docs: %s" % (i + 1, o[i][:160]))
                    print("    L%d gen : %s" % (i + 1, g[i][:160]))
                    break
        else:
            print("  一致: %s" % fname)
    sm = render_sitemap(cfg)
    if os.path.exists(os.path.join(DOCS, "sitemap.xml")):
        if sm != read(os.path.join(DOCS, "sitemap.xml")):
            ok = False
            print("  差分: sitemap.xml")
        else:
            print("  一致: sitemap.xml")
    print("=> " + ("全ページ一致" if ok else "不一致あり"))
    return ok


if __name__ == "__main__":
    cmd = sys.argv[1] if len(sys.argv) > 1 else "build"
    if cmd == "extract":
        extract()
    elif cmd == "build":
        build()
    elif cmd == "verify":
        verify()
    else:
        print(__doc__)
        sys.exit(1)
