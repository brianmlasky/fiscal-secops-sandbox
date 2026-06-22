import json
from collections import defaultdict

def generate_report():
    stats = defaultdict(lambda: {"count": 0, "total_tokens": 0, "total_thoughts": 0})
    
    try:
        with open('audit_log.json', 'r') as f:
            for line in f:
                entry = json.loads(line)
                w = entry['workload']
                stats[w]["count"] += 1
                stats[w]["total_tokens"] += entry['total_tokens']
                stats[w]["total_thoughts"] += entry['thought_tokens']
        
        print(f"{'Workload':<20} | {'Runs':<6} | {'Avg Total':<10} | {'Avg Thought':<10}")
        print("-" * 55)
        for w, s in stats.items():
            avg_total = s['total_tokens'] // s['count']
            avg_thought = s['total_thoughts'] // s['count']
            print(f"{w:<20} | {s['count']:<6} | {avg_total:<10} | {avg_thought:<10}")
            
    except FileNotFoundError:
        print("[!] No audit logs found. Run main.py to generate telemetry.")

if __name__ == "__main__":
    generate_report()