def verify_result(result):
    score = result.get("score", 0.0)
    print(f"[VERIFY] Checking score {score}")
    if not (0.0 < score < 1.0):
        print(f"[VERIFY] FAIL: Score {score} not in (0, 1) exclusive")
    else:
        print("[VERIFY] PASS: Score is in bounds.")
        
    breakdowns = result.get("breakdown_per_lap", [])
    missing_keys = False
    for b in breakdowns:
        bk = b.get("breakdown", {})
        for key in ["correctness", "forward_bonus", "mismatch", "seq_bonus"]:
            if key not in bk:
                print(f"[VERIFY] FAIL: missing {key} in breakdown")
                missing_keys = True
                break
        if missing_keys:
            break
            
    if not missing_keys and len(breakdowns) > 0:
        print("[VERIFY] PASS: Breakdown keys match expected components.")
        
    return not missing_keys and (0.0 < score < 1.0)
