#!/usr/bin/env node

import { spawn, spawnSync } from 'node:child_process';
import { createHash } from 'node:crypto';
import {
  createWriteStream,
  existsSync,
  mkdirSync,
  readFileSync,
  readdirSync,
  renameSync,
  rmSync,
  statSync,
  writeFileSync,
} from 'node:fs';
import { tmpdir } from 'node:os';
import { basename, dirname, extname, isAbsolute, join, resolve } from 'node:path';
import { fileURLToPath } from 'node:url';

const COMPLETE_MARKER = '<<ORCHESTRATION_COMPLETE>>';
const DEFAULT_TIMEOUT_MS = 10 * 60 * 1000;
const SCRIPT_DIR = dirname(fileURLToPath(import.meta.url));
const DEFAULT_WORKSPACE = dirname(SCRIPT_DIR);

const ROLE_DEFAULTS = Object.freeze({
  astra: { provider: 'codex', model: 'gpt-6-astra', effort: 'high' },
  engineer: { provider: 'codex', model: 'gpt-5.6-sol', effort: 'high' },
  investigator: { provider: 'claude', model: 'claude-opus-5', effort: 'high' },
  researcher: { provider: 'claude', model: 'claude-sonnet-5', effort: 'medium' },
});

function usage(exitCode = 0) {
  const out = `Usage:
  node .ai/orchestrate.mjs invoke --role ROLE --context FILE [options]
  node .ai/orchestrate.mjs smoke --context FILE [--cross-review] [options]

invoke options:
  --provider codex|claude       Inferred for the four standard roles
  --model MODEL                 Inferred for the four standard roles
  --effort low|medium|high      Inferred for the four standard roles
  --prompt TEXT                 Additional role instruction
  --prompt-file FILE            Read the additional instruction from a file
  --run-id ID                   Default: UTC timestamp plus random suffix
  --timeout-ms N                Default: ${DEFAULT_TIMEOUT_MS}
  --workspace DIR               Default: parent of this .ai directory
  --no-state                    Do not update .ai/STATE.md

smoke options:
  --cross-review                Add a blind cross-critique round
  --resume                      Reuse matching validated stages in --run-id
  --run-id, --timeout-ms, --workspace, --no-state

The process exits nonzero when a requested CLI/model is unavailable, authentication
fails, output is empty or incomplete, a reported model differs, or any agent fails.`;
  (exitCode ? process.stderr : process.stdout).write(`${out}\n`);
  process.exit(exitCode);
}

function parseArgs(argv) {
  const options = { _: [] };
  for (let i = 0; i < argv.length; i += 1) {
    const arg = argv[i];
    if (!arg.startsWith('--')) {
      options._.push(arg);
      continue;
    }
    const key = arg.slice(2);
    if (key === 'cross-review' || key === 'resume' || key === 'no-state' || key === 'help') {
      options[key] = true;
      continue;
    }
    if (i + 1 >= argv.length || argv[i + 1].startsWith('--')) {
      throw new Error(`Missing value for --${key}`);
    }
    options[key] = argv[++i];
  }
  return options;
}

function safeRunId(value) {
  if (value && !/^[A-Za-z0-9][A-Za-z0-9._-]{0,119}$/.test(value)) {
    throw new Error('Run ID must use only letters, digits, dot, underscore, or dash (max 120 characters).');
  }
  return value || `${new Date().toISOString().replace(/[:.]/g, '-')}-${Math.random().toString(16).slice(2, 8)}`;
}

function safeLabel(value) {
  return value.toLowerCase().replace(/[^a-z0-9._-]+/g, '-').replace(/^-+|-+$/g, '').slice(0, 70) || 'agent';
}

function sha256(value) {
  return createHash('sha256').update(value).digest('hex');
}

function readRequiredFile(path, label) {
  const absolute = resolve(path);
  if (!existsSync(absolute) || !statSync(absolute).isFile()) {
    throw new Error(`${label} is not a readable file: ${absolute}`);
  }
  return { absolute, text: readFileSync(absolute, 'utf8') };
}

function findOnPath(name) {
  if (process.platform === 'win32') {
    // where.exe writes in the active Windows code page. Decoding it as UTF-8
    // corrupts paths such as C:\\Users\\Raí. Walk PATH using Node's native
    // Unicode strings instead.
    const extensions = ['', ...(process.env.PATHEXT || '.COM;.EXE;.BAT;.CMD').split(';').map((value) => value.toLowerCase())];
    const results = [];
    for (const directory of (process.env.PATH || '').split(';').filter(Boolean)) {
      for (const extension of extensions) {
        const candidate = join(directory.replace(/^"|"$/g, ''), `${name}${extension}`);
        if (existsSync(candidate) && statSync(candidate).isFile() && !results.includes(candidate)) results.push(candidate);
      }
    }
    return results;
  }
  const result = spawnSync('which', [name], { encoding: 'utf8' });
  if (result.status !== 0) return [];
  return result.stdout.split(/\r?\n/).map((line) => line.trim()).filter(Boolean);
}

