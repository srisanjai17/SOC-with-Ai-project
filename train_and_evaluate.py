"""Train & Evaluate — demonstrates the full AI learning pipeline.

This script runs the complete lifecycle:
  1. Generate realistic SOC data
  2. Train Isolation Forest + Autoencoder on normal traffic
  3. Score all alerts with adaptive severity scoring
  4. Simulate analyst feedback (mark TP/FP)
  5. Retrain models with feedback
  6. Show improvement in prediction accuracy
  7. Display baseline metrics and cost savings

Usage:
    python train_and_evaluate.py              # Full demo
    python train_and_evaluate.py --verbose     # Detailed output
"""

from __future__ import annotations

import argparse
import sys
import time
from collections import defaultdict

from src.engine.aggregator import TriageAggregator
from src.engine.scorer import AdaptiveSeverityScorer
from src.ml.generator import generate_10k_alerts
from src.ml.anomaly import AnomalyDetector
from src.ml.autoencoder import AutoencoderDetector
from src.ml.behavior import UserBehaviorProfiler
from src.ingestion.metrics import BaselineMetrics
from src.models import Alert


def print_header(text: str):
    print(f"\n{'='*80}")
    print(f"  {text}")
    print(f"{'='*80}\n")


def print_section(text: str):
    print(f"\n  --- {text} ---\n")


def train_isolation_forest(alerts: list[Alert], verbose: bool = False):
    """Train Isolation Forest on alert features."""
    print_section("Training Isolation Forest")

    detector = AnomalyDetector(min_samples_for_training=50)
    SEVERITY_MAP = {"critical": 1.0, "high": 0.75, "medium": 0.50, "low": 0.25, "info": 0.10}

    scores = []
    for i, alert in enumerate(alerts):
        features = {
            "source_ip": alert.metadata.source_ip or "unknown",
            "user": alert.metadata.user or "unknown",
            "hostname": alert.metadata.hostname or "unknown",
            "severity_numeric": list(SEVERITY_MAP.keys()).index(alert.severity) if alert.severity in SEVERITY_MAP else 2,
            "asset_criticality": alert.asset_criticality,
            "confidence": alert.confidence,
            "source_alert_count": 0,
            "category_entropy": 0.5,
            "source_diversity": 1,
        }
        score = detector.observe(features)
        scores.append(score)

        if verbose and i < 10:
            print(f"    Alert {i+1}: {alert.title[:50]:50s} score={score:.3f}")

    stats = detector.get_stats()
    print(f"  Training samples: {stats['training_samples']}")
    print(f"  Model trained: {stats['trained']}")

    # Analyze score distribution
    import numpy as np
    arr = np.array(scores)
    print(f"  Score distribution:")
    print(f"    Mean: {arr.mean():.3f}")
    print(f"    Std:  {arr.std():.3f}")
    print(f"    Min:  {arr.min():.3f}")
    print(f"    Max:  {arr.max():.3f}")
    print(f"    P50:  {np.percentile(arr, 50):.3f}")
    print(f"    P90:  {np.percentile(arr, 90):.3f}")
    print(f"    P99:  {np.percentile(arr, 99):.3f}")

    # Flag anomalies
    anomalous = sum(1 for s in scores if s > 0.7)
    print(f"  Anomalous alerts (score > 0.7): {anomalous} ({anomalous/len(scores)*100:.1f}%)")

    return detector, scores


