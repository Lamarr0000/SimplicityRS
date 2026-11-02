"""Shared structured-control contract. Retry readiness/reads, never a sent action."""
from dataclasses import dataclass
import time


@dataclass(frozen=True)
class Locator:
    name: str = ''
    role: str = ''
    automation_id: str = ''

    def __post_init__(self):
        if not (self.name or self.automation_id):
            raise ValueError('A control name or ID is required')
        if any(len(value)>200 for value in (self.name,self.role,self.automation_id)):
            raise ValueError('Locator exceeds limit')


@dataclass(frozen=True)
class Condition:
    locator: Locator
    property: str
    equals: object

    def __post_init__(self):
        if self.property not in {'name','text','selected','enabled','value'}:
            raise ValueError('Unsupported observable property')


class AmbiguousControl(ValueError):
    pass


class ActionOutcomeUnknown(RuntimeError):
    pass


class ControlSession:
    def __init__(self,adapter,check=lambda:None,clock=time.monotonic,sleep=time.sleep):
        self.adapter,self.check,self.clock,self.sleep=adapter,check,clock,sleep

    def find(self,locator):
        self.check()
        nodes=self.adapter.find(locator)
        if len(nodes)>1:
            raise AmbiguousControl('More than one control matched; refine name/role/ID. No action sent.')
        return nodes[0] if nodes else None

    def read(self,locator):
        return self.find(locator)

    def verify(self,condition,timeout=4):
        deadline=self.clock()+timeout
        while self.clock()<deadline:
            node=self.find(condition.locator)
            if node is not None and node.get('visible') and node.get(condition.property)==condition.equals:
                return True
            self.sleep(.08)
        self.check()
        return False

    def act(self,action,locator,text=None,expected=None,timeout=4):
        if action not in self.adapter.capabilities:
            raise ValueError('Action is not supported by this adapter')
        if action=='fill' and text is None:
            raise ValueError('Fill requires literal text')
        if text is not None and (not isinstance(text,str) or len(text)>2000):
            raise ValueError('Input text exceeds limit')
        deadline=self.clock()+timeout
        previous=None
        while self.clock()<deadline:
            node=self.find(locator)
            stamp=None if node is None else (node.get('token'),node.get('rect'))
            if (node and node.get('visible') and node.get('enabled')
                    and stamp==previous):
                self.check()
                # Adapter re-resolves and guards immediately before the operation.
                # Errors here may mean a side effect occurred. Never replay it.
                try:
                    result=self.adapter.perform(action,locator,node,text)
                    verified=self.verify(expected,timeout) if expected is not None else False
                except InterruptedError:
                    raise
                except Exception as error:
                    raise ActionOutcomeUnknown('Action outcome unknown; operation will not be replayed') from error
                return {'action_sent':True,'backend':self.adapter.backend,'result':result,
                        'outcome_verified':verified if expected is not None else None,
                        'verification':'passed' if verified else ('unverified' if expected else 'not_requested')}
            previous=stamp
            self.sleep(.08)
        raise TimeoutError('Control did not become uniquely visible, enabled and stable; no action sent')
