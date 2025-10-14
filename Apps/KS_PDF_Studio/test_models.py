import time
from src.ai.ai_manager import AIModelManager

SAMPLE_TEXT = (
    "Transformers provide simple APIs to download and run pre-trained models. "
    "This sample text will be summarized by DistilBART to verify the summarization pipeline is working. "
    "We expect a short, coherent summary of the above sentences."
)


def test_distilbart():
    mgr = AIModelManager()
    print('Checking distilbart availability:', mgr.is_model_available('distilbart'))
    if not mgr.is_model_available('distilbart'):
        print('DistilBART not downloaded; attempting download...')
        ok = mgr.download_model('distilbart', show_progress=False)
        print('download_model returned:', ok)
        if not ok:
            print('Download failed; aborting test.')
            return

    print('Loading model into memory...')
    mgr.load_model('distilbart')
    print('Model loaded, running summarization...')

    pipeline = mgr._models['distilbart']
    start = time.time()
    result = pipeline(SAMPLE_TEXT, max_length=60, min_length=10, do_sample=False)
    elapsed = time.time() - start

    print('Inference elapsed: %.2fs' % elapsed)
    try:
        summary = result[0].get('summary_text') if isinstance(result, list) else str(result)
    except Exception:
        summary = str(result)

    print('Summary:')
    print(summary)


if __name__ == '__main__':
    test_distilbart()
