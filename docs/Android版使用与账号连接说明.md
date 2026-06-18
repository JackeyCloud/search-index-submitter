# Android 版使用与账号连接说明

## 当前 Android 版功能

- 大尺寸多行输入框；
- 直接粘贴多个网址；
- 从小红书等平台的整段分享文案中自动提取 URL；
- 自动去除中文标点和多余文案；
- 自动去重；
- 支持在其他 App 中选择“分享”到本工具；
- IndexNow 批量提交；
- 百度普通收录 API；
- Bing Webmaster API 和提交前查重；
- Yandex Webmaster Sitemap API；
- 凭据保存到 Android 应用私有数据中。

## 分享文案提取示例

粘贴：

```text
复制后打开小红书，查看这篇笔记 https://xhslink.com/a1B2C3，更多精彩内容
```

输入框会自动变成：

```text
https://xhslink.com/a1B2C3
```

需要注意：能提取链接不代表用户有权向站长平台提交该链接。百度、Bing、Google、Yandex 和 IndexNow 通常要求用户拥有或验证目标站点。提交不属于自己的小红书、微信公众号或第三方页面，官方 API 可能拒绝。

## 为什么不能让用户直接输入百度或 Google 密码

正规第三方软件不应收集搜索平台账号密码，也不应读取浏览器 Cookie。

正确方式是：

1. 软件打开平台官方登录页；
2. 用户直接在平台页面登录；
3. 平台显示授权范围；
4. 用户同意后，平台向软件返回 OAuth token；
5. 软件只保存可撤销的 token，不接触密码。

## 各平台能否简化

| 平台 | 可以做到的简化 | 发行方前置条件 |
|---|---|---|
| Google | 点击“连接 Google”后通过官方 OAuth 授权 Search Console | 注册 Google OAuth 应用、绑定 Android 包名和签名、配置同意屏幕，公开发行可能需要审核 |
| Yandex | 通过 Yandex OAuth 登录并授权 Webmaster API | 注册 Yandex OAuth 应用 |
| Bing | 官方 OAuth，或让用户复制账号级 API Key | 注册 Bing Webmaster OAuth 应用；API Key 模式无需发行方服务器 |
| 百度 | 打开百度搜索资源平台并引导复制站点 token | 百度普通收录 token 仍与站点相关，没有可替代它的通用第三方登录授权 |
| IndexNow | App 自动生成 Key，并引导部署 Key 文件 | 每个站点仍需把 Key 文件放到网站根目录 |

## 当前 APK 的账号策略

当前开源 APK 不内置任何开发者 OAuth Client ID，避免把测试项目和账号权限硬编码进公共安装包。

现阶段：

- 百度、Bing、IndexNow、Yandex 使用用户自有 token 或 Key；
- 配置页提供完整官方操作指南；
- 不收集任何平台密码；
- Google 使用桌面版 OAuth 客户端流程；Android 一键连接需要发行方先完成 Google OAuth 产品注册。

商业发行版建议增加：

- “连接 Google”按钮；
- “连接 Yandex”按钮；
- “连接 Bing”按钮；
- OAuth token 自动刷新；
- Android Keystore 加密凭据；
- 账号断开与撤销授权；
- 首次启动配置向导；
- Google OAuth 应用审核和隐私政策页面。

## 安装 APK

1. 下载 `SearchIndexSubmitter-Android.apk`。
2. 把 APK 发送到 Android 手机。
3. 在系统设置中临时允许文件管理器安装未知来源应用。
4. 点击 APK 安装。
5. 安装完成后关闭不必要的“允许未知来源”权限。

GitHub Actions 生成的是调试签名 APK，可直接安装测试。正式商业发布应使用私有 release keystore 签名，并通过应用商店或可信下载页分发。
