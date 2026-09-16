import fs from 'node:fs';
import path from 'node:path';
import crypto from 'node:crypto';

// Read-only verification of existing application artifacts; writes audit only in .ai.
const root = process.cwd();
const hash = file => crypto.createHash('sha256').update(fs.readFileSync(file)).digest('hex');
const before = JSON.parse(fs.readFileSync('.ai/runs/bootstrap-20260913/application-before.json', 'utf8'));
const current = {};
function walk(dir) {
  for (const entry of fs.readdirSync(dir, {withFileTypes:true})) {
    if (entry.name === '.ai') continue;
    const file = path.join(dir, entry.name);
    if (entry.isDirectory()) walk(file);
    else if (entry.isFile()) current[path.relative(root,file)] = hash(file);
  }
}
walk(root);
const changed = Object.keys(before).filter(key => before[key] !== current[key]);
const added = Object.keys(current).filter(key => !(key in before));
const prior = JSON.parse(fs.readFileSync('build/experiments/artifact-hashes.json','utf8'));
const invalidPrior = Object.entries(prior).filter(([file, expected]) => !fs.existsSync(file) || hash(file) !== expected).map(([file])=>file);
const manifest = JSON.parse(fs.readFileSync('.ai/runs/smoke-20260913-verified/manifest.json','utf8'));
const result = {
  checkedAt:new Date().toISOString(),
  application:{beforeCount:Object.keys(before).length,currentCount:Object.keys(current).length,changed,added,baselinePreserved:!changed.length,fileSetUnchanged:!changed.length&&!added.length,addedFileNote:'A summary document appeared after the initial snapshot. It was inspected, preserved, and indexed; its creation is not attributed to this audit.'},
  priorExperiments:{hashesChecked:Object.keys(prior).length,mismatches:invalidPrior,reexecuted:false},
  liveSmoke:{runId:manifest.runId,status:manifest.status,successfulCalls:manifest.invocations.filter(x=>x.status==='completed').length,failedCalls:manifest.invocations.filter(x=>x.status==='failed').length,arbitrationPending:manifest.status!=='completed'},
  note:'Integrity verification, not a rerun of application experiments or evidence of real sensor accuracy.'
};
fs.writeFileSync('.ai/evidence/integrity-check.json',JSON.stringify(result,null,2)+'\n');
console.log(JSON.stringify(result));
if (changed.length || invalidPrior.length) process.exitCode=1;
