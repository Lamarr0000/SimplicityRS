// Execute the real client handlers with a simulated microphone and transport.
// No microphone device, browser or network is opened.
const assert=require('node:assert/strict'),fs=require('node:fs'),vm=require('node:vm');
const nodes=new Map(),sent=[];let stopped=0,shutdowns=0,windowCloses=0;
const node=(tag='div')=>({tag,textContent:'',disabled:false,children:[],dataset:{},style:{},append(...values){this.children.push(...values);},querySelector(selector){for(const child of this.children){if(child.tag===selector)return child;const found=child.querySelector?.(selector);if(found)return found;}return null;},setAttribute(){},getTracks(){return[];}});
class WS {static OPEN=1;constructor(){this.readyState=1;this.bufferedAmount=0;}send(data){sent.push(data);}close(){}}
class Audio {constructor(){this.sampleRate=16000;this.audioWorklet={addModule:async()=>{}};}async resume(){}async close(){}createMediaStreamSource(){return {connect(){},disconnect(){}};}}
class Worklet {constructor(){this.port={};}connect(){}disconnect(){}}
const track={stop(){stopped++;}},stream={getTracks:()=>[track],getAudioTracks:()=>[track]};
const sandbox={console,WebSocket:WS,AudioContext:Audio,AudioWorkletNode:Worklet,
 document:{body:{scrollHeight:100},createElement:tag=>node(tag),getElementById:id=>{if(!nodes.has(id))nodes.set(id,node());return nodes.get(id);}},
 navigator:{mediaDevices:{getUserMedia:async()=>stream}},location:{hash:'#test',pathname:'/',host:'localhost'},
 fetch:async(path,options)=>{assert.equal(path,'/shutdown');assert.equal(options.method,'POST');shutdowns++;return {ok:true};},
 history:{replaceState(){}},window:{addEventListener(){},scrollTo(){},close(){windowCloses++;}},setTimeout,clearTimeout};
vm.createContext(sandbox);vm.runInContext(fs.readFileSync(__dirname+'/client.js','utf8'),sandbox);
(async()=>{
 for(const event of [{type:'turn.start',turn:1,text:'test',source:'typed'},
                    {type:'turn.done',turn:1},{type:'error',text:'test error'}]){
   nodes.set('partial',node());nodes.get('partial').textContent='proceed';
   sandbox.nextEvent=event;
   vm.runInContext('ws.onmessage({data:JSON.stringify(nextEvent)})',sandbox);
   assert.equal(nodes.get('partial').textContent,'');
 }
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
 vm.runInContext('findings({title:"Storage",columns:["Drive","Free GiB"],rows:[["C:",12.5]],note:"Current Windows only"})',sandbox);
 const card=nodes.get('messages').children.at(-1);
 assert(card.querySelector('table'));assert(card.dataset.copyText.includes('C:\t12.5'));assert(card.querySelector('button'));
 await vm.runInContext('microphone(true)',sandbox);
 vm.runInContext('ws.onmessage({data:JSON.stringify({type:"app.exit",text:"Closing"})})',sandbox);
 await new Promise(resolve=>setTimeout(resolve,0));
 assert.equal(stopped,2);assert.equal(shutdowns,1);assert.equal(windowCloses,1);
 await vm.runInContext('exitPilot()',sandbox);assert.equal(shutdowns,1);
 console.log('PASS: app exit stops capture, requests shutdown, closes window and ignores duplicate exit.');
 console.log('PASS: audio backlog recovers without mic shutdown; reply stop keeps listening; explicit listening stop closes microphone.');
 console.log('PASS: measured facts render as a table and copy includes the table values.');
})().catch(error=>{console.error(error);process.exitCode=1;});
