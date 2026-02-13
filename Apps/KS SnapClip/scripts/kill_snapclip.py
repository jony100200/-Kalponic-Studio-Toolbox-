import psutil
killed = []
for p in psutil.process_iter(['pid','name','cmdline']):
    try:
        cmd = ' '.join(p.info.get('cmdline') or [])
        if 'main.py' in cmd or 'KS SnapClip' in cmd or 'ks_snapclip' in cmd.lower():
            pid = p.info['pid']
            print('Stopping', pid, cmd)
            try:
                p.kill()
                killed.append(pid)
            except Exception as e:
                print('Failed to kill', pid, e)
    except Exception:
        pass
print('killed:', killed)
