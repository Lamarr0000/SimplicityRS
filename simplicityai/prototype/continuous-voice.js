/* Opt-in continuous capture. All raw audio is bounded memory, posted only locally. */
(()=>{
class SpeechGate {
 constructor(rate,callbacks){this.rate=rate;this.callbacks=callbacks;this.noise=.0005;this.reset();}
 reset(){this.pre=[];this.preSamples=0;this.candidate=0;this.active=false;this.frames=[];this.length=0;this.silence=0;}
 push(samples){
  const block=new Float32Array(samples);const seconds=block.length/this.rate;
  let sum=0;for(const value of block)sum+=value*value;const rms=Math.sqrt(sum/block.length);
  const threshold=Math.max(.003,this.noise*3.5);const voiced=rms>threshold;
  if(!this.active){
   if(!voiced)this.noise=.98*this.noise+.02*rms;
   this.pre.push(block);this.preSamples+=block.length;
   while(this.preSamples>this.rate*.5&&this.pre.length>1)this.preSamples-=this.pre.shift().length;
   this.candidate=voiced?this.candidate+seconds:0;
   if(this.candidate>=.16){this.active=true;this.frames=this.pre;this.length=this.preSamples;this.pre=[];this.preSamples=0;this.callbacks.start();}
  }else{
   this.frames.push(block);this.length+=block.length;this.silence=voiced?0:this.silence+seconds;
   if(this.silence>=.9||this.length>=this.rate*25){
    const limited=this.length>=this.rate*25;const frames=this.frames;this.reset();this.callbacks.end(frames,limited);
   }
  }
 }
}
function encodeWave(frames,rate){
 const count=frames.reduce((sum,frame)=>sum+frame.length,0),buffer=new ArrayBuffer(44+count*2),view=new DataView(buffer);
 const text=(offset,value)=>{for(let i=0;i<value.length;i++)view.setUint8(offset+i,value.charCodeAt(i));};
 text(0,'RIFF');view.setUint32(4,36+count*2,true);text(8,'WAVE');text(12,'fmt ');view.setUint32(16,16,true);view.setUint16(20,1,true);view.setUint16(22,1,true);view.setUint32(24,rate,true);view.setUint32(28,rate*2,true);view.setUint16(32,2,true);view.setUint16(34,16,true);text(36,'data');view.setUint32(40,count*2,true);
 let offset=44;for(const frame of frames)for(const value of frame){view.setInt16(offset,Math.round(Math.max(-1,Math.min(1,value))*32767),true);offset+=2;}
 return buffer;
}
class LiveVoice {
 constructor(context,callbacks){this.context=context;this.callbacks=callbacks;this.generation=0;this.muted=false;this.stream=null;}
 async start(){
  const generation=++this.generation;
  if(!this.context?.audioWorklet)throw Error('Continuous audio is unavailable in this window. Typing remains available.');
  const stream=await navigator.mediaDevices.getUserMedia({audio:{echoCancellation:true,noiseSuppression:true,autoGainControl:true,channelCount:1},video:false});
  if(generation!==this.generation){stream.getTracks().forEach(track=>track.stop());return;}
  this.stream=stream;
  try{
   await this.context.audioWorklet.addModule('/voice-processor.js');
   if(generation!==this.generation)return;
   this.source=this.context.createMediaStreamSource(stream);
   this.processor=new AudioWorkletNode(this.context,'simplicity-microphone');
   this.gate=new SpeechGate(this.context.sampleRate,{start:()=>this.callbacks.start(),end:(frames,limited)=>this.callbacks.end(encodeWave(frames,this.context.sampleRate),limited)});
   this.processor.port.onmessage=event=>{if(generation===this.generation&&!this.muted)this.gate.push(event.data);};
   this.source.connect(this.processor);this.processor.connect(this.context.destination);
   this.mute(this.muted);this.callbacks.ready(stream.getAudioTracks()[0]?.getSettings?.()||{});
   stream.getAudioTracks()[0]?.addEventListener('ended',()=>{if(generation===this.generation){this.stop();this.callbacks.error(Error('Microphone disconnected. You can type instead.'));}});
  }catch(error){this.stop();throw error;}
 }
 mute(value){this.muted=value;this.gate?.reset();this.stream?.getAudioTracks().forEach(track=>{track.enabled=!value;});}
 stop(){this.generation++;if(this.processor){this.processor.port.onmessage=null;this.processor.port.close?.();this.processor.disconnect();}this.source?.disconnect();this.stream?.getTracks().forEach(track=>track.stop());this.stream=null;this.gate?.reset();}
}
globalThis.SimplicitySpeechGate=SpeechGate;globalThis.SimplicityWave=encodeWave;globalThis.LiveVoice=LiveVoice;
})();
