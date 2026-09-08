"""Demo script — SOC with AI v2

Exercises the full pipeline:
  - Smart alert filtering (false positives, duplicates, low-confidence)
  - Adaptive severity scoring (ML anomaly, IP reputation, behavior deviation)
  - Alert correlation (grouping related alerts)
  - Data-driven explanations with factor breakdown
  - Analyst feedback loop (simulated)
  - SIEM/SOAR integration status

Usage:
    python demo.py              -> pretty-printed CLI output
    python demo.py --json       -> full JSON output
    python demo.py --feedback   -> include simulated feedback loop demo
"""

from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timezone, timedelta

from src.models import Alert, AlertMetadata
from src.engine.aggregator import TriageAggregator


def _now(hours_ago: float = 0) -> datetime:
    return datetime.now(timezone.utc) - timedelta(hours=hours_ago)


SAMPLE_ALERTS: list[dict] = [
    #  CRITICAL: Active ransomware + credential theft (same attacker) 
    {
        "title": "Ransomware encryption detected on WS-PROD-03",
        "description": "Rapid file encryption activity detected across multiple shares. Process mimikatz.exe spawned cmd.exe then invoked vssadmin to delete shadow copies.",
        "source": "edr", "severity": "critical", "category": "malware",
        "timestamp": _now(0.1),
        "metadata": {
            "source_ip": "10.0.5.32", "destination_ip": "10.0.1.50",
            "hostname": "WS-PROD-03", "user": "svc-backup",
            "process_name": "mimikatz.exe",
            "mitre_technique": "T1486", "mitre_tactic": "impact",
        },
        "confidence": 0.97, "asset_criticality": 0.95,
        "threat_intel_match": True,
        "tags": ["ransomware", "critical-infrastructure"],
    },
    {
        "title": "Credential dump tool execution on DC-01",
        "description": "Mimikatz execution detected on domain controller. LSASS process accessed by unauthorized binary.",
        "source": "edr", "severity": "critical", "category": "credential_access",
        "timestamp": _now(0.2),
        "metadata": {
            "source_ip": "10.0.1.10", "hostname": "DC-01", "user": "SYSTEM",
            "process_name": "mimikatz.exe",
            "mitre_technique": "T1003", "mitre_tactic": "credential_access",
        },
        "confidence": 0.95, "asset_criticality": 1.0,
        "threat_intel_match": True,
        "tags": ["credential-theft", "domain-controller"],
    },

    #  HIGH: Lateral movement + exfil + C2 
    {
        "title": "Data exfiltration to external IP",
        "description": "Large volume of encrypted data transferred to 198.51.100.23 over port 443 in the last 2 hours.",
        "source": "firewall", "severity": "high", "category": "data_exfiltration",
        "timestamp": _now(0.5),
        "metadata": {
            "source_ip": "10.0.5.32", "destination_ip": "198.51.100.23",
            "destination_port": 443, "hostname": "WS-PROD-03", "user": "svc-backup",
        },
        "confidence": 0.85, "asset_criticality": 0.9,
    },
    {
        "title": "Lateral movement via PsExec to DB-PROD",
        "description": "PsExec service started on DB-PROD by svc-backup from WS-PROD-03.",
        "source": "siem", "severity": "high", "category": "lateral_movement",
        "timestamp": _now(1.5),
        "metadata": {
            "source_ip": "10.0.5.32", "destination_ip": "10.0.2.20",
            "hostname": "DB-PROD", "user": "svc-backup",
            "mitre_technique": "T1021", "mitre_tactic": "lateral_movement",
        },
        "confidence": 0.88, "asset_criticality": 0.85,
    },
    {
        "title": "DNS query to known C2 domain",
        "description": "Internal host resolved dz4k7q9.example.com — Emotet C2 infrastructure.",
        "source": "ndr", "severity": "high", "category": "command_and_control",
        "timestamp": _now(0.3),
        "metadata": {
            "source_ip": "10.0.4.18", "hostname": "WORKSTATION-18",
            "domain": "dz4k7q9.example.com",
            "mitre_technique": "T1071",
        },
        "confidence": 0.88, "asset_criticality": 0.5,
        "threat_intel_match": True,
    },

    #  MEDIUM 
    {
        "title": "Brute force login attempts on VPN gateway",
        "description": "847 failed login attempts from 203.0.113.45 in 10 minutes.",
        "source": "ids", "severity": "medium", "category": "initial_access",
        "timestamp": _now(2),
        "metadata": {
            "source_ip": "203.0.113.45", "destination_port": 4433,
            "hostname": "VPN-GW-01", "user": "multiple",
            "mitre_technique": "T1110",
        },
        "confidence": 0.75, "asset_criticality": 0.6,
    },
    {
        "title": "Suspicious PowerShell execution",
        "description": "PowerShell decoded Base64 command and downloaded content from external URL.",
        "source": "edr", "severity": "medium", "category": "execution",
        "timestamp": _now(3),
        "metadata": {
            "source_ip": "10.0.3.47", "hostname": "WORKSTATION-47",
            "user": "jdoe", "process_name": "powershell.exe",
            "url": "https://evil.example.com/payload.ps1",
            "mitre_technique": "T1059",
        },
        "confidence": 0.7, "asset_criticality": 0.4,
    },
    {
        "title": "New scheduled task created on SRV-WEB-02",
        "description": "Scheduled task SystemUpdate points to PowerShell script in %TEMP%.",
        "source": "siem", "severity": "medium", "category": "persistence",
        "timestamp": _now(4),
        "metadata": {
            "source_ip": "10.0.2.15", "hostname": "SRV-WEB-02",
            "user": "Administrator", "mitre_technique": "T1053",
        },
        "confidence": 0.65, "asset_criticality": 0.55,
    },
    {
        "title": "Phishing email delivered to finance team",
        "description": "Email Urgent: Invoice Payment Required with credential harvesting link.",
        "source": "email", "severity": "medium", "category": "phishing",
        "timestamp": _now(8),
        "metadata": {
            "email_subject": "Urgent: Invoice Payment Required",
            "url": "https://pay-secure.example.com/login",
            "user": "finance@corp.com",
        },
        "confidence": 0.5, "asset_criticality": 0.5,
    },
    {
        "title": "SSH brute force from Tor exit node",
        "description": "200+ SSH failures from 185.220.101.1 in 5 minutes.",
        "source": "firewall", "severity": "medium", "category": "initial_access",
        "timestamp": _now(12),
        "metadata": {
            "source_ip": "185.220.101.1", "destination_port": 22,
            "hostname": "jump-server-01",
        },
        "confidence": 0.72, "asset_criticality": 0.6,
    },

    #  LOW / INFO / DUPLICATE / FALSE POSITIVE 
    {
        "title": "Port scan detected from internal host",
        "description": "WORKSTATION-22 performed SYN scan across 10.0.1.0/24.",
        "source": "ndr", "severity": "low", "category": "discovery",
        "timestamp": _now(6),
        "metadata": {
            "source_ip": "10.0.3.22", "hostname": "WORKSTATION-22",
            "mitre_technique": "T1046",
        },
        "confidence": 0.6, "asset_criticality": 0.3,
    },
    {
        "title": "Anomalous admin login time",
        "description": "User admin_jsmith logged into PROD-APP-01 at 03:47 UTC.",
        "source": "siem", "severity": "low", "category": "initial_access",
        "timestamp": _now(10),
        "metadata": {"hostname": "PROD-APP-01", "user": "admin_jsmith"},
        "confidence": 0.4, "asset_criticality": 0.5,
    },
    {
        "title": "Routine antivirus scan completed",
        "description": "Windows Defender scheduled scan completed. No threats found.",
        "source": "edr", "severity": "info", "category": "unknown",
        "timestamp": _now(5),
        "metadata": {"hostname": "WORKSTATION-47"},
        "confidence": 0.1, "asset_criticality": 0.1,
    },
    {
        "title": "Known false positive: admin tool flagged as malware",
        "description": "Sysinternals PsExec flagged — previously confirmed as FP.",
        "source": "edr", "severity": "low", "category": "unknown",
        "timestamp": _now(3),
        "metadata": {"hostname": "WORKSTATION-12", "rule_id": "EDR-999"},
        "confidence": 0.2, "asset_criticality": 0.2,
        "is_known_true_positive": False,
    },
]


