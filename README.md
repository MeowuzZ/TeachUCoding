# TeachUCoding · 领航者课程平台

可独立部署的文字课程与本地项目学习平台。提供「笃行 · AI 产品研修」「致用 · 全栈工程研修」两条路径，包含 48 节产品课程、1,063 节工程课程、1,111 份项目作业包及参考实现。

宣传页支持连续滚动、分区入场动画、阅读进度与深浅色切换。代码练习在学习者自己的电脑上完成，平台不运行学员代码。

## 快速部署

只需要 **Python 3.10 或更新版本**，无需 Node.js、npm、数据库安装或第三方 Python 包。Python 可从 [python.org](https://www.python.org/downloads/) 安装。首次启动会自动重组、校验并展开仓库中的课程资源包，然后创建本地 SQLite 数据库。

### Windows

在 PowerShell 或命令提示符执行：

```powershell
git clone https://github.com/MeowuzZ/TeachUCoding.git
cd TeachUCoding
py -3 server.py
```

也可下载仓库 ZIP，解压后双击 `start-windows.bat`。安装 Python 时如未安装 `py` 启动器，可改用 `python server.py`。

### macOS / Linux

```bash
git clone https://github.com/MeowuzZ/TeachUCoding.git
cd TeachUCoding
python3 server.py
```

也可执行 `bash start.sh`。所有系统启动后访问 **http://127.0.0.1:8876**；按 `Ctrl+C` 停止。Windows、macOS 和 Linux 使用相同的代码与课程资源。

端口被占用时：

```bash
python3 server.py --port 8888
```

Windows 对应为 `py -3 server.py --port 8888`。需要局域网访问时加 `--host 0.0.0.0`，通过服务器的实际 IP 访问，并按需要设置系统防火墙。默认仅允许本机访问。

### Docker（跨系统）

已安装 Docker Engine 或 Docker Desktop 时：

```bash
docker compose up -d --build
```

访问 **http://127.0.0.1:8876**。查看日志和停止：

```bash
docker compose logs -f
docker compose down
```

学习账号与记录保存在 `teachucoding-data` 数据卷。更新镜像或执行 `down` 不会删除记录；`down -v` 会删除数据卷，请勿在保留学习数据时使用。

## 账号、同步与部署边界

- 不登录也可阅读、下载作业，进度和笔记保存在当前浏览器。
- 自带服务器提供邮箱/密码注册、登录和退出，账号记录保存在同一个 SQLite 数据库，可供连接同一部署的不同设备同步。
- 邮箱仅作登录名，不发送验证邮件。本版本没有找回密码、邮件验证、管理员后台与作业上传服务。
- 静态托管也可使用课程与浏览器本地记录，但不能提供账号注册与跨设备同步；请不要将静态托管描述为完整账号部署。
- 前端字母拼图用于分步展示参考实现，不是服务器端鉴权。源码公开后，参考代码可直接读取。

## 公网运行

内置 HTTP 服务器适合本地、小规模教学和容器部署。公网应置于提供 HTTPS 的反向代理后，设置：

```text
TEACHU_PUBLIC_ORIGIN=https://your-course.example
TEACHU_SECURE_COOKIE=1
TEACHU_DATA_DIR=/var/lib/teachucoding
```

代理将请求转发至 `127.0.0.1:8876`，保留原始 Host。`TEACHU_PUBLIC_ORIGIN` 必须与浏览器地址完全一致（不带结尾斜杠），用于校验写入来源；HTTPS 部署开启安全 Cookie。多实例共享同一 SQLite 文件的部署不在本版本支持范围内。

可用参数与环境变量：

| 参数 / 环境变量 | 默认值 | 用途 |
|---|---|---|
| `--host` / `HOST` | `127.0.0.1` | 监听地址 |
| `--port` / `PORT` | `8876` | 监听端口 |
| `TEACHU_DATA_DIR` | 仓库内 `data/` | 账号、会话与学习记录 |
| `TEACHU_PUBLIC_ORIGIN` | 当前 HTTP Host | 公网 HTTPS 来源校验 |
| `TEACHU_SECURE_COOKIE` | `0` | HTTPS 部署设为 `1` |
| `--prepare-only` | — | 仅展开课程，供静态部署使用 |

备份前停止服务，复制整个 `data/` 目录；恢复时停止服务后放回同一目录。升级前先备份：

```bash
git pull --ff-only
python3 server.py
```

Docker 用户更新后执行 `docker compose up -d --build`。新版本会依据资源包校验值更新课程文件，`data/` 中的账号与学习记录不会被覆盖。

## 项目结构

```text
public/                   页面、样式、浏览器模块与第三方解析器
assets/                   分片保存的版本化课程资源包
course-assets.tar.gz      启动时重组的课程资源包（不提交）
course-assets.sha256      课程资源完整性校验值
course-data.json          产品课程源数据
content/                  工程知识说明与代码示例
curriculum/               项目路线源数据
project-templates/        Web、Java、Python 本地项目模板
scripts/                  课程和作业维护工具
server.py                 静态文件、账号与学习记录服务
Dockerfile / compose.yaml 容器部署
CHANGELOG.md              版本更新日志
THIRD_PARTY_NOTICES.md     第三方组件许可说明
```

首次启动生成的 `public/engineering/`、`public/homework/` 等目录不直接提交到 Git，统一由资源包还原，避免重复存储数千份文件。编辑这些生成文件后，运行 `python3 scripts/package-assets.py` 更新资源包及校验值。

## 验证与维护

```bash
python3 -m unittest discover -s tests -p "test_*.py" -v
```

可选：安装 Node.js 后验证前端模块与重新生成搜索索引：

```bash
node tests/curriculum-navigation.mjs
node tests/audit-markdown.mjs
node scripts/build-search.cjs
```

GitHub Actions 配置了 Windows、macOS、Linux 的 Python 验证矩阵；本机验证与远端 CI 结果分别记录，不将尚未运行的系统列为已通过。

## 版本更新日志

### v1.0.1 · 2026-11-05

- 显式指定中文资料的 UTF-8 编码。
- 修复全新检出时的检查报告目录创建。
- 关闭本地 Python 项目的数据库连接，避免 Windows 文件占用。

### v1.0.0 · 2026-11-05

- 整理两条课程路径、完整课文、项目作业和参考实现，统一课程命名与页面样式。
- 宣传页改为连续滚动，增加分区入场效果、阅读进度和深浅色显示。
- 修复正文强调标签的 Markdown 渲染，保留代码块原样展示。
- 代码练习改为本地项目下载，停用平台内代码执行和作业上传。
- 提供独立邮箱/密码账号与学习记录同步，不依赖特定开发平台登录。
- 增加 Python 标准库启动器、Windows 启动脚本、Docker 部署与跨系统验证配置。
- 发布目录排除本地缓存、历史快照、协作过程记录和旧构建文件。

详细记录见 [CHANGELOG.md](CHANGELOG.md)。第三方组件许可见 [THIRD_PARTY_NOTICES.md](THIRD_PARTY_NOTICES.md)。
