import os
import sys

# Add parent directory to path so we can import modules
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from graders.phase_grader import run_phase
from graders.verifier import verify_result
from agents.easy_agent import EasyRuleAgent
from agents.medium_agent import MediumAgent
from agents.hard_agent import HardMultiFactorAgent

os.environ['API_BASE_URL'] = 'http://localhost/v1'
os.environ['API_KEY'] = 'sk-dummy'
os.environ['MODEL_NAME'] = 'gpt-4o-mini'

tasks = [
    {'task_id': 'easy', 'agent': EasyRuleAgent()},
    {'task_id': 'medium', 'agent': MediumAgent()},
    {'task_id': 'hard', 'agent': HardMultiFactorAgent()}
]

print('[START] task=gp-stratz', flush=True)
step_count = 0
total = 0

for t in tasks:
    result = run_phase(t['task_id'], t['agent'])
    score = result.get('score', 0.5)
    
    # Run verifier silently or assert?
    is_valid = verify_result(result)
    if not is_valid:
        print(f"[WARN] Result validation failed for {t['task_id']}")
        
    step_count += 1
    total += score
    print(f"[STEP] step={step_count} task={t['task_id']} score={score:.10f}", flush=True)

overall_score = total / len(tasks)
print(f"[END] task=gp-stratz score={overall_score:.10f} steps={step_count}", flush=True)
