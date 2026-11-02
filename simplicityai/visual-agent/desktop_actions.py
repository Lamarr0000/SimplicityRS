"""Literal UI-TARS action decoding. No model-authored code is executed."""
import ast
import re
from probe import parse_click

KEYS = {'ctrl','alt','shift','enter','return','tab','esc','escape','space','backspace',
        'home','end','left','right','up','down','pageup','pagedown','f1','f2','f3','f4',
        'f5','f6','f7','f8','f9','f10','f11','f12'}


def requested_app(task,apps):
    """Route only an explicit leading launch request, using the existing catalog."""
    text=task.strip().lower()
    text=re.sub(r'^(?:(?:please|can you|could you)\s+)+','',text)
    match=re.match(r'^(?:open|launch|start)\s+(?:up\s+)?(?:the\s+)?(.+)$',text)
    if not match:return None
    rest=match[1]
    matches=[app for app in apps if re.match(re.escape(app.replace('_',' '))+
        r'(?=$|[.?!,;:]|\s+(?:and|then|to|please)\b)',rest)]
    return max(matches,key=len) if matches else None


def decode(text,width,height,apps=()):
    lines=re.findall(r'^Action:\s*(.+)$',text,re.M)
    if not lines and len(text.strip().splitlines())==1: lines=[text.strip()]
    if len(lines)!=1: raise ValueError('Expected one action')
    node=ast.parse(lines[0],mode='eval').body
    if not isinstance(node,ast.Call) or not isinstance(node.func,ast.Name) or node.args:
        raise ValueError('Expected a literal named action')
    name=node.func.id
    if any(item.arg is None for item in node.keywords): raise ValueError('Expanded arguments are not supported')
    args={item.arg:ast.literal_eval(item.value) for item in node.keywords}
    if len(args)!=len(node.keywords): raise ValueError('Duplicate arguments')
    if name=='open_app' and set(args)=={'name'} and args['name'] in apps:
        return {'kind':name,'name':args['name']}
    if name in {'click','left_double','right_single'} and set(args)=={'start_box'}:
        canonical='Action: click(start_box='+repr(args['start_box'])+')'
        return {'kind':name,'point':parse_click(canonical,width,height)}
    if name=='type' and set(args)=={'content'} and isinstance(args['content'],str):
        content=args['content']
        if not content or len(content)>2000 or any(ord(ch)<32 for ch in content.rstrip('\n')):
            raise ValueError('Type requires 1–2000 literal characters and optional final newline')
        return {'kind':name,'content':content.rstrip('\n'),'submit':content.endswith('\n')}
    if name=='hotkey' and set(args)=={'key'} and isinstance(args['key'],str):
        keys=args['key'].lower().replace('+',' ').split()
        if not 1<=len(keys)<=3 or any(key not in KEYS and not re.fullmatch('[a-z0-9]',key) for key in keys):
            raise ValueError('Unsupported key combination')
        return {'kind':name,'shortcut':'+'.join('enter' if key=='return' else key for key in keys)}
    if name=='scroll' and set(args)=={'start_box','direction'} and args['direction'] in {'up','down','left','right'}:
        point=parse_click('Action: click(start_box='+repr(args['start_box'])+')',width,height)
        return {'kind':name,'point':point,'direction':args['direction']}
    if name=='drag' and set(args)=={'start_box','end_box'}:
        points=[parse_click('Action: click(start_box='+repr(args[key])+')',width,height)
                for key in ('start_box','end_box')]
        return {'kind':name,'point':points[0],'end':points[1]}
    if name=='wait' and not args:return {'kind':name}
    if name in {'finished','call_user'} and set(args)<= {'content'}:
        content=args.get('content','')
        if not isinstance(content,str) or len(content)>2000:raise ValueError('Invalid final message')
        return {'kind':name,'content':content}
    raise ValueError('Unsupported action or argument shape')


def to_screen(point, image_size, screen_size, origin=(0,0)):
    x,y=point
    w,h=image_size
    sw,sh=screen_size
    if not (0<=x<w and 0<=y<h):raise ValueError('Point outside screenshot')
    return [origin[0]+min(sw-1,round(x*sw/w)),origin[1]+min(sh-1,round(y*sh/h))]
