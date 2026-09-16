import fs from 'node:fs';
import path from 'node:path';
import os from 'node:os';
import crypto from 'node:crypto';
import {spawnSync,spawn} from 'node:child_process';

const root = process.cwd();
const run = path.join(root, '.ai', 'runs', 'bootstrap-20260913');
fs.mkdirSync(run, {recursive:true});
const npm = path.join(process.env.APPDATA, 'npm', 'node_modules');
const claude = path.join(npm, '@anthropic-ai', 'claude-code', 'bin', 'claude.exe');
const codex = path.join(npm, '@openai', 'codex', 'bin', 'codex.js');
if (process.argv[2] === 'probe') {
  const role = process.argv[3];
  const models = {astra:['gpt-6-astra','high'],sol:['gpt-5.6-sol','high'],opus:['claude-opus-5','high'],sonnet:['claude-sonnet-5','medium']};
  if (!models[role]) throw new Error('Unknown probe role');
  const [model,effort] = models[role];
  const dir = path.join(run,`probe-${role}-${Date.now()}`);
  fs.mkdirSync(dir);
  const cwd = fs.mkdtempSync(path.join(os.tmpdir(),'boxflow-probe-'));
  const prompt = 'Teste de infraestrutura: responda somente à pergunta matemática fornecida, sem ferramentas, leitura ou gravação de arquivos e sem delegar. Qual o volume em litros de uma caixa com base de 30 cm por 30 cm e preenchimento uniforme de 12 cm? Inclua a conta em uma frase. Não declare sua identidade de modelo.';
  fs.writeFileSync(path.join(dir,'prompt.md'),prompt);
  fs.writeFileSync(path.join(dir,'context.md'),'Geometria ideal; nenhuma informação ou arquivo do projeto é necessário.');
  fs.writeFileSync(path.join(cwd,'empty-mcp.json'),'{"mcpServers":{}}');
  const isClaude = role==='opus'||role==='sonnet';
  const exe = isClaude?claude:process.execPath;
  const args = isClaude?['-p','--model',model,'--effort',effort,'--output-format','stream-json','--verbose','--tools','','--strict-mcp-config','--mcp-config',path.join(cwd,'empty-mcp.json'),'--no-session-persistence','--setting-sources','user']: [codex,'-a','never','exec','--model',model,'-c',`model_reasoning_effort=${effort}`,'--json','--ephemeral','--ignore-user-config','--skip-git-repo-check','-c','project_doc_max_bytes=0','-o',path.join(dir,'result.md'),'-'];
  const started=Date.now();
  const record={RUN_ID:path.basename(run),TIMESTAMP:new Date(started).toISOString(),AGENT:role,MODEL:model,EFFORT:effort,PROMPT_FILE:path.join(dir,'prompt.md'),CONTEXT_FILE:path.join(dir,'context.md'),COMMAND:[exe,...args],EXIT_CODE:null,STDOUT_FILE:path.join(dir,'stdout.jsonl'),STDERR_FILE:path.join(dir,'stderr.txt'),DURATION_MS:null,STATUS:'RUNNING',CWD:cwd};
  fs.writeFileSync(path.join(dir,'execution.json'),JSON.stringify(record,null,2));
  const out=fs.openSync(record.STDOUT_FILE,'w'),err=fs.openSync(record.STDERR_FILE,'w');
  const child=spawn(exe,args,{cwd,windowsHide:true,stdio:['pipe',out,err]});
  let timeout=false;
  const timer=setTimeout(()=>{timeout=true;spawnSync('taskkill.exe',['/PID',String(child.pid),'/T','/F'],{windowsHide:true});},180000);
  child.stdin.on('error',()=>{});
  child.stdin.end(prompt);
  child.on('error',e=>{record.ERROR=e.message;});
  await new Promise(resolve=>child.on('close',(code,signal)=>{clearTimeout(timer);fs.closeSync(out);fs.closeSync(err);record.EXIT_CODE=code;record.SIGNAL=signal;record.DURATION_MS=Date.now()-started;record.STATUS=timeout?'TIMEOUT':code===0?'COMPLETED_PENDING_VALIDATION':'CLI_ERROR';fs.writeFileSync(path.join(dir,'execution.json'),JSON.stringify(record,null,2));resolve();}));
  console.log(JSON.stringify({dir,status:record.STATUS,exit:record.EXIT_CODE}));
  console.log(fs.readFileSync(record.STDOUT_FILE,'utf8').slice(-14000));
  console.log(fs.readFileSync(record.STDERR_FILE,'utf8').slice(-3000));
}
if (process.argv[2] === 'preflight') {
  const commands = [
    ['claude-version', claude, ['--version']], ['claude-help',claude,['--help']],
    ['codex-version',process.execPath,[codex,'--version']], ['codex-help',process.execPath,[codex,'--help']],
    ['codex-exec-help',process.execPath,[codex,'exec','--help']],
  ];
  const records = [];
  for (const [name, exe, args] of commands) {
    const started = Date.now();
    const result = spawnSync(exe,args,{encoding:'utf8',windowsHide:true,timeout:30000});
    fs.writeFileSync(path.join(run,name+'.stdout.txt'),result.stdout ?? '');
    fs.writeFileSync(path.join(run,name+'.stderr.txt'),result.stderr ?? String(result.error ?? ''));
    records.push({RUN_ID:path.basename(run),TIMESTAMP:new Date(started).toISOString(),AGENT:'PREFLIGHT_NO_MODEL',MODEL:null,EFFORT:null,PROMPT_FILE:null,CONTEXT_FILE:null,COMMAND:[exe,...args],EXIT_CODE:result.status,STDOUT_FILE:name+'.stdout.txt',STDERR_FILE:name+'.stderr.txt',DURATION_MS:Date.now()-started,STATUS:result.status===0?'SUCCESS':'CLI_ERROR'});
  }
  fs.writeFileSync(path.join(run,'preflight.json'),JSON.stringify(records,null,2));
  const snapshot = {};
  function walk(dir) { for(const entry of fs.readdirSync(dir,{withFileTypes:true})) {
    if (entry.name === '.ai') continue;
    const file = path.join(dir,entry.name);
    if(entry.isDirectory()) walk(file);
    else if(entry.isFile()) snapshot[path.relative(root,file)] = crypto.createHash('sha256').update(fs.readFileSync(file)).digest('hex');
  }}
  walk(root);
  fs.writeFileSync(path.join(run,'application-before.json'),JSON.stringify(snapshot,null,2));
  console.log(JSON.stringify({preflight:records.map(r=>[r.AGENT,r.STDOUT_FILE,r.STATUS]),snapshotFiles:Object.keys(snapshot).length}));
}
if (process.argv[2] === 'context7' || process.argv[2] === 'context7-codex') {
  const endpoint = 'https://mcp.context7.com/mcp';
  let session;
  async function rpc(id,method,params) {
    const response = await fetch(endpoint,{method:'POST',headers:{'Content-Type':'application/json','Accept':'application/json, text/event-stream',...(session?{'Mcp-Session-Id':session}:{})},body:JSON.stringify({jsonrpc:'2.0',id,method,params}),signal:AbortSignal.timeout(45000)});
    session = response.headers.get('mcp-session-id') ?? session;
    const raw = await response.text();
    fs.writeFileSync(path.join(run,`context7-${id}.txt`),raw);
    if (!response.ok) throw new Error(`Context7 HTTP ${response.status}: ${raw.slice(0,300)}`);
    const value = raw.startsWith('data:') || raw.startsWith('event:') ? raw.split('\n').filter(x=>x.startsWith('data:')).map(x=>JSON.parse(x.slice(5))).find(x=>x.id===id) : JSON.parse(raw);
    if(value?.error) throw new Error(JSON.stringify(value.error));
    return value?.result;
  }
  try {
    await rpc(1,'initialize',{protocolVersion:'2024-11-05',capabilities:{},clientInfo:{name:'boxflow-preflight',version:'1.0'}});
    if (process.argv[2] === 'context7-codex') {
      console.log(JSON.stringify(await rpc(5,'tools/call',{name:'query-docs',arguments:{libraryId:'/openai/codex',query:'codex exec explicit model and model_reasoning_effort high, JSONL output events, disable tools and MCP for isolated noninteractive reasoning'}})));
      process.exit(0);
    }
    const result = await rpc(2,'tools/call',{name:'resolve-library-id',arguments:{libraryName:'Claude Code',query:'Claude Code CLI selecting exact Opus 5 Sonnet 5 model and effort in noninteractive print mode'}});
    console.log(JSON.stringify(result));
    console.log(JSON.stringify(await rpc(3,'tools/call',{name:'query-docs',arguments:{libraryId:'/websites/code_claude',query:'Run Claude Code headless with an exact model ID and effort, stream-json metadata for verifying actual model, tools disabled'}})));
    console.log(JSON.stringify(await rpc(4,'tools/call',{name:'resolve-library-id',arguments:{libraryName:'OpenAI Codex',query:'Codex exec CLI choosing explicit model and model_reasoning_effort high with JSONL output for automation'}})));
  } catch(e) {fs.writeFileSync(path.join(run,'context7-status.json'),JSON.stringify({status:'TOOL_UNAVAILABLE',error:e.message,timestamp:new Date().toISOString()},null,2));console.log(e.message);process.exitCode=1;}
}
