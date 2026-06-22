import json
from collections import defaultdict

# Blended rate: $0.15 per 1M tokens (estimate for Gemini 1.5 Flash)
PRICE_PER_TOKEN = 0.15 / 1_000_000

def generate_report():
    stats = defaultdict(lambda: {"count": 0, "total_tokens": 0})
    try:
        with open('audit_log.json', 'r') as f:
            for line in f:
                entry = json.loads(line)
                w = entry['workload']
                stats[w]["count"] += 1
                stats[w]["total_tokens"] += entry['total_tokens']
        
        print(f"{'Workload':<20} | {'Runs':<6} | {'Avg Tokens':<12} | {'Est. Cost (USD)':<15}")
        print("-" * 65)
        for w, s in stats.items():
            avg_tokens = s['total_tokens'] // s['count']
            est_cost = (s['total_tokens'] * PRICE_PER_TOKEN) / s['count']
            print(f"{w:<20} | {s['count']:<6} | {avg_tokens:<12} | ${est_cost:.6f}")
            
    except FileNotFoundError:
        print("[!] No audit logs found. Run main.py to generate telemetry.")

if __name__ == "__main__":
    generate_report()