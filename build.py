#!/usr/bin/env python3
"""PharmaPedia Japan - 統合サイトビルダー

全ブログのRSSフィードから記事を集約し、静的サイトを生成する。
"""
import json
import shutil
import xml.etree.ElementTree as ET
from datetime import datetime
from pathlib import Path
from urllib.parse import quote

import feedparser
import requests
from jinja2 import Environment, FileSystemLoader

import config
from eyecatch import get_eyecatch_url

BASE_DIR = Path(__file__).parent
TEMPLATE_DIR = BASE_DIR / "templates"
OUTPUT_DIR = BASE_DIR / "site"
CACHE_DIR = BASE_DIR / "cache"
STATIC_ARTICLES_DIR = BASE_DIR / "static_articles"
STATIC_ARTICLES_JSON = BASE_DIR / "static_articles.json"


def fetch_articles():
    """全ブログのRSSフィードから記事を取得"""
    all_articles = []

    for blog in config.BLOGS:
        feed_url = blog["feed_url"]
        print(f"[取得中] {blog['name']}: {feed_url}")

        try:
            feed = feedparser.parse(feed_url)
            if feed.bozo and not feed.entries:
                print(f"  [警告] RSSパース失敗、直接取得を試行")
                resp = requests.get(feed_url, timeout=15)
                resp.raise_for_status()
                feed = feedparser.parse(resp.text)

            for entry in feed.entries:
                pub_date = None
                if hasattr(entry, "published_parsed") and entry.published_parsed:
                    pub_date = datetime(*entry.published_parsed[:6])
                elif hasattr(entry, "updated_parsed") and entry.updated_parsed:
                    pub_date = datetime(*entry.updated_parsed[:6])

                article = {
                    "title": entry.get("title", "無題"),
                    "link": entry.get("link", blog["url"]),
                    "description": entry.get("summary", entry.get("description", "")),
                    "date": pub_date or datetime.now(),
                    "date_str": pub_date.strftime("%Y-%m-%d") if pub_date else "N/A",
                    "blog_name": blog["name"],
                    "blog_short": blog["short_name"],
                    "category": blog["category"],
                    "color": blog["color"],
                    "icon": blog["icon"],
                }
                # HTML tags除去
                if article["description"]:
                    import re
                    article["description"] = re.sub(r"<[^>]+>", "", article["description"])[:200]

                article["eyecatch_url"] = get_eyecatch_url(
                    blog_name=blog["name"],
                    category=article.get("category", ""),
                    keyword=article.get("title", ""),
                    slug=article.get("link", ""),
                )

                all_articles.append(article)

            print(f"  -> {len(feed.entries)}件取得")

        except Exception as e:
            print(f"  [エラー] {blog['name']}: {e}")

    all_articles.sort(key=lambda a: a["date"], reverse=True)
    print(f"\n合計: {len(all_articles)}件の記事を取得")
    return all_articles


def save_cache(articles):
    """記事キャッシュを保存（差分蓄積用）"""
    CACHE_DIR.mkdir(parents=True, exist_ok=True)
    cache_file = CACHE_DIR / "articles.json"

    # 既存キャッシュを読み込み
    existing = {}
    if cache_file.exists():
        try:
            with open(cache_file, "r", encoding="utf-8") as f:
                cached = json.load(f)
            existing = {a["link"]: a for a in cached}
        except (json.JSONDecodeError, IOError):
            pass

    # 新しい記事をマージ
    for article in articles:
        a_copy = dict(article)
        a_copy["date"] = a_copy["date"].isoformat()
        existing[article["link"]] = a_copy

    # static_articles.json があれば、ハブ独自記事もマージ（日次ビルドで消えない）
    if STATIC_ARTICLES_JSON.exists():
        try:
            with open(STATIC_ARTICLES_JSON, "r", encoding="utf-8") as f:
                static_list = json.load(f)
            for sa in static_list:
                # date が無ければ now、ある場合は文字列のまま保持
                if "date" not in sa or not sa["date"]:
                    sa["date"] = datetime.now().isoformat()
                existing[sa["link"]] = sa
            print(f"  static_articles.json から {len(static_list)} 件マージ")
        except (json.JSONDecodeError, IOError) as e:
            print(f"  [警告] static_articles.json 読み込み失敗: {e}")

    merged = sorted(existing.values(), key=lambda a: a["date"], reverse=True)

    with open(cache_file, "w", encoding="utf-8") as f:
        json.dump(merged, f, ensure_ascii=False, indent=2)

    print(f"キャッシュ保存: {len(merged)}件（新規{len(articles)}件 + 既存{len(merged) - len(articles)}件）")
    return merged


