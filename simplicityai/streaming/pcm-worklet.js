// Newly written capture code: 512 mono samples per frame, no saved recording.
class Capture extends AudioWorkletProcessor {
  constructor(){super();this.frame=new Int16Array(512);this.used=0;}
  process(inputs){
    const source=inputs[0]?.[0];
    if(source) for(const sample of source){
      this.frame[this.used++]=Math.max(-32768,Math.min(32767,Math.round(sample*32768)));
      if(this.used===512){this.port.postMessage(this.frame.buffer,[this.frame.buffer]);this.frame=new Int16Array(512);this.used=0;}
    }
    return true;
  }
}
registerProcessor('simplicity-capture',Capture);
