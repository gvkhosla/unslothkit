import type { ExtensionAPI } from "@earendil-works/pi-coding-agent";
import { Type } from "typebox";
import { execFile } from "node:child_process";
import { promisify } from "node:util";
import path from "node:path";
import { fileURLToPath } from "node:url";

const execFileAsync = promisify(execFile);
const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);
const REPO = process.env.UNSLOTHKIT_REPO || path.resolve(__dirname, "../..");

type RunResult = { stdout: string; stderr: string; exitCode: number };

async function runUnslothKit(args: string[], cwd = REPO): Promise<RunResult> {
  try {
    const result = await execFileAsync("python3", ["-m", "unslothkit", ...args], {
      cwd,
      timeout: 120_000,
      maxBuffer: 1024 * 1024 * 5,
    });
    return { stdout: result.stdout ?? "", stderr: result.stderr ?? "", exitCode: 0 };
  } catch (error: any) {
    return {
      stdout: error?.stdout ?? "",
      stderr: error?.stderr ?? error?.message ?? String(error),
      exitCode: typeof error?.code === "number" ? error.code : 1,
    };
  }
}

function asText(result: RunResult): string {
  const pieces = [];
  pieces.push(`exitCode: ${result.exitCode}`);
  if (result.stdout.trim()) pieces.push(`stdout:\n${result.stdout.trim()}`);
  if (result.stderr.trim()) pieces.push(`stderr:\n${result.stderr.trim()}`);
  return pieces.join("\n\n");
}

