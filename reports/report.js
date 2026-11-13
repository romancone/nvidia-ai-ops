'use strict';
const fmt=(v,n=1)=>v==null?'—':Number(v).toLocaleString('en-US',{maximumFractionDigits:n,minimumFractionDigits:n});
const esc=s=>String(s??'').replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
const range=v=>!v?.length?'—':Math.max(...v)-Math.min(...v)<.005?fmt(v[0],2):`${fmt(Math.min(...v),2)}–${fmt(Math.max(...v),2)}`;
const chip=s=>`<span class="chip">${esc(s)}</span>`;
let data;
const hardwareFor=variant=>data.hardware_profiles?.[variant.hardware_profile]??data.hardware;
const hardwareMemory=hardware=>`<span class="chip hardware-chip" title="Installed capacity; reported usable ${fmt(hardware.vram_gib,2)} GiB">${hardware.installed_vram_gib} GiB VRAM</span><span class="chip hardware-chip" title="Installed capacity; OS reports ${fmt(hardware.ram_gib,2)} GiB">${hardware.installed_dram_gib} GiB DRAM</span>`;
const occupied=(free,total)=>free==null?null:total-free;
const occupiedVram=(metrics,hardware)=>metrics?.sampled_vram_used_gib??occupied(metrics?.engine_gpu_free_gib,hardware.vram_gib);
function preferred(variant,workload,c){
 const rows=data.runs.filter(r=>r.variant===variant&&r.workload===workload&&r.clients===c&&r.metrics);
 if(variant==='strata-iq3s')return rows.find(r=>r.configuration.cache_mib===5120);
 if(variant==='strata-nvfp4')return rows.find(r=>r.configuration.decode_share===0)||rows[0];
 return rows[0];
}
const disk=v=>`${fmt(v.disk?.bytes/2**30,1)} GiB on disk`;
function cards(){
 document.querySelector('#cards').innerHTML=data.models.flatMap(model=>model.variants.map(key=>{
  const v=data.variants[key];
  const hardware=hardwareFor(v);
  return `<section class="model-group"><header class="model-heading"><div><span class="eyebrow">${esc(v.engine)} · ${esc(v.label)}</span><h2>${esc(model.name)}</h2></div><a href="${model.page}#${key}">All benchmarks →</a></header><div class="chips hardware-row">${hardwareMemory(hardware)}</div><div class="chips">${chip(disk(v))}${chip('256K context')}${chip('KV '+v.kv)}${chip('MTP '+v.mtp)}${v.ple?chip('PLE '+v.ple):''}</div><div class="workload-cards">${['Short','Long','Max'].map(workload=>{
   const budget={Short:'512 input · 256 output',Long:'32,768 input · 256 output',Max:'≈245,752 input · ≤16,384 output'}[workload];
   const users=[...new Set(data.runs.filter(r=>r.variant===key&&r.workload===workload&&r.metrics).map(r=>r.clients))].sort((a,b)=>a-b);
   const rows=users.map(c=>{
    const m=preferred(key,workload,c)?.metrics;
    return `<tr><td>${c}</td><td class="speed">${fmt(m?.decode_per_request_tps)}</td><td>${fmt(m?.ttft_s,2)}</td><td>${fmt(occupied(m?.min_mem_free_gib,hardware.ram_gib),1)}</td><td>${fmt(occupiedVram(m,hardware),1)}</td></tr>`;
   }).join('');
   return `<article class="card"><header class="workload-heading"><h3>${workload}</h3><span class="budget">${budget}</span></header><div class="table-wrap"><table class="card-table"><thead><tr><th>Users</th><th>tok/s/user</th><th>TTFT (s)</th><th>DRAM</th><th>VRAM</th></tr></thead><tbody>${rows||'<tr><td colspan="5" class="unmeasured">Not measured</td></tr>'}</tbody></table></div><p class="memory-label">DRAM and VRAM usage (GiB)</p></article>`;
  }).join('')}</div><p class="note">${esc(v.note)}</p></section>`;
 })).join('');
}
function filterTable(panel){
 const workload=panel.querySelector('[data-filter="workload"][aria-pressed="true"]').dataset.value;
 const users=panel.querySelector('[data-filter="users"][aria-pressed="true"]').dataset.value;
 panel.querySelectorAll('tbody tr[data-workload]').forEach(row=>{
  row.hidden=(workload!=='All'&&row.dataset.workload!==workload)||(users!=='All'&&row.dataset.users!==users);
 });
 panel.querySelector('.no-results').hidden=!!panel.querySelector('tbody tr[data-workload]:not([hidden])');
}
function filters(runs){
 const button=(kind,value)=>`<button type="button" data-filter="${kind}" data-value="${value}" aria-pressed="${value==='All'}">${value}</button>`;
 const workloads=['All',...['Short','Long','Max'].filter(w=>runs.some(r=>r.workload===w))];
 const users=['All',...new Set(runs.map(r=>r.clients).sort((a,b)=>a-b))];
 return `<div class="toolbar"><div><span class="filter-label">Input size</span><div class="seg" aria-label="Input size">${workloads.map(w=>button('workload',w)).join('')}</div></div><div><span class="filter-label">Users</span><div class="seg" aria-label="Users">${users.map(c=>button('users',c)).join('')}</div></div></div>`;
}
function modelPage(id){
 const model=data.models.find(m=>m.id===id);
 document.querySelector('#model-content').innerHTML=model.variants.map(key=>{
  const v=data.variants[key];
  const hardware=hardwareFor(v);
  const showStrataSettings=v.engine==='Strata';
  const runs=data.runs.filter(r=>r.variant===key&&r.metrics).sort((a,b)=>['Short','Long','Max'].indexOf(a.workload)-['Short','Long','Max'].indexOf(b.workload)||a.clients-b.clients||(a.configuration.cache_mib||0)-(b.configuration.cache_mib||0)||(a.configuration.decode_share||0)-(b.configuration.decode_share||0));
  return `<section class="panel" id="${key}"><span class="eyebrow">${esc(v.engine)}</span><h2>${esc(v.label)}</h2><div class="chips hardware-row">${hardwareMemory(hardware)}</div><div class="chips">${chip(disk(v))}${chip('256K context')}${chip('KV '+v.kv)}${chip('MTP '+v.mtp)}${v.ple?chip('PLE '+v.ple):''}${v.current_cache_mib?chip('Current cache '+v.current_cache_mib+' MiB'):''}</div><p class="muted">${esc(v.sampling)} · <a href="../profiles/${v.profile}.yml">Deployment profile</a></p><p class="notice">${esc(v.note)}</p>${filters(runs)}<div class="table-wrap"><table><thead><tr><th>Workload</th><th>Users</th>${showStrataSettings?'<th>Cache MiB</th><th>Decode share</th>':''}<th>Decode/user (tok/s)</th><th>TTFT (s)</th><th>Common window (s)</th><th>Longest pause (s)</th><th>DRAM occupied (GiB)</th><th>VRAM occupied (GiB)</th></tr></thead><tbody>${runs.map(r=>`<tr id="${esc(r.id)}" data-workload="${r.workload}" data-users="${r.clients}"><td>${r.workload}${r.metrics.cached_input_tokens?' · warm':''}${r.metrics.timing_source==='engine'?' *':''}</td><td>${r.clients}</td>${showStrataSettings?`<td>${r.configuration.cache_mib??'—'}</td><td>${r.configuration.decode_share??'—'}</td>`:''}<td>${fmt(r.metrics.decode_per_request_tps)}</td><td>${fmt(r.metrics.ttft_s,2)}</td><td>${range(r.metrics.common_decode_s)}</td><td>${fmt(r.metrics.max_fragment_gap_s,2)}</td><td>${fmt(occupied(r.metrics.min_mem_free_gib,hardware.ram_gib),2)}</td><td>${fmt(occupiedVram(r.metrics,hardware),2)}</td></tr>`).join('')}</tbody></table></div><p class="no-results muted" hidden>No completed measurement for this selection.</p><p class="caption">Short: 512/256 tokens · Long: 32,768/256 · Max: ≈245,752 / up to 16,384. Different EOS lengths and warm inputs are not equal-work speed comparisons. * Saved engine timing; other rows use client events.</p></section>`;
 }).join('');
 document.querySelectorAll('[data-filter]').forEach(button=>button.addEventListener('click',()=>{
  const panel=button.closest('.panel');
  panel.querySelectorAll(`[data-filter="${button.dataset.filter}"]`).forEach(b=>b.setAttribute('aria-pressed',String(b===button)));
  filterTable(panel);
 }));
 const repeat=data.runs.find(r=>r.model_key===id&&r.history_cache);
 if(repeat){
  const section=document.createElement('section');section.className='panel';section.id='cache-8960';
  section.innerHTML=`<h2>IQ3_S · cache 8960 MiB</h2><p>Max with four clients: ${repeat.history_cache.parked_after_batch} histories remained in RAM (${fmt(repeat.history_cache.bytes_after_batch/2**30,2)} GiB); both were restored after switching conversations.</p><p class="muted">52 GiB cgroup · 10 GiB OS reserve · maximum sampled occupied DRAM ${fmt(occupied(repeat.metrics.min_mem_free_gib,data.hardware.ram_gib),2)} GiB (including OS and filesystem cache). One input was warm; this repeat is separate from the cold 5120 MiB series.</p>`;
  document.querySelector('#model-content').append(section);
 }
 const functional=data.runs.filter(r=>r.model_key===id&&r.answers);
 for(const r of functional){
  const section=document.createElement('section');section.className='panel';
  section.innerHTML=`<h2>Saved functional answers</h2><p class="muted">NVFP4/GPTQ · decode share 0.5 · tool calling, image/history and recovery checks. These checks do not score general model quality.</p>`;
  for(const a of r.answers){
   const el=document.createElement('details');const summary=document.createElement('summary');summary.textContent=a.id;el.append(summary);
   if(a.image_url?.startsWith('data:image/')){const img=document.createElement('img');img.src=a.image_url;img.alt='Saved input image for '+a.id;el.append(img);}
   const pre=document.createElement('pre');pre.textContent=a.response.choices?.map(c=>c.message?.content||JSON.stringify(c.message?.tool_calls)).join('\n')||'No text';el.append(pre);section.append(el);
  }
  document.querySelector('#model-content').append(section);
 }
}
function renderReport(d){
 data=d;
 document.querySelectorAll("[data-platform]").forEach(el=>{const h=d.hardware;const memory=[h,...Object.values(d.hardware_profiles??{})];el.innerHTML=`<span><strong>CPU</strong> ${esc(h.cpu)} · ${h.cpu_cores} cores / ${h.cpu_threads} threads</span><span><strong>GPU</strong> ${esc(h.gpu)} · ${h.installed_vram_gib} GiB VRAM</span><span><strong>DRAM</strong> ${memory.map(m=>`${m.installed_dram_gib} GiB ${esc(m.dram_type)}-${m.dram_speed_mts} · ${esc(m.dram_modules)}`).join(' / ')}</span>`;});
 document.querySelectorAll("[data-hardware]").forEach(el=>{el.textContent=`${d.hardware.gpu} · ${d.hardware.vram_gib} GiB VRAM · ${[d.hardware,...Object.values(d.hardware_profiles??{})].map(h=>fmt(h.ram_gib,2)).join(' / ')} GiB RAM · ${d.hardware.os}`;});
 if(document.querySelector('#cards'))cards();
 if(document.body.dataset.model)modelPage(document.body.dataset.model);
 document.querySelector('#loading')?.remove();
}

function showLoadError(error){
 const loading=document.querySelector('#loading');
 if(loading)loading.textContent='Could not load benchmark results. '+error.message;
}

const datasetScript=document.createElement('script');
datasetScript.src='benchmark-data.js';
datasetScript.onload=()=>{
 try{renderReport(window.benchmarkDataset);}catch(error){showLoadError(error);}
};
datasetScript.onerror=()=>showLoadError(new Error('Missing reports/benchmark-data.js.'));
document.head.append(datasetScript);
