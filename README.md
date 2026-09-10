# 宅配食・ミールキット比較ナビ

- 公開URL: https://taka2813.github.io/takushoku-blog/
- 公開方法: GitHub Pages（`main` ブランチの `docs/` フォルダ）
- 収益化: A8.net アフィリエイト

## 構成

```
build.py            静的サイトジェネレーター（Python 標準ライブラリのみ・追加インストール不要）
config.json         サイト設定（サイト名・GA4測定ID・ページ一覧＝sitemap順）
templates/page.html 全ページ共通の雛形。可変部分だけ {{PLACEHOLDER}}
content/
  <slug>.json       各ページのメタ情報（タイトル・説明・canonical・構造化データ など）
  <slug>.body.html  各ページの本文（<main>…</main> の中身）。記事の加筆はこのファイルを編集する
static/             docs/ にそのままコピーするファイル（style.css, robots.txt）
docs/               ビルド出力（GitHub Pages が配信する実体。直接編集しない）
```

> 元の Cowork セッションで使われていた build.py は取り出せなかったため、
> 公開済み HTML から出力を完全再現できる形で 2026-09-10 に組み直したもの。
> `python build.py verify` で、生成結果が既存 docs/ と一致することを確認済み。

## 使い方

```
python build.py build     # content/ + templates/ + config.json -> docs/ を再生成
python build.py verify    # 生成結果が現 docs/ と一致するか確認
python build.py extract    # docs/*.html から content/ を作り直す（通常は不要）
```

ローカル確認:

```
python -m http.server 8765 --directory docs
# http://localhost:8765/ をブラウザで開く
```

## 記事を加筆する手順

1. `content/<slug>.body.html` を編集する（HTML。見出しは `<h2 id="...">`、表は
   `<div class="table-wrap"><table>…</table></div>`、CTA は `<div class="aff-box">…</div>`）。
2. 本文冒頭の `<nav class="toc">` の項目を、追加・変更した `<h2>` に合わせて直す。
3. `<p class="meta">… ／ 更新日: YYYY-MM-DD</p>` と、`content/<slug>.json` の
   構造化データ内 `dateModified` を、加筆した日付に更新する。
4. `python build.py build` を実行し、`python -m http.server` で表示を確認する。
5. 変更を commit し、`git push`（GitHub Pages が自動反映）。

### やってはいけないこと
- 実際に試していない体験を「実食した」等と偽って書かない。
  書けるのは「編集部が公式サイト・資料で確認した情報」の範囲まで。
- 記事本文に断定的な医療アドバイスを書かない（「医師・管理栄養士に相談を」と促す）。
- 人為的な被リンク購入・スパム投稿はしない。

## 未対応・要ユーザー対応
- GA4 測定ID未取得（取得後 `config.json` の `google_analytics_id` に設定）
- 運営者情報ページの問い合わせ先メール未設定（`content/about.body.html`）
- 審査中の A8.net プログラム: やわらかダイニング / ウェルネスダイニング×2 / TastyTable FOOD / ツクリオ