function expandShimPath(raw, shimPath) {
  const base = dirname(shimPath);
  return raw
    .replace(/%dp0%/gi, `${base}\\`)
    .replace(/\$basedir(?:\/|\\)/gi, `${base}\\`)
    .replace(/\$basedir/gi, base);
}

function parseNpmShim(shimPath) {
  const text = readFileSync(shimPath, 'utf8');
  const candidates = [];
  const quoted = /["']([^"'\r\n]*(?:node_modules|bin)[^"'\r\n]*?\.(?:js|mjs|cjs|exe))["']/gi;
  for (const match of text.matchAll(quoted)) {
    candidates.push(expandShimPath(match[1], shimPath));
  }
  const target = candidates.find((candidate) => existsSync(candidate));
  if (!target) throw new Error(`Could not discover a native entrypoint from npm shim: ${shimPath}`);
  if (extname(target).toLowerCase() === '.exe') return { command: target, prefix: [], source: shimPath };
  const bundledNode = join(dirname(shimPath), 'node.exe');
  return { command: existsSync(bundledNode) ? bundledNode : process.execPath, prefix: [target], source: shimPath };
}

function entryFromPath(path) {
  const absolute = resolve(path);
  if (!existsSync(absolute)) throw new Error(`Configured executable does not exist: ${absolute}`);
  const ext = extname(absolute).toLowerCase();
  if (ext === '.cmd' || ext === '.ps1' || ext === '') {
    try {
      return parseNpmShim(absolute);
    } catch (error) {
      if (ext !== '') throw error;
    }
  }
  if (['.js', '.mjs', '.cjs'].includes(ext)) {
    return { command: process.execPath, prefix: [absolute], source: 'explicit-node-script' };
  }
  return { command: absolute, prefix: [], source: 'native-executable' };
}

function resolveEntrypoint(provider) {
  const override = process.env[provider === 'codex' ? 'AI_CODEX_BIN' : 'AI_CLAUDE_BIN'];
  if (override) return entryFromPath(override);
  const found = findOnPath(provider);
  if (found.length === 0) throw new Error(`${provider} CLI is unavailable on PATH`);

  // npm's .cmd/.ps1 wrappers require a shell. Read the wrapper and launch its
  // underlying JS/native target directly so user text never enters shell syntax.
  const shim = found.find((path) => ['.cmd', '.ps1'].includes(extname(path).toLowerCase()));
  if (shim) return parseNpmShim(shim);
  const native = found.find((path) => extname(path).toLowerCase() === '.exe') || found[0];
  return entryFromPath(native);
}

function atomicWrite(path, text) {
  mkdirSync(dirname(path), { recursive: true });
  const temp = `${path}.${process.pid}.${Math.random().toString(16).slice(2)}.tmp`;
  writeFileSync(temp, text, 'utf8');
  try {
    renameSync(temp, path);
  } catch (error) {
    if (process.platform !== 'win32' || !existsSync(path)) throw error;
    rmSync(path, { force: true });
    renameSync(temp, path);
  }
}

function stateText({ runId, phase, hypotheses = [], completed = [], pending = [], failed = [], nextAction }) {
  const section = (name, values) => `${name}:\n${values.length ? values.map((v) => `- ${v}`).join('\n') : '- none'}`;
  return [
    `CURRENT_RUN: ${runId}`,
    `CURRENT_PHASE: ${phase}`,
    section('ACTIVE_HYPOTHESES', hypotheses),
    section('COMPLETED_TASKS', completed),
    section('PENDING_TASKS', pending),
    section('FAILED_TASKS', failed),
    `NEXT_ACTION: ${nextAction || 'none'}`,
    '',
  ].join('\n');
}

function updateState(aiRoot, state) {
  atomicWrite(join(aiRoot, 'STATE.md'), stateText(state));
}

function nextInvocationDir(runDir, role) {
  const count = existsSync(runDir) ? readdirSync(runDir).filter((name) => /^\d{3}-/.test(name)).length : 0;
  const path = join(runDir, `${String(count + 1).padStart(3, '0')}-${safeLabel(role)}`);
  mkdirSync(path, { recursive: false });
  return path;
}

function makePrompt({ role, instruction, context }) {
  return `You are the ${role} in a controlled multi-agent analysis. Work only from the supplied context. Do not assume access to files, tools, prior conversations, or other agents unless their text appears below. Be explicit about uncertainty. Produce a self-contained answer.\n\nROLE INSTRUCTION\n${instruction}\n\nCONTEXT\n${context}\n\nCompletion protocol: finish your response with this exact marker on its own line:\n${COMPLETE_MARKER}\n`;
}

function recursivelyCollectModels(value, models = []) {
  if (!value || typeof value !== 'object') return models;
  for (const [key, child] of Object.entries(value)) {
    if ((key === 'model' || key === 'model_name' || key === 'modelName') && typeof child === 'string') models.push(child);
    else recursivelyCollectModels(child, models);
  }
  return models;
}

