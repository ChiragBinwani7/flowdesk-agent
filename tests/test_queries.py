import json
import sys
import os
from datetime import datetime

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from app.graph.graph import graph

QUERIES_FILE = os.path.join(
    os.path.dirname(__file__),
    "../data/example-queries.json"
)

REPORT_FILE = os.path.join(
    os.path.dirname(__file__),
    "../evaluation_report.json"
)

EMPTY_STATE = {
    "customer": None, "plan": None, "docs": None, "incidents": None,
    "route": None, "decision": None, "answer": None,
    "escalation": False, "escalation_reason": None, "ticket_id": None,
    "status": None, "confidence": None,
    "tools_used": [], "execution_trace": [], "citations": [],
}


def run_query(customer_id, query):
    return graph.invoke({**EMPTY_STATE, "customer_id": customer_id, "query": query})


def main():
    with open(QUERIES_FILE) as f:
        test_cases = json.load(f)

    results = []
    passed = 0

    print(f"\nRunning {len(test_cases)} test cases...\n")
    print(f"{'ID':<30} {'EXPECT ESC':<12} {'GOT ESC':<10} {'STATUS':<12} RESULT")
    print("-" * 78)

    for tc in test_cases:
        qid          = tc["id"]
        customer_id  = tc["customer_id"]
        query        = tc["query"]
        expected_esc = tc["expected_escalation"]
        difficulty   = tc.get("difficulty", "")

        try:
            result   = run_query(customer_id, query)
            got_esc  = result.get("escalation", False)
            status   = result.get("status", "?")
            ok       = got_esc == expected_esc
            passed  += int(ok)

            results.append({
                "id":            qid,
                "difficulty":    difficulty,
                "customer_id":   customer_id,
                "query":         query,
                "expected_escalation": expected_esc,
                "got_escalation":      got_esc,
                "status":        status,
                "confidence":    result.get("confidence"),
                "ticket_id":     result.get("ticket_id"),
                "tools_used":    [t["tool"] for t in result.get("tools_used", [])],
                "answer_snippet":result.get("answer", "")[:120],
                "citations":     result.get("citations", []),
                "execution_trace": result.get("execution_trace", []),
                "pass":          ok,
            })

            print(f"{qid:<30} {str(expected_esc):<12} {str(got_esc):<10} {status:<12} {'PASS' if ok else 'FAIL'}")

        except Exception as e:
            results.append({"id": qid, "pass": False, "error": str(e), "difficulty": difficulty})
            print(f"{qid:<30} {str(expected_esc):<12} {'ERROR':<10} {'error':<12} FAIL  ({e})")

    total = len(results)
    print("-" * 78)

    # metrics by difficulty
    by_difficulty = {}
    for r in results:
        d = r.get("difficulty", "unknown")
        if d not in by_difficulty:
            by_difficulty[d] = {"pass": 0, "total": 0}
        by_difficulty[d]["total"] += 1
        by_difficulty[d]["pass"]  += int(r.get("pass", False))

    # metrics by escalation expectation
    should_escalate   = [r for r in results if r.get("expected_escalation") == True]
    should_not        = [r for r in results if r.get("expected_escalation") == False]
    esc_correct       = sum(1 for r in should_escalate if r.get("pass"))
    no_esc_correct    = sum(1 for r in should_not     if r.get("pass"))

    print(f"\nResult: {passed}/{total} passed ({round(passed/total*100)}%)")
    print()
    print("By difficulty:")
    for d, m in sorted(by_difficulty.items()):
        print(f"  {d:<8} {m['pass']}/{m['total']}")
    print()
    print("By escalation:")
    print(f"  Should escalate:     {esc_correct}/{len(should_escalate)}")
    print(f"  Should NOT escalate: {no_esc_correct}/{len(should_not)}")

    if passed >= 15:
        print(f"\nASSIGNMENT REQUIREMENT MET (need 15, got {passed})")
    else:
        print(f"\nASSIGNMENT REQUIREMENT NOT MET (need 15, got {passed})")

    failures = [r for r in results if not r.get("pass")]
    if failures:
        print("\nFailed cases:")
        for r in failures:
            if "error" in r:
                print(f"  {r['id']} — exception: {r['error']}")
            else:
                print(f"  {r['id']} — expected escalation={r.get('expected_escalation')}, got={r.get('got_escalation')}")

    # save JSON report
    report = {
        "run_at":    datetime.now().isoformat(),
        "summary": {
            "total":       total,
            "passed":      passed,
            "failed":      total - passed,
            "pass_rate":   round(passed / total * 100, 1),
            "by_difficulty": by_difficulty,
            "escalation_accuracy": {
                "should_escalate":     {"pass": esc_correct,    "total": len(should_escalate)},
                "should_not_escalate": {"pass": no_esc_correct, "total": len(should_not)},
            },
        },
        "results": results,
    }

    with open(REPORT_FILE, "w") as f:
        json.dump(report, f, indent=2)

    print(f"\nFull report saved to: {REPORT_FILE}")
    return 0 if passed >= 15 else 1


if __name__ == "__main__":
    sys.exit(main())
