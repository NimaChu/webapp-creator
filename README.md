# WebApp Creator

用一句自然语言描述需求，创建可以独立运行的轻量网页应用。

WebApp Creator 是一个面向 AI 编程助手的技能包。它默认把应用做成一个
`index.html`：不用安装前端框架，不用运行构建命令，也不依赖某个发布平台。
完成后可以直接在浏览器打开、放进 U 盘、发给别人，或者部署到任意静态网站服务。

如果应用需要 AI，也可以连接你自己电脑上的模型或其他
OpenAI-compatible 接口；普通计算器、小游戏等应用完全不需要模型。

## 能做什么

- 小工具：计算器、转换器、生成器、表单和文件处理工具
- 数据看板：指标、趋势、筛选、对比和异常列表
- 引导流程：配置向导、诊断问答和分步骤任务
- 知识应用：指南、FAQ、笔记和可搜索资料
- 网页小游戏：适配鼠标、键盘和触屏的轻量游戏
- HTML 演示：全屏播放、键盘翻页和打印输出
- AI 工具：文本生成、图片理解、图片生成和代码辅助

所有类型都优先采用原生 HTML、CSS 和 JavaScript，保持轻量、透明、容易修改。

## 最简单的使用方法

### 1. 准备环境

你只需要：

- Git
- Python 3.10 或更新版本
- Chrome、Edge、Safari 或 Firefox 等现代浏览器
- 支持自定义技能的 AI 编程助手，例如 Codex

不使用 AI 模型功能时，不需要 API Key，也不需要安装 Node.js。

### 2. 安装技能

以 Codex 为例，在终端执行：

```bash
git clone https://github.com/NimaChu/webapp-creator.git \
  ~/.codex/skills/webapp-creator
```

重新打开 Codex，让它发现新技能。

如果你已经下载了仓库，可以先运行自检：

```bash
cd ~/.codex/skills/webapp-creator
python3 scripts/check_skill.py
```

看到 `Self-check passed` 就说明技能包工作正常。

### 3. 直接描述想法

不需要先决定技术方案，像平时说话一样告诉 AI：

> 使用 webapp-creator 做一个旅行费用分摊工具。支持多人、多币种，结果可以复制，手机也要好用。

或者：

> 使用 webapp-creator 做一个单词消除小游戏。保存最高分，触屏和键盘都能玩，最后交付一个 index.html。

再比如本地 AI 工具：

> 使用 webapp-creator 做一个本地文章改写工具，连接 OpenAI-compatible 模型，支持流式输出和取消生成。

AI 会根据需求选择合适的应用类型，完成界面、交互、验证和本地预览。

## 不通过 AI，也可以直接使用

进入仓库目录后，先查看支持的应用类型：

```bash
python3 scripts/webapp.py kinds
```

创建一个普通网页工具：

```bash
python3 scripts/webapp.py scaffold \
  --kind tool \
  --out my-app \
  --title "我的小工具" \
  --summary "帮助我完成一个重复任务"
```

在浏览器中预览：

```bash
python3 scripts/webapp.py serve my-app --open
```

检查应用是否完整：

```bash
python3 scripts/webapp.py validate my-app --strict
```

打包成 ZIP：

```bash
python3 scripts/webapp.py build my-app --out my-app.zip
```

`my-app/index.html` 就是应用入口。脚手架只是起点，正式交付前仍应把示例内容和行为改成真实需求。

## 连接本地 AI 模型

先创建带文本模型能力的应用：

```bash
python3 scripts/webapp.py scaffold \
  --kind tool \
  --ai text \
  --out my-ai-app \
  --title "本地 AI 工具" \
  --summary "使用我自己的模型处理文本"
```

复制生成的配置模板：

```bash
cp my-ai-app/.webapp.local.example.json \
  my-ai-app/.webapp.local.json
```

打开 `.webapp.local.json`，填写模型服务的 `baseUrl` 和 `model`。例如，本地模型服务
提供 OpenAI-compatible 接口时，配置大致如下：

```json
{
  "chat": {
    "baseUrl": "http://127.0.0.1:11434/v1",
    "model": "your-local-model",
    "apiKeyEnv": "",
    "timeoutSeconds": 120
  }
}
```

然后启动应用：

```bash
python3 scripts/webapp.py serve my-ai-app --open
```

模型请求由本地代理转发。密钥不会写入 HTML，`.webapp.local.json` 也不会被打进交付 ZIP。
如果远程接口需要密钥，请在 `apiKeyEnv` 中填写环境变量名称，把密钥保存在对应环境变量里。

## 为什么默认是单个 HTML

- 双击即可运行，迁移和备份都很简单
- 不依赖 React、Tailwind、npm 或构建服务器
- HTML、样式和逻辑都能直接查看和修改
- 普通静态托管、局域网和离线环境都能使用
- 本地模型配置与应用文件分离，不把凭证交给网页

当图片、音视频、WASM 或复杂逻辑过大时，也可以拆成多个本地文件；项目仍保持纯静态和可移植。

## 常见问题

### 双击 `index.html` 后某些功能不能用

浏览器可能限制本地文件的剪贴板、模块或文件访问权限。使用本地服务器打开：

```bash
python3 scripts/webapp.py serve <应用目录> --open
```

### 提示找不到本地模型

确认模型服务已经启动，并检查 `.webapp.local.json` 中的 `baseUrl` 和 `model`。
访问 `/runtime/health` 可以查看当前配置状态。

### 构建时提示 ZIP 已存在

为防止误覆盖，构建默认保留已有文件。确认可以替换后再执行：

```bash
python3 scripts/webapp.py build <应用目录> --out <应用名>.zip --force
```

### 可以发布到哪里

输出是普通静态网页，可以放在本机、NAS、任意静态文件服务器或静态网站托管服务上。
发布不是运行应用的必要条件。

## 项目结构

```text
webapp-creator/
├── SKILL.md                  # AI 使用的核心工作流
├── assets/starters/          # 六类应用与 AI 工具起点
├── references/               # 设计、游戏、演示和本地模型规范
├── scripts/webapp.py         # 创建、检查、预览和打包
├── scripts/local_runtime.py  # 可选的本地模型代理
├── scripts/check_skill.py    # 全仓自检
└── tests/                    # 安全、HTML 和构建测试
```

## 给开发者

修改技能、脚本或 starter 后运行：

```bash
python3 scripts/check_skill.py
```

自检会验证技能元数据、Python 脚本、运行时配置、全部 starter、严格 HTML 规则、
构建流程和单元测试。