function extractModelUsage(events, requestedModel) {
  const modelUsage = {};
  for (const event of events) {
    if (!event?.modelUsage || typeof event.modelUsage !== 'object') continue;
    Object.assign(modelUsage, event.modelUsage);
  }
  return {
    modelUsage,
    auxiliaryModels: Object.keys(modelUsage).filter((model) => !matchesModel(requestedModel, model)),
  };
}

function parseJsonLines(text) {
  const events = [];
  const invalid = [];
  for (const line of text.split(/\r?\n/).filter((item) => item.trim())) {
    try { events.push(JSON.parse(line)); } catch { invalid.push(line); }
  }
  return { events, invalid };
}

function extractClaudeResult(events) {
  const event = [...events].reverse().find((item) => item?.type === 'result');
  if (!event) return { text: '', completeEvent: false, error: 'missing result event', event: null };
  const value = typeof event.result === 'string' ? event.result :
    typeof event.result?.text === 'string' ? event.result.text : '';
  const isError = event.is_error === true || event.subtype !== 'success' || event.error ||
    (event.terminal_reason && event.terminal_reason !== 'completed') || event.stop_reason === 'max_tokens';
  return { text: value, completeEvent: !isError, error: isError ? String(event.error || event.subtype || 'result error') : null, event };
}

function hasCodexCompletion(events) {
  return events.some((event) => ['turn.completed', 'turn_complete', 'response.completed'].includes(event?.type));
}

function codexFatalEvents(events) {
  // item.completed/item.type=error is often an advisory emitted alongside a
  // valid completion (for example a skill-budget warning), so only terminal or
  // top-level errors invalidate the run.
  return events.filter((event) => ['error', 'turn.failed', 'turn_failed', 'response.failed'].includes(event?.type));
}

function normalizedModel(value) {
  return String(value || '').trim().toLowerCase();
}

function matchesModel(requested, observed) {
  return normalizedModel(requested) === normalizedModel(observed);
}

async function killTree(child) {
  if (!child.pid) return;
  if (process.platform === 'win32') {
    spawnSync('taskkill.exe', ['/PID', String(child.pid), '/T', '/F'], { windowsHide: true, stdio: 'ignore' });
    return;
  }
  try { process.kill(-child.pid, 'SIGKILL'); } catch { try { child.kill('SIGKILL'); } catch {} }
}

function removeIsolatedDirectory(path) {
  const absolute = resolve(path);
  const tempRoot = resolve(tmpdir());
  const relativePrefix = `${tempRoot}${process.platform === 'win32' ? '\\' : '/'}`.toLowerCase();
  if (!absolute.toLowerCase().startsWith(relativePrefix) || !basename(absolute).startsWith('boxflow-agent-')) {
    throw new Error(`Refusing to remove unexpected isolation directory: ${absolute}`);
  }
  rmSync(absolute, { recursive: true, force: true });
}

async function runProcess({ command, argv, cwd, stdin, stdoutPath, stderrPath, timeoutMs, environmentOverrides = {} }) {
  return new Promise((resolvePromise) => {
    const started = Date.now();
    const stdoutStream = createWriteStream(stdoutPath, { flags: 'wx' });
    const stderrStream = createWriteStream(stderrPath, { flags: 'wx' });
    const stdout = [];
    const stderr = [];
    let timedOut = false;
    let settled = false;
    let spawnError = null;
    const child = spawn(command, argv, {
      cwd,
      env: { ...process.env, ...environmentOverrides },
      shell: false,
      windowsHide: true,
      detached: process.platform !== 'win32',
      stdio: ['pipe', 'pipe', 'pipe'],
    });
    child.stdout.on('data', (chunk) => { stdout.push(chunk); stdoutStream.write(chunk); });
    child.stderr.on('data', (chunk) => { stderr.push(chunk); stderrStream.write(chunk); });
    child.on('error', (error) => { spawnError = error; });
    const timer = setTimeout(async () => {
      timedOut = true;
      await killTree(child);
    }, timeoutMs);
    child.on('close', (exitCode, signal) => {
      if (settled) return;
      settled = true;
      clearTimeout(timer);
      stdoutStream.end(() => stderrStream.end(() => resolvePromise({
        exitCode,
        signal,
        timedOut,
        spawnError,
        stdout: Buffer.concat(stdout).toString('utf8'),
        stderr: Buffer.concat(stderr).toString('utf8'),
        durationMs: Date.now() - started,
      })));
    });
    child.stdin.on('error', () => {});
    child.stdin.end(stdin);
  });
}

