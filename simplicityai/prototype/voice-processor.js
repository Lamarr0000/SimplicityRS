// AudioWorklet runs off the UI thread; emits ~21ms blocks at 48 kHz.
class SimplicityMicrophone extends AudioWorkletProcessor {
 constructor(){super();this.block=new Float32Array(1024);this.used=0;}
 process(inputs,outputs){
  const input=inputs[0]?.[0];
  if(input)for(let i=0;i<input.length;i++){this.block[this.used++]=input[i];if(this.used===1024){const block=this.block;this.port.postMessage(block,[block.buffer]);this.block=new Float32Array(1024);this.used=0;}}
  // Output stays silent. The microphone is never looped to speakers.
  return true;
 }
}
registerProcessor('simplicity-microphone',SimplicityMicrophone);
