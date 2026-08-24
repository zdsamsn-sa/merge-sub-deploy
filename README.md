# Merge-sub

用于合并和管理代理订阅的 Node.js 应用程序。可将多个订阅源合并为一个，并支持通过 URL 参数动态替换节点 Cloudflare 优选域名或 IP。


## 功能特点

- **订阅合并**：支持合并多个 VMess、VLESS、Trojan、Hysteria2、Anytls、ss 等协议的订阅链接。
- **节点管理**：支持手动添加自定义节点，支持 API 自动添加单节点或订阅。
- **动态替换**：通过 URL 参数 `?CFIP=...&CFPORT=...` 动态替换节点地址和端口，不修改原始配置。
- **Web 管理界面**：提供简单的 Web 界面用于管理订阅和节点。
- **Modal / Docker / GitHub Actions**：可一键部署到 Modal，或用 Docker 运行。

## 环境变量（应用本身）

| 变量名 | 描述 | 默认值 | 是否必填 |
| :--- | :--- | :--- | :--- |
| `USERNAME` | Web 管理界面用户名 | `admin` | 建议改 |
| `PASSWORD` | Web 管理界面密码 | `admin` | 建议改 |
| `SUB_TOKEN` | 订阅路径 Token（访问 `/TOKEN`） | 根据主机名自动生成 | **强烈建议固定** |
| `API_URL` | 外部订阅转换 API 地址 | `https://sublink.eooce.com` | 可选 |
| `SERVER_PORT` 或 `PORT` | 服务端口 | `3000` | 一般不用改 |
| `DATA_DIR` | 数据存储目录 | `./data`（Modal 上为 `/app/data`） | 一般不用改 |

> 在 Modal 上，上述变量通过 **Modal Secret** `merge-sub-secrets` 注入（见下文）。

---

## 方式一：GitHub Actions → Modal（推荐）

### 1. 准备 Modal 账号与 Token

1. 注册并登录 [https://modal.com](https://modal.com)
2. 打开 **Settings → API Tokens → New Token**，记下：
   - `Token ID`（形如 `ak-...`）
   - `Token Secret`（形如 `as-...`）

### 2. 在 Modal 创建应用 Secret（账号密码 / Token）

在本地（或任意已登录 Modal 的机器）执行：

```bash
pip install modal
modal setup   # 若尚未登录

modal secret create merge-sub-secrets \
  USERNAME=admin \
  PASSWORD=你的强密码 \
  SUB_TOKEN=一串随机长字符串 \
  API_URL=https://sublink.eooce.com
```

也可在 Modal 控制台 **Secrets** 页面用 UI 创建同名 Secret，键名必须一致。

### 3. 把代码推到 GitHub

将本目录（含 `app.js`、`modal_app.py`、`package.json`、`public/`、`.github/`）作为仓库根目录推送：

```bash
git init
git add .
git commit -m "Merge-sub Modal ready"
git branch -M main
git remote add origin https://github.com/你的用户名/你的仓库.git
git push -u origin main
```

### 4. 配置 GitHub Repository Secrets

仓库 → **Settings → Secrets and variables → Actions → New repository secret**，添加：

| Secret 名称 | 值 |
| :--- | :--- |
| `MODAL_TOKEN_ID` | Modal 的 Token ID |
| `MODAL_TOKEN_SECRET` | Modal 的 Token Secret |

**不要**把 `USERNAME` / `PASSWORD` / `SUB_TOKEN` 写进 GitHub Secrets（除非你改 workflow 去创建 Modal Secret）。应用运行时的凭证应放在 **Modal Secret** `merge-sub-secrets` 里。

### 5. 触发部署

- 推送到 `main` 且改动了相关文件时，会自动运行 `.github/workflows/deploy-modal.yml`
- 或到 **Actions** 页选择 **Deploy to Modal** → **Run workflow** 手动触发

部署成功后，在 Actions 日志或 Modal 控制台可见类似 URL：

```text
https://你的工作区--merge-sub-web.modal.run
```

访问该地址，用 Secret 中设置的用户名/密码登录。订阅地址为：

```text
https://你的工作区--merge-sub-web.modal.run/你的SUB_TOKEN
```

可选 CF 优选：

```text
https://.../你的SUB_TOKEN?CFIP=1.1.1.1&CFPORT=443
```

数据保存在 Modal Volume `merge-sub-data`，重新部署不会丢。

### 6. 常用 Modal 命令

```bash
modal app list
modal app logs merge-sub
modal app stop merge-sub
modal volume list
```

---

## 方式二：本地直接 Modal 部署（不经过 GitHub）

```bash
cd merge-sub-deploy   # 本项目根目录
pip install modal
modal setup

# 先创建 Secret（同上）
modal secret create merge-sub-secrets USERNAME=admin PASSWORD=xxx SUB_TOKEN=yyy

# 临时测试
modal serve modal_app.py

# 正式部署
modal deploy modal_app.py
```

---

## 方式三：Docker

```bash
docker run -d \
  --name merge-sub \
  -p 3000:3000 \
  -e USERNAME=admin \
  -e PASSWORD=你的密码 \
  -e SUB_TOKEN=你的token \
  -v $(pwd)/data:/app/data \
  --restart unless-stopped \
  $(docker build -q .)
```

或使用已有镜像 `eooce/merge-sub:latest`（若上游已发布）。

---

## 原版 ZIP 中需要注意的问题（本目录已修复）

| 问题 | 说明 |
| :--- | :--- |
| `body-parser` 未声明 | `app.js` 中 `require('body-parser')`，原 `package.json` 缺少依赖 → 已加入 |
| 启动逻辑错误 | 定义了 `startServer()` 却执行了未定义的 `server.listen(...)` → 已改为正确调用 `startServer()`，并绑定 `0.0.0.0` |
| 保活代码依赖未定义变量 | `PROJECT_URL` 未定义会导致保活异常；Modal 不需要平台保活逻辑 → 已移除 |
| `express: "latest"` | 不利于可复现构建 → 已固定版本 |
| `workers/` | 仅 Cloudflare Worker 脚本，主 Node 服务不依赖，Modal 镜像已 ignore |

---

## API 简要

管理界面路径需要 Basic Auth；`/api/*` 与订阅路径 `/{SUB_TOKEN}` 不要求管理密码。

- `POST /api/add-subscriptions` — body: `{ "subscription": "url1\nurl2" }`
- `POST /api/add-nodes` — body: `{ "nodes": "vmess://...\nvless://..." }`
- `DELETE /api/delete-subscriptions` / `DELETE /api/delete-nodes`
- `GET /{SUB_TOKEN}` — 合并后的订阅内容

---

## 开源协议

MIT
