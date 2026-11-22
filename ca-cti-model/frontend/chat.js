(() => {
  const by = id => document.getElementById(id);
  const newId = () => 'chat_' + (globalThis.crypto?.randomUUID?.().replaceAll('-','') || Date.now().toString(36));
  let session = localStorage.getItem('cti_chat_session') || newId();
  localStorage.setItem('cti_chat_session',session);
  by('aiSessionLabel').textContent = `Session ${session.slice(-8)}`;
  // Render a limited Markdown subset using DOM text nodes only (no HTML injection).
  function setMessage(el, raw, role){
    el.replaceChildren();
    const text=String(raw ?? '');
    if(role==='user'){el.textContent=text;return;}
    const lines=text.replace(/\r\n?/g,'\n').split('\n');
    let list=null;
    function inline(parent,value){
      const parts=value.split(/(\*\*[^*\n]+\*\*|`[^`\n]+`)/g);
      for(const part of parts){
        if(part.startsWith('**')&&part.endsWith('**')&&part.length>4){const b=document.createElement('strong');b.textContent=part.slice(2,-2);parent.appendChild(b);}
        else if(part.startsWith('`')&&part.endsWith('`')&&part.length>2){const c=document.createElement('code');c.textContent=part.slice(1,-1);parent.appendChild(c);}
        else parent.appendChild(document.createTextNode(part));
      }
    }
    for(const rawLine of lines){
      const line=rawLine.trimEnd();
      if(!line.trim()){list=null;continue;}
      const bullet=line.match(/^\s*(?:[-*•]|\d+\.)\s+(.+)$/);
      if(bullet){if(!list){list=document.createElement('ul');el.appendChild(list);}const li=document.createElement('li');inline(li,bullet[1]);list.appendChild(li);continue;}
      list=null;
      const heading=line.match(/^\s*#{1,4}\s+(.+)$/);
      const block=document.createElement(heading?'h4':'p');inline(block,heading?heading[1]:line.trim());el.appendChild(block);
    }
  }
  function bubble(role,text){
    const el=document.createElement('div');el.className='ai-bubble '+role;
    setMessage(el, text, role);
    by('aiMessages').appendChild(el);el.scrollIntoView({block:'end',behavior:'smooth'});return el;
  }
  function sources(rows){
    const box=by('aiSources');box.replaceChildren();if(!rows?.length)return;
    const title=document.createElement('strong');title.textContent='Retrieved sources';box.appendChild(title);
    for(const row of rows){
      const d=document.createElement('div');
      d.textContent=`[${row.label}] ${row.title} · ${row.type}${row.training?' · TRAINING':''}`;
      if(row.url?.startsWith('https://')||row.url?.startsWith('http://')){
        const a=document.createElement('a');a.textContent=' ↗ Open source';a.href=row.url;a.target='_blank';a.rel='noopener noreferrer';d.appendChild(a);
      }
      box.appendChild(d);
    }
  }
  async function health(){
    try {const r=await fetch('/api/chat/health');const h=await r.json();
      by('aiStatus').textContent=h.ok?`MongoDB ✓ · ${h.ollama?'Ollama ✓':'Ollama offline'} · ${h.knowledge_chunks} chunks`:'Chatbot unavailable';
    } catch {by('aiStatus').textContent='Chatbot unavailable';}
  }
  async function load(){
    try{const r=await fetch('/api/chat/sessions/'+encodeURIComponent(session));if(!r.ok)return;
      const data=await r.json();if(data.messages?.length){by('aiMessages').replaceChildren();data.messages.forEach(m=>bubble(m.role,m.content));}
    }catch{}
  }
  by('aiForm').addEventListener('submit',async event=>{
    event.preventDefault();const prompt=by('aiInput').value.trim();if(prompt.length<2)return;
    by('aiInput').value='';bubble('user',prompt);const pending=bubble('assistant',by('aiMode').value==='cti'?'Searching CTI and lab evidence…':'Thinking…');
    by('aiSubmit').disabled=true;
    try{const r=await fetch('/api/chat',{method:'POST',headers:{'content-type':'application/json'},body:JSON.stringify({message:prompt,platform:by('aiPlatform').value,mode:by('aiMode').value,session_id:session})});
      const data=await r.json();if(!r.ok)throw Error(data.error||data.detail||'Unable to answer');
      setMessage(pending,data.answer,'assistant'); sources(data.sources);
      by('aiMessages').scrollTop=by('aiMessages').scrollHeight;
      by('aiStatus').textContent=`${data.route==='general'?'General chat':'MongoDB retrieval'} · ${data.llm_used?'AI generated':'AI fallback'} · ${data.latency_ms}ms`;
    }catch(error){pending.textContent='Chat error: '+error.message;}finally{by('aiSubmit').disabled=false;}
  });
  by('aiNew').addEventListener('click',()=>{session=newId();localStorage.setItem('cti_chat_session',session);by('aiMessages').replaceChildren();bubble('assistant','New conversation started.');by('aiSources').replaceChildren();by('aiSessionLabel').textContent=`Session ${session.slice(-8)}`;});
  health();load();
})();
