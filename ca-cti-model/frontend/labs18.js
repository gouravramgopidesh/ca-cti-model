(() => {
 const $=id=>document.getElementById(id), grid=$('labsGrid'); if(!grid)return;
 let labs=[];
 function render(){
   const term=$('labsSearch').value.toLowerCase().trim(),filter=$('labsFilter').value;
   grid.replaceChildren(); const shown=labs.filter(l=>(filter==='all'||(filter==='verified')===l.source_available)&&(`${l.title} ${l.summary} ${l.number}`).toLowerCase().includes(term));
   $('labsCount').textContent=`${shown.length} of ${labs.length} labs`;
   for(const l of shown){
     const card=document.createElement('article');card.className='lab-card';
     const heading=document.createElement('div');heading.className='lab-card-heading';
     const number=document.createElement('span');number.className='lab-number';number.textContent=`LAB ${String(l.number).padStart(2,'0')}`;
     const badge=document.createElement('span');badge.className='lab-badge '+(l.source_available?'available':'pending');badge.textContent=l.source_available?'README available':'Source pending';
     heading.append(number,badge);const title=document.createElement('h3');title.textContent=l.title;
     const desc=document.createElement('p');desc.textContent=l.summary;
     const actions=document.createElement('div');actions.className='lab-actions';
     const ask=document.createElement('button');ask.type='button';ask.textContent='Ask AI about Lab '+l.number;
     ask.addEventListener('click',()=>{
       const inp=$('aiInput'),mode=$('aiMode');if(inp){inp.value=`Explain Lab ${l.number}: ${l.title}. Use actual ingested coursework when available; otherwise say the source documents are not available.`;if(mode)mode.value='cti';location.hash='#assistant';inp.focus();}
     });actions.appendChild(ask);
     const status=document.createElement('small');status.textContent=l.evidence_status;
     card.append(heading,title,desc,status,actions);grid.appendChild(card);
   }
   if(!shown.length){const p=document.createElement('p');p.className='muted';p.textContent='No matching labs.';grid.appendChild(p);}
 }
 fetch('/labs.json',{cache:'no-store'}).then(r=>{if(!r.ok)throw Error('Lab catalog unavailable');return r.json()}).then(data=>{labs=data;render()}).catch(err=>{grid.textContent='Unable to load lab catalog: '+err.message});
 $('labsSearch').addEventListener('input',render);$('labsFilter').addEventListener('change',render);
})();