def _build_alerts(raw: list[dict]) -> list[Alert]:
    alerts = []
    for r in raw:
        meta = r.pop("metadata", {})
        alerts.append(Alert(**r, metadata=AlertMetadata(**meta)))
    return alerts


def print_results(results, filter_stats=None):
    R = "\033[0m"
    B = "\033[1m"
    DIM = "\033[2m"
    C = {"escalate":"\033[91m", "investigate":"\033[93m", "monitor":"\033[94m", "suppress":"\033[90m", "auto_close":"\033[90m"}

    print(f"\n{B}{'='*100}")
    print(f"  SOC with AI v2 — Adaptive Scoring + ML Anomaly Detection")
    print(f"{'='*100}{R}\n")

    if filter_stats:
        print(f"  {DIM}Filters: {filter_stats.get('suppressed',0)} suppressed, {filter_stats.get('auto_closed',0)} auto-closed")
        print(f"  Active rules: {', '.join(filter_stats.get('active_rules',[]))}{R}\n")

    header = f"  {'#':<3} {'Score':<6} {'Action':<12} {'Title':<50} {'MITRE':<8} {'Group'}"
    print(f"{B}{header}{R}")
    print(f"  {'-'*3} {'-'*6} {'-'*12} {'-'*50} {'-'*8} {'-'*8}")

    for i, r in enumerate(results, 1):
        score = r.priority.composite
        action = r.action if isinstance(r.action, str) else r.action.value
        color = C.get(action, "")
        summary = r.explanation.summary[:50] if len(r.explanation.summary) > 50 else r.explanation.summary
        mitre = r.explanation.mitre_mapping or "-"
        group = r.group_id or ""
        print(f"  {color}{i:<3} {score:<6.1f} {action:<12} {summary:<50} {mitre:<8} {group}{R}")

    print()

    # Top 3 with full explanation
    print(f"{B}  --- Top 3 Alerts -- Detailed Explanation + Factor Breakdown ---{R}\n")
    for i, r in enumerate(results[:3], 1):
        color = C.get(r.action if isinstance(r.action, str) else r.action.value, "")
        score = r.priority
        print(f"  {color}{B}[{score.composite:.1f}/10] {r.explanation.summary}{R}")

        # Factor breakdown
        factors = [
            ("Threat", score.threat_score, "\033[91m"),
            ("Asset", score.asset_score, "\033[93m"),
            ("Confidence", score.confidence_score, "\033[95m"),
            ("Correlation", score.correlation_score, "\033[94m"),
            ("Temporal", score.temporal_score, "\033[96m"),
        ]
        bar_width = 30
        for label, val, c in factors:
            filled = int(val * bar_width)
            bar = f"{c}{'#' * filled}{'.' * (bar_width - filled)}{R}"
            print(f"    {label:<12} [{bar}] {val*100:.0f}%")
        print()

        # Reasoning
        for para in r.explanation.reasoning.split("\n\n"):
            if para.strip():
                print(f"  {DIM}{para}{R}")
        print()

        if r.explanation.recommended_actions:
            print(f"  {B}Recommended:{R}")
            for act in r.explanation.recommended_actions[:5]:
                print(f"    -> {act}")
        print()

    # Integration status
    print(f"{B}  --- SIEM/SOAR Integration Status ---{R}\n")
    print(f"  Splunk  (HEC): offline  (configure splunk_url + hec_token)")
    print(f"  ELK     (bulk): offline  (configure elasticsearch_url)")
    print(f"  XSOAR   (API):  offline  (configure xsoar_url + api_key)")
    print()


