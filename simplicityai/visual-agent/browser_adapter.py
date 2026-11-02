"""Playwright implementation of the same locator/action/verification contract.

The caller owns the page/context and permission policy. No user browser profile
is opened or attached by this module. No model-authored JavaScript is evaluated.
"""


class BrowserAdapter:
    backend='playwright'
    capabilities={'click','fill'}

    def __init__(self,page,guard=lambda:None):
        self.page,self.guard=page,guard

    def locate(self,locator):
        if locator.role:
            item=self.page.get_by_role(locator.role,name=locator.name,exact=True) if locator.name else self.page.get_by_role(locator.role)
            if locator.automation_id:
                item=item.and_(self.page.get_by_test_id(locator.automation_id))
            return item
        if locator.automation_id:
            if locator.name:raise ValueError('Use a role when combining browser name and ID')
            return self.page.get_by_test_id(locator.automation_id)
        return self.page.get_by_text(locator.name,exact=True)

    def find(self,locator):
        self.guard()
        item=self.locate(locator)
        count=item.count()
        if count!=1:return [{}]*count
        box=item.bounding_box()
        role=locator.role
        text=item.inner_text(timeout=1000)
        return [{'token':(locator.name,role,locator.automation_id),
                 'name':locator.name,'text':text,'enabled':item.is_enabled(),
                 'visible':item.is_visible(),'selected':item.get_attribute('aria-selected')=='true',
                 'value':item.input_value(timeout=1000) if role in {'textbox','combobox'} else None,
                 'rect':None if not box else (box['x'],box['y'],box['width'],box['height'])}]

    def perform(self,action,locator,observed,text):
        self.guard()
        item=self.locate(locator)
        # Playwright supplies action-time strictness, visibility and event checks.
        if action=='fill':item.fill(text,timeout=4000)
        else:item.click(timeout=4000)
        return 'Playwright action returned; independent outcome check follows when supplied'
