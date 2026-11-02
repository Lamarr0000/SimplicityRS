"""Session-owned findings survive cancelled model turns; safe table presentation."""
import re

EMOJI=re.compile('[\U0001F1E6-\U0001FAFF\u2600-\u27BF\uFE0F\u200D]')


def clean_reply(text):return EMOJI.sub('',text)


def spoken_text(text):
    text=clean_reply(text)
    text=re.sub(r'\*\*([^*]+)\*\*|__([^_]+)__',lambda match:match[1] or match[2],text)
    text=re.sub(r'`([^`]+)`',r'\1',text)
    text=re.sub(r'\[([^\]]+)\]\([^)]+\)',r'\1',text)
    text=re.sub(r'^\s*#{1,6}\s*','',text)
    return re.sub(r'^\s*\*\*|\*\*\s*$','',text).strip()


def table_view(result):
    area=result.get('area','diagnostic');sections=result.get('sections',[])
    note='Measured in the Windows running SimplicityAI. This does not inspect another/offline Windows installation.'
    if result.get('simulation'):note='SIMULATION ONLY — synthetic records; no real measurement. '+note
    if area=='drivers':note+=' Installed driver records only; update availability was not checked.'
    if area=='storage':
        section=next((item for item in sections if any('DeviceID' in row for row in item.get('data',[]))),{})
        columns=['Drive','Free GiB','Total GiB','Free %']
        rows=[[row.get('DeviceID'),row.get('FreeGiB','Unknown'),row.get('SizeGiB','Unknown'),row.get('FreePercent','Unknown')] for row in section.get('data',[])]
    elif area=='processes':
        columns=['Process','PID','CPU % of machine']
        rows=[[row.get('name'),row.get('pid'),row.get('cpu_percent_of_machine')] for row in result.get('top_processes',[])]
        note+=' Short CPU-time sample, not a diagnosis or memory ranking.'
    elif area=='devices':
        columns=['Device','Class','Problem code','Status'];rows=[]
        for section in sections:
            rows.extend([[r.get('Name'),r.get('PNPClass'),r.get('ConfigManagerErrorCode'),r.get('Status')] for r in section.get('data',[]) if r.get('ConfigManagerErrorCode') not in (None,0)])
        if not rows:
            rows=[['No nonzero problem code in returned records','', '', 'See inventory bounds']] if any(s.get('status')=='available' for s in sections) else [['Device inventory unavailable','Unknown','Unknown','Unknown']]
    elif area=='drivers':
        columns=['Device','Provider','Version','Signed']
        rows=[[r.get('DeviceName'),r.get('DriverProviderName'),r.get('DriverVersion'),r.get('IsSigned')] for s in sections for r in s.get('data',[])]
    else:
        columns=['Check','Status','Details'];rows=[]
        for section in sections:
            detail=section.get('reason') or f"{section.get('returned_count',len(section.get('data',[])))} returned records"
            rows.append([section.get('name'),section.get('status','unknown'),detail])
    if not rows:rows=[['No records returned']+['Unknown']*(len(columns)-1)]
    unavailable=[s.get('reason','Unavailable') for s in sections if s.get('status')=='unknown']
    if unavailable:note+=' Unavailable checks: '+'; '.join(unavailable)[:500]
    if any(s.get('truncated') for s in sections):note+=' Inventory is bounded; use a focused query for omitted records.'
    return {'title':area.capitalize()+' — measured facts','columns':columns,'rows':rows[:12],
            'note':note,'checked_utc':result.get('checked_utc'),'area':area}


def table_text(view):
    cell=lambda value:str('Unknown' if value is None else value).replace('|','/').replace('\n',' ')
    return view['title']+'\n\n'+'| '+' | '.join(view['columns'])+' |\n'+'| '+' | '.join(['---']*len(view['columns']))+' |\n'+'\n'.join('| '+' | '.join(map(cell,row))+' |' for row in view['rows'])+'\n\n'+view['note']
