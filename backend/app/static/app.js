
(() => {
  const $ = id => document.getElementById(id);
  let token = localStorage.getItem("mergemind_admin_token") || "";
  let selectedId = null;
  let selectedArtifact = "plan";
  const esc = value => String(value ?? "").replace(/[&<>"']/g, c => ({"&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;","'":"&#39;"}[c]));
  const headers = () => ({ "Content-Type":"application/json", "X-MergeMind-Admin-Token":token });
  function notice(id, message, kind="") { const el=$(id); el.textContent=message; el.className="notice "+kind; el.classList.remove("hidden"); }
  function hide(id){$(id).classList.add("hidden");}
  async function api(path, options={}) {
    const response = await fetch(path,{...options,headers:{...headers(),...(options.headers||{})}});
    const data = await response.json().catch(()=>({detail:response.statusText}));
    if(!response.ok) throw new Error(data.detail || "Request failed");
    return data;
  }
  function setApiState(ok,text){$("apiState").innerHTML='<span class="dot '+(ok?'ok':'')+'"></span><span>'+esc(text)+'</span>';}
  async function unlock(){
    token=$("adminToken").value.trim();
    if(!token){notice("globalNotice","Enter the local admin token.");return;}
    localStorage.setItem("mergemind_admin_token",token);
    try{
      await api("/api/switch/status");
      $("workspace").classList.remove("hidden");hide("globalNotice");setApiState(true,"Workspace unlocked");
      await Promise.all([loadStatus(),loadWorkflows()]);
    }catch(e){localStorage.removeItem("mergemind_admin_token");token="";setApiState(false,"Access denied");notice("globalNotice",e.message,"warn");}
  }
  async function loadStatus(){
    const s=await api("/api/switch/status");
    const connected=Object.values(s.agents||{}).filter(a=>a.connected).length;
    $("switchState").innerHTML='<span class="dot '+(connected===5?'ok':'warn')+'"></span><span>'+connected+'/5 agents connected</span>';
    $("agentCount").textContent=(s.registered_agents||[]).length+" registered";
    $("agentList").innerHTML=(s.registered_agents||[]).map(a=>{
      const live=s.agents?.[a.role]?.connected;
      return '<div class="agent"><strong>'+esc(a.name)+'</strong><small><span class="dot '+(live?'ok':'')+'" style="display:inline-block;vertical-align:middle"></span> '+(live?'Connected':'Registered · waiting for room access')+'</small></div>';
    }).join("") || '<div class="empty">No Switch agents registered yet.</div>';
    if(s.base_url)$("switchUrl").value=s.base_url;
    if(s.room_id)$("roomId").value=s.room_id;
  }
  async function loadWorkflows(){
    const list=await api("/api/workflows");
    $("workflowCount").textContent=list.length+" workflows";
    $("workflowList").innerHTML=list.length?list.map(w=>'<div class="workflow" data-id="'+esc(w.id)+'"><strong>'+esc(w.title)+'</strong><p>'+esc(w.repository)+'</p><div class="meta"><span class="pill '+(w.status==="awaiting_approval"?"warn":w.status==="failed"||w.status==="rejected"?"bad":w.status==="approved"?"good":"")+'">'+esc(w.status.replaceAll("_"," "))+'</span><span class="hint">'+new Date(w.updated_at).toLocaleString()+'</span></div></div>').join(""):'<div class="empty">No workflows yet. Start with a real public GitHub issue or task.</div>';
    document.querySelectorAll(".workflow").forEach(el=>el.addEventListener("click",()=>showWorkflow(el.dataset.id)));
  }
  async function showWorkflow(id){
    selectedId=id; const w=await api("/api/workflows/"+encodeURIComponent(id));
    $("detail").classList.remove("hidden");$("detailTitle").textContent=w.title;$("detailStatus").textContent=w.status.replaceAll("_"," ");
    $("detailRepo").textContent=w.repository;$("detailId").textContent=w.id;
    $("approve").classList.toggle("hidden",w.status!=="awaiting_approval");
    $("reject").classList.toggle("hidden",w.status!=="awaiting_approval");
    const keys=["plan","research","patch","review"].filter(k=>w.artifacts?.[k]);
    $("artifactTabs").innerHTML=keys.map(k=>'<button class="'+(k===selectedArtifact?'':'secondary')+'" data-artifact="'+k+'">'+k+'</button>').join("");
    if(!keys.includes(selectedArtifact))selectedArtifact=keys[0]||"";
    document.querySelectorAll("[data-artifact]").forEach(el=>el.addEventListener("click",()=>{selectedArtifact=el.dataset.artifact;showWorkflow(id);}));
    $("artifact").textContent=selectedArtifact?(w.artifacts[selectedArtifact]||""):"No agent artifacts have arrived yet.";
    $("timeline").innerHTML=(w.events||[]).map(e=>'<div class="event"><strong>'+esc(e.actor)+' · '+esc(e.kind.replaceAll("_"," "))+'</strong><p>'+esc(e.message)+'</p><time>'+new Date(e.timestamp).toLocaleString()+'</time></div>').join("")||'<div class="empty">No activity yet.</div>';
  }
  $("saveToken").addEventListener("click",unlock);
  $("adminToken").value=token;
  $("adminToken").addEventListener("keydown",e=>{if(e.key==="Enter")unlock();});
  $("refresh").addEventListener("click",async()=>{try{await Promise.all([loadStatus(),loadWorkflows()]);}catch(e){notice("globalNotice",e.message,"warn");}});
  $("registerSwitch").addEventListener("click",async()=>{
    const button=$("registerSwitch");button.disabled=true;button.textContent="Registering…";
    try{
      const result=await api("/api/switch/register",{method:"POST",body:JSON.stringify({base_url:$("switchUrl").value.trim(),registration_key:$("registrationKey").value,room_id:$("roomId").value.trim()})});
      $("registrationKey").value="";notice("switchNotice",result.registered_roles.length+" agents registered. "+result.next_step,"good");
      await new Promise(r=>setTimeout(r,1200));await loadStatus();
    }catch(e){notice("switchNotice",e.message,"warn");}
    finally{button.disabled=false;button.textContent="Register five agents";}
  });
  $("startTask").addEventListener("click",async()=>{
    const button=$("startTask");button.disabled=true;button.textContent="Dispatching…";
    try{
      const w=await api("/api/workflows",{method:"POST",body:JSON.stringify({title:$("taskTitle").value.trim(),description:$("taskDescription").value.trim(),repository:$("repoUrl").value.trim(),mode:"switch"})});
      $("taskTitle").value="";$("taskDescription").value="";notice("globalNotice","Workflow created and dispatched to the Switch coordinator.","good");
      await loadWorkflows();await showWorkflow(w.id);
    }catch(e){notice("globalNotice",e.message,"warn");}
    finally{button.disabled=false;button.textContent="Dispatch through Switch";}
  });
  $("approve").addEventListener("click",async()=>{
    if(!selectedId)return;
    if(!confirm("Record approval of this review? This does not apply, commit, merge, deploy, or submit the patch."))return;
    try{await api("/api/workflows/"+selectedId+"/approve",{method:"POST"});await showWorkflow(selectedId);await loadWorkflows();}
    catch(e){notice("globalNotice",e.message,"warn");}
  });
  $("reject").addEventListener("click",async()=>{
    if(!selectedId)return;
    if(!confirm("Reject this proposed patch? No repository changes will be made."))return;
    try{await api("/api/workflows/"+selectedId+"/reject",{method:"POST"});await showWorkflow(selectedId);await loadWorkflows();}
    catch(e){notice("globalNotice",e.message,"warn");}
  });
  if(token)unlock();
})();
