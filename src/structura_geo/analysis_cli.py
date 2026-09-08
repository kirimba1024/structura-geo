import argparse
import json

def parse_args(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("path")
    ap.add_argument("--json", action="store_true")
    ap.add_argument(
        "--histogram",
        action="store_true",
        help="print block name/count/percent instead of the full report",
    )
    return ap.parse_args(argv)


def print_analysis(analyzer, *, histogram=False, json_output=False):
    if histogram:
        hist = analyzer.block_histogram()
        total = sum(hist.values()) or 1
        rows = [
            {"block": name, "count": n, "percent": round(100 * n / total, 2)}
            for name, n in hist.most_common()
        ]
        if json_output:
            print(json.dumps(rows, indent=2))
        else:
            for row in rows:
                print(f"{row['count']:7d}  {row['percent']:5.1f}%  {row['block']}")
        return

    r = analyzer.report()
    if json_output:
        print(json.dumps(r, indent=2))
    else:
        print(f"summary               : {r['summary']}")
        for k, v in r.items():
            if k in ("warnings", "summary"):
                continue
            print(f"{k:22s}: {v}")
        if r["warnings"]:
            print("warnings:")
            for w in r["warnings"]:
                print(f"  - {w}")
        else:
            print("warnings: none")
