"""Measured application state and bounded recovery; never chooses input actions."""
import json


def observed_calculator(nodes, complete):
    if not complete:
        return None
    displays=[n.get('name','') for n in nodes if n.get('automation_id')=='CalculatorResults']
    expressions=[n.get('name','') for n in nodes if n.get('automation_id')=='CalculatorExpression']
    if len(displays)!=1 or len(expressions)>1:
        return None
    return {'display':displays[0][:100], 'expression':expressions[0][:100] if expressions else ''}


class ProgressHistory:
    def __init__(self):
        self.executed=[]
        self.warned=set()

    def key(self,state,action):
        return json.dumps([state,action],sort_keys=True)

    def review(self,state,action):
        if state is None:
            return ''
        key=self.key(state,action)
        if self.executed.count(key)<2:
            return ''
        if key in self.warned:
            raise RuntimeError('Repeated state/action after recovery feedback; completion unverified')
        self.warned.add(key)
        return ('No input was sent. This same observed state and proposed action have occurred twice '
                'already. Those attempts returned to this state. Re-read the task and current evidence, '
                'retain correct partial progress, and choose a different action or call_user().')

    def record(self,state,action):
        if state is not None:
            self.executed.append(self.key(state,action))
            self.executed=self.executed[-24:]


def observed_action(action, points, nodes):
    """Normalize coordinate jitter only when a single observed control owns it."""
    if action['kind']=='click' and len(points)==1:
        x,y=points[0]
        hits=[]
        for node in nodes:
            if node.get('type')!='ButtonControl' or not node.get('automation_id') or not node.get('rect'):
                continue
            left,top,right,bottom=node['rect']
            if left<=x<right and top<=y<bottom:
                hits.append(node['automation_id'])
        if len(hits)==1:
            return {'kind':'click','control':hits[0]}
    return action
