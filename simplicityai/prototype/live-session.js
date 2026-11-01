/* Owns one opt-in live microphone session and invalidates interrupted transcripts. */
(()=>{
class LiveSession {
 constructor(context,options){this.context=context;this.options=options;this.turn=0;this.active=false;this.transcribing=false;this.phase='idle';}
 async start(muted=false){
  this.active=true;this.muted=muted;this.phase='starting';
  this.capture=new LiveVoice(this.context,{
   start:()=>this.started(),end:(audio,limited)=>this.ended(audio,limited),
   ready:settings=>{this.settings=settings;this.phase=this.muted?'muted':'listening';this.options.status(this.muted?'Microphone muted.':'Listening — you can interrupt a reply by speaking.');},
   error:error=>this.fail(error)
  });
  this.capture.muted=muted;
  try{
   await this.capture.start();if(!this.active)return;
   this.options.api('/voice/stream/prepare',{}).catch(error=>{if(this.active&&this.turn===0)this.fail(error);});
  }catch(error){this.fail(error);}
 }
 started(){
  if(!this.active||this.muted)return;
  this.turn++;this.phase='recording';
  if(this.transcribing){this.abort?.abort();this.transcribing=false;this.options.api('/voice/stream/stop',{}).catch(()=>{});}
  Promise.resolve(this.options.interrupt()).catch(error=>this.fail(error));
  this.options.status('Listening to your new message…');
 }
 async ended(audio,limited){
  if(!this.active||this.muted)return;
  const turn=this.turn;this.phase='transcribing';this.transcribing=true;this.abort=new AbortController();this.options.status('Transcribing your message locally…');
  try{
   const response=await fetch('/voice/stream/transcribe',{method:'POST',headers:{'X-ThemHands-Token':this.options.token,'Content-Type':'audio/wav'},body:audio,signal:this.abort.signal});
   const value=await response.json();if(!this.active||turn!==this.turn)return;
   if(!response.ok)throw Error(value.error||'Speech recognition unavailable');
   this.transcribing=false;this.phase='listening';
   if(value.text)await this.options.text(value.text,limited);
   else this.options.status('No clear words recognized. I am still listening.');
  }catch(error){if(this.active&&turn===this.turn&&error.name!=='AbortError')this.fail(error);}
 }
 mute(value){this.muted=value;this.turn++;this.capture?.mute(value);this.abort?.abort();if(this.transcribing)this.options.api('/voice/stream/stop',{}).catch(()=>{});this.transcribing=false;this.phase=value?'muted':'listening';}
 fail(error){this.stop();this.options.error(error);}
 stop(){this.active=false;this.turn++;this.phase='idle';this.capture?.stop();this.abort?.abort();this.options.api('/voice/stream/stop',{}).catch(()=>{});}
}
globalThis.LiveSession=LiveSession;
})();
