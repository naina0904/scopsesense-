import os
import json
import re
from backend.srs.parser import SRSParser
from backend.srs.extractor import SRSFeatureExtractor

SRS_PATH = os.path.join('data', 'uploads', 'srs_7f6125c1cb3848d8ab6d969eb8b09983_auroraengineeringplatform (1).xlsx')
print('SRS_PATH', SRS_PATH)
print('EXISTS', os.path.exists(SRS_PATH))
parser = SRSParser()
parsed = parser.parse(SRS_PATH)
content = parsed.get('raw_content', '')
print('INPUT_LEN', len(content))
print('FEATURE_MARKER_COUNT', content.count('Feature:'))
print('feature_marker_lower_count', content.count('feature:'))
print('PREVIEW', content[:1000])
print('HAS_FEATURE_TEXT', 'Feature:' in content)
print('HAS_FEATURE_NOCASE_TEXT', 'feature:' in content)

extractor = SRSFeatureExtractor()
print('[EXTRACT_FEATURES] START')
try:
    result = extractor.extract_features(content)
    print('[EXTRACT_FEATURES] RESULT_COUNT', len(result))
    print('[EXTRACT_FEATURES] RESULT_SAMPLE', json.dumps(result[:5], indent=2))
except Exception as e:
    print('[EXTRACT_FEATURES] EXCEPTION', repr(e))
    result = []

print('[EXTRACT_FEATURES] DONE')
print('FINAL_FEATURE_COUNT', len(result))
