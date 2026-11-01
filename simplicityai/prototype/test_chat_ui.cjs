const fs=require('fs'),vm=require('vm'),assert=require('assert');
const html=fs.readFileSync(require('path').join(__dirname,'index.html'),'utf8');
const ids=[...html.matchAll(/id="([^"]+)"/g)].map(m=>m[1]);assert.equal(new Set(ids).size,ids.length);
assert(!html.includes('id="speech-voice"'));assert(html.includes('Advanced tools and test modes'));
const script=html.match(/<script>([\s\S]*?)<\/script>/)[1].replace('poll();setInterval(poll,1000);','');
const elements={},requests=[];let copied='',audioCount=0;
const element=id=>elements[id]??={value:'',textContent:'',hidden:false,style:{},replaceChildren(){},append(){}};
const context=vm.createContext({document:{getElementById:element,createElement:()=>({style:{},append(){}})},navigator:{clipboard:{writeText:async text=>{copied=text}}},location:{hash:'',pathname:'/'},sessionStorage:{getItem(){return ''}},history:{replaceState(){}},console,
 fetch:async(path,options)=>{requests.push(path);return {ok:true,json:async()=>({ok:true}),blob:async()=>({})}},
 URL:{createObjectURL:()=> 'blob:local',revokeObjectURL(){}},Audio:function(){audioCount++;this.play=async()=>{};this.pause=()=>{}}});
vm.runInContext(script,context);
(async()=>{
 element('symptoms').value='Websites will not load';element('prepare-guide').onclick();
 assert.equal(element('target-question').hidden,false);assert.equal(requests.length,0);
 element('target-current').onclick();assert.equal(element('mode').value,'network');assert.equal(element('next-actions').hidden,false);assert.equal(requests.length,0);
 element('target-other').onclick();assert.equal(element('start').disabled,true);assert.equal(element('next-actions').hidden,true);
 element('target').value='current';element('symptoms').value='Windows keeps crashing';element('prepare-guide').onclick();assert.equal(element('mode').value,'integrity');
 element('symptoms').value='';element('voice-draft').value='Websites do not load';element('voice-use').onclick();assert.equal(element('symptoms').value,'Websites do not load');assert.equal(requests.length,0);
 for(const [id,variable,text] of [['copy-reply','replyText','ANSWER'],['copy-facts','factsText','FACTS'],['copy-evidence','evidenceText','LOG']]){vm.runInContext(`${variable}=${JSON.stringify(text)}`,context);await element(id).onclick();assert.equal(copied,text);}
 await vm.runInContext("speakText('Hello')",context);assert.equal(audioCount,1);assert(requests.includes('/speech/read'));
 await vm.runInContext('stopSpeech()',context);assert(requests.includes('/speech/stop'));
 await vm.runInContext("speakText('x'.repeat(2001))",context);assert.equal(audioCount,1);
 console.log('Chat target questions, no automatic task starts, reviewed voice text, isolated Copy controls, fixed Kokoro playback and Stop passed.');
})().catch(error=>{console.error(error);process.exitCode=1});
