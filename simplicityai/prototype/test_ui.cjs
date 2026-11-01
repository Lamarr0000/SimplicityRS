const fs=require('fs'),vm=require('vm'),assert=require('assert');
const html=fs.readFileSync(require('path').join(__dirname,'index.html'),'utf8');
const script=html.match(/<script>([\s\S]*?)<\/script>/)[1].replace('poll();setInterval(poll,1000);','');
const elements={};const elem=id=>elements[id]??=( {textContent:'',replaceChildren(){},append(){},style:{}} );
let copied='';const context=vm.createContext({document:{getElementById:elem,createElement:()=>({style:{},append(){}})},navigator:{clipboard:{writeText:async text=>{copied=text}}},location:{hash:'',pathname:'/'},sessionStorage:{getItem(){return ''}},history:{replaceState(){}},console});
vm.runInContext(script,context);
(async()=>{
 for(const [id,variable,text] of [['copy-reply','replyText','ANSWER ONLY'],['copy-facts','factsText','FACTS ONLY'],['copy-evidence','evidenceText','RAW TOOL EVIDENCE']]){
  vm.runInContext(`${variable}=${JSON.stringify(text)}`,context);await elem(id).onclick();assert.equal(copied,text);
 }
 context.navigator.clipboard.writeText=async()=>{throw Error('denied')};
 await elem('copy-facts').onclick();assert.match(elem('facts-copy-status').textContent,/Copy unavailable/);
 assert.equal((html.match(/class="panel-header"/g)||[]).length,3);
 elem('problem').value='web';elem('target').value='other';elem('prepare-guide').onclick();assert.equal(elem('start').disabled,true);assert.match(elem('guide-plan').textContent,/cannot inspect/);elem('target').value='current';elem('symptoms').value='Test symptom';elem('prepare-guide').onclick();assert.equal(elem('mode').value,'network');assert.equal(elem('start').disabled,false);elem('problem').value='crash';elem('prepare-guide').onclick();assert.equal(elem('mode').value,'integrity');console.log('Guided target restriction and check routing passed.'); console.log('Three isolated copy actions, clipboard failure feedback, and three panel headers passed.');
})().catch(e=>{console.error(e);process.exitCode=1});