def run_feedback_demo(aggregator, alerts):
    """Simulate an analyst submitting feedback on several alerts."""
    print(f"\033[1m  --- Analyst Feedback Loop Demo ---\033[0m\n")
    print(f"  Simulating analyst reviewing 5 alerts and submitting feedback...\n")

    feedbacks = [
        (alerts[0], True, "Ransomware confirmed — SOC-lead verified"),
        (alerts[1], True, "Credential theft confirmed on DC-01"),
        (alerts[5], True, "Brute force confirmed — multiple accounts affected"),
        (alerts[6], False, "PowerShell was legitimate admin script"),
        (alerts[12], False, "Known FP — PsExec is admin tool"),
    ]

    for alert, is_tp, note in feedbacks:
        result = aggregator.submit_feedback(
            alert, is_tp, analyst_id="demo-analyst", note=note,
        )
        tp_str = "\033[92mTRUE POSITIVE\033[0m" if is_tp else "\033[91mFALSE POSITIVE\033[0m"
        print(f"  {tp_str} | {alert.title[:50]}")
        if result.get("anomaly_detector_retrained"):
            print(f"    ** Anomaly detector retrained on accumulated data **")
    print()

    # Show updated metrics
    metrics = aggregator.feedback_loop.get_metrics()
    print(f"  Feedback Metrics:")
    print(f"    Total feedback:    {metrics['total_feedback']}")
    print(f"    True positives:    {metrics['true_positives']}")
    print(f"    False positives:   {metrics['false_positives']}")
    print(f"    Overall accuracy:  {metrics['overall_accuracy']*100:.1f}%")
    if metrics.get('recent_accuracy_50') is not None:
        print(f"    Recent accuracy:   {metrics['recent_accuracy_50']*100:.1f}%")
    if metrics.get('improvement_signal') is not None:
        imp = metrics['improvement_signal']
        sign = "+" if imp >= 0 else ""
        print(f"    Improvement:       {sign}{imp*100:.1f}%")
    print()

    # Show adaptive scorer stats
    scorer_stats = aggregator.adaptive_scorer.get_stats()
    print(f"  Adaptive Scorer Stats:")
    ad = scorer_stats.get("anomaly_detector", {})
    bp = scorer_stats.get("behavior_profiler", {})
    ip = scorer_stats.get("ip_reputation", {})
    hd = scorer_stats.get("historical_db", {})
    print(f"    Anomaly detector:  trained={ad.get('trained',False)}, samples={ad.get('training_samples',0)}")
    print(f"    Behavior profiler: tracked_users={bp.get('tracked_users',0)}")
    print(f"    IP reputation:     known_malicious={ip.get('known_malicious',0)}, feedback_adjusted={ip.get('feedback_adjusted',0)}")
    print(f"    Historical DB:     categories={hd.get('categories_tracked',0)}, incidents={hd.get('total_incidents',0)}")
    print()