function commandFor(provider, entry, { model, effort, outputFile, mcpConfig }) {
  if (provider === 'codex') {
    return {
      command: entry.command,
      argv: [
        ...entry.prefix,
        '-a', 'never',
        '-s', 'read-only',
        '--disable', 'plugins',
        '--disable', 'skill_search',
        '-c', 'skip_host_skill_discovery=true',
        '-c', 'project_doc_max_bytes=0',
        '-c', 'mcp_servers={}',
        'exec',
        '--model', model,
        '-c', `model_reasoning_effort=${effort}`,
        '--json',
        '--ephemeral',
        '--ignore-user-config',
        '--skip-git-repo-check',
        '-o', outputFile,
        '-',
      ],
    };
  }
  return {
    command: entry.command,
    argv: [
      ...entry.prefix,
      '-p',
      '--model', model,
      '--effort', effort,
      '--output-format', 'stream-json',
      '--verbose',
      '--tools', '',
      '--disable-slash-commands',
      '--safe-mode',
      '--system-prompt', 'You are a text-only analysis worker. Follow the user prompt exactly. Do not use tools, files, memory, skills, plugins, hooks, or external context.',
      '--settings', '{"disableAllHooks":true}',
      '--strict-mcp-config',
      '--mcp-config', mcpConfig,
      '--setting-sources', 'user',
      '--no-session-persistence',
    ],
  };
}

