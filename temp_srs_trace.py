import os, sys, json, traceback
ROOT = os.path.abspath('.')
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)
from backend.core.audit_workflow import AuditWorkflow
from backend.srs.parser import SRSParser
from backend.srs.extractor import SRSFeatureExtractor
from backend.llm.manager import LLMManager

SRS_PATH = r"C:\Users\Raghuram\Desktop\AI\validation-repos\healthy-enterprise\docs\srs.txt"
print("SRS_PATH:", SRS_PATH)
print("EXISTS:", os.path.exists(SRS_PATH))

extractor = SRSFeatureExtractor()
orig_extract = extractor.extract_features

llm_called = {'value': False}
orig_llm_generate = LLMManager.generate

def wrapped_llm_generate(self, prompt):
    print("[TRACE] SRSFeatureExtractor: LLM path entered")
    llm_called['value'] = True
    try:
        return orig_llm_generate(self, prompt)
    except Exception as e:
        print("[TRACE] LLM generate raised:", repr(e))
        raise

LLMManager.generate = wrapped_llm_generate

orig_extractor = SRSFeatureExtractor.extract_features

def wrapped_extract(self, content):
    print("[TRACE] SRSFeatureExtractor.extract_features called")
    try:
        features = orig_extractor(self, content)
        print("[TRACE] SRSFeatureExtractor returned", len(features), "features")
        print("[TRACE] Raw extractor output:", json.dumps(features, indent=2) if isinstance(features, list) else repr(features))
        return features
    except Exception as e:
        print("[TRACE] extract_features exception:", repr(e))
        traceback.print_exc()
        raise

SRSFeatureExtractor.extract_features = wrapped_extract

try:
    wf = AuditWorkflow()
    repository_context = {
        'contributors': [],
        'activity': [],
        'repository_start_date': '2026-01-01T00:00:00',
        'latest_activity_date': '2026-05-30T00:00:00',
    }
    print("[TRACE] Starting AuditWorkflow.execute_audit")
    result = wf.execute_audit(repository_context=repository_context, srs_path=SRS_PATH)
    print("[TRACE] AuditWorkflow finished")
    print("semantic_features count:", len(result.get('semantic_features', [])))
    print("semantic_features:", json.dumps(result.get('semantic_features', []), indent=2)[:2000])
    print("llm_called:", llm_called['value'])
except Exception as e:
    print("[TRACE] AuditWorkflow execution raised:", repr(e))
    traceback.print_exc()
finally:
    LLMManager.generate = orig_llm_generate
    SRSFeatureExtractor.extract_features = orig_extractor
