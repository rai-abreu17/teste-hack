'use strict';
let lastData=null,mode='map';
const $=id=>document.getElementById(id);
const fmt=(v,n=2)=>v==null?'—':Number(v).toLocaleString('pt-BR',{minimumFractionDigits:n,maximumFractionDigits:n});
const states={valid:'Válida',partial:'Parcial',unavailable:'Indisponível',stale:'Desatualizada'};
function canvas(id){const el=$(id),r=el.getBoundingClientRect(),dpr=window.devicePixelRatio||1;el.width=Math.round(r.width*dpr);el.height=Math.round(r.height*dpr);const c=el.getContext('2d');c.scale(dpr,dpr);return {c,w:r.width,h:r.height};}
function color(z){const t=Math.max(0,Math.min(1,z/(lastData?.geometry?.display_max_height_m||.2)));return `rgb(${Math.round(222-201*t)},${Math.round(238-124*t)},${Math.round(234-121*t)})`;}
function noData(c,w,h,text){c.fillStyle='#f5f8fa';c.fillRect(0,0,w,h);c.fillStyle='#8197a5';c.font='13px Segoe UI, Arial';c.textAlign='center';c.fillText(text,w/2,h/2);c.textAlign='left';}
function surface(d){
  const {c,w,h}=canvas('surface');if(!d?.grid){noData(c,w,h,'Aguardando pontos do sensor');return;}
  if(mode==='map'){
    const g=d.grid,W=d.geometry.width_m,D=d.geometry.depth_m,s=Math.min((w-72)/W,(h-48)/D),ox=(w-W*s)/2,oy=14;
    for(let iy=0;iy<g.ny;iy++)for(let ix=0;ix<g.nx;ix++){
      const z=g.height_m[iy*g.nx+ix],x=ox+ix*g.cell_m*s,y=oy+(g.ny-1-iy)*g.cell_m*s,a=g.cell_m*s;
      c.fillStyle=z===null?'#e6eaee':color(z);c.fillRect(x,y,a+.15,a+.15);
      if(z===null){c.strokeStyle='#bac5cd';c.lineWidth=.55;c.beginPath();c.moveTo(x,y+a);c.lineTo(x+a,y);c.stroke();}
    }
    c.strokeStyle='#6c8898';c.lineWidth=1;c.strokeRect(ox,oy,W*s,D*s);
    c.setLineDash([4,4]);c.strokeStyle='#859fac';
    [d.geometry.base_width_m,W-d.geometry.base_width_m].forEach(x=>{c.beginPath();c.moveTo(ox+x*s,oy);c.lineTo(ox+x*s,oy+D*s);c.stroke();});c.setLineDash([]);
    const [sx,sy]=d.sensor_pose.translation_m;c.beginPath();c.arc(ox+sx*s,oy+(D-sy)*s,4,0,Math.PI*2);c.fillStyle='#e9993f';c.fill();c.strokeStyle='white';c.lineWidth=1.5;c.stroke();
    c.fillStyle='#718999';c.font='10px Segoe UI, Arial';c.textAlign='center';c.fillText(fmt(W)+' m · FRENTE ABERTA',w/2,oy+D*s+20);
    c.save();c.translate(ox-15,oy+D*s/2);c.rotate(-Math.PI/2);c.fillText(fmt(D)+' m',0,0);c.restore();c.textAlign='left';
    $('surface-caption').textContent='Mapa visto de cima. Ponto laranja: posição horizontal do sensor. Tracejados: limite das bases inclinadas. Sem interpolação nas lacunas hachuradas.';
  }else{
    const W=d.geometry.width_m,D=d.geometry.depth_m,Z=Math.max(d.geometry.height_m,d.sensor_pose.translation_m[2]);
    const scale=Math.min(w/(2.7*Math.max(W,D)),h/(1.65*Z)),proj=(x,y,z)=>[w/2+(x-W/2-(y-D/2))*.80*scale,h*.83+(x-W/2+y-D/2)*.34*scale-z*scale];
    c.strokeStyle='#d7e1e7';c.lineWidth=1;
    for(let i=0;i<=6;i++){const x=W*i/6,y=D*i/6;c.beginPath();c.moveTo(...proj(x,0,0));c.lineTo(...proj(x,D,0));c.moveTo(...proj(0,y,0));c.lineTo(...proj(W,y,0));c.stroke();}
    [...d.points].sort((a,b)=>a[0]+a[1]-b[0]-b[1]).forEach(p=>{const [x,y]=proj(...p);c.fillStyle=color(p[2]);c.fillRect(x-1.4,y-1.4,2.8,2.8);});
    const [x,y]=proj(...d.sensor_pose.translation_m);c.fillStyle='#e9993f';c.beginPath();c.arc(x,y,4,0,Math.PI*2);c.fill();c.font='10px Segoe UI, Arial';c.fillText('ToF Mock',x+7,y+3);
    $('surface-caption').textContent='Projeção dos pontos aceitos pelo cálculo. Vigas, paredes e retornos inválidos são excluídos. O sensor aparece em laranja.';
  }
}
function history(d){
  const {c,w,h}=canvas('history'),list=d?.history||[];if(!list.length){noData(c,w,h,'O histórico começa na primeira varredura');return;}
  const left=42,right=w-19,top=20,bottom=h-58,max=Math.max(.001,...list.map(p=>p.observed_volume_m3||0))*1.15;
  const x=i=>list.length===1?(left+right)/2:left+(right-left)*i/(list.length-1),y=v=>bottom-(bottom-top)*v/max;
  c.font='10px Segoe UI, Arial';c.lineWidth=1;
  for(let i=0;i<=4;i++){const v=max*i/4,yy=y(v);c.strokeStyle='#edf2f5';c.beginPath();c.moveTo(left,yy);c.lineTo(right,yy);c.stroke();c.fillStyle='#8b9faa';c.textAlign='right';c.fillText(fmt(v,4),left-8,yy+3);}c.textAlign='left';c.fillText('m³',left,top-7);
  c.strokeStyle='#1f819e';c.lineWidth=2;c.beginPath();let started=false;
  list.forEach((p,i)=>{if(p.observed_volume_m3==null){started=false;return;}const xx=x(i),yy=y(p.observed_volume_m3);if(!started){c.moveTo(xx,yy);started=true;}else c.lineTo(xx,yy);});c.stroke();
  list.forEach((p,i)=>{if(p.observed_volume_m3==null)return;c.fillStyle=p.state==='valid'?'#25aa82':'#1f819e';c.beginPath();c.arc(x(i),y(p.observed_volume_m3),2.4,0,Math.PI*2);c.fill();});
  c.setLineDash([4,4]);c.strokeStyle='#8c9da6';c.lineWidth=1;c.beginPath();list.forEach((p,i)=>{const xx=x(i),yy=bottom-(bottom-top)*p.coverage_fraction;i?c.lineTo(xx,yy):c.moveTo(xx,yy);});c.stroke();c.setLineDash([]);
  c.fillStyle='#8499a8';c.textAlign='left';c.fillText(new Date(list[0].received_at).toLocaleTimeString('pt-BR'),left,bottom+20);c.textAlign='right';c.fillText(new Date(list.at(-1).received_at).toLocaleTimeString('pt-BR'),right,bottom+20);c.textAlign='left';
  c.fillStyle='#1f819e';c.fillRect(left,h-16,10,3);c.fillText('Volume observado',left+16,h-11);c.fillStyle='#879ba7';c.fillText('Cobertura de 0 a 100%',Math.max(left+145,w-155),h-11);
}
function details(d){
  const fields=[['Origem',d.source==='simulation'?'Simulação':'—'],['Transporte',d.transport==='native-c-test'?'Teste local do gerador C':'ESP32 no Wokwi'],['Perfil','VL53L5CX · 64 zonas ideais'],['Precisão','Não validada para o sensor físico'],['Dispositivo',d.device_id],['Sessão de inicialização',d.boot_id],['Varredura',d.sequence],['Referência',d.reference_id],['Aquisição no relógio simulado',`${d.acquisition_start_ms} ms · duração ${d.acquisition_duration_ms} ms`],['Retornos válidos',`${d.valid_returns} de ${d.total_returns} (não equivale à cobertura)`],['Área não observada',`${fmt(d.unobserved_area_m2)} m²`],['Volume adicional possível nas lacunas',`Até ${fmt(d.unobserved_possible_volume_m3)} m³, considerando apenas o limite de altura da cena. Não é intervalo de precisão.`]];
  $('details').replaceChildren();for(const [k,v] of fields){const a=document.createElement('dt'),b=document.createElement('dd');a.textContent=k;b.textContent=v??'—';$('details').append(a,b);}
}
function render(d){
  const state=d.measurement_state||'unavailable';$('state').textContent=states[state];$('state').className='state '+state;$('box').textContent=d.box_id||'BOX-DEMO-01';
  const old=d.is_previous_measurement&&d.observed_volume_m3!=null;
  $('volume-label').textContent=old?'Último volume observado':d.total_volume_m3!=null?'Volume total reconstruído':'Volume observado';
  $('volume').textContent=fmt(d.observed_volume_m3,5);$('volume').classList.toggle('muted',!!old);
  $('condition').textContent=old?'Leitura anterior. Não representa uma atualização atual.':state==='unavailable'?'Sem uma medição de volume utilizável.':d.total_volume_m3!=null?'Cobertura da grade completa. Precisão física não validada.':'Parcela reconstruída. O volume total pode ser maior.';
  $('coverage').textContent=fmt(d.coverage_fraction==null?null:d.coverage_fraction*100,1);$('coverage-bar').style.width=(d.coverage_fraction||0)*100+'%';
  $('area').textContent=d.grid?`${fmt(d.observed_area_m2)} de ${fmt(d.geometry.width_m*d.geometry.depth_m)} m² com suporte de medição.`:'A cobertura representa área, não quantidade de raios.';
  $('updated').textContent=d.received_at?new Date(d.received_at).toLocaleTimeString('pt-BR'):'—';
  $('age').textContent=d.received_at?`${new Date(d.received_at).toLocaleDateString('pt-BR')} · idade aproximada ${fmt(d.age_seconds,0)} s`:'Nenhum dado recebido';
  $('reason').textContent=d.reason;$('history-count').textContent=(d.history?.length||0)+' leituras';surface(d);history(d);if(d.grid)details(d);
}
async function poll(){
  try{const response=await fetch('/api/latest',{cache:'no-store'});if(!response.ok)throw new Error('HTTP '+response.status);lastData=await response.json();render(lastData);$('connection-dot').className='online';$('connection').textContent='Receptor conectado';}
  catch(e){$('connection-dot').className='';$('connection').textContent='Receptor desconectado';if(lastData?.grid){render({...lastData,measurement_state:'stale',is_previous_measurement:true,reason:'Conexão com o receptor interrompida. Exibindo a última leitura recebida.'});}else $('reason').textContent='Não foi possível consultar o receptor.';}
  finally{setTimeout(poll,2000);}
}
for(const [id,value] of [['map-mode','map'],['points-mode','points']])$(id).addEventListener('click',()=>{mode=value;for(const [other,v] of [['map-mode','map'],['points-mode','points']]){$(other).classList.toggle('active',v===mode);$(other).setAttribute('aria-pressed',String(v===mode));}surface(lastData);});
window.addEventListener('resize',()=>{surface(lastData);history(lastData);});poll();