def run_10k_scenario():
    """Run the full 10,000-alert overnight SOC scenario."""
    from src.ml.generator import generate_10k_alerts
    import time

    print(f"\n  {'='*80}")
    print(f"  10,000-ALERT OVERNIGHT SOC SCENARIO")
    print(f"  {'='*80}\n")

    print(f"  Generating 10,000 realistic alerts...", file=sys.stderr)
    t0 = time.time()
    alerts = generate_10k_alerts()
    t_gen = time.time() - t0
    print(f"  Generated {len(alerts)} alerts in {t_gen:.1f}s\n")

    # Severity distribution before triage
    sev_counts = {}
    for a in alerts:
        sev_counts[a.severity] = sev_counts.get(a.severity, 0) + 1
    print(f"  Before triage:")
    for sev in ["critical", "high", "medium", "low", "info"]:
        count = sev_counts.get(sev, 0)
        bar = "#" * (count // 50)
        print(f"    {sev:<10} {count:>5}  {bar}")
    print()

    # Run triage
    print(f"  Running AI triage pipeline...", file=sys.stderr)
    t0 = time.time()
    aggregator = TriageAggregator()
    results = aggregator.triage(alerts)
    t_triage = time.time() - t0
    print(f"  Triage completed in {t_triage:.2f}s\n")

    # Results summary
    kept = len(results)
    suppressed_count = len(alerts) - kept
    action_counts = {}
    for r in results:
        a = r.action if isinstance(r.action, str) else r.action.value
        action_counts[a] = action_counts.get(a, 0) + 1

    print(f"  {''*60}")
    print(f"  RESULTS SUMMARY")
    print(f"  {''*60}")
    print(f"  Total alerts received:    {len(alerts):>6}")
    print(f"  After AI filtering:       {kept:>6}  ({kept/len(alerts)*100:.1f}%)")
    print(f"  Noise suppressed:         {suppressed_count:>6}  ({suppressed_count/len(alerts)*100:.1f}%)")
    print(f"  Correlated groups:        {len(aggregator.correlator._groups):>6}")
    print(f"  Time to triage:           {t_triage:>6.2f}s")
    print(f"  Alerts per second:        {len(alerts)/t_triage:>6.0f}")
    print()

    print(f"  Action Distribution:")
    for action in ["escalate", "investigate", "monitor", "suppress"]:
        count = action_counts.get(action, 0)
        bar = "#" * (count // 20)
        print(f"    {action:<12} {count:>5}  {bar}")
    print()

    # Top 10 critical alerts
    print(f"  {''*60}")
    print(f"  TOP 10 CRITICAL ALERTS (analysts see these first)")
    print(f"  {''*60}\n")
    print(f"  {'#':<3} {'Score':<6} {'Action':<12} {'MITRE':<8} {'Title'}")
    print(f"  {'-'*3} {'-'*6} {'-'*12} {'-'*8} {'-'*55}")
    for i, r in enumerate(results[:10], 1):
        score = r.priority.composite
        action = r.action if isinstance(r.action, str) else r.action.value
        mitre = r.explanation.mitre_mapping or "-"
        title = r.explanation.summary[:55] if len(r.explanation.summary) > 55 else r.explanation.summary
        color = "\033[91m" if action == "escalate" else ("\033[93m" if action == "investigate" else "")
        print(f"  {color}{i:<3} {score:<6.1f} {action:<12} {mitre:<8} {title}\033[0m")
    print()

    # Show one detailed explanation
    top = results[0]
    print(f"  {''*60}")
    print(f"  DETAILED EXPLANATION: TOP ALERT")
    print(f"  {''*60}\n")
    print(f"  {top.explanation.summary}")
    print()
    for para in top.explanation.reasoning.split("\n\n")[:4]:
        if para.strip():
            print(f"  {para}")
    print()
    if top.explanation.recommended_actions:
        print(f"  Recommended:")
        for act in top.explanation.recommended_actions[:4]:
            print(f"    -> {act}")
    print()

    # Filter stats
    stats = aggregator.filter.get_stats()
    print(f"  Filter Stats: {stats['suppressed']} suppressed, {stats['auto_closed']} auto-closed")
    print(f"  Active rules: {', '.join(stats['active_rules'])}")
    print()
    print(f"  {'='*80}")
    print(f"  SCENARIO COMPLETE — {suppressed_count} alerts filtered, top {action_counts.get('escalate',0)} escalated")
    print(f"  {'='*80}\n")


def main():
    parser = argparse.ArgumentParser(description="SOC with AI v2 Demo")
    parser.add_argument("--json", action="store_true", help="Output full JSON")
    parser.add_argument("--feedback", action="store_true", help="Run feedback loop demo")
    parser.add_argument("--10k", action="store_true", dest="ten_k", help="Run the 10,000-alert scenario")
    args = parser.parse_args()

    if args.ten_k:
        run_10k_scenario()
        return

    alerts = _build_alerts([dict(a) for a in SAMPLE_ALERTS])
    print(f"\n  Processing {len(alerts)} alerts through the AI triage pipeline...\n", file=sys.stderr)

    aggregator = TriageAggregator()
    results = aggregator.triage(alerts)
    kept, suppressed = aggregator.filter.filter_alerts(alerts)

    if args.json:
        output = {
            "results": [r.model_dump() for r in results],
            "total_received": len(SAMPLE_ALERTS),
            "after_filtering": len(results),
            "suppressed": len(suppressed),
            "filter_stats": aggregator.filter.get_stats(),
            "adaptive_scorer": aggregator.adaptive_scorer.get_stats(),
            "feedback": aggregator.feedback_loop.get_metrics(),
        }
        print(json.dumps(output, indent=2, default=str))
    else:
        print_results(results, aggregator.filter.get_stats())

    if args.feedback:
        # Rebuild alerts (since _build_alerts consumes the dicts)
        alerts2 = _build_alerts([dict(a) for a in SAMPLE_ALERTS])
        run_feedback_demo(aggregator, alerts2)

        # Re-triage to show scores may have shifted
        print(f"\033[1m  --- Re-Triage After Feedback ---\033[0m\n")
        print(f"  Running triage again with updated adaptive models...\n")
        results2 = aggregator.triage(alerts2)
        print(f"  {'#':<3} {'Old':<6} {'New':<6} {'Action':<12} {'Title'}")
        print(f"  {'-'*3} {'-'*6} {'-'*6} {'-'*12} {'-'*50}")
        for i, (old, new) in enumerate(zip(results, results2), 1):
            old_s = old.priority.composite
            new_s = new.priority.composite
            delta = new_s - old_s
            delta_str = f"\033[92m+{delta:.1f}\033[0m" if delta > 0.01 else (f"\033[91m{delta:.1f}\033[0m" if delta < -0.01 else "  0.0")
            title = new.explanation.summary[:50] if len(new.explanation.summary) > 50 else new.explanation.summary
            action = new.action if isinstance(new.action, str) else new.action.value
            print(f"  {i:<3} {old_s:<6.1f} {new_s:<6.1f} {action:<12} {title} ({delta_str})")
        print()


if __name__ == "__main__":
    main()
