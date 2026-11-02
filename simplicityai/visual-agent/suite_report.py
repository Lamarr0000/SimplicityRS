"""Compact persistent summaries; detailed logs remain alongside each case."""
from pathlib import Path


def summarize(case, records, log_path):
    outcomes=[row.get('outcome_verification') for row in records if row.get('outcome_verification')]
    outcome=outcomes[-1] if outcomes else {}
    return {'case':case, 'status':outcome.get('status','verified' if outcome.get('verified') else 'unverified'),
            'verified':outcome.get('verified',False),'outcome':outcome,
            'stop_reason':next((row['reason'] for row in reversed(records) if row.get('stopped')),None),
            'model_seconds':round(sum(row.get('model_seconds',0) for row in records),3),
            'actions':sum('driver' in row for row in records), 'log':log_path,
            'screenshot':str(Path(log_path).with_suffix('.png')) if Path(log_path).with_suffix('.png').is_file() else None}