async function invokeAgent(config) {
  const { aiRoot, runId, provider, role, task = role, model, effort, contextSource, context, instruction, timeoutMs } = config;
  if (!['codex', 'claude'].includes(provider)) throw new Error(`Unsupported provider: ${provider}`);
  if (!['low', 'medium', 'high'].includes(effort)) throw new Error(`Unsupported effort: ${effort}`);
  const runDir = join(aiRoot, 'runs', runId);
  mkdirSync(runDir, { recursive: true });
  const invocationDir = nextInvocationDir(runDir, role);
  const stdoutPath = join(invocationDir, 'stdout.jsonl');
  const stderrPath = join(invocationDir, 'stderr.log');
  const resultPath = join(invocationDir, 'result.md');
  const promptPath = join(invocationDir, 'prompt.txt');
  const contextPath = join(invocationDir, 'context.txt');
  const metadataPath = join(invocationDir, 'metadata.json');
  const mcpConfig = join(invocationDir, 'empty-mcp.json');
  const prompt = makePrompt({ role, instruction, context });
  writeFileSync(promptPath, prompt, 'utf8');
  writeFileSync(contextPath, context, 'utf8');
  writeFileSync(mcpConfig, '{"mcpServers":{}}\n', 'utf8');

  atomicWrite(metadataPath, `${JSON.stringify({
    schemaVersion: 1,
    runId,
    timestamp: new Date().toISOString(),
    agent: role,
    agentTask: task,
    provider,
    requestedModel: model,
    observedModel: null,
    effort,
    prompt: { file: basename(promptPath), sha256: sha256(prompt) },
    context: { source: contextSource, file: basename(contextPath), sha256: sha256(context) },
    command: null,
    argv: [],
    exitCode: null,
    stdout: basename(stdoutPath),
    stderr: basename(stderrPath),
    durationMs: 0,
    status: 'starting',
  }, null, 2)}\n`);

  let entry;
  let command;
  let argv = [];
  let processResult = { exitCode: null, signal: null, timedOut: false, stdout: '', stderr: '', durationMs: 0 };
  let setupError = null;
  const environmentOverrides = provider === 'claude' ? {
    CLAUDE_CODE_DISABLE_NONESSENTIAL_TRAFFIC: '1',
    CLAUDE_CODE_DISABLE_TERMINAL_TITLE: '1',
  } : {};
  const timestamp = new Date().toISOString();
  try {
    entry = resolveEntrypoint(provider);
    ({ command, argv } = commandFor(provider, entry, { model, effort, outputFile: resultPath, mcpConfig }));
    const isolatedCwd = join(tmpdir(), `boxflow-agent-${runId}-${safeLabel(role)}-${Math.random().toString(16).slice(2)}`);
    mkdirSync(isolatedCwd, { recursive: true });
    const startingMetadata = JSON.parse(readFileSync(metadataPath, 'utf8'));
    atomicWrite(metadataPath, `${JSON.stringify({ ...startingMetadata, command, argv, cwd: isolatedCwd, status: 'running' }, null, 2)}\n`);
    try {
      processResult = await runProcess({ command, argv, cwd: isolatedCwd, stdin: prompt, stdoutPath, stderrPath, timeoutMs, environmentOverrides });
    } finally {
      removeIsolatedDirectory(isolatedCwd);
    }
  } catch (error) {
    setupError = error;
    if (!existsSync(stdoutPath)) writeFileSync(stdoutPath, '', 'utf8');
    if (!existsSync(stderrPath)) writeFileSync(stderrPath, `${error.stack || error}\n`, 'utf8');
  }

  const parsed = parseJsonLines(processResult.stdout);
  const allReportedModels = [...new Set(recursivelyCollectModels(parsed.events))];
  const diagnosticModels = allReportedModels.filter((value) => /^<.*>$/.test(value));
  const reportedModels = allReportedModels.filter((value) => !/^<.*>$/.test(value));
  const observedModel = reportedModels.length === 1 ? reportedModels[0] : null;
  const { modelUsage, auxiliaryModels } = extractModelUsage(parsed.events, model);
  let outputText = '';
  let protocolComplete = false;
  let protocolError = null;
  let permissionDenials = [];
  let fatalEvents = [];
  if (provider === 'codex') {
    outputText = existsSync(resultPath) ? readFileSync(resultPath, 'utf8') : '';
    protocolComplete = hasCodexCompletion(parsed.events);
    fatalEvents = codexFatalEvents(parsed.events);
    if (!protocolComplete) protocolError = 'missing Codex completion event';
  } else {
    const claude = extractClaudeResult(parsed.events);
    outputText = claude.text;
    protocolComplete = claude.completeEvent;
    protocolError = claude.error;
    permissionDenials = Array.isArray(claude.event?.permission_denials) ? claude.event.permission_denials : [];
    writeFileSync(resultPath, outputText, 'utf8');
  }

  const outputHasMarker = outputText.trimEnd().endsWith(COMPLETE_MARKER);
  const cleanOutput = outputHasMarker ? outputText.trimEnd().slice(0, -COMPLETE_MARKER.length).trimEnd() : outputText;
  if (outputHasMarker) writeFileSync(resultPath, `${cleanOutput}\n`, 'utf8');
  const failureReasons = [];
  const failureCodes = [];
  const fail = (code, reason) => { failureCodes.push(code); failureReasons.push(reason); };
  const combinedDiagnostics = `${processResult.stderr}\n${processResult.stdout}`;
  if (setupError || processResult.spawnError) fail('TOOL_UNAVAILABLE', `unavailable: ${setupError?.message || processResult.spawnError?.message}`);
  if (processResult.timedOut) fail('TIMEOUT', 'timeout');
  if (processResult.exitCode !== 0) {
    if (/hit your usage limit|quota exceeded|usage_limit_reached|insufficient_quota/i.test(combinedDiagnostics)) {
      fail('USAGE_LIMIT', `exit code ${processResult.exitCode}: provider usage limit`);
    } else if (/auth(?:entication|orization)?\s+(?:failed|required)|not logged in|login required|invalid api key|unauthorized/i.test(combinedDiagnostics)) {
      fail('AUTH_FAILED', `exit code ${processResult.exitCode}: authentication failure`);
    } else if (/(?:model).*(?:not found|does not exist|unavailable|unsupported|invalid)|(?:unknown|invalid) model/i.test(combinedDiagnostics)) {
      fail('MODEL_UNAVAILABLE', `exit code ${processResult.exitCode}: requested model unavailable`);
    } else {
      fail('PROCESS_ERROR', `exit code ${processResult.exitCode}`);
    }
  }
  if (parsed.invalid.length) fail('INCOMPLETE', `invalid stream JSON (${parsed.invalid.length} line(s))`);
  if (!protocolComplete) fail('INCOMPLETE', `incomplete protocol: ${protocolError || 'completion event absent'}`);
  if (fatalEvents.length) fail('PROCESS_ERROR', `fatal CLI event: ${fatalEvents.map((event) => event.type).join(', ')}`);
  if (permissionDenials.length) fail('TOOL_UNAVAILABLE', `Claude reported ${permissionDenials.length} permission denial(s)`);
  if (!cleanOutput.trim()) fail('INCOMPLETE', 'empty output');
  if (!outputHasMarker) fail('INCOMPLETE', 'incomplete output: completion marker absent');
  if (reportedModels.length > 1) fail('MODEL_MISMATCH', `ambiguous observed models: ${reportedModels.join(', ')}`);
  if (observedModel && !matchesModel(model, observedModel)) fail('MODEL_MISMATCH', `model mismatch: requested ${model}, observed ${observedModel}`);
  if (provider === 'claude' && !observedModel) fail('MODEL_UNVERIFIED', 'Claude did not report an unambiguous primary model');

  const status = failureReasons.length ? 'failed' : 'completed';
  const metadata = {
    schemaVersion: 1,
    runId,
    timestamp,
    agent: role,
    agentTask: task,
    provider,
    requestedModel: model,
    observedModel,
    observedModelSource: observedModel ? 'cli-json-stream' : 'not-reported-by-cli',
    auxiliaryModels,
    modelUsage,
    diagnosticModels,
    effort,
    prompt: { file: basename(promptPath), sha256: sha256(prompt) },
    context: { source: contextSource, file: basename(contextPath), sha256: sha256(context) },
    command: command || null,
    argv,
    entrypointSource: entry?.source || null,
    environmentOverrides: Object.keys(environmentOverrides),
    exitCode: processResult.exitCode,
    signal: processResult.signal,
    stdout: basename(stdoutPath),
    stderr: basename(stderrPath),
    result: basename(resultPath),
    resultSha256: sha256(cleanOutput.trim()),
    durationMs: processResult.durationMs,
    timedOut: processResult.timedOut,
    protocolComplete,
    completionMarkerPresent: outputHasMarker,
    status,
    failureCode: failureCodes[0] || null,
    failureCodes: [...new Set(failureCodes)],
    failureReasons,
  };
  atomicWrite(metadataPath, `${JSON.stringify(metadata, null, 2)}\n`);
  return { metadata, output: cleanOutput, invocationDir };
}

