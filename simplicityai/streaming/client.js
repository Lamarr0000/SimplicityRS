'use strict';
const $=id=>document.getElementById(id), token=location.hash.slice(1);
history.replaceState(null,'',location.pathname);
const ws=new WebSocket(`ws://${location.host}/session`);
let ready=false,listening=false,muted=false,sound=true,stream,context,capture,source,currentTurn=0,answer,busy=false;
let transportPaused=false;
const activity=[],evidence=[];
function send(value){if(ws.readyState===WebSocket.OPEN)ws.send(JSON.stringify(value));}
function status(text){$('status').textContent=text;}
function scroll(){window.scrollTo({top:document.body.scrollHeight,behavior:'smooth'});}
function voiceDisplay(text){
  // Presentation only: raw recognition stays in evidence and model input.
  if(text!==text.toUpperCase())return text;
  const terms={ram:'RAM',cpu:'CPU',gpu:'GPU',dns:'DNS',tpm:'TPM',usb:'USB',ssd:'SSD',hdd:'HDD',pc:'PC',ai:'AI',uefi:'UEFI',bios:'BIOS',http:'HTTP',https:'HTTPS',ip:'IP',ipv4:'IPv4',ipv6:'IPv6',sfc:'SFC',dism:'DISM',windows:'Windows',bitlocker:'BitLocker',simplicityai:'SimplicityAI',themhands:'ThemHands',chatgpt:'ChatGPT',lenovo:'Lenovo',nvidia:'NVIDIA',i:'I'};
  return text.toLowerCase().replace(/\b[a-z][a-z0-9]*\b/g,word=>terms[word]||word).replace(/(^|[.!?]\s+)([a-z])/g,(_,prefix,char)=>prefix+char.toUpperCase());
}
function message(text,role){const node=document.createElement('div');node.className='message '+role;const body=document.createElement('span');body.textContent=text;node.append(body);$('messages').append(node);scroll();return node;}
function copyButton(node){if(node.querySelector('button'))return;const button=document.createElement('button');button.className='copy';button.textContent='Copy';button.onclick=()=>navigator.clipboard.writeText(node.dataset.copyText||node.querySelector('span').textContent).catch(()=>status('Copy unavailable. Select the text to copy.'));node.append(button);}
function findings(view){
  const node=message(view.title,'assistant measured-facts'),table=document.createElement('table');table.style.cssText='width:100%;border-collapse:collapse;font-size:.9em;white-space:normal;margin:12px 0';
  const row=(cells,header)=>{const tr=document.createElement('tr');for(const value of cells){const cell=document.createElement(header?'th':'td');cell.textContent=value===null||value===undefined?'Unknown':String(value);cell.style.cssText='text-align:left;padding:8px;border-bottom:1px solid #40516a;overflow-wrap:anywhere';tr.append(cell);}table.append(tr);};
  row(view.columns,true);for(const values of view.rows)row(values,false);node.append(table);const note=document.createElement('small');note.textContent=view.note;node.append(note);
  node.dataset.copyText=view.title+'\n'+[view.columns,...view.rows].map(values=>values.map(x=>x??'Unknown').join('\t')).join('\n')+'\n'+view.note;copyButton(node);scroll();
}