export default function unslothKitExtension(pi: ExtensionAPI) {
  pi.on("resources_discover", async () => ({
    skillPaths: [path.join(REPO, "skills")],
  }));

  pi.on("session_start", async (_event, ctx) => {
    ctx.ui.setStatus("unslothkit", "UnslothKit ready");
  });

  pi.registerCommand("unsloth", {
    description: "Open the UnslothKit beginner fine-tuning launcher",
    handler: async (_args, ctx) => {
      const action = await ctx.ui.select("UnslothKit", [
        "Doctor: check environment",
        "Recommend: pick model for task/hardware",
        "Quickstart: interactive terminal wizard",
        "New project: guided fine-tuning scaffold",
        "Data check: lint JSONL training data",
        "Show quick start",
      ]);
      if (!action) return;

      if (action.startsWith("Doctor")) {
        const result = await runUnslothKit(["doctor"]);
        ctx.ui.notify(asText(result), result.exitCode === 0 ? "info" : "warning");
        return;
      }

      if (action.startsWith("Recommend")) {
        const task = (await ctx.ui.input("Task", "support-bot, domain-qa, writing-style, extractor, classifier")) || "support-bot";
        const vram = await ctx.ui.input("VRAM GB (optional)", "Leave blank to auto-detect");
        const args = ["recommend", "--task", task];
        if (vram?.trim()) args.push("--vram-gb", vram.trim(), "--no-detect");
        const result = await runUnslothKit(args);
        ctx.ui.notify(asText(result), result.exitCode === 0 ? "info" : "warning");
        return;
      }

      if (action.startsWith("Quickstart")) {
        ctx.ui.notify("Run this in your terminal:\npython3 -m unslothkit quickstart\n\nThis asks a few questions, creates a project, imports optional CSV/JSONL data, and checks it.", "info");
        return;
      }

      if (action.startsWith("New project")) {
        const projectDir = (await ctx.ui.input("Project directory", "Absolute path or path relative to current cwd")) || "./my-unsloth-bot";
        if (!projectDir) return;
        const task = (await ctx.ui.input("Task", "support-bot, domain-qa, writing-style, extractor, classifier")) || "support-bot";
        const model = (await ctx.ui.input("Model preset", "tiny-smoke-test, beginner-3b, qwen-7b-quality, or HF model id")) || "tiny-smoke-test";
        const fullPath = path.isAbsolute(projectDir) ? projectDir : path.join(ctx.cwd, projectDir);
        const result = await runUnslothKit(["new", fullPath, "--task", task, "--model", model]);
        ctx.ui.notify(asText(result), result.exitCode === 0 ? "info" : "warning");
        return;
      }

      if (action.startsWith("Data check")) {
        const file = (await ctx.ui.input("Data file", "Path to train.jsonl")) || "data/train.jsonl";
        if (!file) return;
        const fullPath = path.isAbsolute(file) ? file : path.join(ctx.cwd, file);
        const result = await runUnslothKit(["data", "check", fullPath]);
        ctx.ui.notify(asText(result), result.exitCode === 0 ? "info" : "warning");
        return;
      }

      ctx.ui.notify(`Quick start:\ncd ${REPO}\npython3 -m unslothkit doctor\npython3 -m unslothkit recommend --task support-bot\npython3 -m unslothkit new ~/my-bot --task support-bot --model tiny-smoke-test`, "info");
    },
  });

  pi.registerTool({
    name: "unslothkit_doctor",
    label: "UnslothKit Doctor",
    description: "Check local Python, GPU, Unsloth dependencies, and Hugging Face token readiness for Unsloth fine-tuning.",
    promptSnippet: "Check whether the local environment is ready for Unsloth fine-tuning",
    promptGuidelines: ["Use unslothkit_doctor before attempting local Unsloth training."],
    parameters: Type.Object({}),
    async execute() {
      const result = await runUnslothKit(["doctor"]);
      return { content: [{ type: "text", text: asText(result) }], details: result, isError: result.exitCode !== 0 };
    },
  });

  pi.registerTool({
    name: "unslothkit_recommend",
    label: "UnslothKit Recommend",
    description: "Recommend beginner-safe Unsloth model presets for a task and optional VRAM budget.",
    promptSnippet: "Recommend an Unsloth model preset for a beginner task and GPU budget",
    promptGuidelines: ["Use unslothkit_recommend before creating an Unsloth fine-tuning project."],
    parameters: Type.Object({
      task: Type.String({ default: "support-bot", description: "Task such as support-bot, domain-qa, writing-style, extractor, classifier, code-helper" }),
      vramGb: Type.Optional(Type.Number({ description: "Available GPU VRAM in GB" })),
    }),
    async execute(_id, params) {
      const args = ["recommend", "--task", params.task || "support-bot"];
      if (params.vramGb) args.push("--vram-gb", String(params.vramGb), "--no-detect");
      const result = await runUnslothKit(args);
      return { content: [{ type: "text", text: asText(result) }], details: result, isError: result.exitCode !== 0 };
    },
  });

  pi.registerTool({
    name: "unslothkit_create_project",
    label: "UnslothKit Create Project",
    description: "Create a generated Unsloth fine-tuning project with train.py, chat.py, eval.py, config, sample data, and notes.",
    promptSnippet: "Create a beginner Unsloth fine-tuning project scaffold",
    promptGuidelines: ["Use unslothkit_create_project after clarifying the user's task and selecting a small model preset."],
    parameters: Type.Object({
      projectDir: Type.String({ description: "Directory to create. Absolute path or relative to current Pi cwd." }),
      task: Type.String({ default: "support-bot" }),
      model: Type.String({ default: "tiny-smoke-test", description: "Preset such as tiny-smoke-test or beginner-3b, or a Hugging Face model id" }),
      force: Type.Optional(Type.Boolean({ default: false })),
    }),
    async execute(_id, params, _signal, _onUpdate, ctx) {
      const fullPath = path.isAbsolute(params.projectDir) ? params.projectDir : path.join(ctx.cwd, params.projectDir);
      const args = ["new", fullPath, "--task", params.task || "support-bot", "--model", params.model || "tiny-smoke-test"];
      if (params.force) args.push("--force");
      const result = await runUnslothKit(args);
      return { content: [{ type: "text", text: asText(result) }], details: { ...result, projectDir: fullPath }, isError: result.exitCode !== 0 };
    },
  });

  pi.registerTool({
    name: "unslothkit_check_data",
    label: "UnslothKit Data Check",
    description: "Lint and preview a JSONL training/eval file before Unsloth fine-tuning.",
    promptSnippet: "Validate and preview Unsloth chat/instruction JSONL data",
    promptGuidelines: ["Use unslothkit_check_data before running train.py for any Unsloth project."],
    parameters: Type.Object({
      file: Type.String({ description: "Path to JSONL data file. Absolute or relative to current Pi cwd." }),
      previews: Type.Optional(Type.Number({ default: 3 })),
    }),
    async execute(_id, params, _signal, _onUpdate, ctx) {
      const fullPath = path.isAbsolute(params.file) ? params.file : path.join(ctx.cwd, params.file);
      const result = await runUnslothKit(["data", "check", fullPath, "--previews", String(params.previews || 3)]);
      return { content: [{ type: "text", text: asText(result) }], details: { ...result, file: fullPath }, isError: result.exitCode !== 0 };
    },
  });
}
