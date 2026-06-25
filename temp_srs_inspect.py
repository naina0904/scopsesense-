import os, json
from backend.srs.parser import SRSParser
from backend.srs.extractor import SRSFeatureExtractor

srs_path = r'C:\Users\Raghuram\Desktop\AI\validation-repos\healthy-enterprise\docs\srs.txt'
print('SRS_PATH:', srs_path)
print('EXISTS:', os.path.exists(srs_path))
parser = SRSParser()
parsed = parser.parse(srs_path)
raw = parsed['raw_content']
print('PARSED_RAW_LENGTH:', len(raw))
print('PREVIEW:\n' + raw[:1000].replace('\n','\\n'))
print('CLEANED_LINES_COUNT:', len(parsed['cleaned_lines']))
extractor = SRSFeatureExtractor()
features = extractor.extract_features(raw)
print('FEATURE_COUNT:', len(features))
print('FEATURES_RAW:', json.dumps(features, indent=2))
