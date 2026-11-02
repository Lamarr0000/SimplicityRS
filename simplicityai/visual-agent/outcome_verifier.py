"""Read-only acceptance predicates, independent of the visual model's claims."""
import time

CASES = {
    'notepad-text': ('notepad.exe', 'In the blank Untitled Notepad document, type Offline visual control test. Do not save, close, or edit other tabs. Finish when that exact sentence is visible.'),
    'task-manager-performance': ('taskmgr.exe', 'Open Task Manager and select its Performance tab. Do not end any processes or change settings. Finish when the Performance view is visible.'),
}
TEST_TEXT = 'Offline visual control test'


def evaluate(case, process, nodes, complete=True):
    result = {'case': case, 'verified': False, 'method': 'fresh foreground Windows UI Automation',
              'reason': 'Required evidence was not observed'}
    if case not in CASES:
        result['reason'] = 'No independent verifier for this task'
    elif process.lower() != CASES[case][0]:
        result['reason'] = 'Requested application is not foreground'
    elif not complete:
        result['reason'] = 'Accessibility observation was incomplete'
    elif case == 'notepad-text':
        result['verified'] = any(n.get('type') in {'DocumentControl', 'EditControl'}
            and n.get('text', '').rstrip('\r\n') == TEST_TEXT for n in nodes)
    else:
        selected = any(n.get('name', '').strip() == 'Performance' and n.get('selected') is True
                       for n in nodes)
        metrics = {n.get('name', '').strip() for n in nodes}
        result['verified'] = selected and 'CPU' in metrics and 'Memory' in metrics
    if result['verified']:
        result['reason'] = 'Acceptance outcome observed; does not certify all task constraints'
    return result


def collect(hwnd, check, limit=400, seconds=3):
    """Bound traversal and text reads; never invoke, focus, select or send input."""
    from windows_mcp import uia
    nodes = []
    deadline = time.monotonic() + seconds
    with uia.UIAutomationInitializerInThread():
        pending = [(uia.ControlFromHandle(hwnd), 0)]
        while pending:
            check()
            if len(nodes) >= limit or time.monotonic() > deadline:
                return nodes, False
            control, depth = pending.pop()
            node = {'name': control.Name, 'type': control.ControlTypeName}
            if not control.IsOffscreen and not control.IsPassword:
                if node['name'].strip() == 'Performance':
                    pattern = control.GetPattern(uia.PatternId.SelectionItemPattern)
                    node['selected'] = bool(pattern and pattern.IsSelected)
                if node['type'] in {'DocumentControl', 'EditControl'}:
                    pattern = control.GetPattern(uia.PatternId.TextPattern)
                    if pattern:
                        node['text'] = pattern.DocumentRange.GetText(2048)
                nodes.append(node)
            else:
                # Count hidden nodes toward the traversal budget, without their content.
                nodes.append({})
            children = control.GetChildren()
            if depth >= 16 and children:
                return nodes, False
            pending.extend((child, depth + 1) for child in reversed(children))
    return nodes, True


def verify(case, identity, identify, foreground, check):
    check()
    if identify(foreground()) != identity:
        return {'case': case, 'verified': False, 'reason': 'Foreground changed before verification'}
    try:
        nodes, complete = collect(identity['hwnd'], check)
        check()
        if identify(foreground()) != identity:
            return {'case': case, 'verified': False, 'reason': 'Foreground changed during verification'}
        result = evaluate(case, identity['process'], nodes, complete)
        # Do not copy unrelated application text into the evidence log.
        result['observed_controls'] = len(nodes)
        return result
    except InterruptedError:
        raise
    except Exception as error:
        return {'case': case, 'verified': False, 'reason': 'Accessibility check unavailable: '+type(error).__name__}
