import sys, os, traceback
from src.ai.ai_manager import AIModelManager
import requests

def main():
    try:
        print('Python executable:', sys.executable)
        m = AIModelManager()
        print('Cache dir:', m.cache_dir)
        print('Cache exists:', os.path.exists(m.cache_dir))
        try:
            test_file = os.path.join(str(m.cache_dir), '.__write_test')
            with open(test_file, 'w') as f:
                f.write('test')
            os.remove(test_file)
            print('Cache writable: True')
        except Exception as e:
            print('Cache writable: False', e)

        # Quick network check
        try:
            r = requests.get('https://huggingface.co', timeout=5)
            print('Network check: status', r.status_code)
        except Exception as e:
            print('Network check failed:', e)

        # Attempt download (may be large). We run with show_progress=False to keep output minimal.
        print('\nStarting model download (this may take a while)')
        try:
            ok = m.download_model('distilbart', show_progress=False)
            print('download_model returned:', ok)
        except Exception:
            print('download_model raised exception:')
            traceback.print_exc()

    except Exception:
        traceback.print_exc()

if __name__ == '__main__':
    main()
