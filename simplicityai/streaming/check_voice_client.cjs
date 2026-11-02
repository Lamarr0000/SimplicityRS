// Execute the real client handlers with a simulated microphone and transport.
// No microphone device, browser or network is opened.
const assert=require('node:assert/strict'),fs=require('node:fs'),vm=require('node:vm');
const nodes=new Map(),sent=[];let stopped=0;
const node=()=>({textContent:'',disabled:false,setAttribute(){},getTracks(){return[];}});
class WS {static OPEN=1;constructor(){this.readyState=1;this.bufferedAmount=0;}send(data){sent.push(data);}close(){}}
class Audio {constructor(){this.sampleRate=16000;this.audioWorklet={addModule:async()=>{}};}async resume(){}async close(){}createMediaStreamSource(){return {connect(){},disconnect(){}};}}
class Worklet {constructor(){this.port={};}connect(){}disconnect(){}}
const track={stop(){stopped++;}},stream={getTracks:()=>[track],getAudioTracks:()=>[track]};
const sandbox={console,WebSocket:WS,AudioContext:Audio,AudioWorkletNode:Worklet,
 document:{getElementById:id=>{if(!nodes.has(id))nodes.set(id,node());return nodes.get(id);}},
 navigator:{mediaDevices:{getUserMedia:async()=>stream}},location:{hash:'#test',pathname:'/',host:'localhost'},
 history:{replaceState(){}},window:{addEventListener(){}},setTimeout,clearTimeout};
vm.createContext(sandbox);vm.runInContext(fs.readFileSync(__dirname+'/client.js','utf8'),sandbox);
(async()=>{
 await vm.runInContext('microphone(true)',sandbox);
 vm.runInContext('ws.bufferedAmount=129000;capture.port.onmessage({data:new ArrayBuffer(1024)})',sandbox);
 assert.equal(vm.runInContext('listening && transportPaused',sandbox),true);assert.equal(stopped,0);
 vm.runInContext('ws.bufferedAmount=0;capture.port.onmessage({data:new ArrayBuffer(1024)})',sandbox);
 assert.equal(vm.runInContext('listening && !transportPaused',sandbox),true);
 assert(sent.some(value=>typeof value==='string'&&value.includes('audio_resumed')));
 vm.runInContext('ws.onmessage({data:JSON.stringify({type:"voice.stop",listening:true})})',sandbox);
 assert.equal(vm.runInContext('listening',sandbox),true);assert.equal(stopped,0);
 vm.runInContext('ws.onmessage({data:JSON.stringify({type:"voice.stop",listening:false})})',sandbox);
 await new Promise(resolve=>setTimeout(resolve,0));
 assert.equal(vm.runInContext('listening',sandbox),false);assert.equal(stopped,1);
 console.log('PASS: audio backlog recovers without mic shutdown; reply stop keeps listening; explicit listening stop closes microphone.');
})().catch(error=>{console.error(error);process.exitCode=1;});