function appendManifest(aiRoot, runId, record) {
  const path = join(aiRoot, 'runs', runId, 'manifest.json');
  let manifest = { runId, createdAt: new Date().toISOString(), invocations: [], status: 'running' };
  if (existsSync(path)) manifest = JSON.parse(readFileSync(path, 'utf8'));
  manifest.invocations.push({
    agent: record.metadata.agent,
    status: record.metadata.status,
    requestedModel: record.metadata.requestedModel,
    observedModel: record.metadata.observedModel,
    directory: basename(record.invocationDir),
  });
  manifest.updatedAt = new Date().toISOString();
  if (record.metadata.status === 'failed') manifest.status = 'failed';
  atomicWrite(path, `${JSON.stringify(manifest, null, 2)}\n`);
}

async function runOne(options) {
  if (!options.context || !options.role) throw new Error('invoke requires --context and --role');
  const workspace = resolve(options.workspace || DEFAULT_WORKSPACE);
  const aiRoot = join(workspace, '.ai');
  const runId = safeRunId(options['run-id']);
  const defaults = ROLE_DEFAULTS[options.role] || {};
  const provider = options.provider || defaults.provider;
  const model = options.model || defaults.model;
  const effort = options.effort || defaults.effort;
  if (!provider || !model || !effort) throw new Error('Custom roles require --provider, --model, and --effort');
  const source = readRequiredFile(options.context, 'Context');
  let instruction = options.prompt || `Analyze the supplied task as ${options.role}. Return concrete findings and next actions.`;
  if (options['prompt-file']) instruction = readRequiredFile(options['prompt-file'], 'Prompt file').text;
  if (!options['no-state']) updateState(aiRoot, { runId, phase: 'single-invocation', pending: [options.role], nextAction: `Run ${options.role}` });
  const timeoutMs = Number(options['timeout-ms'] || DEFAULT_TIMEOUT_MS);
  if (!Number.isFinite(timeoutMs) || timeoutMs <= 0) throw new Error('--timeout-ms must be a positive number');
  const result = await invokeAgent({ aiRoot, runId, provider, role: options.role, model, effort, contextSource: source.absolute, context: source.text, instruction, timeoutMs });
  appendManifest(aiRoot, runId, result);
  const manifestPath = join(aiRoot, 'runs', runId, 'manifest.json');
  const manifest = JSON.parse(readFileSync(manifestPath, 'utf8'));
  manifest.status = result.metadata.status;
  manifest[result.metadata.status === 'completed' ? 'completedAt' : 'failedAt'] = new Date().toISOString();
  if (result.metadata.status === 'completed') manifest.finalResult = join(basename(result.invocationDir), 'result.md');
  atomicWrite(manifestPath, `${JSON.stringify(manifest, null, 2)}\n`);
  if (!options['no-state']) updateState(aiRoot, {
    runId,
    phase: result.metadata.status,
    completed: result.metadata.status === 'completed' ? [options.role] : [],
    failed: result.metadata.status === 'failed' ? [`${options.role}: ${result.metadata.failureReasons.join('; ')}`] : [],
    nextAction: result.metadata.status === 'completed' ? 'Review result' : 'Resolve failure before continuing',
  });
  process.stdout.write(`${JSON.stringify({ runId, status: result.metadata.status, result: join(result.invocationDir, 'result.md'), metadata: join(result.invocationDir, 'metadata.json') })}\n`);
  if (result.metadata.status !== 'completed') process.exitCode = 1;
}

function bundleOutputs(label, records) {
  return records.map((record, index) => `## ${label} ${index + 1}: ${record.metadata.agent}\n${record.output}`).join('\n\n');
}

function loadResumeHistory(aiRoot, runId, stages) {
  const runDir = join(aiRoot, 'runs', runId);
  const records = new Map();
  const failures = [];
  if (!existsSync(runDir)) return { records, failures };
  let stageIndex = 0;
  const directories = readdirSync(runDir).filter((name) => /^\d{3}-/.test(name)).sort();
  for (const directory of directories) {
    const invocationDir = join(runDir, directory);
    const metadataPath = join(invocationDir, 'metadata.json');
    if (!existsSync(metadataPath)) continue;
    const metadata = JSON.parse(readFileSync(metadataPath, 'utf8'));
    const current = stages[stageIndex];
    const task = metadata.agentTask || (current?.role === metadata.agent ? current.task : null);
    if (metadata.status === 'failed') {
      failures.push(`${task || metadata.agent}: prior attempt ${metadata.failureCode || 'FAILED'} (${(metadata.failureReasons || []).join('; ')})`);
      continue;
    }
    if (metadata.status !== 'completed' || !task) continue;
    records.set(task, {
      metadata,
      output: existsSync(join(invocationDir, 'result.md')) ? readFileSync(join(invocationDir, 'result.md'), 'utf8').trim() : '',
      invocationDir,
      reused: true,
    });
    if (current?.task === task) stageIndex += 1;
  }
  return { records, failures };
}