def load_all_articles(fresh_articles):
    """RSSから取得した記事 + キャッシュをマージして返す"""
    merged = save_cache(fresh_articles)

    # JSON形式をarticle形式に戻す
    articles = []
    for a in merged:
        a_copy = dict(a)
        if isinstance(a_copy["date"], str):
            try:
                a_copy["date"] = datetime.fromisoformat(a_copy["date"])
            except ValueError:
                a_copy["date"] = datetime.now()
        a_copy["date_str"] = a_copy["date"].strftime("%Y-%m-%d")
        articles.append(a_copy)

    articles.sort(key=lambda a: a["date"], reverse=True)
    return articles


def build_site(all_articles):
    """静的サイトを生成"""
    print("\n[ビルド開始]")

    if OUTPUT_DIR.exists():
        shutil.rmtree(OUTPUT_DIR)
    OUTPUT_DIR.mkdir(parents=True)
    (OUTPUT_DIR / "category").mkdir()

    env = Environment(
        loader=FileSystemLoader(str(TEMPLATE_DIR)),
        autoescape=True,
    )

    site_ctx = {
        "name": config.SITE_NAME,
        "tagline": config.SITE_TAGLINE,
        "description": config.SITE_DESCRIPTION,
        "url": config.SITE_URL,
        "ga_id": config.GOOGLE_ANALYTICS_ID,
    }

    category_counts = {}
    for blog in config.BLOGS:
        count = len([a for a in all_articles if a["category"] == blog["category"]])
        category_counts[blog["category"]] = count

    common = {
        "site": site_ctx,
        "blogs": config.BLOGS,
        "year": datetime.now().year,
    }

    # 1. トップページ
    tmpl = env.get_template("index.html")
    html = tmpl.render(
        **common,
        page="index",
        latest_articles=all_articles[:9],
        total_articles=len(all_articles),
        category_counts=category_counts,
    )
    (OUTPUT_DIR / "index.html").write_text(html, encoding="utf-8")
    print("  index.html 生成")

    # 2. 記事一覧
    tmpl = env.get_template("articles.html")
    html = tmpl.render(**common, page="articles", all_articles=all_articles)
    (OUTPUT_DIR / "articles.html").write_text(html, encoding="utf-8")
    print("  articles.html 生成")

    # 3. カテゴリページ
    tmpl = env.get_template("category.html")
    for blog in config.BLOGS:
        cat_articles = [a for a in all_articles if a["category"] == blog["category"]]
        html = tmpl.render(**common, page=blog["short_name"].lower(), blog=blog, articles=cat_articles)
        (OUTPUT_DIR / "category" / f"{blog['short_name'].lower()}.html").write_text(html, encoding="utf-8")
        print(f"  category/{blog['short_name'].lower()}.html 生成 ({len(cat_articles)}件)")

    # 4. YouTube
    tmpl = env.get_template("youtube.html")
    html = tmpl.render(**common, page="youtube")
    (OUTPUT_DIR / "youtube.html").write_text(html, encoding="utf-8")
    print("  youtube.html 生成")

    # 5. sitemap.xml
    generate_sitemap(all_articles)

    # 6. robots.txt
    robots = f"User-agent: *\nAllow: /\nSitemap: {config.SITE_URL}/sitemap.xml\n"
    (OUTPUT_DIR / "robots.txt").write_text(robots, encoding="utf-8")
    print("  robots.txt 生成")

    # 7. RSS
    generate_rss(all_articles)

    # 8. static_articles ディレクトリを site/articles へコピー（ハブ独自記事を維持）
    if STATIC_ARTICLES_DIR.exists():
        target = OUTPUT_DIR / "articles"
        target.mkdir(parents=True, exist_ok=True)
        copied = 0
        for src in STATIC_ARTICLES_DIR.glob("*.html"):
            shutil.copy2(src, target / src.name)
            copied += 1
        if copied:
            print(f"  static_articles/ から {copied} 件コピー -> site/articles/")

    print(f"\n[ビルド完了] {OUTPUT_DIR}")