// Keep playback offsets across an interruption. New confirmed requests clear it.
class Playback {
  constructor(){this.queue=[];this.node=null;this.offset=0;this.paused=false;this.started=0;this.ctx=null;}
  async unlock(){if(!this.ctx)this.ctx=new AudioContext();await this.ctx.resume();}
  add(event){if(!sound)return;const raw=atob(event.pcm),bytes=Uint8Array.from(raw,c=>c.charCodeAt(0));const view=new DataView(bytes.buffer),data=new Float32Array(bytes.length/2);for(let i=0;i<data.length;i++)data[i]=view.getInt16(i*2,true)/32768;this.queue.push({data,rate:event.rate});this.play();}
  play(){if(this.paused||this.node||!this.queue.length||!this.ctx||this.ctx.state!=='running')return;const item=this.queue[0],buffer=this.ctx.createBuffer(1,item.data.length,item.rate);buffer.copyToChannel(item.data,0);const node=this.ctx.createBufferSource();node.buffer=buffer;node.connect(this.ctx.destination);this.node=node;this.started=this.ctx.currentTime;node.onended=()=>{if(this.node!==node)return;this.node=null;this.queue.shift();this.offset=0;this.play();};node.start(0,this.offset);}
  pause(){this.paused=true;if(this.node){const node=this.node;this.offset+=this.ctx.currentTime-this.started;this.node=null;node.onended=null;node.stop();if(this.queue.length&&this.offset>=this.queue[0].data.length/this.queue[0].rate){this.queue.shift();this.offset=0;}}}
  resume(){this.paused=false;this.play();}
  clear(){this.pause();this.queue=[];this.offset=0;this.paused=false;}
  async close(){this.clear();if(this.ctx)await this.ctx.close();}
}
const playback=new Playback();
async function microphone(enabled){
  if(!enabled){listening=false;transportPaused=false;send({type:'listen',enabled:false});if(stream)stream.getTracks().forEach(t=>t.stop());if(capture)capture.disconnect();if(source)source.disconnect();if(context)await context.close();stream=context=capture=source=null;}
  else {
    await playback.unlock();stream=await navigator.mediaDevices.getUserMedia({audio:{channelCount:1,echoCancellation:true,noiseSuppression:true,autoGainControl:true}});
    context=new AudioContext({sampleRate:16000});if(context.sampleRate!==16000)throw Error('16 kHz capture unavailable. Type instead.');
    await context.audioWorklet.addModule('/pcm-worklet.js');source=context.createMediaStreamSource(stream);capture=new AudioWorkletNode(context,'simplicity-capture');
    capture.port.onmessage=event=>{if(listening&&!muted&&ws.readyState===WebSocket.OPEN){
      if(ws.bufferedAmount>128000){if(!transportPaused){transportPaused=true;send({type:'listen',enabled:false});send({type:'client_event',event:'audio_backpressure'});status('Audio delayed — keeping voice on; please repeat after it resumes.');}return;}
      if(transportPaused){if(ws.bufferedAmount>16000)return;transportPaused=false;send({type:'listen',enabled:true});send({type:'client_event',event:'audio_resumed'});status('Listening resumed — please repeat the last phrase.');}
      ws.send(event.data);
    }};
    send({type:'listen',enabled:true});listening=true;muted=false;source.connect(capture);capture.connect(context.destination);await context.resume();
  }
  $('talk').textContent=listening?'Stop talking':'Talk';$('talk').setAttribute('aria-pressed',String(listening));$('mute').disabled=!listening;$('mute').textContent='Mute mic';status(listening?'Listening — you can speak now.':'Voice off. You can type.');
}
ws.onopen=()=>send({token});
ws.onmessage=event=>{
  const value=JSON.parse(event.data),kind=value.type;
  if(kind!=='audio'){activity.push(value);if(/timing|activity|review/.test(kind))evidence.push(value);}
  if(kind==='ready'){ready=true;$('talk').disabled=$('send').disabled=false;status(value.text);}
  else if(kind==='status')status(value.text);
  else if(kind==='findings')findings(value.view);
  else if(kind==='activity'&&['action','status'].includes(value.activity_kind))status(value.text);
  else if(kind==='transcript.partial'){$('partial').textContent=voiceDisplay(value.text);scroll();}
  else if(kind==='transcript.final')$('partial').textContent='';
  else if(kind==='voice.pause'){playback.pause();send({type:'playback',retained:playback.queue.length>0});}
  else if(kind==='voice.resume')playback.resume();
  else if(kind==='audio.clear')playback.clear();
  else if(kind==='voice.stop'){playback.clear();if(value.listening===false)microphone(false);else status('Reply stopped. Listening — you can speak now.');}
  else if(kind==='task.cancelled'){playback.clear();busy=false;message(value.source==='voice'?voiceDisplay(value.text):value.text,'user');copyButton(message(value.reply,'assistant'));status(listening?'Task stopped. Listening.':'Task stopped.');}
  else if(kind==='turn.start'){currentTurn=value.turn;busy=true;playback.clear();message(value.source==='voice'?voiceDisplay(value.text):value.text,'user');answer=message('','assistant');status('Thinking…');}
  else if(kind==='text.delta'&&value.turn===currentTurn){answer.querySelector('span').textContent+=value.text;status('Replying…');scroll();}
  else if(kind==='audio'&&value.turn===currentTurn)playback.add(value);
  else if(kind==='turn.done'||kind==='turn.stopped'){busy=false;if(answer)copyButton(answer);status(listening?'Listening — you can speak now.':'Reply ready.');}
  else if(kind==='review')status('Please type or repeat that short phrase: '+value.text);
  else if(kind==='error'){busy=false;playback.clear();status(value.text);}
  else if(kind==='chat.reset'){$('messages').replaceChildren();$('partial').textContent='';answer=null;activity.length=evidence.length=0;status('New chat ready.');}
};
ws.onclose=async()=>{ready=false;await microphone(false);playback.clear();$('talk').disabled=$('send').disabled=true;status('Session closed. Reopen the pilot to reconnect.');};
$('talk').onclick=()=>microphone(!listening).catch(async error=>{await microphone(false);status(error.message);});
$('mute').onclick=()=>{muted=!muted;stream?.getAudioTracks().forEach(t=>t.enabled=!muted);send({type:'listen',enabled:!muted});$('mute').textContent=muted?'Unmute mic':'Mute mic';$('mute').setAttribute('aria-pressed',String(muted));status(muted?'Microphone muted.':'Listening — you can speak now.');};
$('sound').onclick=async()=>{sound=!sound;if(sound)await playback.unlock();else playback.clear();send({type:'sound',enabled:sound});$('sound').textContent=sound?'Sound on':'Sound off';$('sound').setAttribute('aria-pressed',String(sound));};
$('composer').onsubmit=async event=>{event.preventDefault();if(!ready)return;const text=$('text').value.trim();if(!text)return;await playback.unlock();send({type:'chat',text});$('text').value='';};
$('text').onkeydown=event=>{if(event.key==='Enter'&&!event.shiftKey){event.preventDefault();$('composer').requestSubmit();}};
$('stop').onclick=()=>{playback.clear();send({type:'cancel'});busy=false;status('Stopping reply…');};
$('new').onclick=()=>{if(busy){status('Stop the current reply before starting a new chat.');return;}playback.clear();send({type:'reset'});};
for(const [id,items] of [['activity',activity],['evidence',evidence]])$(id).onclick=()=>{$('detail-text').textContent=items.map(x=>JSON.stringify(x,null,2)).join('\n');$('details').showModal();};
$('copy-details').onclick=()=>navigator.clipboard.writeText($('detail-text').textContent).catch(()=>status('Select the evidence text to copy.'));
$('close-details').onclick=()=>$('details').close();
$('exit').onclick=async()=>{await microphone(false);await playback.close();send({type:'cancel'});await fetch('/shutdown',{method:'POST',headers:{'X-ThemHands-Token':token}});window.close();};
window.addEventListener('pagehide',()=>{stream?.getTracks().forEach(t=>t.stop());send({type:'close'});ws.close();});
