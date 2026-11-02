"""Fresh UIA locators with input delivered through the existing takeover-aware driver."""
from control_session import Locator

ROLES={'ButtonControl':'button','TabItemControl':'tab','EditControl':'textbox',
       'DocumentControl':'document','TextControl':'text','ListItemControl':'listitem',
       'TreeItemControl':'treeitem'}


def matches(node,locator):
    return ((not locator.name or node.get('name')==locator.name)
            and (not locator.role or ROLES.get(node.get('type'))==locator.role)
            and (not locator.automation_id or node.get('automation_id')==locator.automation_id))


class WindowsAdapter:
    backend='windows-uia+guarded-input'
    capabilities={'click'}

    def __init__(self,snapshot,guard,click,allow=lambda node:None):
        self.snapshot,self.guard,self.click,self.allow=snapshot,guard,click,allow

    def find(self,locator):
        self.guard()
        nodes,complete=self.snapshot()
        if not complete:
            raise ValueError('Incomplete Windows accessibility observation; no structured action sent')
        return [dict(n,token=n.get('runtime_id'),visible=True) for n in nodes if matches(n,locator)]

    def perform(self,action,locator,observed,text):
        fresh=self.find(locator)
        if len(fresh)!=1 or not fresh[0].get('token') or fresh[0].get('token')!=observed.get('token'):
            raise ValueError('Control identity changed before action; no input sent')
        node=fresh[0]
        if not node.get('enabled') or node.get('rect')!=observed.get('rect'):
            raise ValueError('Control readiness changed before action; no input sent')
        self.allow(node)
        left,top,right,bottom=node['rect']
        if right<=left or bottom<=top:raise ValueError('Control has no usable bounds')
        point=[round((left+right)/2),round((top+bottom)/2)]
        self.guard()
        return self.click(point)


def available_controls(nodes):
    return [{'name':n.get('name','')[:120],'role':ROLES[n['type']],
             'id':n.get('automation_id','')[:120]} for n in nodes
            if n.get('type') in {'ButtonControl','TabItemControl','ListItemControl','TreeItemControl'}
            and n.get('runtime_id') and n.get('enabled')][:65]