function validateResumeRecord(record, { defaults, role, context, instruction, task }) {
  const expectedPrompt = makePrompt({ role, instruction, context });
  const mismatches = [];
  if (record.metadata.agent !== role) mismatches.push('role');
  if (record.metadata.provider !== defaults.provider) mismatches.push('provider');
  if (record.metadata.requestedModel !== defaults.model) mismatches.push('requested model');
  if (record.metadata.effort !== defaults.effort) mismatches.push('effort');
  if (record.metadata.context?.sha256 !== sha256(context)) mismatches.push('context hash');
  if (record.metadata.prompt?.sha256 !== sha256(expectedPrompt)) mismatches.push('prompt hash');
  if (!record.metadata.protocolComplete || !record.metadata.completionMarkerPresent || !record.output.trim()) mismatches.push('completion validation');
  if (record.metadata.observedModel && !matchesModel(defaults.model, record.metadata.observedModel)) mismatches.push('observed model');
  if (record.metadata.exitCode !== 0 || record.metadata.status !== 'completed') mismatches.push('successful exit');
  if (readFileSync(join(record.invocationDir, 'prompt.txt'), 'utf8') !== expectedPrompt) mismatches.push('archived prompt');
  if (readFileSync(join(record.invocationDir, 'context.txt'), 'utf8') !== context) mismatches.push('archived context');
  const parsed = parseJsonLines(readFileSync(join(record.invocationDir, 'stdout.jsonl'), 'utf8'));
  const rawOutput = defaults.provider === 'claude'
    ? extractClaudeResult(parsed.events).text
    : [...parsed.events].reverse().find((event) => event.type === 'item.completed' && event.item?.type === 'agent_message')?.item.text || '';
  const rawComplete = defaults.provider === 'claude'
    ? extractClaudeResult(parsed.events).completeEvent
    : hasCodexCompletion(parsed.events) && codexFatalEvents(parsed.events).length === 0;
  const rawHasMarker = rawOutput.trimEnd().endsWith(COMPLETE_MARKER);
  const rawClean = rawHasMarker ? rawOutput.trimEnd().slice(0, -COMPLETE_MARKER.length).trim() : '';
  if (parsed.invalid.length || !rawComplete || !rawHasMarker || rawClean !== record.output.trim()) mismatches.push('raw stream/result integrity');
  if (record.metadata.resultSha256 && record.metadata.resultSha256 !== sha256(record.output.trim())) mismatches.push('result hash');
  if (mismatches.length) throw new Error(`Cannot resume ${task}; prior completed record differs in ${mismatches.join(', ')}`);
}

