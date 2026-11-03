"""Opt-in elevated online inventory/export acceptance check. Never installs drivers."""
import argparse
from datetime import datetime
import json
from pathlib import Path
import subprocess
import sys
from driver_packages import DriverPackages,verify_backup


def main():
    parser=argparse.ArgumentParser();parser.add_argument('--export',action='store_true');parser.add_argument('--launch-pilot',action='store_true');args=parser.parse_args()
    root=Path('C:/SimplicityAI-Lab/ControlAdapter')
    if not root.is_dir():raise RuntimeError('Existing validation directory is required')
    report=root/('driver-live-'+datetime.now().strftime('%Y%m%d-%H%M%S-%f')+'.json')
    result={'simulation':False,'source':'online','offline_export_tested':False,'install_or_remove_requested':False}
    service=DriverPackages()
    try:
        result['phase']='inventory'
        if args.export:
            plan=service.prepare('online',str(root),lambda:None)
            result['inventory_count']=plan['package_count']
            result['phase']='export'
            result['export']=service.export(plan['plan_id'],lambda:None)
            result['verification']=verify_backup(result['export']['destination'],lambda:None)
            result['passed']=bool(result['verification']['verified'])
        else:
            result['inventory_count']=service.inventory('online',lambda:None)['count']
            result['passed']=True
    except Exception as error:result.update(passed=False,error=str(error))
    finally:
        with report.open('x',encoding='utf-8') as output:json.dump(result,output,indent=2)
        if args.launch_pilot:
            subprocess.Popen([sys.executable,str(Path(__file__).with_name('launch.py')),'--model','qwen3:8b'],creationflags=subprocess.CREATE_NO_WINDOW)
    print(str(report))


if __name__=='__main__':main()
