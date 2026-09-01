
"use client";

import React, { useEffect, useState } from "react";
import { Button } from "@/components/ui/button";
import { listProjects } from "@/lib/management-api";
import { toast } from "sonner";
import {
  FlaskConical,
  Lightbulb,
  GitBranch,
  FilePlus,
  Zap,
  RotateCcw,
  ShieldCheck,
  Send,
  FileText,
} from "lucide-react";
import { cn } from "@/lib/utils";
import type { Project } from "@/types/chat";

interface QuickAction {
  id: string;
  label: string;
  icon: React.ReactNode;
  getPrompt: (projectName?: string) => string;
}

const QUICK_ACTIONS: QuickAction[] = [
  {
    id: "change-impact-analysis",
    label: "变更影响分析 & 回归推荐",
    icon: <GitBranch className="size-3.5" />,
    getPrompt: (projectName) =>
      projectName
        ? `分析项目 "${projectName}" 最近的代码变更，识别受影响的 API 接口，并推荐回归测试范围。`
        : "分析最近的代码变更，识别受影响的 API 接口，并推荐回归测试范围。",
  },
  {
    id: "generate-test-cases",
    label: "自动生成测试用例",
    icon: <FilePlus className="size-3.5" />,
    getPrompt: (projectName) =>
      projectName
        ? `基于项目 "${projectName}" 的 OpenAPI 规范，生成完整的 API 测试用例（覆盖正向、负向、边界场景）。`
        : "基于 OpenAPI 规范，生成完整的 API 测试用例（覆盖正向、负向、边界场景）。",
  },
  {
    id: "api-functional-test",
    label: "接口功能测试",
    icon: <FlaskConical className="size-3.5" />,
    getPrompt: (projectName) =>
      projectName
        ? `基于项目 "${projectName}" 的 OpenAPI 规范生成 pytest 脚本，并执行接口功能测试。`
        : "基于 OpenAPI 规范生成 pytest 脚本，并执行接口功能测试。",
  },
  {
    id: "run-smoke",
    label: "冒烟测试",
    icon: <Zap className="size-3.5" />,
    getPrompt: (projectName) =>
      projectName
        ? `为项目 "${projectName}" 运行冒烟测试，验证核心接口可用。`
        : "运行冒烟测试，验证核心接口可用。",
  },
  {
    id: "run-regression",
    label: "全量回归测试",
    icon: <RotateCcw className="size-3.5" />,
    getPrompt: (projectName) =>
      projectName
        ? `为项目 "${projectName}" 运行全量回归测试。`
        : "运行全量回归测试。",
  },
  {
    id: "contract-test",
    label: "契约测试",
    icon: <ShieldCheck className="size-3.5" />,
    getPrompt: (projectName) =>
      projectName
        ? `验证项目 "${projectName}" 的 API 是否符合 OpenAPI 规范。`
        : "验证 API 是否符合 OpenAPI 规范。",
  },
  {
    id: "single-endpoint-debug",
    label: "单接口调试",
    icon: <Send className="size-3.5" />,
    getPrompt: (projectName) =>
      projectName
        ? `帮我调试项目 "${projectName}" 中的一个 API 接口。请引导我提供请求方法、路径、Headers 和 Body，然后执行并分析结果。`
        : "帮我调试一个 API 接口。请引导我提供请求方法、路径、Headers 和 Body，然后执行并分析结果。",
  },
  {
    id: "generate-report",
    label: "生成测试报告",
    icon: <FileText className="size-3.5" />,
    getPrompt: (projectName) =>
      projectName
        ? `汇总项目 "${projectName}" 最近的测试结果，生成结构化的测试报告。`
        : "汇总最近的测试结果，生成结构化的测试报告。",
  },
];

interface QuickActionsProps {
  project?: Project;
  onProjectChange?: (project: Project | undefined) => void;
  onSendMessage: (text: string) => void;
  isLoading?: boolean;
  className?: string;
}

export function QuickActions({
  project,
  onProjectChange,
  onSendMessage,
  isLoading,
  className,
}: QuickActionsProps) {
  const [projects, setProjects] = useState<Project[]>([]);
  const [loading, setLoading] = useState(false);
  const initializedRef = React.useRef(false);

  useEffect(() => {
    let mounted = true;
    setLoading(true);
    listProjects()
      .then((data) => {
        if (!mounted) return;
        const parsed = (data || []).map((item) => item as Project);
        setProjects(parsed);
        if (parsed.length > 0 && !initializedRef.current) {
          initializedRef.current = true;
          onProjectChange?.(parsed[0]);
        }
      })
      .catch((err) => {
        if (!mounted) return;
        toast.error("加载项目失败", {
          description: err instanceof Error ? err.message : String(err),
        });
      })
      .finally(() => {
        if (mounted) setLoading(false);
      });
    return () => {
      mounted = false;
    };
  }, [onProjectChange]);

  const handleAction = (action: QuickAction) => {
    if (isLoading) return;
    const prompt = action.getPrompt(project?.name);
    onSendMessage(prompt);
  };

  return (
    <div className={cn("flex flex-col gap-2", className)}>
      <div className="flex flex-wrap items-center gap-2">
        <div className="flex items-center gap-2">
          <Lightbulb className="size-4 text-muted-foreground" />
          <span className="text-sm text-muted-foreground">快捷提示:</span>
        </div>
        {QUICK_ACTIONS.map((action) => (
          <Button
            key={action.id}
            variant="outline"
            size="sm"
            disabled={isLoading || loading}
            onClick={() => handleAction(action)}
            className="h-7 gap-1.5 text-xs"
          >
            {action.icon}
            {action.label}
          </Button>
        ))}
      </div>
      {projects.length > 0 && (
        <div className="flex items-center gap-2">
          <span className="text-sm text-muted-foreground">选择项目:</span>
          <select
            value={project?.id || ""}
            onChange={(e) => {
              const selected = projects.find((p) => p.id === e.target.value);
              onProjectChange?.(selected);
            }}
            disabled={isLoading || loading}
            className="h-7 rounded-md border border-border bg-background px-2 text-xs outline-none focus:ring-1 focus:ring-ring"
          >
            {projects.map((project) => (
              <option
                key={project.id}
                value={project.id}
                className="text-xs"
              >
                {project.name}
              </option>
            ))}
          </select>
        </div>
      )}
    </div>
  );
}