def train_autoencoder(alerts: list[Alert], verbose: bool = False):
    """Train Autoencoder on alert features."""
    print_section("Training Autoencoder")

    detector = AutoencoderDetector(input_dim=11, min_samples=50, retrain_every=100)
    SEVERITY_MAP = {"critical": 1.0, "high": 0.75, "medium": 0.50, "low": 0.25, "info": 0.10}

    scores = []
    retrain_count = 0
    for i, alert in enumerate(alerts):
        features = [
            SEVERITY_MAP.get(alert.severity, 0.5),
            0.5,  # ip_reputation placeholder
            0.3,  # behavior_deviation placeholder
            alert.confidence,
            alert.asset_criticality,
            1.0 if alert.threat_intel_match else 0.0,
            float(list(SEVERITY_MAP.keys()).index(alert.severity)) / 4.0,
            float(alert.timestamp.hour) / 24.0 if alert.timestamp else 0.5,
            0.5,  # historical_risk placeholder
            0.3,  # anomaly placeholder
            1.0 if alert.metadata.mitre_technique else 0.0,
        ]
        score, retrained = detector.observe_and_score(features)
        scores.append(score)
        if retrained:
            retrain_count += 1

        if verbose and i < 10:
            print(f"    Alert {i+1}: score={score:.3f} retrained={retrained}")

    stats = detector.get_stats()
    print(f"  Buffer size: {stats['buffer_size']}")
    print(f"  Model trained: {stats['trained']}")
    print(f"  Retrain count: {retrain_count}")
    print(f"  Reconstruction threshold: {stats['threshold']}")

    import numpy as np
    arr = np.array(scores)
    print(f"  Score distribution:")
    print(f"    Mean: {arr.mean():.3f}, Std: {arr.std():.3f}")
    print(f"    P90: {np.percentile(arr, 90):.3f}, P99: {np.percentile(arr, 99):.3f}")

    return detector, scores


def train_behavior_profiler(alerts: list[Alert], verbose: bool = False):
    """Train user behavior profiler on alert patterns."""
    print_section("Training User Behavior Profiler")

    profiler = UserBehaviorProfiler()

    deviation_scores = []
    for alert in alerts:
        user = alert.metadata.user or "unknown"
        event = {
            "source_ip": alert.metadata.source_ip,
            "category": alert.category,
            "hostname": alert.metadata.hostname,
            "hour": alert.timestamp.hour if alert.timestamp else 12,
        }
        score = profiler.score_event(user, event)
        deviation_scores.append(score)

    stats = profiler.get_stats()
    print(f"  Tracked users: {stats['tracked_users']}")

    # Show per-user profiles
    print(f"\n  Top user profiles:")
    user_stats = []
    for uid in list(stats.get('profiles', {}).keys())[:10]:
        us = profiler.get_user_stats(uid)
        if us:
            user_stats.append(us)
    user_stats.sort(key=lambda x: x.get('total_events', 0), reverse=True)
    for us in user_stats[:8]:
        print(f"    {us['user_id']:15s} events={us['total_events']:>4d}  "
              f"ips={us['known_source_ips']:>2d}  "
              f"avg/day={us['avg_alerts_per_day']:.1f}")

    import numpy as np
    arr = np.array(deviation_scores)
    print(f"\n  Deviation score distribution:")
    print(f"    Mean: {arr.mean():.3f}, Std: {arr.std():.3f}")
    high_dev = sum(1 for s in deviation_scores if s > 0.5)
    print(f"    High deviation (>0.5): {high_dev} ({high_dev/len(deviation_scores)*100:.1f}%)")

    return profiler, deviation_scores


def simulate_analyst_feedback(aggregator: TriageAggregator, alerts: list[Alert],
                               results: list, verbose: bool = False):
    """Simulate analyst feedback and measure improvement."""
    print_section("Simulating Analyst Feedback Loop")

    # Feedback strategy: mark top 20% as TP, bottom 10% as FP
    n_feedback = min(50, len(results))
    n_tp = int(n_feedback * 0.7)
    n_fp = n_feedback - n_tp

    alert_map = {a.id: a for a in alerts}

    print(f"  Submitting {n_feedback} feedback signals ({n_tp} TP, {n_fp} FP)...")

    # Record scores before feedback
    pre_scores = [r.priority.composite for r in results[:n_feedback]]

    for i in range(n_feedback):
        result = results[i]
        alert = alert_map.get(result.alert_id)
        if not alert:
            continue

        is_tp = i < n_tp
        note = "Confirmed by analyst" if is_tp else "False positive - noisy detection"
        aggregator.submit_feedback(alert, is_tp, analyst_id="eval-analyst", note=note)

        if verbose:
            tp_label = "TP" if is_tp else "FP"
            print(f"    [{tp_label}] {alert.title[:50]:50s} score={result.priority.composite:.1f}")

    # Show feedback metrics
    metrics = aggregator.feedback_loop.get_metrics()
    print(f"\n  Feedback Metrics:")
    print(f"    Total feedback:   {metrics['total_feedback']}")
    print(f"    True positives:   {metrics['true_positives']}")
    print(f"    False positives:  {metrics['false_positives']}")
    print(f"    Overall accuracy: {metrics['overall_accuracy']*100:.1f}%")
    if metrics.get('recent_accuracy_50') is not None:
        print(f"    Recent accuracy:  {metrics['recent_accuracy_50']*100:.1f}%")

    return pre_scores


