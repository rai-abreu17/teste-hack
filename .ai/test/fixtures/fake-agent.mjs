#!/usr/bin/env node

// TEST FIXTURE ONLY. This process emulates CLI envelopes; it never calls a model.
import { writeFileSync } from 'node:fs';

const args = process.argv.slice(2);
const mode = process.env.FAKE_AGENT_MODE || 'success';
const isCodex = args.includes('exec');
const modelIndex = args.indexOf('--model');
const requested = modelIndex >= 0 ? args[modelIndex + 1] : 'unknown';
const observed = mode === 'mismatch' ? 'definitely-the-wrong-model' : requested;
const marker = mode === 'incomplete' ? '' : '\n<<ORCHESTRATION_COMPLETE>>';

let input = '';
process.stdin.resume();
process.stdin.setEncoding('utf8');
process.stdin.on('data', (chunk) => { input += chunk; });
process.stdin.on('end', () => {
  if (process.env.FAKE_AGENT_FAIL_ROLE && input.startsWith(`You are the ${process.env.FAKE_AGENT_FAIL_ROLE} `)) {
    process.stderr.write(`TEST FIXTURE forced ${process.env.FAKE_AGENT_FAIL_ROLE} failure\n`);
    process.exitCode = 9;
    return;
  }
  if (mode === 'auth') {
    process.stderr.write('TEST FIXTURE authentication failed\n');
    process.exitCode = 7;
    return;
  }
  if (mode === 'quota') {
    process.stderr.write("TEST FIXTURE You've hit your usage limit.\n");
    process.exitCode = 1;
    return;
  }
  if (mode === 'model-unavailable') {
    process.stderr.write('TEST FIXTURE requested model not found\n');
    process.exitCode = 8;
    return;
  }
  if (mode === 'empty') {
    if (isCodex) process.stdout.write(`${JSON.stringify({ type: 'turn.completed', model: observed })}\n`);
    else process.stdout.write(`${JSON.stringify({ type: 'result', subtype: 'success', is_error: false, model: observed, result: '' })}\n`);
    return;
  }
  const answer = `fake answer${marker}`;
  if (isCodex) {
    const outputIndex = args.indexOf('-o');
    if (outputIndex >= 0) writeFileSync(args[outputIndex + 1], answer, 'utf8');
    process.stdout.write(`${JSON.stringify({ type: 'thread.started', model: observed })}\n`);
    process.stdout.write(`${JSON.stringify({ type: 'item.completed', item: { type: 'agent_message', text: answer } })}\n`);
    if (mode === 'fatal') process.stdout.write(`${JSON.stringify({ type: 'turn.failed', error: 'TEST FIXTURE fatal event' })}\n`);
    if (mode !== 'no-completion') process.stdout.write(`${JSON.stringify({ type: 'turn.completed' })}\n`);
  } else {
    process.stdout.write(`${JSON.stringify({ type: 'system', subtype: 'init', model: observed })}\n`);
    if (mode !== 'no-completion') process.stdout.write(`${JSON.stringify({ type: 'result', subtype: 'success', is_error: false, result: answer, permission_denials: mode === 'permission' ? [{ tool: 'TEST FIXTURE' }] : [] })}\n`);
  }
});
