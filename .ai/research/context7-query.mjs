import fs from 'node:fs';
const [mode,subject,...words]=process.argv.slice(2);
if(!['resolve','query'].includes(mode)||!subject||!words.length) throw new Error('Usage: resolve library query | query libraryId query');
const query=words.join(' ');
let session;
async function rpc(id,method,params) {
  const r=await fetch('https://mcp.context7.com/mcp',{method:'POST',headers:{'Content-Type':'application/json',Accept:'application/json, text/event-stream',...(session?{'Mcp-Session-Id':session}:{})},body:JSON.stringify({jsonrpc:'2.0',id,method,params}),signal:AbortSignal.timeout(45000)});
  session=r.headers.get('mcp-session-id')??session;
  const raw=await r.text();
  if(!r.ok) throw new Error(`Context7 HTTP ${r.status}: ${raw.slice(0,200)}`);
  const v=raw.startsWith('data:')||raw.startsWith('event:')?raw.split('\n').filter(x=>x.startsWith('data:')).map(x=>JSON.parse(x.slice(5))).find(x=>x.id===id):JSON.parse(raw);
  if(v.error)throw new Error(JSON.stringify(v.error));return v.result;
}
await rpc(1,'initialize',{protocolVersion:'2024-11-05',capabilities:{},clientInfo:{name:'boxflow-research',version:'1.0'}});
const result=await rpc(2,'tools/call',{name:mode==='resolve'?'resolve-library-id':'query-docs',arguments:mode==='resolve'?{libraryName:subject,query}:{libraryId:subject,query}});
const file=`.ai/research/raw/context7-${mode}-${Date.now()}.json`;
fs.writeFileSync(file,JSON.stringify({timestamp:new Date().toISOString(),mode,subject,query,result},null,2));
console.log(JSON.stringify({file,result}));