def retrain_and_compare(aggregator: TriageAggregator, alerts: list[Alert],
                         pre_scores: list[float], verbose: bool = False):
    """Retrain models and compare scores before/after."""
    print_section("Retraining Models with Feedback")

    # Trigger retraining
    aggregator.adaptive_scorer.anomaly_detector.train()

    # Re-triage with a fresh aggregator to compare scores
    print("  Re-triaging with updated models...")
    fresh_agg = TriageAggregator()
    # Transfer learned state
    fresh_agg.adaptive_scorer.ip_reputation = aggregator.adaptive_scorer.ip_reputation
    fresh_agg.adaptive_scorer.historical_db = aggregator.adaptive_scorer.historical_db
    fresh_agg.adaptive_scorer.anomaly_detector = aggregator.adaptive_scorer.anomaly_detector
    fresh_agg.adaptive_scorer.autoencoder = aggregator.adaptive_scorer.autoencoder
    fresh_agg.adaptive_scorer.behavior_profiler = aggregator.adaptive_scorer.behavior_profiler
    fresh_agg.feedback_loop = aggregator.feedback_loop
    results_after = fresh_agg.triage(alerts)

    # Compare top alerts
    print(f"\n  Score comparison (top {min(10, len(results_after))} alerts):")
    print(f"  {'#':<3} {'Before':<8} {'After':<8} {'Delta':<8} {'Action':<12} {'Title'}")
    print(f"  {'-'*3} {'-'*8} {'-'*8} {'-'*8} {'-'*12} {'-'*40}")

    for i in range(min(10, len(results_after))):
        after = results_after[i]
        before_score = pre_scores[i] if i < len(pre_scores) else after.priority.composite
        delta = after.priority.composite - before_score
        delta_str = f"+{delta:.2f}" if delta > 0 else f"{delta:.2f}"
        color = "\033[92m" if delta > 0.01 else ("\033[91m" if delta < -0.01 else "")
        reset = "\033[0m" if color else ""
        action = after.action if isinstance(after.action, str) else after.action.value
        title = after.explanation.summary[:40] if len(after.explanation.summary) > 40 else after.explanation.summary
        print(f"  {color}{i+1:<3} {before_score:<8.2f} {after.priority.composite:<8.2f} "
              f"{delta_str:<8} {action:<12} {title}{reset}")

    # Show score distribution change
    post_scores = [r.priority.composite for r in results_after[:len(pre_scores)]]
    import numpy as np
    pre_arr = np.array(pre_scores[:len(post_scores)])
    post_arr = np.array(post_scores)
    delta_arr = post_arr - pre_arr

    print(f"\n  Aggregate score changes:")
    print(f"    Mean before: {pre_arr.mean():.2f}")
    print(f"    Mean after:  {post_arr.mean():.2f}")
    print(f"    Mean delta:  {delta_arr.mean():+.2f}")
    print(f"    Alerts with score increase: {sum(1 for d in delta_arr if d > 0.01)}")
    print(f"    Alerts with score decrease: {sum(1 for d in delta_arr if d < -0.01)}")

    return results_after


