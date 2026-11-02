"""Evidence-based session export and bounded current-Windows CPU sampling."""
from datetime import datetime
import time
import psutil
from desktop_tools import create_text


def export_conversation(transcript,filename=None,folder=None):
    messages=[dict(message) for message in transcript if message.get('role') in {'user','assistant'}]
    if not messages:raise ValueError('There is no recorded conversation to export')
    filename=filename or datetime.now().strftime('Conversation-%Y%m%d-%H%M%S-%f.txt')
    heading=('SimplicityAI recorded conversation\n'
             'Raw recognized wording is preserved. Export includes recorded user and assistant messages\n'
             'through the export request; it cannot include the later export confirmation.\n\n')
    content=heading+'\n\n'.join(f"{message['role'].capitalize()}:\n{message.get('content','')}" for message in messages)+'\n'
    result=create_text(filename,content,folder,max_bytes=4_000_000)
    return {**result,'source':'app-recorded transcript, not model reconstruction','message_count':len(messages),
            'user_messages':sum(message['role']=='user' for message in messages),
            'assistant_messages':sum(message['role']=='assistant' for message in messages),
            'through_message_id':messages[-1].get('id'),'includes_export_confirmation':False}


def sample_cpu(check_stop,duration=1.0):
    check_stop();started=time.monotonic();processes=[];denied=0
    for process in psutil.process_iter(['pid','name','create_time']):
        try:
            if process.pid==0:continue
            cpu=process.cpu_times();processes.append((process,process.info,cpu.user+cpu.system))
        except (psutil.Error,OSError):denied+=1
    started=time.monotonic()
    while time.monotonic()-started<duration:
        check_stop();time.sleep(.025)
    elapsed=time.monotonic()-started;cores=psutil.cpu_count() or 1;rows=[];gone=0
    for process,info,before in processes:
        check_stop()
        try:
            if process.create_time()!=info['create_time']:gone+=1;continue
            cpu=process.cpu_times();percent=max(0,min(100,(cpu.user+cpu.system-before)/elapsed/cores*100))
            rows.append({'pid':process.pid,'name':info['name'],'cpu_percent_of_machine':round(percent,2)})
        except (psutil.Error,OSError):gone+=1
    rows.sort(key=lambda row:row['cpu_percent_of_machine'],reverse=True)
    return {'checked_local':datetime.now().astimezone().isoformat(),'sample_seconds':round(elapsed,3),
            'logical_processors':cores,'top_processes':rows[:10],
            'highest_sampled_process':rows[0] if rows and rows[0]['cpu_percent_of_machine']>0 else None,
            'unavailable_at_start':denied,'exited_or_unavailable_after':gone,'changes_made':False,
            'scope':'Windows running SimplicityAI only',
            'limitations':'Short CPU-time sample normalized across logical processors, not Task Manager CPU Utility. Not lifetime CPU, memory ranking or a diagnosis. Newly started/unavailable processes are not ranked.'}
