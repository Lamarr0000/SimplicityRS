"""Bounded screenshot/action/feedback test in a simulated UI, never the user's desktop."""
import base64
import io
import json
import time
import urllib.request
from PIL import Image, ImageDraw, ImageFont
from probe import ROOT, URL, parse_click


def main():
    font = ImageFont.truetype('C:/Windows/Fonts/segoeui.ttf', 25)
    state = 0
    injected_miss = False
    records = []
    history = []
    for step in range(8):
        image = Image.new('RGB', (1120, 784), '#edf1f7')
        draw = ImageDraw.Draw(image)
        draw.text((40, 35), 'Recovery diagnostics - simulated interface', fill='#152138', font=font)
        boxes = {}
        if state == 0:
            title = 'Choose a diagnostic area'
            labels = ['Devices','Network','Storage'] if injected_miss else ['Storage','Devices','Network']
        elif state == 1:
            title, labels = 'Storage: choose a check', ['Drive space report', 'Back', 'Disk properties']
        else:
            title, labels = 'Drive space report: C: has 80 GB free of 128 GB', ['Back']
        draw.text((60, 150), title, fill='#152138', font=font)
        for position, label in enumerate(labels):
            box = (55+position*355, 280, 390+position*355, 370)
            boxes[label] = box
            draw.rounded_rectangle(box, 10, fill='#244c85')
            draw.text((box[0]+12, box[1]+28), label, fill='white', font=font)
        image.save(ROOT/f'feedback-step-{step}.png')
        stream = io.BytesIO()
        image.save(stream, 'PNG')
        prompt = ("You are a GUI agent given a task, action history and current screenshot. "
                  "Perform the next action. Output exactly one line: Action: click(start_box='(x,y)') "
                  "or Action: finished(). Use screenshot pixel coordinates.\n"
                  "Task: Open Storage, then open Drive space report. Finish only when the report is visible.\n"
                  f"Previous actions: {history}")
        payload = {'model':'ui-tars','temperature':0,'max_tokens':128,'messages':[
            {'role':'user','content':[{'type':'text','text':prompt},
                {'type':'image_url','image_url':{'url':'data:image/png;base64,'+
                    base64.b64encode(stream.getvalue()).decode()}}]}]}
        started = time.perf_counter()
        req = urllib.request.Request(URL, json.dumps(payload).encode(), {'Content-Type':'application/json'})
        with urllib.request.urlopen(req, timeout=90) as response:
            data = json.load(response)
        text = data['choices'][0]['message']['content']
        row = {'step':step,'state_before':state,'seconds':round(time.perf_counter()-started,3),'output':text}
        if text.strip() == 'Action: finished()':
            row['verified_complete'] = state == 2
            records.append(row)
            break
        try:
            x,y = parse_click(text, *image.size)
            hit = next((label for label,(l,t,r,b) in boxes.items() if l<=x<=r and t<=y<=b),None)
            row['hit'] = hit
            if state == 0 and hit == 'Storage' and not injected_miss:
                injected_miss = True
                row['injected_missed_click_and_layout_change'] = True
            elif state == 0 and hit == 'Storage': state = 1
            elif state == 1 and hit == 'Drive space report': state = 2
            elif hit == 'Back': state = max(0,state-1)
        except (ValueError, SyntaxError, TypeError) as error:
            row['error'] = str(error)
            records.append(row)
            break
        row['state_after'] = state
        records.append(row)
        history.append(text)
    result = {'simulation':True,'real_desktop_actions':False,
              'miss_and_layout_change_injected':injected_miss,
              'verified_complete':bool(records and records[-1].get('verified_complete')),
              'steps':records}
    (ROOT/'feedback-results.json').write_text(json.dumps(result,indent=2),encoding='utf-8')
    print(json.dumps(result),flush=True)
    return 0 if result['verified_complete'] else 1


if __name__ == '__main__':
    raise SystemExit(main())
