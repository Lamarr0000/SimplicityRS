"""Bounded Calculator UI operation. The answer comes only from the actual display."""
import re
from desktop import BUTTONS


EXPRESSION=r'([0-9]{1,4}(?:\.[0-9]{1,4})?)\s*([+*/×÷-])\s*([0-9]{1,4}(?:\.[0-9]{1,4})?)'


def validate(expression):
    match=re.fullmatch(EXPRESSION,expression.strip()) if isinstance(expression,str) else None
    if not match:raise ValueError('Calculator supports one operation between two nonnegative numbers, up to four digits on each side of the decimal.')
    return match.groups()


def calculate(calc,expression,emit,check_stop):
    first,operator,second=validate(expression)
    check_stop();emit('action','ThemHands is opening Calculator in the Windows running SimplicityAI.')
    state=calc.call('open_calculator',{})
    if not state.get('usable'):raise RuntimeError('Calculator controls are unavailable')
    buttons=['clearButton']
    for index,part in enumerate([first,second]):
        if index:buttons.append({'+':'plusButton','-':'minusButton','*':'multiplyButton','×':'multiplyButton','/':'divideButton','÷':'divideButton'}[operator])
        buttons.extend('decimalSeparatorButton' if digit=='.' else 'num'+digit+'Button' for digit in part)
    buttons.append('equalButton')
    for button in buttons:
        check_stop();emit('action','Calculator: pressing '+BUTTONS[button]+', then reading the display.')
        state=calc.call('press_calculator_button',{'button_id':button,'observation':state['observation']})
    check_stop();emit('action','ThemHands is independently rereading Calculator after equals.')
    state=calc.call('observe_calculator',{})
    if state.get('display') is None:raise RuntimeError('Calculator final display could not be verified')
    return {**state,'requested_expression':expression,'final_display_reread':True,'scope':'Windows running SimplicityAI only'}
