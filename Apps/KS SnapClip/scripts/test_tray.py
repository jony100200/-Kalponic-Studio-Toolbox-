import logging
try:
    import pystray
    from PIL import Image, ImageDraw
except Exception as e:
    print('pystray import failed', e)
    raise

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def create_image():
    img = Image.new('RGB', (64,64), color=(40,40,40))
    d = ImageDraw.Draw(img)
    d.rectangle((8,8,56,56), fill=(200,80,80))
    d.text((18,18), "KS", fill=(255,255,255))
    return img

icon = pystray.Icon('ks_snapclip_test', create_image(), 'KS SnapClip Test')

import threading, time

def _run_icon():
    try:
        icon.run()
    except Exception as e:
        logging.exception('pystray icon run failed: %s', e)

th = threading.Thread(target=_run_icon, daemon=True)
th.start()
# wait a few seconds to let icon appear
time.sleep(6)
try:
    icon.stop()
    logging.info('Stopped test icon')
except Exception as e:
    logging.exception('Failed to stop test icon: %s', e)