def generate_sitemap(articles):
    """sitemap.xml を生成"""
    url = config.SITE_URL
    now = datetime.now().strftime("%Y-%m-%d")
    lines = [
        '<?xml version="1.0" encoding="UTF-8"?>',
        '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">',
        f'  <url><loc>{url}/</loc><lastmod>{now}</lastmod><changefreq>daily</changefreq><priority>1.0</priority></url>',
        f'  <url><loc>{url}/articles.html</loc><lastmod>{now}</lastmod><changefreq>daily</changefreq><priority>0.9</priority></url>',
        f'  <url><loc>{url}/youtube.html</loc><lastmod>{now}</lastmod><changefreq>weekly</changefreq><priority>0.7</priority></url>',
    ]
    for blog in config.BLOGS:
        lines.append(
            f'  <url><loc>{url}/category/{blog["short_name"].lower()}.html</loc>'
            f'<lastmod>{now}</lastmod><changefreq>daily</changefreq><priority>0.8</priority></url>'
        )
    lines.append("</urlset>")
    (OUTPUT_DIR / "sitemap.xml").write_text("\n".join(lines), encoding="utf-8")
    print("  sitemap.xml 生成")


def generate_rss(articles):
    """統合RSS フィードを生成"""
    url = config.SITE_URL
    now = datetime.now().strftime("%a, %d %b %Y %H:%M:%S +0900")
    lines = [
        '<?xml version="1.0" encoding="UTF-8"?>',
        '<rss version="2.0" xmlns:atom="http://www.w3.org/2005/Atom">',
        "  <channel>",
        f"    <title>{esc(config.SITE_NAME)}</title>",
        f"    <link>{url}</link>",
        f"    <description>{esc(config.SITE_DESCRIPTION)}</description>",
        f"    <language>ja</language>",
        f"    <lastBuildDate>{now}</lastBuildDate>",
        f'    <atom:link href="{url}/feed.xml" rel="self" type="application/rss+xml"/>',
    ]
    for a in articles[:30]:
        lines.append("    <item>")
        lines.append(f"      <title>{esc(a['title'])}</title>")
        lines.append(f"      <link>{esc(a['link'])}</link>")
        lines.append(f"      <guid>{esc(a['link'])}</guid>")
        if a.get("description"):
            lines.append(f"      <description>{esc(a['description'][:300])}</description>")
        lines.append(f"      <category>{esc(a['category'])}</category>")
        lines.append("    </item>")
    lines.extend(["  </channel>", "</rss>"])
    (OUTPUT_DIR / "feed.xml").write_text("\n".join(lines), encoding="utf-8")
    print("  feed.xml 生成")


def esc(text):
    return text.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;").replace('"', "&quot;")


def main():
    print(f"=== {config.SITE_NAME} サイトビルド ===")
    print(f"日時: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")

    fresh_articles = fetch_articles()
    all_articles = load_all_articles(fresh_articles)
    build_site(all_articles)


if __name__ == "__main__":
    main()
