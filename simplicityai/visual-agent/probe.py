"""Image-only local grounding gate. Never sends desktop input or captures user screens."""
import ast
import base64
import io
import json
import re
import time
import urllib.request
import urllib.error
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

ROOT = Path('C:/SimplicityAI-Lab/VisualAgent')
URL = 'http://127.0.0.1:8772/v1/chat/completions'


def parse_click(text, width, height):
    """UI-TARS 1.5 coordinates use the resized image's pixel space (upstream guide)."""
    actions = re.findall(r'^Action:\s*(.+)$', text, re.M)
    if len(actions) != 1:
        raise ValueError('Expected exactly one Action line')
    call = ast.parse(actions[0].strip(), mode='eval').body
    if not isinstance(call, ast.Call) or not isinstance(call.func, ast.Name):
        raise ValueError('Invalid action')
    if call.func.id != 'click' or call.args or len(call.keywords) != 1:
        raise ValueError('This probe only accepts one literal click(start_box=...)')
    key = call.keywords[0]
    if key.arg != 'start_box':
        raise ValueError('Expected start_box')
    box = ast.literal_eval(key.value)
    if not isinstance(box, str):
        raise ValueError('Expected coordinate string')
    box = box.replace('<|box_start|>', '').replace('<|box_end|>', '')
    coords = ast.literal_eval(box)
    if not isinstance(coords, (list, tuple)) or len(coords) not in (2, 4):
        raise ValueError('Invalid coordinate count')
    limits = (width, height) if len(coords) == 2 else (width, height, width, height)
    if any(type(v) not in (int, float) or not 0 <= v < limit
           for v, limit in zip(coords, limits)):
        raise ValueError('Coordinates outside image')
    x, y = coords[:2]
    if len(coords) == 4:
        x, y = (x+coords[2])/2, (y+coords[3])/2
    return x, y


def main():
    ROOT.mkdir(parents=True, exist_ok=True)
    deadline = time.monotonic()+120
    while True:
        try:
            with urllib.request.urlopen('http://127.0.0.1:8772/health', timeout=3) as response:
                if json.load(response).get('status') == 'ok':
                    break
        except (urllib.error.URLError, TimeoutError):
            pass
        if time.monotonic() >= deadline:
            raise TimeoutError('Local model did not become ready in 120 seconds')
        time.sleep(1)
    font = ImageFont.truetype('C:/Windows/Fonts/segoeui.ttf', 25)
    results = []
    # Dimensions are multiples of 28 and provide >=1024 vision tokens, avoiding
    # implicit resizing. Targets occupy left, middle and right across the cases.
    for index, target in enumerate(['Network', 'Storage', 'Devices']):
        image = Image.new('RGB', (1120, 784), '#edf1f7')
        draw = ImageDraw.Draw(image)
        draw.text((40, 35), 'Recovery diagnostics - visual fixture', fill='#152138', font=font)
        boxes = {}
        labels = ['Network', 'Devices', 'Storage']
        labels = labels[index:]+labels[:index]
        for position, label in enumerate(labels):
            box = (90+position*295, 250, 345+position*295, 340)
            boxes[label] = box
            draw.rounded_rectangle(box, 10, fill='#244c85')
            draw.text((box[0]+35, box[1]+25), label, fill='white', font=font)
        path = ROOT/f'grounding-{index}.png'
        image.save(path)
        stream = io.BytesIO()
        image.save(stream, format='PNG')
        prompt = ("You are a GUI agent. Given a task and screenshot, perform the next action.\n"
                  "Output Format: Action: click(start_box='<|box_start|>(x,y)<|box_end|>')\n"
                  f"User Instruction: Click the {target} button.")
        payload = {'model':'ui-tars', 'messages':[{'role':'user','content':[
            {'type':'text','text':prompt}, {'type':'image_url','image_url':{
                'url':'data:image/png;base64,'+base64.b64encode(stream.getvalue()).decode()}}]}],
            'temperature':0, 'max_tokens':256}
        started = time.perf_counter()
        request = urllib.request.Request(URL, json.dumps(payload).encode(),
                                         {'Content-Type':'application/json'})
        with urllib.request.urlopen(request, timeout=180) as response:
            data = json.load(response)
        text = data['choices'][0]['message']['content']
        row = {'target':target, 'seconds':round(time.perf_counter()-started, 3),
               'output':text, 'usage':data.get('usage'), 'timings':data.get('timings')}
        try:
            x, y = parse_click(text, *image.size)
            left, top, right, bottom = boxes[target]
            row.update(coordinates=[x,y], correct=left <= x <= right and top <= y <= bottom)
        except (ValueError, TypeError, SyntaxError) as error:
            row.update(correct=False, error=str(error))
        results.append(row)
        (ROOT/'grounding-results.json').write_text(json.dumps(results, indent=2), encoding='utf-8')
        print(json.dumps(row), flush=True)
    return 0 if all(row['correct'] for row in results) else 1


if __name__ == '__main__':
    raise SystemExit(main())
