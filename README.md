# xsagent

面向长篇小说创作的 AI 智能体系统（Web + API）。

## 快速开始

### 环境要求

- Python 3.11+
- （可选）Node.js 18+ — 前端 P4 阶段使用

### 启动 Web 前端（P4）

```bash
# 终端 1：API
python -m xsagent

# 终端 2：前端（Vite 代理 /api → :8000）
cd packages/web && npm install && npm run dev
```

浏览器访问 `http://localhost:5173`

### 推荐创作流程

1. **LLM 配置**（侧栏底部）— DeepSeek 填 API Key，或测试时用 `simulator`
2. **新建项目** → 进入概览，按「新手路径」逐步完成
3. **创作引导** — AI 问答 3–6 轮 → 生成草案 → Diff 预览 → 应用到设定集
4. **章节规划** — 规模推导 + 章节蓝图
5. **写作** — 触发 AI 写作，监督面板处理高风险项

### 安装依赖

```bash
cd /path/to/xsagent
python -m venv .venv
pip install -e ".[dev]"
```

macOS / Linux 激活虚拟环境：

```bash
source .venv/bin/activate
```

Windows PowerShell：

```powershell
.venv\Scripts\Activate.ps1
```

### 本地配置

复制示例配置后再填写密钥。`config.yaml` 不会进入 Git。

```bash
# macOS / Linux
cp config.example.yaml config.yaml

# Windows
copy config.example.yaml config.yaml
```

DeepSeek Key 也可以只放在环境变量里，不必写入文件：

```bash
# macOS / Linux
export XSAGENT_LLM_MODE=deepseek
export XSAGENT_DEEPSEEK_API_KEY=sk-your-key

# Windows PowerShell
$env:XSAGENT_LLM_MODE = "deepseek"
$env:XSAGENT_DEEPSEEK_API_KEY = "sk-your-key"
```

### 启动 API 服务

```bash
# 方式一
python -m xsagent

# 方式二
uvicorn xsagent.api.app:create_app --factory --reload --port 8000
```

服务默认监听 `http://0.0.0.0:8000`。API 文档：`http://localhost:8000/docs`

### 环境变量

| 变量 | 默认 | 说明 |
|------|------|------|
| `XSAGENT_DATA_DIR` | `./data/projects` | 项目存储根目录 |
| `XSAGENT_LLM_MODE` | `simulator` | `simulator` / `ollama` / `deepseek` |
| `XSAGENT_DEEPSEEK_API_KEY` | 空 | DeepSeek API Key，优先于 `config.yaml` |
| `XSAGENT_OLLAMA_BASE_URL` | `http://localhost:11434` | Ollama 服务地址 |
| `XSAGENT_OLLAMA_MODEL` | `qwen2.5:14b` | Ollama 默认模型 |

示例见 `config.example.yaml`。本机配置写在 `config.yaml`（已忽略，勿提交）。

### P0 API 示例

```bash
# 创建项目
curl -X POST http://localhost:8000/api/projects \
  -H "Content-Type: application/json" \
  -d '{"name":"夜半来信","genre":"悬疑"}'

# 查询健康度
curl http://localhost:8000/api/projects/{project_id}/status
```

### 运行测试

```bash
pytest
```

## 项目结构

```
src/xsagent/     # Python 后端
packages/web/    # React 前端（P4）
templates/       # 项目初始化模板
tests/           # 单元测试 + API 测试
```

## 开发阶段

当前：**P4 Web UI（进行中）** — 设计系统、AppShell、项目列表/概览、写作页、监督面板骨架。

详见 [开发文档与计划.md](./开发文档与计划.md)。

### P3 API 端点

| 方法 | 路径 | 说明 |
|------|------|------|
| `POST` | `/api/projects/{id}/jobs/write-chapter` | 默认异步提交写作任务 |
| `POST` | `/api/projects/{id}/jobs/write-chapter-sync` | 同步执行（调试/回归） |
| `POST` | `/api/projects/{id}/jobs/write-chapter-submit` | 显式异步提交（与默认等价） |
| `GET` | `/api/projects/{id}/jobs/{job_id}` | 查询任务状态 |
| `GET` | `/api/projects/{id}/jobs/{job_id}/events` | SSE 事件流（progress/chunk/complete） |
| `GET` | `/api/projects/{id}/pending` | 待处理高风险事项 |
| `GET` | `/api/projects/{id}/supervision` | 监督面板聚合数据 |
| `POST` | `/api/projects/{id}/supervision/resolve` | 处理待办（apply/ignore/rollback） |
| `POST` | `/api/projects/{id}/onboarding/start` | 开始深度问答引导 |
| `POST` | `/api/projects/{id}/onboarding/answer` | 提交一轮回答 |
| `POST` | `/api/projects/{id}/onboarding` | 根据问答生成 Story Bible 草案 |
| `POST` | `/api/projects/{id}/onboarding/apply` | 应用引导草案（并标记引导完成） |
| `GET` | `/api/projects/{id}/onboarding/session` | 查询当前引导会话 |
| `POST` | `/api/projects/{id}/bible/patch` | Patch 预览/应用 |

环境变量 `XSAGENT_LLM_MODE`：`simulator`（测试）| `ollama`（本地模型）| `deepseek`（官方 API）

### DeepSeek 配置（Web）

1. 打开 `http://localhost:5173/settings/llm`
2. 将运行模式切换为 `deepseek`
3. 填写 `DeepSeek API Key`、模型（默认 `deepseek-v4-pro`）
4. 推荐设置：`reasoning_effort=high`、`thinking=enabled`、开启“隐藏思考内容”

也可改本机 `config.yaml` 的 `llm` 段（此文件不要提交）：

```yaml
llm:
  mode: "deepseek"
  deepseek_base_url: "https://api.deepseek.com"
  deepseek_api_key: ""
  deepseek_model: "deepseek-v4-pro"
  deepseek_reasoning_effort: "high"
  deepseek_thinking_enabled: true
  strip_think_tags: true
```

### P1 API 端点

| 方法 | 路径 | 说明 |
|------|------|------|
| `GET/PUT` | `/api/projects/{id}/bible/{section}` | Bible 分区读写（characters/plot/world/notes/timeline） |
| `PATCH` | `/api/projects/{id}/bible/{section}/locks` | 更新字段锁 |
| `GET/POST` | `/api/projects/{id}/chapters` | 章节列表 / 创建 |
| `GET/PUT` | `/api/projects/{id}/chapters/{cid}` | 章节读写 |
| `GET` | `/api/projects/{id}/outlines` | 三级大纲聚合 |
| `GET/PUT` | `/api/projects/{id}/outlines/master` | 总纲 |
| `GET/PUT` | `/api/projects/{id}/outlines/volumes/{vid}` | 分卷 |
| `GET/PUT` | `/api/projects/{id}/outlines/chapters/{cid}` | 章级蓝图 |
| `POST` | `/api/projects/{id}/outlines/generate-master` | 从 Bible 生成总纲与分卷弧线 |
| `POST` | `/api/projects/{id}/outlines/generate` | 批量/分卷/指定章生成蓝图 |
| `POST` | `/api/projects/{id}/outlines/chapters/{cid}/generate` | 单章蓝图预览 |
| `GET/POST` | `/api/projects/{id}/snapshots` | 快照列表 / 创建 |
| `POST` | `/api/projects/{id}/snapshots/{sid}/rollback` | 回滚 |
| `GET` | `/api/projects/{id}/logs/actions` | 操作日志 |

## 许可证

[MIT](./LICENSE) © 2026 DukeoHu
