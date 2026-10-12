import { useEffect, useState } from "react";
import { useMutation, useQuery } from "@tanstack/react-query";
import { api } from "../api/client";
import type { LLMConfig } from "../api/types";
import { Badge, Button, Card, Input, Label } from "../components/primitives";
import { Toast } from "../components/feedback";
import "./LLMSettingsPage.css";

export function LLMSettingsPage() {
  const [form, setForm] = useState<LLMConfig | null>(null);
  const [toast, setToast] = useState<{ type: "success" | "error"; message: string } | null>(
    null,
  );

  const configQuery = useQuery({
    queryKey: ["llm-config"],
    queryFn: api.getLLMConfig,
  });

  useEffect(() => {
    if (configQuery.data) {
      setForm(configQuery.data);
    }
  }, [configQuery.data]);

  const saveMutation = useMutation({
    mutationFn: (payload: LLMConfig) => api.updateLLMConfig(payload),
    onSuccess: (data) => {
      setForm(data);
      setToast({ type: "success", message: "LLM 配置已保存并即时生效" });
    },
    onError: (err: Error) => {
      setToast({ type: "error", message: err.message || "保存失败" });
    },
  });

  useEffect(() => {
    if (!toast) return;
    const timer = setTimeout(() => setToast(null), 2600);
    return () => clearTimeout(timer);
  }, [toast]);

  if (!form) {
    return <p className="animate-pulse-subtle">加载 LLM 配置…</p>;
  }

  return (
    <div className="animate-fade-in">
      <h1 className="page-title">LLM 配置</h1>
      <p className="page-subtitle">配置 Ollama 或 DeepSeek 官方 API（含 Token 与思考模式）</p>

      <Card padding="md">
        <div className="llm-settings__form">
          <div>
            <Label htmlFor="llm-mode">运行模式</Label>
            <select
              id="llm-mode"
              className="input"
              value={form.mode}
              onChange={(e) =>
                setForm((prev) =>
                  prev ? { ...prev, mode: e.target.value as LLMConfig["mode"] } : prev,
                )
              }
            >
              <option value="simulator">simulator（测试）</option>
              <option value="ollama">ollama（本地模型）</option>
              <option value="deepseek">deepseek（官方 API）</option>
            </select>
          </div>

          {form.mode === "ollama" && (
            <>
              <div>
                <Label htmlFor="llm-model">Ollama 模型名称</Label>
                <Input
                  id="llm-model"
                  value={form.ollama_model}
                  onChange={(e) =>
                    setForm((prev) => (prev ? { ...prev, ollama_model: e.target.value } : prev))
                  }
                  placeholder="例如：deepseek-r1:latest"
                />
              </div>

              <div className="llm-settings__full">
                <Label htmlFor="llm-base-url">Ollama Base URL</Label>
                <Input
                  id="llm-base-url"
                  value={form.ollama_base_url}
                  onChange={(e) =>
                    setForm((prev) =>
                      prev ? { ...prev, ollama_base_url: e.target.value } : prev,
                    )
                  }
                  placeholder="http://localhost:11434"
                />
              </div>

              <div>
                <Label htmlFor="llm-think">思考模式（Ollama）</Label>
                <select
                  id="llm-think"
                  className="input"
                  value={String(form.ollama_think)}
                  onChange={(e) =>
                    setForm((prev) =>
                      prev ? { ...prev, ollama_think: e.target.value === "true" } : prev,
                    )
                  }
                >
                  <option value="true">开启</option>
                  <option value="false">关闭</option>
                </select>
              </div>
            </>
          )}

          {form.mode === "deepseek" && (
            <>
              <div className="llm-settings__full">
                <Label htmlFor="deepseek-api-key" required>
                  DeepSeek API Key
                </Label>
                <Input
                  id="deepseek-api-key"
                  type="password"
                  value={form.deepseek_api_key}
                  onChange={(e) =>
                    setForm((prev) =>
                      prev ? { ...prev, deepseek_api_key: e.target.value } : prev,
                    )
                  }
                  placeholder="sk-..."
                />
              </div>

              <div>
                <Label htmlFor="deepseek-model">DeepSeek 模型</Label>
                <Input
                  id="deepseek-model"
                  value={form.deepseek_model}
                  onChange={(e) =>
                    setForm((prev) =>
                      prev ? { ...prev, deepseek_model: e.target.value } : prev,
                    )
                  }
                  placeholder="deepseek-v4-pro"
                />
              </div>

              <div>
                <Label htmlFor="deepseek-base-url">DeepSeek Base URL</Label>
                <Input
                  id="deepseek-base-url"
                  value={form.deepseek_base_url}
                  onChange={(e) =>
                    setForm((prev) =>
                      prev ? { ...prev, deepseek_base_url: e.target.value } : prev,
                    )
                  }
                  placeholder="https://api.deepseek.com"
                />
              </div>

              <div>
                <Label htmlFor="deepseek-reasoning-effort">Reasoning Effort</Label>
                <select
                  id="deepseek-reasoning-effort"
                  className="input"
                  value={form.deepseek_reasoning_effort}
                  onChange={(e) =>
                    setForm((prev) =>
                      prev
                        ? { ...prev, deepseek_reasoning_effort: e.target.value }
                        : prev,
                    )
                  }
                >
                  <option value="low">low</option>
                  <option value="medium">medium</option>
                  <option value="high">high</option>
                </select>
              </div>

              <div>
                <Label htmlFor="deepseek-thinking-enabled">Thinking</Label>
                <select
                  id="deepseek-thinking-enabled"
                  className="input"
                  value={String(form.deepseek_thinking_enabled)}
                  onChange={(e) =>
                    setForm((prev) =>
                      prev
                        ? { ...prev, deepseek_thinking_enabled: e.target.value === "true" }
                        : prev,
                    )
                  }
                >
                  <option value="true">enabled</option>
                  <option value="false">disabled</option>
                </select>
              </div>
            </>
          )}

          <div>
            <Label htmlFor="llm-strip-think">隐藏思考内容</Label>
            <select
              id="llm-strip-think"
              className="input"
              value={String(form.strip_think_tags)}
              onChange={(e) =>
                setForm((prev) =>
                  prev ? { ...prev, strip_think_tags: e.target.value === "true" } : prev,
                )
              }
            >
              <option value="true">是（推荐）</option>
              <option value="false">否</option>
            </select>
          </div>
        </div>

        <p className="llm-settings__hint">
          官方 API 推荐：`mode=deepseek`、`model=deepseek-v4-pro`、`reasoning_effort=high`、
          `thinking=enabled`；为避免思考链干扰正文，建议同时开启“隐藏思考内容”。
        </p>

        <div className="llm-settings__actions">
          <Button
            onClick={() => saveMutation.mutate(form)}
            disabled={saveMutation.isPending}
          >
            保存配置
          </Button>
          <Badge variant={form.mode === "ollama" ? "accent" : "default"}>
            当前模式：{form.mode}
          </Badge>
        </div>
      </Card>

      {toast && <Toast type={toast.type} message={toast.message} />}
    </div>
  );
}
