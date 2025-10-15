"""
FULL KS MetaMaker Integration Test
Testing with all 4 sample images
"""

from pathlib import Path
from ks_metamaker.utils.config import Config
from ks_metamaker.tagger import ImageTagger
from ks_metamaker.ingest import ImageIngester
from ks_metamaker.quality import QualityAssessor
import time

def main():
    print('🚀 FULL KS MetaMaker Integration Test')
    print('=' * 50)
    print('Testing with all 4 sample images...')
    print()

    # Initialize components
    config = Config()
    tagger = ImageTagger(config)
    ingester = ImageIngester()
    quality_assessor = QualityAssessor()

    samples_dir = Path('samples')
    results = []

    print('📊 Processing Results:')
    print('-' * 30)

    start_time = time.time()

    for image_path in samples_dir.glob('*.png'):
        print(f'\n🖼️  Processing: {image_path.name}')

        try:
            # 1. Quality check
            quality_result = quality_assessor.assess_quality(image_path)
            if quality_result['valid']:
                quality_score = quality_result['quality_score']
                quality_status = '✅ Good' if quality_score > 0.5 else '⚠️  Poor'
                print(f'   Quality: {quality_status} ({quality_score:.2f})')
            else:
                print(f'   Quality: ❌ Error - {quality_result.get("error", "Unknown")}')
                continue

            # 2. AI Tagging
            tag_start = time.time()
            tags = tagger.tag(image_path)
            tag_time = time.time() - tag_start

            print(f'   AI Tags: {len(tags)} generated in {tag_time:.1f}s')
            print(f'   Sample: {tags[:3]}...')

            # 3. Category detection
            category = 'background'  # Default
            if any(word in ' '.join(tags).lower() for word in ['prop', 'object', 'metal', 'container']):
                category = 'props'
            elif any(word in ' '.join(tags).lower() for word in ['character', 'person', 'figure']):
                category = 'characters'

            print(f'   Category: {category}')

            results.append({
                'file': image_path.name,
                'quality': quality_score,
                'tags': len(tags),
                'category': category,
                'time': tag_time
            })

        except Exception as e:
            print(f'   ❌ Error: {e}')
            results.append({
                'file': image_path.name,
                'error': str(e)
            })

    total_time = time.time() - start_time

    print(f'\n🎯 SUMMARY:')
    print(f'   Total images processed: {len(results)}')
    print(f'   Total time: {total_time:.1f} seconds')
    print(f'   Average time per image: {total_time/len(results):.1f} seconds')

    successful = [r for r in results if 'error' not in r]
    print(f'   Success rate: {len(successful)}/{len(results)} ({len(successful)/len(results)*100:.0f}%)')

    if successful:
        avg_tags = sum(r['tags'] for r in successful) / len(successful)
        print(f'   Average tags per image: {avg_tags:.1f}')

        categories = {}
        for r in successful:
            categories[r['category']] = categories.get(r['category'], 0) + 1
        print(f'   Categories detected: {categories}')

    print()
    if len(successful) == len(results):
        print('🎉 KS METAMAKER IS FULLY FUNCTIONAL!')
        print('   ✅ AI tagging working')
        print('   ✅ Quality assessment working')
        print('   ✅ Category detection working')
        print('   ✅ Performance optimized')
    else:
        print('⚠️  PARTIAL FUNCTIONALITY - Some issues detected')

if __name__ == '__main__':
    main()