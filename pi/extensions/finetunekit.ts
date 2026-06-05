import type { ExtensionAPI } from "@earendil-works/pi-coding-agent";
import { Type } from "typebox";
import { execFile, spawn } from "node:child_process";
import { existsSync, mkdirSync, readFileSync, realpathSync, writeFileSync } from "node:fs";
import { promisify } from "node:util";
import path from "node:path";
import { fileURLToPath } from "node:url";

const execFileAsync = promisify(execFile);
const __filename = realpathSync(fileURLToPath(import.meta.url));
const __dirname = path.dirname(__filename);
const REPO = process.env.FINETUNEKIT_REPO || path.resolve(__dirname, "../..");

type RunResult = { stdout: string; stderr: string; exitCode: number };
type ActiveRun = {
  id: string;
  kind: "train";
  projectDir: string;
  logPath: string;
  startedAt: number;
  status: "running" | "exited";
  exitCode?: number | null;
};

async function runFineTuneKit(args: string[], cwd = REPO, timeout = 120_000): Promise<RunResult> {
  try {
    const result = await execFileAsync("python3", ["-m", "finetunekit", ...args], {
      cwd,
      timeout,
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

async function runProjectScript(projectDir: string, script: string, args: string[] = [], timeout = 1_800_000): Promise<RunResult> {
  try {
    const result = await execFileAsync("python3", [script, ...args], {
      cwd: projectDir,
      timeout,
      maxBuffer: 1024 * 1024 * 10,
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

function resolveUserPath(value: string, cwd: string): string {
  if (value.startsWith("~/")) return path.join(process.env.HOME || cwd, value.slice(2));
  return path.isAbsolute(value) ? value : path.join(cwd, value);
}

function isProjectDir(projectDir: string): boolean {
  return existsSync(path.join(projectDir, "train.py")) && existsSync(path.join(projectDir, "config.json"));
}

function tailFile(file: string, maxChars = 1600): string {
  try {
    const text = readFileSync(file, "utf8");
    return text.length > maxChars ? text.slice(-maxChars) : text;
  } catch {
    return "";
  }
}

function writeRunLog(logPath: string, text: string) {
  writeFileSync(logPath, text, { flag: "a" });
}

export default function fineTuneKitExtension(pi: ExtensionAPI) {
  const activeRuns = new Map<string, ActiveRun>();
  let widgetTimer: NodeJS.Timeout | undefined;

  function renderWidget(ctx: any) {
    const runs = Array.from(activeRuns.values()).slice(-3);
    if (runs.length === 0) {
      ctx.ui.setStatus("finetunekit", "FineTuneKit ready");
      ctx.ui.setWidget("finetunekit", []);
      return;
    }
    const latest = runs[runs.length - 1];
    const elapsed = Math.round((Date.now() - latest.startedAt) / 1000);
    const tail = tailFile(latest.logPath, 500).split("\n").filter(Boolean).slice(-5);
    ctx.ui.setStatus("finetunekit", `${latest.kind}: ${latest.status}${latest.exitCode !== undefined ? ` (${latest.exitCode})` : ""}`);
    ctx.ui.setWidget("finetunekit", [
      `FineTuneKit ${latest.kind}: ${latest.status} • ${elapsed}s`,
      `Project: ${latest.projectDir}`,
      `Log: ${latest.logPath}`,
      ...tail.map((line) => `│ ${line.slice(0, 100)}`),
    ]);
  }

  function ensureWidgetTimer(ctx: any) {
    if (widgetTimer) return;
    widgetTimer = setInterval(() => renderWidget(ctx), 3000);
    widgetTimer.unref?.();
  }

  function startTraining(projectDir: string, ctx: any): ActiveRun {
    if (!isProjectDir(projectDir)) {
      throw new Error(`${projectDir} does not look like a FineTuneKit project (missing train.py/config.json)`);
    }
    const runDir = path.join(projectDir, ".finetunekit", "runs");
    mkdirSync(runDir, { recursive: true });
    const id = `train-${new Date().toISOString().replace(/[:.]/g, "-")}`;
    const logPath = path.join(runDir, `${id}.log`);
    const run: ActiveRun = { id, kind: "train", projectDir, logPath, startedAt: Date.now(), status: "running" };
    activeRuns.set(id, run);
    writeRunLog(logPath, `FineTuneKit training run ${id}\nProject: ${projectDir}\nCommand: python3 train.py\n\n`);
    const child = spawn("python3", ["train.py"], { cwd: projectDir, env: process.env });
    child.stdout.on("data", (chunk) => writeRunLog(logPath, chunk.toString()));
    child.stderr.on("data", (chunk) => writeRunLog(logPath, chunk.toString()));
    child.on("error", (error) => {
      run.status = "exited";
      run.exitCode = 1;
      writeRunLog(logPath, `\n[process error] ${error.message}\n`);
      renderWidget(ctx);
    });
    child.on("exit", (code) => {
      run.status = "exited";
      run.exitCode = code;
      writeRunLog(logPath, `\n[process exited] code=${code}\n`);
      renderWidget(ctx);
      ctx.ui.notify(`FineTuneKit training finished with code ${code}. Log: ${logPath}`, code === 0 ? "info" : "warning");
    });
    ensureWidgetTimer(ctx);
    renderWidget(ctx);
    return run;
  }

  async function checkTrainData(projectDir: string): Promise<RunResult> {
    return runFineTuneKit(["data", "check", path.join(projectDir, "data", "train.jsonl"), "--previews", "2"], REPO);
  }

  pi.on("resources_discover", async () => ({
    skillPaths: [path.join(REPO, "skills")],
  }));

  pi.on("session_start", async (_event, ctx) => {
    ctx.ui.setStatus("finetunekit", "FineTuneKit ready");
  });

  pi.on("session_shutdown", async () => {
    if (widgetTimer) clearInterval(widgetTimer);
  });

  pi.registerCommand("finetune", {
    description: "Open the FineTuneKit agent-native fine-tuning launcher",
    handler: async (_args, ctx) => {
      const action = await ctx.ui.select("FineTuneKit", [
        "Demo: create tiny sample project",
        "Doctor: check environment",
        "Recommend: pick model for task/hardware",
        "New project: guided fine-tuning scaffold",
        "Data check: lint JSONL training data",
        "Convert data: CSV -> JSONL",
        "Split data: train/eval JSONL",
        "Start training: approved background run",
        "Eval: base model",
        "Eval: adapter",
        "Status: show active run/log",
        "Show quick start",
      ]);
      if (!action) return;

      if (action.startsWith("Demo")) {
        const projectDir = (await ctx.ui.input("Demo project directory", "Absolute path or path relative to current cwd")) || "./finetunekit-demo";
        const fullPath = resolveUserPath(projectDir, ctx.cwd);
        const result = await runFineTuneKit(["demo", fullPath, "--force"]);
        ctx.ui.notify(asText(result), result.exitCode === 0 ? "info" : "warning");
        return;
      }

      if (action.startsWith("Doctor")) {
        const result = await runFineTuneKit(["doctor"]);
        ctx.ui.notify(asText(result), result.exitCode === 0 ? "info" : "warning");
        return;
      }

      if (action.startsWith("Recommend")) {
        const task = (await ctx.ui.input("Task", "support-bot, domain-qa, writing-style, extractor, classifier")) || "support-bot";
        const vram = await ctx.ui.input("VRAM GB (optional)", "Leave blank to auto-detect");
        const args = ["recommend", "--task", task];
        if (vram?.trim()) args.push("--vram-gb", vram.trim(), "--no-detect");
        const result = await runFineTuneKit(args);
        ctx.ui.notify(asText(result), result.exitCode === 0 ? "info" : "warning");
        return;
      }

      if (action.startsWith("New project")) {
        const projectDir = (await ctx.ui.input("Project directory", "Absolute path or path relative to current cwd")) || "./my-finetune-bot";
        const task = (await ctx.ui.input("Task", "support-bot, domain-qa, writing-style, extractor, classifier")) || "support-bot";
        const model = (await ctx.ui.input("Model preset", "tiny-smoke-test, beginner-3b, qwen-7b-quality, or HF model id")) || "tiny-smoke-test";
        const fullPath = resolveUserPath(projectDir, ctx.cwd);
        const result = await runFineTuneKit(["new", fullPath, "--task", task, "--model", model]);
        ctx.ui.notify(asText(result), result.exitCode === 0 ? "info" : "warning");
        return;
      }

      if (action.startsWith("Data check")) {
        const file = (await ctx.ui.input("Data file", "Path to train.jsonl")) || "data/train.jsonl";
        const fullPath = resolveUserPath(file, ctx.cwd);
        const result = await runFineTuneKit(["data", "check", fullPath]);
        ctx.ui.notify(asText(result), result.exitCode === 0 ? "info" : "warning");
        return;
      }

      if (action.startsWith("Convert")) {
        const input = await ctx.ui.input("Input CSV", "support.csv");
        if (!input) return;
        const output = (await ctx.ui.input("Output JSONL", "data/train.jsonl")) || "data/train.jsonl";
        const result = await runFineTuneKit(["data", "convert", resolveUserPath(input, ctx.cwd), resolveUserPath(output, ctx.cwd)]);
        ctx.ui.notify(asText(result), result.exitCode === 0 ? "info" : "warning");
        return;
      }

      if (action.startsWith("Split")) {
        const input = await ctx.ui.input("Input JSONL", "data/all.jsonl");
        if (!input) return;
        const trainOut = (await ctx.ui.input("Train output", "data/train.jsonl")) || "data/train.jsonl";
        const evalOut = (await ctx.ui.input("Eval output", "data/eval.jsonl")) || "data/eval.jsonl";
        const result = await runFineTuneKit(["data", "split", resolveUserPath(input, ctx.cwd), resolveUserPath(trainOut, ctx.cwd), resolveUserPath(evalOut, ctx.cwd)]);
        ctx.ui.notify(asText(result), result.exitCode === 0 ? "info" : "warning");
        return;
      }

      if (action.startsWith("Start training")) {
        const projectDir = resolveUserPath((await ctx.ui.input("Project directory", ".")) || ".", ctx.cwd);
        const dataReport = await checkTrainData(projectDir);
        if (dataReport.exitCode !== 0) {
          ctx.ui.notify(`Data check failed; not training.\n\n${asText(dataReport)}`, "warning");
          return;
        }
        const ok = await ctx.ui.confirm("Start training?", `This will run python train.py in:\n${projectDir}\n\nContinue?`);
        if (!ok) return;
        const run = startTraining(projectDir, ctx);
        ctx.ui.notify(`Started training in background. Log: ${run.logPath}`, "info");
        return;
      }

      if (action.startsWith("Eval")) {
        const projectDir = resolveUserPath((await ctx.ui.input("Project directory", ".")) || ".", ctx.cwd);
        const base = action.includes("base");
        const result = await runProjectScript(projectDir, "eval.py", base ? ["--base"] : []);
        ctx.ui.notify(asText(result), result.exitCode === 0 ? "info" : "warning");
        return;
      }

      if (action.startsWith("Status")) {
        renderWidget(ctx);
        const latest = Array.from(activeRuns.values()).slice(-1)[0];
        ctx.ui.notify(latest ? `Latest run: ${latest.status}\nLog: ${latest.logPath}\n\n${tailFile(latest.logPath)}` : "No active FineTuneKit runs in this Pi session.", "info");
        return;
      }

      ctx.ui.notify(`Quick start:\ncd ${REPO}\npython3 -m finetunekit demo /tmp/finetunekit-demo\npython3 -m finetunekit quickstart\n\nIn Pi: /finetune`, "info");
    },
  });

  pi.registerTool({
    name: "finetunekit_doctor",
    label: "FineTuneKit Doctor",
    description: "Check local Python, GPU, Unsloth dependencies, and Hugging Face token readiness for Unsloth fine-tuning.",
    promptSnippet: "Check whether the local environment is ready for Unsloth fine-tuning",
    promptGuidelines: ["Use finetunekit_doctor before attempting local Unsloth training."],
    parameters: Type.Object({}),
    async execute() {
      const result = await runFineTuneKit(["doctor"]);
      return { content: [{ type: "text", text: asText(result) }], details: result, isError: result.exitCode !== 0 };
    },
  });

  pi.registerTool({
    name: "finetunekit_recommend",
    label: "FineTuneKit Recommend",
    description: "Recommend beginner-safe Unsloth model presets for a task and optional VRAM budget.",
    promptSnippet: "Recommend an Unsloth model preset for a beginner task and GPU budget",
    promptGuidelines: ["Use finetunekit_recommend before creating an Unsloth fine-tuning project."],
    parameters: Type.Object({
      task: Type.String({ default: "support-bot", description: "Task such as support-bot, domain-qa, writing-style, extractor, classifier, code-helper" }),
      vramGb: Type.Optional(Type.Number({ description: "Available GPU VRAM in GB" })),
    }),
    async execute(_id, params) {
      const args = ["recommend", "--task", params.task || "support-bot"];
      if (params.vramGb) args.push("--vram-gb", String(params.vramGb), "--no-detect");
      const result = await runFineTuneKit(args);
      return { content: [{ type: "text", text: asText(result) }], details: result, isError: result.exitCode !== 0 };
    },
  });

  pi.registerTool({
    name: "finetunekit_create_project",
    label: "FineTuneKit Create Project",
    description: "Create a generated Unsloth fine-tuning project with train.py, chat.py, eval.py, config, sample data, and notes.",
    promptSnippet: "Create a beginner Unsloth fine-tuning project scaffold",
    promptGuidelines: ["Use finetunekit_create_project after clarifying the user's task and selecting a small model preset."],
    parameters: Type.Object({
      projectDir: Type.String({ description: "Directory to create. Absolute path or relative to current Pi cwd." }),
      task: Type.String({ default: "support-bot" }),
      model: Type.String({ default: "tiny-smoke-test", description: "Preset such as tiny-smoke-test or beginner-3b, or a Hugging Face model id" }),
      force: Type.Optional(Type.Boolean({ default: false })),
    }),
    async execute(_id, params, _signal, _onUpdate, ctx) {
      const fullPath = resolveUserPath(params.projectDir, ctx.cwd);
      const args = ["new", fullPath, "--task", params.task || "support-bot", "--model", params.model || "tiny-smoke-test"];
      if (params.force) args.push("--force");
      const result = await runFineTuneKit(args);
      return { content: [{ type: "text", text: asText(result) }], details: { ...result, projectDir: fullPath }, isError: result.exitCode !== 0 };
    },
  });

  pi.registerTool({
    name: "finetunekit_check_data",
    label: "FineTuneKit Data Check",
    description: "Lint and preview a JSONL training/eval file before Unsloth fine-tuning.",
    promptSnippet: "Validate and preview Unsloth chat/instruction JSONL data",
    promptGuidelines: ["Use finetunekit_check_data before running train.py for any Unsloth project."],
    parameters: Type.Object({
      file: Type.String({ description: "Path to JSONL data file. Absolute or relative to current Pi cwd." }),
      previews: Type.Optional(Type.Number({ default: 3 })),
    }),
    async execute(_id, params, _signal, _onUpdate, ctx) {
      const fullPath = resolveUserPath(params.file, ctx.cwd);
      const result = await runFineTuneKit(["data", "check", fullPath, "--previews", String(params.previews || 3)]);
      return { content: [{ type: "text", text: asText(result) }], details: { ...result, file: fullPath }, isError: result.exitCode !== 0 };
    },
  });

  pi.registerTool({
    name: "finetunekit_convert_data",
    label: "FineTuneKit Convert Data",
    description: "Convert CSV instruction/prompt/question data into chat JSONL and immediately validate it.",
    promptSnippet: "Convert beginner CSV data to FineTuneKit/Unsloth chat JSONL",
    promptGuidelines: ["Use finetunekit_convert_data when the user provides CSV data for fine-tuning."],
    parameters: Type.Object({
      input: Type.String({ description: "CSV input path. Absolute or relative to current Pi cwd." }),
      output: Type.String({ description: "JSONL output path. Absolute or relative to current Pi cwd." }),
    }),
    async execute(_id, params, _signal, _onUpdate, ctx) {
      const result = await runFineTuneKit(["data", "convert", resolveUserPath(params.input, ctx.cwd), resolveUserPath(params.output, ctx.cwd)]);
      return { content: [{ type: "text", text: asText(result) }], details: result, isError: result.exitCode !== 0 };
    },
  });

  pi.registerTool({
    name: "finetunekit_split_data",
    label: "FineTuneKit Split Data",
    description: "Split one JSONL file into held-out train/eval JSONL files and validate both.",
    promptSnippet: "Create train/eval JSONL splits before fine-tuning",
    promptGuidelines: ["Use finetunekit_split_data when the user has one dataset file and no held-out eval set."],
    parameters: Type.Object({
      input: Type.String({ description: "Input JSONL path. Absolute or relative to current Pi cwd." }),
      trainOutput: Type.String({ description: "Train JSONL output path." }),
      evalOutput: Type.String({ description: "Eval JSONL output path." }),
      evalRatio: Type.Optional(Type.Number({ default: 0.1 })),
    }),
    async execute(_id, params, _signal, _onUpdate, ctx) {
      const result = await runFineTuneKit([
        "data", "split",
        resolveUserPath(params.input, ctx.cwd),
        resolveUserPath(params.trainOutput, ctx.cwd),
        resolveUserPath(params.evalOutput, ctx.cwd),
        "--eval-ratio", String(params.evalRatio || 0.1),
      ]);
      return { content: [{ type: "text", text: asText(result) }], details: result, isError: result.exitCode !== 0 };
    },
  });

  pi.registerTool({
    name: "finetunekit_start_training",
    label: "FineTuneKit Start Training",
    description: "Run data check, ask approval, then start python train.py in the background with a Pi status widget and log file.",
    promptSnippet: "Start a FineTuneKit training job after data validation and approval",
    promptGuidelines: ["Use finetunekit_start_training only after data is checked and the user has approved training."],
    parameters: Type.Object({
      projectDir: Type.String({ description: "Generated FineTuneKit project directory." }),
      requireApproval: Type.Optional(Type.Boolean({ default: true })),
    }),
    async execute(_id, params, _signal, _onUpdate, ctx) {
      const projectDir = resolveUserPath(params.projectDir, ctx.cwd);
      const dataReport = await checkTrainData(projectDir);
      if (dataReport.exitCode !== 0) {
        return { content: [{ type: "text", text: `Data check failed; not training.\n\n${asText(dataReport)}` }], details: dataReport, isError: true };
      }
      if (params.requireApproval !== false && ctx.hasUI) {
        const ok = await ctx.ui.confirm("Start FineTuneKit training?", `Run python train.py in:\n${projectDir}\n\nThis can use GPU time. Continue?`);
        if (!ok) return { content: [{ type: "text", text: "Training cancelled by user." }], details: { cancelled: true } };
      }
      const run = startTraining(projectDir, ctx);
      return { content: [{ type: "text", text: `Started training in background.\nProject: ${projectDir}\nLog: ${run.logPath}` }], details: run };
    },
  });

  pi.registerTool({
    name: "finetunekit_run_eval",
    label: "FineTuneKit Run Eval",
    description: "Run eval.py for a generated FineTuneKit project, either base model or adapter.",
    promptSnippet: "Run base or adapter eval for a FineTuneKit project",
    promptGuidelines: ["Use finetunekit_run_eval to compare base vs fine-tuned adapter outputs."],
    parameters: Type.Object({
      projectDir: Type.String({ description: "Generated FineTuneKit project directory." }),
      base: Type.Optional(Type.Boolean({ default: false, description: "Evaluate base model instead of adapter." })),
      limit: Type.Optional(Type.Number({ default: 20 })),
    }),
    async execute(_id, params, _signal, _onUpdate, ctx) {
      const projectDir = resolveUserPath(params.projectDir, ctx.cwd);
      const args = [];
      if (params.base) args.push("--base");
      if (params.limit) args.push("--limit", String(params.limit));
      const result = await runProjectScript(projectDir, "eval.py", args);
      return { content: [{ type: "text", text: asText(result) }], details: result, isError: result.exitCode !== 0 };
    },
  });
}