def show_baseline_metrics(alerts: list[Alert], results: list, triage_time: float):
    """Display comprehensive baseline metrics."""
    print_section("Baseline Metrics & Cost Analysis")

    metrics = BaselineMetrics()
    suppressed = len(alerts) - len(results)
    metrics.record_batch(alerts, results, suppressed, triage_time)
    summary = metrics.get_summary()

    print(f"  Volume:")
    print(f"    Total alerts received:    {summary['total_alerts_received']:>8,}")
    print(f"    After AI filtering:       {summary['total_triaged']:>8,}")
    print(f"    Noise suppressed:         {summary['total_suppressed']:>8,}")
    print(f"    Suppression rate:         {summary['suppression_rate_pct']:>8}")

    print(f"\n  Performance:")
    print(f"    Triage time:              {summary['timing']['avg_triage_time_seconds']:>8.2f}s")
    print(f"    Alerts per second:        {summary['timing']['avg_alerts_per_second']:>8.0f}")

    print(f"\n  Impact vs Manual Triage:")
    print(f"    Manual hours needed:      {summary['impact']['estimated_manual_hours']:>8.1f} hrs")
    print(f"    AI-assisted hours:        {summary['impact']['estimated_automated_hours']:>8.1f} hrs")
    print(f"    Time saved:               {summary['impact']['time_saved_hours']:>8.1f} hrs")
    print(f"    Time saved:               {summary['impact']['time_saved_pct']:>8}")
    print(f"    Cost saved (at $75/hr):   ${summary['impact']['estimated_cost_saved_usd']:>8,.2f}")
    print(f"    Automation rate:          {summary['impact']['automation_rate_pct']:>8}")

    print(f"\n  Distribution:")
    for sev, count in sorted(summary['distributions']['severity'].items()):
        bar = "#" * min(count // 20, 40)
        print(f"    {sev:<10} {count:>6}  {bar}")

    print(f"\n  Industry Comparison:")
    for key, val in summary['industry_comparison'].items():
        print(f"    {key:30s} {val}")


def main():
    parser = argparse.ArgumentParser(description="Train & Evaluate AI Triage Models")
    parser.add_argument("--verbose", action="store_true", help="Detailed output")
    args = parser.parse_args()

    print_header("SOC with AI — Training & Evaluation Pipeline")

    # 1. Generate data
    print_section("Step 1: Generating Training Data")
    alerts = generate_10k_alerts(seed=42)[:2000]
    print(f"  Generated {len(alerts)} alerts")

    sev = defaultdict(int)
    for a in alerts:
        sev[a.severity] += 1
    print(f"  Severity distribution: {dict(sev)}")

    # 2. Train Isolation Forest
    if_detector, iso_scores = train_isolation_forest(alerts, args.verbose)

    # 3. Train Autoencoder
    ae_detector, ae_scores = train_autoencoder(alerts, args.verbose)

    # 4. Train Behavior Profiler
    profiler, beh_scores = train_behavior_profiler(alerts, args.verbose)

    # 5. Full triage
    print_section("Step 5: Full Pipeline Triage")
    aggregator = TriageAggregator()
    t0 = time.time()
    results = aggregator.triage(alerts)
    triage_time = time.time() - t0
    print(f"  Triaged {len(alerts)} -> {len(results)} alerts in {triage_time:.2f}s")
    print(f"  Suppressed: {len(alerts) - len(results)} ({(len(alerts)-len(results))/len(alerts)*100:.1f}%)")

    # 6. Simulate feedback
    pre_scores = simulate_analyst_feedback(aggregator, alerts, results, args.verbose)

    # 7. Retrain and compare
    results_after = retrain_and_compare(aggregator, alerts, pre_scores, args.verbose)

    # 8. Baseline metrics
    show_baseline_metrics(alerts, results_after, triage_time)

    # 9. Persist learned ensemble/RL state so the API server starts pre-trained
    from src.ml.ensemble import save_ensemble_state
    from pathlib import Path as _Path
    state_path = _Path(__file__).resolve().parent / "models" / "trained" / "ensemble_state.pkl"
    scorer = aggregator.adaptive_scorer
    if save_ensemble_state(state_path, scorer.ensemble, scorer.rl_adapter):
        print_section("Step 9: Model Persistence")
        print(f"  Saved ensemble state: {state_path}")
        print(f"  RL feedback processed: {scorer.rl_adapter._feedback_count}")
    else:
        print("  WARNING: failed to save ensemble state")

    print_header("Training Complete — Models are now learning from data and feedback")


if __name__ == "__main__":
    main()
