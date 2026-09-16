// Execute the actual WASM with a minimal host for documented Wokwi callbacks.
// This validates our protocol/state/display code, not ESP32 emulation or Wokwi timing.
import fs from 'node:fs';
import path from 'node:path';
import {fileURLToPath} from 'node:url';
import assert from 'node:assert/strict';
const root=path.resolve(path.dirname(fileURLToPath(import.meta.url)),'..');
const memory=new WebAssembly.Memory({initial:256});
const mem=()=>new Uint8Array(memory.buffer),view=()=>new DataView(memory.buffer);
const string=p=>{let e=p;while(mem()[e])e++;return new TextDecoder().decode(mem().subarray(p,e));};
const attrs=new Map(),names=new Map(),display=new Uint8Array(256*218*4);
let instance,i2c,timer,pendingTimer=null,nanos=0,writes=0;
const env={memory,
  attrInit:(p,value)=>{const id=attrs.size+1;attrs.set(id,value);names.set(string(p),id);return id;},
  attrReadFloat:id=>attrs.get(id),
  pinInit:()=>1,
  i2cInit:p=>{i2c={user:view().getUint32(p,true),address:view().getUint32(p+4,true),connect:view().getUint32(p+16,true),read:view().getUint32(p+20,true),write:view().getUint32(p+24,true)};return 1;},
  timerInit:p=>{timer={user:view().getUint32(p,true),callback:view().getUint32(p+4,true)};return 1;},
  timerStart:(id,micros,repeat)=>{assert.equal(id,1);assert.equal(repeat,0);pendingTimer={due:nanos+micros*1000};},
  getSimNanos:()=>nanos,
  framebufferInit:(w,h)=>{view().setUint32(w,256,true);view().setUint32(h,218,true);return 1;},
  bufferWrite:(id,offset,p,length)=>{assert.equal(id,1);assert(offset>=0&&offset+length<=display.length);display.set(mem().subarray(p,p+length),offset);writes++;}
};
const wasi={fd_close:()=>0,fd_fdstat_get:()=>0,fd_seek:()=>0,
  fd_write:(fd,iov,n,written)=>{let total=0;for(let i=0;i<n;i++)total+=view().getUint32(iov+i*8+4,true);view().setUint32(written,total,true);return 0;}};
({instance}=await WebAssembly.instantiate(fs.readFileSync(path.join(root,'wokwi/boxflow-lidar.chip.wasm')),{env,wasi_snapshot_preview1:wasi}));
const call=(index,...args)=>instance.exports.__indirect_function_table.get(index)(...args);
const connect=reading=>call(i2c.connect,i2c.user,0x42,reading?1:0);
const write=v=>call(i2c.write,i2c.user,v);
const set=(name,value)=>attrs.set(names.get(name),value);
const address=p=>{assert(connect(false));assert(write(p>>8));assert(write(p&255));};
const read=(p,n)=>{address(p);assert(connect(true));return Uint8Array.from({length:n},()=>call(i2c.read,i2c.user));};
const capture=()=>{address(0xffff);return write(0xa1);};
const finish=()=>{assert(pendingTimer);nanos=pendingTimer.due;pendingTimer=null;call(timer.callback,timer.user);};
const seq=()=>new DataView(read(0,64).buffer).getUint32(8,true);
instance.exports.chipInit();assert.equal(i2c.address,0x42);assert.equal(seq(),0);
nanos=3000e6;assert(capture());assert.equal(read(5,1)[0],0);
// Change scene controls DURING acquisition. Snapshot must retain the old fill.
set('fill',0);finish();assert.equal(seq(),1);
const header=read(0,64);assert.equal(header[4],2);assert.equal(new DataView(header.buffer).getUint16(24,true),8);
assert.equal(new DataView(header.buffer).getUint16(30,true),3);
const len=64+new DataView(header.buffer).getUint16(58,true),raw=new Uint8Array(len);assert.equal(len,704);
for(let p=0;p<len;p+=28)raw.set(read(p,Math.min(28,len-p)),p);
assert.deepEqual(read(0,64),header);assert.equal(raw[5],1);
// Controls alone cannot mutate the exposed frame while it is being read.
set('fill',100);assert.deepEqual(read(0,len),raw);
// Freeze acknowledges requests but does not create fresh data or a fresh sequence.
set('freeze',1);assert(capture());assert.equal(seq(),1);assert.equal(pendingTimer,null);
set('freeze',0);assert(capture());finish();assert.equal(seq(),2);
set('i2cFault',1);assert.equal(connect(false),0);assert.equal(connect(true),0);set('i2cFault',0);
assert.equal(read(len+100,1)[0],255);assert.equal(read(65535,2)[0],255);
// Recover after failure and verify a new frame is generated.
set('fill',75);assert(capture());finish();assert.equal(seq(),3);
fs.mkdirSync(path.join(root,'build'),{recursive:true});
fs.writeFileSync(path.join(root,'build/wasm-frame.bin'),raw);
fs.writeFileSync(path.join(root,'build/framebuffer.rgba'),display);
assert(writes>100);assert(display.some((v,i)=>i%4!==3&&v>100));
console.log('WASM OK: initialization, snapshot, 28-byte blocks, stable frame, freeze, NACK, bounds, recovery and RGBA display.');
