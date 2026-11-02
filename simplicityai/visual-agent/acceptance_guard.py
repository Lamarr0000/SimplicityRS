"""Narrow acceptance-test boundaries, not a general task understanding system."""
from outcome_verifier import TEST_TEXT


def document_state(identity, nodes, complete):
    if not complete or identity['process'] != 'notepad.exe':
        raise InterruptedError('Notepad document could not be identified; no input sent')
    tabs = [n for n in nodes if n.get('type') == 'TabItemControl' and n.get('selected')]
    documents = [n for n in nodes if n.get('type') == 'DocumentControl' and 'text' in n]
    if len(tabs) != 1 or len(documents) != 1:
        raise InterruptedError('Expected one selected Notepad tab and one visible document; no input sent')
    tab, doc = tabs[0], documents[0]
    if not tab.get('runtime_id') or not doc.get('runtime_id'):
        raise InterruptedError('Stable document identity unavailable; no input sent')
    return tab, doc


def bind_document(identity, nodes, complete):
    tab, doc = document_state(identity, nodes, complete)
    if identity['title'].lstrip('*') != 'Untitled - Notepad' or tab['name'] not in {'Untitled', 'Untitled. Unmodified.'}:
        raise InterruptedError('Notepad test requires a new Untitled tab. No document was edited.')
    if doc['text'].rstrip('\r\n'):
        raise InterruptedError('Notepad test requires an empty document. No document was edited.')
    return {'window': [identity[k] for k in ('hwnd', 'pid', 'created')],
            'tab': tab['runtime_id'], 'document': doc['runtime_id']}


def check_document(binding, identity, nodes, complete):
    tab, doc = document_state(identity, nodes, complete)
    if (binding['window'] != [identity[k] for k in ('hwnd', 'pid', 'created')]
            or binding['tab'] != tab['runtime_id'] or binding['document'] != doc['runtime_id']):
        raise InterruptedError('Notepad document changed; stopped without further input')
    if doc['text'].rstrip('\r\n') not in ('', TEST_TEXT):
        raise InterruptedError('Unexpected document content; stopped without further input')
    return doc


def require_document_action(action, doc, points):
    kind = action['kind']
    if kind in {'wait', 'finished', 'call_user'}:
        return
    if kind == 'type' and action['content'] == TEST_TEXT and not action['submit'] and not doc['text'].rstrip('\r\n'):
        return
    if kind == 'click' and len(points) == 1:
        x, y = points[0]
        left, top, right, bottom = doc['rect']
        if left <= x < right and top <= y < bottom:
            return
    raise InterruptedError('Action is outside the bound Notepad text-entry test; no input sent')
