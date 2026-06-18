# 新站搜索引擎一键提交

一个 Python + PySide6 桌面工具，用于批量通知搜索平台发现新站 URL 和 Sitemap。

默认会在提交前执行收录查重。Google 使用 URL Inspection API，Bing 使用 Webmaster `GetUrlInfo`；只有明确确认已收录的 URL 才会跳过。百度、IndexNow、360、神马等没有稳定公开的精确 URL 查询 API 时会显示“无法确认”并继续提交，避免漏提。

> 提交只代表通知搜索引擎抓取，不代表保证收录或排名。站点仍需可访问、内容合规、允许抓取，并在要求的平台完成所有权验证。

## 支持情况

| 平台 | 自动方式 | 前置条件 |
|---|---|---|
| Bing、Yandex 等 | IndexNow 批量 URL | 在站点根目录部署 IndexNow Key 文件 |
| 百度 | 普通收录 API | 百度搜索资源平台已验证站点和 token |
| Google | Search Console Sitemap API | 已验证站点、Google OAuth 桌面客户端 JSON |
| Bing | Webmaster URL API | 已验证站点和 API Key；通常与 IndexNow 二选一即可 |
| Yandex | Webmaster Sitemap API | 已验证站点和 OAuth Token |
| 360 搜索 | 人工入口提示 | 当前没有纳入稳定公开 API |
| 神马搜索 | 人工入口提示 | 当前没有纳入稳定公开 API |

Google 的旧 Sitemap Ping 接口已经退役；Google Indexing API 只适用于官方限定的结构化内容类型，因此本工具不把它用于普通网站。

## 安装与运行

```bash
cd /Users/jackey/Desktop/seo
python3 -m venv .venv
.venv/bin/python -m pip install --upgrade pip setuptools
.venv/bin/pip install -r requirements.txt
.venv/bin/python run.py
```

CLI 示例：

```bash
.venv/bin/search-index-submit example.com https://example.org/page --dry-run
.venv/bin/search-index-submit --file sites.txt --providers indexnow,baidu,google --json
```

配置保存在 `~/.search-index-submitter/config.json`，文件权限会设置为 `0600`。不要把该文件提交到 Git。

## 平台配置

### IndexNow

生成一个 Key，把内容为该 Key 的 `{key}.txt` 放在站点根目录，然后在工具中填写 Key。若 Key 文件不在默认位置，再填写完整 Key 文件 URL。

### 百度

在百度搜索资源平台验证站点，打开“普通收录 -> API 提交”，复制 token。单站可填写默认 token；多站在映射框填写 `example.com=token,example.org=token2`，工具会按域名选择对应 token。

### Google

在 Google Cloud 创建“桌面应用”OAuth 客户端，启用 Search Console API，下载客户端 JSON。首次正式提交时会打开浏览器授权。Search Console 中的站点属性必须和输入的协议、域名形式匹配。

### Bing / Yandex

两者均可通过 IndexNow 收到 URL 更新。单独启用对应站长平台 API，主要用于需要再次向平台账户提交 URL 或 Sitemap 的场景。

## 官方资料

- [Google Sitemap API](https://developers.google.com/webmaster-tools/v1/sitemaps/submit)
- [Google URL Inspection API](https://developers.google.com/webmaster-tools/v1/urlInspection.index/inspect)
- [Google 退役 Sitemap Ping](https://developers.google.com/search/blog/2023/06/sitemaps-lastmod-ping)
- [Google Indexing API 使用范围](https://developers.google.com/search/apis/indexing-api/v3/using-api)
- [IndexNow API](https://www.indexnow.org/documentation)
- [百度搜索资源平台](https://ziyuan.baidu.com/linksubmit/index)
- [Bing IndexNow](https://www.bing.com/indexnow)
- [Bing GetUrlInfo](https://learn.microsoft.com/en-us/dotnet/api/microsoft.bing.webmaster.api.interfaces.iwebmasterapi.geturlinfo)
- [Yandex Webmaster API](https://yandex.com/dev/webmaster/doc/en/)

## Codex Skill

仓库内包含 `codex-skill/submit-new-site-indexing`。安装到当前用户：

```bash
cp -R codex-skill/submit-new-site-indexing ~/.codex/skills/
```