async function smoke(options) {
  if (!options.context) throw new Error('smoke requires --context');
  if (options.resume && !options['run-id']) throw new Error('--resume requires --run-id');
  const workspace = resolve(options.workspace || DEFAULT_WORKSPACE);
  const aiRoot = join(workspace, '.ai');
  const runId = safeRunId(options['run-id']);
  const source = readRequiredFile(options.context, 'Context');
  const timeoutMs = Number(options['timeout-ms'] || DEFAULT_TIMEOUT_MS);
  if (!Number.isFinite(timeoutMs) || timeoutMs <= 0) throw new Error('--timeout-ms must be a positive number');
  const stages = [
    { role: 'astra', task: 'Astra plan' },
    { role: 'engineer', task: 'engineer blind analysis' },
    { role: 'investigator', task: 'investigator blind analysis' },
    { role: 'researcher', task: 'researcher blind analysis' },
    ...(options['cross-review'] ? [
      { role: 'engineer', task: 'engineer cross-review' },
      { role: 'investigator', task: 'investigator cross-review' },
    ] : []),
    { role: 'astra', task: 'Astra arbitration' },
  ];
  const history = options.resume ? loadResumeHistory(aiRoot, runId, stages) : { records: new Map(), failures: [] };
  const runDir = join(aiRoot, 'runs', runId);
  if (!options.resume && existsSync(join(runDir, 'manifest.json'))) throw new Error(`Run ${runId} already exists; choose a new --run-id or use --resume`);
  const completed = [];
  const failed = [...history.failures];
  const pending = stages.map(({ task }) => task);
  const invoke = async (role, context, instruction, task) => {
    const defaults = ROLE_DEFAULTS[role];
    if (!options['no-state']) updateState(aiRoot, { runId, phase: `running ${task}`, completed, pending: [...pending], failed, nextAction: task });
    const reusable = history.records.get(task);
    if (reusable) {
      validateResumeRecord(reusable, { defaults, role, context, instruction, task });
      const index = pending.indexOf(task);
      if (index >= 0) pending.splice(index, 1);
      completed.push(`${task} (reused)`);
      if (!options['no-state']) updateState(aiRoot, { runId, phase: `reused ${task}`, completed, pending: [...pending], failed, nextAction: pending[0] || 'Review final result' });
      return reusable;
    }
    const result = await invokeAgent({ aiRoot, runId, ...defaults, role, task, contextSource: source.absolute, context, instruction, timeoutMs });
    appendManifest(aiRoot, runId, result);
    const index = pending.indexOf(task);
    if (index >= 0 && result.metadata.status === 'completed') pending.splice(index, 1);
    (result.metadata.status === 'completed' ? completed : failed).push(result.metadata.status === 'completed' ? task : `${task}: ${result.metadata.failureCode || 'FAILED'} (${result.metadata.failureReasons.join('; ')})`);
    if (!options['no-state']) updateState(aiRoot, { runId, phase: result.metadata.status === 'completed' ? `completed ${task}` : `failed ${task}`, completed, pending: [...pending], failed, nextAction: result.metadata.status === 'completed' ? (pending[0] || 'Review final result') : 'Stop: resolve failed agent' });
    if (result.metadata.status !== 'completed') throw new Error(`${role} failed: ${result.metadata.failureReasons.join('; ')}`);
    return result;
  };

  if (!options['no-state']) updateState(aiRoot, { runId, phase: options.resume ? 'resuming' : 'planning', pending: [...pending], failed, nextAction: pending[0] });
  const plan = await invoke('astra', source.text, 'Create a compact investigation plan. Identify decision criteria, unknowns, and assignments for an engineer, investigator, and researcher. Do not solve the task yet.', 'Astra plan');
  const blindContext = `${source.text}\n\nASTRA PLAN\n${plan.output}`;
  const specialistSpecs = [
    ['engineer', 'Independently analyze implementation feasibility, technical risks, and concrete validation steps. Do not speculate about other specialists.'],
    ['investigator', 'Independently challenge assumptions, seek failure modes, and explain the strongest evidence needed. Do not speculate about other specialists.'],
    ['researcher', 'Independently organize relevant facts, gaps, and testable hypotheses. Do not speculate about other specialists.'],
  ];
  const specialistResults = [];
  // Sequential execution avoids interleaved credential prompts while keeping each
  // specialist blind to peer output. Their prompt contexts are otherwise identical.
  for (const [role, instruction] of specialistSpecs) specialistResults.push(await invoke(role, blindContext, instruction, `${role} blind analysis`));

  let reviews = [];
  if (options['cross-review']) {
    const engineer = specialistResults.find((result) => result.metadata.agent === 'engineer');
    const investigator = specialistResults.find((result) => result.metadata.agent === 'investigator');
    reviews = [
      await invoke('engineer', `${source.text}\n\nANONYMOUS PEER FINDING\n${investigator.output}`, 'Cross-critique the anonymous peer finding. Identify agreements, contradictions, unsupported claims, and decisive tests.', 'engineer cross-review'),
      await invoke('investigator', `${source.text}\n\nANONYMOUS PEER FINDING\n${engineer.output}`, 'Cross-critique the anonymous peer finding. Identify agreements, contradictions, unsupported claims, and decisive tests.', 'investigator cross-review'),
    ];
  }

  const arbitrationContext = [source.text, 'ASTRA PLAN', plan.output, 'BLIND SPECIALIST ROUND', bundleOutputs('Specialist', specialistResults), ...(reviews.length ? ['CROSS-CRITIQUES', bundleOutputs('Review', reviews)] : [])].join('\n\n');
  const arbitration = await invoke('astra', arbitrationContext, 'Arbitrate the evidence. Resolve contradictions, reject unsupported claims, state remaining uncertainty, and produce a concrete final recommendation with verification steps.', 'Astra arbitration');
  const manifestPath = join(aiRoot, 'runs', runId, 'manifest.json');
  const manifest = JSON.parse(readFileSync(manifestPath, 'utf8'));
  manifest.status = 'completed';
  manifest.completedAt = new Date().toISOString();
  manifest.finalResult = join(basename(arbitration.invocationDir), 'result.md');
  atomicWrite(manifestPath, `${JSON.stringify(manifest, null, 2)}\n`);
  if (!options['no-state']) updateState(aiRoot, { runId, phase: 'completed', completed, failed, nextAction: 'Review Astra arbitration' });
  process.stdout.write(`${JSON.stringify({ runId, status: 'completed', result: join(arbitration.invocationDir, 'result.md'), manifest: manifestPath })}\n`);
}

async function main() {
  let options;
  try { options = parseArgs(process.argv.slice(2)); } catch (error) { process.stderr.write(`${error.message}\n`); usage(2); }
  if (options.help) usage(0);
  const command = options._[0];
  if (!['invoke', 'smoke'].includes(command)) usage(2);
  try {
    if (command === 'invoke') await runOne(options);
    else await smoke(options);
  } catch (error) {
    process.stderr.write(`orchestration failed: ${error.stack || error}\n`);
    process.exitCode = 1;
  }
}

if (process.argv[1] && resolve(process.argv[1]) === resolve(fileURLToPath(import.meta.url))) await main();

export { COMPLETE_MARKER, ROLE_DEFAULTS, invokeAgent, parseNpmShim, resolveEntrypoint, stateText };
