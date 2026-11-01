const fs=require('fs'),vm=require('vm'),assert=require('assert');
const html=fs.readFileSync(require('path').join(__dirname,'index.html'),'utf8');
assert(!html.includes('<select'));assert(!html.includes('Show my next step'));
const ids=[...html.matchAll(/id="([^"]+)"/g)].map(m=>m[1]);assert.equal(ids.length,new Set(ids).size);
const script=html.match(/<script>([\s\S]*?)<\/script>/)[1].replace('poll();setInterval(poll,1000);','');
const elements={},requests=[],order=[];let copied='',starts=0,lastNode=null;
const make=()=>({value:'',textContent:'',hidden:false,children:[],replaceChildren(){this.children=[]},append(...children){this.children.push(...children)},setAttribute(){}});
const el=id=>elements[id]??=make();
let state={busy:false,status:'Ready',events:[],health_snapshot:null,chat_transcript:[]},voice={state:'idle',capture_id:0};
const fetcher=async(path,options)=>{requests.push({path,body:options?.body?JSON.parse(options.body):null});order.push(path);return {ok:true,json:async()=>path==='/state'?state:path==='/voice/state'?voice:{ok:true},arrayBuffer:async()=>new ArrayBuffer(4)}};
const sandbox=vm.createContext({console,document:{getElementById:el,createElement:make},navigator:{clipboard:{writeText:async text=>{copied=text}}},location:{hash:'',pathname:'/'},sessionStorage:{getItem(){return ''}},history:{replaceState(){}},fetch:fetcher,
 AudioContext:function(){this.state='suspended';this.destination={};this.resume=async()=>{order.push('resume');this.state='running'};this.decodeAudioData=async()=>({});this.createBufferSource=()=>{lastNode={connect(){},disconnect(){},stop(){},start(){starts++}};return lastNode}}});
vm.runInContext(script,sandbox);const tick=()=>new Promise(setImmediate);
(async()=>{
 assert.equal(requests.length,0);
 el('message').value='My computer freezes';state={...state,busy:true,status:'Thinking',chat_transcript:[{id:0,role:'user',content:'My computer freezes'}]};
 await el('send').onclick();assert.equal(requests.find(r=>r.path==='/start').body.mode,'chat');assert(order.indexOf('resume')<order.indexOf('/start'));
 state={...state,busy:false,chat_transcript:[...state.chat_transcript,{id:1,role:'assistant',content:'When did this start?'}]};
 await vm.runInContext('poll()',sandbox);await tick();assert.equal(starts,1);assert.equal(requests.filter(r=>r.path==='/voice/start').length,0);
 await el('chat').children.at(-1).children[0].children[0].onclick();assert.equal(copied,'When did this start?');
 vm.runInContext('autoNext=true',sandbox);state={...state,busy:true,chat_transcript:[...state.chat_transcript,{id:2,role:'assistant',content:'Another reply'}]};
 await vm.runInContext('poll()',sandbox);await tick();assert.equal(starts,1);
 state.busy=false;await vm.runInContext('poll()',sandbox);await tick();assert.equal(starts,2);
 let resolve;sandbox.fetch=(path,options)=>path==='/speech/read'?new Promise(r=>resolve=r):fetcher(path,options);
 const pending=vm.runInContext("speak('Late reply')",sandbox);await vm.runInContext('stopSpeech()',sandbox);resolve({ok:true,arrayBuffer:async()=>new ArrayBuffer(4)});await pending;assert.equal(starts,2);
 sandbox.fetch=fetcher;await el('talk').onclick();assert.equal(requests.filter(r=>r.path==='/voice/start').length,1);
 await el('stop').onclick();assert(requests.some(r=>r.path==='/voice/stop'));
 console.log('Conversation UI passed: no forms or automatic capture, chat submission, audio unlock before async work, automatic spoken reply, Copy, completion race, cancellation and explicit Talk/Stop.');
})().catch(error=>{console.error(error);process.exitCode=1});
