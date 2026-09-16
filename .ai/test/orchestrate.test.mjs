import assert from 'node:assert/strict';
import { mkdtempSync, mkdirSync, readFileSync, writeFileSync, readdirSync } from 'node:fs';
import { tmpdir } from 'node:os';
import { dirname, join, resolve } from 'node:path';
import { spawnSync } from 'node:child_process';
import test from 'node:test';
import { fileURLToPath } from 'node:url';

const here = dirname(fileURLToPath(import.meta.url));
const runner = resolve(here, '..', 'orchestrate.mjs');
const fake = resolve(here, 'fixtures', 'fake-agent.mjs');

function invoke(mode = 'success', extra = []) {
  const workspace = mkdtempSync(join(tmpdir(), 'boxflow-orchestrator-test-'));
  mkdirSync(join(workspace, '.ai'), { recursive: true });
  const context = join(workspace, 'context.txt');
  writeFileSync(context, 'Explicit fake test context.', 'utf8');
  const result = spawnSync(process.execPath, [runner, 'invoke', '--role', 'engineer', '--context', context, '--workspace', workspace, '--run-id', `fake-${mode}`, '--no-state', ...extra], {
    encoding: 'utf8',
    env: { ...process.env, AI_CODEX_BIN: fake, AI_CLAUDE_BIN: fake, FAKE_AGENT_MODE: mode },
  });
  const roleIndex = extra.lastIndexOf('--role');
  const role = roleIndex >= 0 ? extra[roleIndex + 1] : 'engineer';
  const metadata = JSON.parse(readFileSync(join(workspace, '.ai', 'runs', `fake-${mode}`, `001-${role}`, 'metadata.json'), 'utf8'));
  return { result, metadata, workspace };
}

test('fake success records exact model, argv, streams, and completed status', () => {
  const { result, metadata } = invoke();
  assert.equal(result.status, 0, result.stderr);
  assert.equal(metadata.status, 'completed');
  assert.equal(metadata.requestedModel, 'gpt-5.6-sol');
  assert.equal(metadata.observedModel, 'gpt-5.6-sol');
  assert.ok(metadata.argv.includes('gpt-5.6-sol'));
  assert.equal(metadata.completionMarkerPresent, true);
});

for (const [mode, expected] of [
  ['auth', 'exit code 7'],
  ['empty', 'empty output'],
  ['incomplete', 'completion marker absent'],
  ['no-completion', 'incomplete protocol'],
  ['mismatch', 'model mismatch'],
  ['model-unavailable', 'requested model unavailable'],
  ['fatal', 'fatal CLI event'],
]) {
  test(`fake ${mode} fails closed`, () => {
    const { result, metadata } = invoke(mode);
    assert.notEqual(result.status, 0);
    assert.equal(metadata.status, 'failed');
    assert.match(metadata.failureReasons.join(' | '), new RegExp(expected));
  });
}

test('fake auth failure has a machine-readable AUTH_FAILED code', () => {
  const { metadata } = invoke('auth');
  assert.equal(metadata.failureCode, 'AUTH_FAILED');
  assert.ok(metadata.failureCodes.includes('INCOMPLETE'));
});

test('fake unavailable model has a machine-readable MODEL_UNAVAILABLE code', () => {
  const { metadata } = invoke('model-unavailable');
  assert.equal(metadata.failureCode, 'MODEL_UNAVAILABLE');
});

test('fake Claude permission denial fails closed', () => {
  const { result, metadata } = invoke('permission', ['--role', 'investigator']);
  assert.notEqual(result.status, 0);
  assert.ok(metadata.failureCodes.includes('TOOL_UNAVAILABLE'));
});

test('missing configured executable fails as unavailable and still writes metadata', () => {
  const workspace = mkdtempSync(join(tmpdir(), 'boxflow-orchestrator-test-'));
  mkdirSync(join(workspace, '.ai'), { recursive: true });
  const context = join(workspace, 'context.txt');
  writeFileSync(context, 'Explicit fake test context.', 'utf8');
  const missing = join(workspace, 'does-not-exist.exe');
  const result = spawnSync(process.execPath, [runner, 'invoke', '--role', 'engineer', '--context', context, '--workspace', workspace, '--run-id', 'fake-unavailable', '--no-state'], {
    encoding: 'utf8',
    env: { ...process.env, AI_CODEX_BIN: missing },
  });
  assert.notEqual(result.status, 0);
  const metadata = JSON.parse(readFileSync(join(workspace, '.ai', 'runs', 'fake-unavailable', '001-engineer', 'metadata.json'), 'utf8'));
  assert.equal(metadata.status, 'failed');
  assert.equal(metadata.failureCode, 'TOOL_UNAVAILABLE');
  assert.match(metadata.failureReasons.join(' | '), /unavailable/);
});

test('fake usage limit is classified without model substitution', () => {
  const { metadata } = invoke('quota');
  assert.equal(metadata.failureCode, 'USAGE_LIMIT');
  assert.equal(metadata.requestedModel, 'gpt-5.6-sol');
});

function fakeWorkflow() {
  const workspace = mkdtempSync(join(tmpdir(), 'boxflow-orchestrator-test-'));
  const context = join(workspace, 'context.txt');
  writeFileSync(context, 'FAKE FIXTURE ONLY: bounded geometry task.');
  const runDir = join(workspace, '.ai', 'runs', 'fake-resume');
  const call = (resume, failRole = '') => spawnSync(process.execPath, [runner, 'smoke', '--context', context, '--workspace', workspace, '--run-id', 'fake-resume', '--cross-review', ...(resume ? ['--resume'] : [])], {
    encoding: 'utf8', timeout: 20000,
    env: { ...process.env, AI_CODEX_BIN: fake, AI_CLAUDE_BIN: fake, FAKE_AGENT_MODE: 'success', FAKE_AGENT_FAIL_ROLE: failRole },
  });
  return { call, runDir, workspace };
}

test('resume reuses successful stages, preserves failure, and does not call models again after completion', () => {
  const { call, runDir, workspace } = fakeWorkflow();
  assert.notEqual(call(false, 'researcher').status, 0);
  const original = readFileSync(join(runDir, '001-astra', 'metadata.json'), 'utf8');
  const resumed = call(true);
  assert.equal(resumed.status, 0, resumed.stderr);
  assert.equal(readFileSync(join(runDir, '001-astra', 'metadata.json'), 'utf8'), original);
  const count = () => readdirSync(runDir).filter(name => /^\d{3}-/.test(name)).length;
  assert.equal(count(), 8);
  assert.equal(call(true).status, 0);
  assert.equal(count(), 8, 'completed calls must never be repeated');
  assert.match(readFileSync(join(workspace, '.ai', 'STATE.md'), 'utf8'), /prior attempt/);
});

test('resume rejects changed saved answer before running another process', () => {
  const { call, runDir } = fakeWorkflow();
  assert.equal(call(false).status, 0);
  writeFileSync(join(runDir, '001-astra', 'result.md'), 'tampered answer');
  const result = call(true);
  assert.notEqual(result.status, 0);
  assert.match(result.stderr, /raw stream\/result integrity|result hash/);
  assert.equal(readdirSync(runDir).filter(name => /^\d{3}-/.test(name)).length, 7);
});
