"""Application reporting of measured driver/device facts; no health inference."""


def rows(record):
    return [row for section in record.get('sections',[]) if section.get('status')=='available'
            for row in section.get('data',[]) if isinstance(row,dict)]


def report(findings,explain=False):
    devices=findings.get('devices',{})
    drivers=findings.get('drivers',{})
    device_rows=rows(devices);driver_rows=rows(drivers)
    codes=[row['ConfigManagerErrorCode'] for row in device_rows if row.get('ConfigManagerErrorCode') is not None]
    problems=sum(code!=0 for code in codes)
    prefix='SIMULATION ONLY. ' if devices.get('simulation') or drivers.get('simulation') else ''
    if not codes:
        first='The returned records do not establish device problem-code status.'
    elif problems:
        first=f'Windows reported nonzero problem codes for {problems} returned device records.'
    else:
        first='No nonzero device problem codes were found in the returned rows.'
    if explain:
        return prefix+first+" A signing field is not a driver health test. These checks do not establish that every driver works correctly or is up to date."
    if driver_rows:
        signed=sum(row.get('IsSigned') is True for row in driver_rows)
        unknown=sum(type(row.get('IsSigned')) is not bool for row in driver_rows)
        detail=f' Of {len(driver_rows)} installed driver records returned, {signed} are marked signed and {unknown} have unknown signing status.'
    else:detail=' Installed driver signing records were unavailable or empty.'
    return prefix+first+detail+" This limited check does not prove all drivers work correctly or are current; update availability and individual hardware function were not tested."
