#!/usr/bin/env python3
"""
Life Reality Layer — Adaptive Learner
Runs every Sunday at 7 AM AST (11 UTC) before the Sunday review.

Reads checkin_log.csv + accountability memory_log.csv (existing system).
Calculates completion rates, identifies drift patterns, surfaces what is
and is not working. After 4 weeks of data, begins suggesting realistic
schedule adjustments.

Never reduces the standard — holds the vision while acknowledging real capacity.
Output goes to stdout — Hermes cron delivers it to Telegram.
"""

import csv
import json
import os
import sys
from collections import defaultdict
from datetime import date, datetime, timedelta
from pathlib import Path

LIFE_DIR     = Path(__file__).parent
CONFIG_F     = LIFE_DIR / 'life_reality_config.json'
CHECKIN_LOG  = LIFE_DIR / 'checkin_log.csv'
ACCT_LOG     = Path('/root/Hetzner/CC_NOW/accountability/memory_log.csv')
MIN_WEEKS    = 4   # weeks of data before making suggestions


def load_config():
    if CONFIG_F.exists():
        with open(CONFIG_F) as f:
            return json.load(f)
    return {}


def load_checkin_log(days_back=7):
    if not CHECKIN_LOG.exists():
        return []
    cutoff = date.today() - timedelta(days=days_back)
    rows = []
    try:
        with open(CHECKIN_LOG, newline='') as f:
            for row in csv.DictReader(f):
                try:
                    if date.fromisoformat(row['date']) >= cutoff:
                        rows.append(row)
                except (ValueError, KeyError):
                    pass
    except Exception:
        pass
    return rows


def load_all_checkin_log():
    """Load all historical check-in data for week-count calculation."""
    if not CHECKIN_LOG.exists():
        return []
    rows = []
    try:
        with open(CHECKIN_LOG, newline='') as f:
            rows = list(csv.DictReader(f))
    except Exception:
        pass
    return rows


def load_accountability_log(days_back=7):
    if not ACCT_LOG.exists():
        return []
    cutoff = date.today() - timedelta(days=days_back)
    rows = []
    try:
        with open(ACCT_LOG, newline='') as f:
            for row in csv.DictReader(f):
                try:
                    if date.fromisoformat(row['date']) >= cutoff:
                        rows.append(row)
                except (ValueError, KeyError):
                    pass
    except Exception:
        pass
    return rows


def count_data_weeks():
    """Count how many distinct calendar weeks appear in checkin_log.csv."""
    all_rows = load_all_checkin_log()
    if not all_rows:
        return 0
    weeks = set()
    for row in all_rows:
        try:
            d = date.fromisoformat(row['date'])
            weeks.add(d.isocalendar()[:2])  # (year, week_number)
        except (ValueError, KeyError):
            pass
    return len(weeks)


def checkin_analysis(rows):
    """
    Analyse this week's check-in records.
    Returns dict of block → {sent, recorded, wins, partials, gaps, completion_pct}
    """
    blocks = ['morning', 'afternoon', 'evening', 'night']
    stats  = {b: {'sent': 0, 'recorded': 0, 'wins': 0, 'partials': 0, 'gaps': 0} for b in blocks}

    for row in rows:
        block = row.get('block', '').lower()
        if block not in stats:
            continue
        status    = row.get('status', '')
        completed = row.get('completed', '').lower()

        if status == 'sent':
            stats[block]['sent'] += 1
        elif status == 'recorded':
            stats[block]['recorded'] += 1
            if completed == 'yes':
                stats[block]['wins'] += 1
            elif completed == 'partial':
                stats[block]['partials'] += 1
            elif completed in ('no', ''):
                stats[block]['gaps'] += 1

    # Calculate completion percentage
    for block, s in stats.items():
        total = s['wins'] + s['partials'] + s['gaps']
        if total > 0:
            s['completion_pct'] = round((s['wins'] + 0.5 * s['partials']) / total * 100)
        else:
            s['completion_pct'] = None

    return stats


def interruption_patterns(rows):
    """Extract recurring interruption reasons from this week's data."""
    reasons = []
    for row in rows:
        r = row.get('interruption_reason', '').strip()
        if r:
            reasons.append(r)
    return reasons


def accountability_summary(acct_rows):
    """Summarize accountability log data for this week."""
    wins  = [r for r in acct_rows if r.get('gap_win') == 'WIN']
    gaps  = [r for r in acct_rows if r.get('gap_win') == 'GAP']
    by_pillar = defaultdict(lambda: {'wins': 0, 'gaps': 0})
    for r in acct_rows:
        pillar = r.get('pillar', 'UNKNOWN')
        key    = r.get('gap_win', '').lower()
        if key in ('win', 'gap'):
            by_pillar[pillar][key + 's'] += 1

    flagged = {}
    if len(gaps) >= 3:
        gap_items = defaultdict(int)
        for r in gaps:
            gap_items[r.get('planned', '').strip()] += 1
        flagged = {k: v for k, v in gap_items.items() if v >= 3}

    return {
        'total_entries': len(acct_rows),
        'wins': len(wins),
        'gaps': len(gaps),
        'by_pillar': dict(by_pillar),
        'flagged': flagged,
    }


def generate_suggestions(block_stats, acct_summary, data_weeks):
    """
    After MIN_WEEKS of data: suggest realistic schedule adjustments.
    Never removes the standard — adjusts timing or sequencing.
    """
    if data_weeks < MIN_WEEKS:
        return []

    suggestions = []
    config = load_config()
    protected = set(config.get('adaptive_learner', {}).get('protected_blocks', []))
    threshold = config.get('adaptive_learner', {}).get('flag_threshold_completion_pct', 60)

    for block, stats in block_stats.items():
        pct = stats.get('completion_pct')
        if pct is not None and pct < threshold:
            suggestions.append(
                f'{block.upper()} BLOCK — {pct}% completion rate over {data_weeks} weeks. '
                f'Consider: Does this block have the right energy level for the tasks assigned? '
                f'The standard stays — the TIMING may need adjustment.'
            )

    # Check accountability flagged items
    for item, count in acct_summary.get('flagged', {}).items():
        if not any(p.lower() in item.lower() for p in protected):
            suggestions.append(
                f'PATTERN: "{item}" missed {count}+ times. '
                f'Is this physically viable at its current time slot? '
                f'Consider moving it or marking it TESTING.'
            )

    return suggestions


def main():
    today     = date.today()
    week_end  = today.isoformat()
    week_start = (today - timedelta(days=7)).isoformat()
    data_weeks = count_data_weeks()

    checkin_rows = load_checkin_log(days_back=7)
    acct_rows    = load_accountability_log(days_back=7)

    block_stats  = checkin_analysis(checkin_rows)
    reasons      = interruption_patterns(checkin_rows)
    acct_summary = accountability_summary(acct_rows)
    suggestions  = generate_suggestions(block_stats, acct_summary, data_weeks)

    lines = [
        'LIFE REALITY — WEEKLY ADAPTIVE REPORT',
        f'Week: {week_start} → {week_end}',
        f'Data on file: {data_weeks} week{"s" if data_weeks != 1 else ""}',
        '=' * 40,
    ]

    # --- Check-in coverage ---
    lines += ['', 'CHECK-IN COVERAGE THIS WEEK', '─' * 40]
    has_checkin_data = any(s['sent'] > 0 for s in block_stats.values())

    if not has_checkin_data:
        lines.append('No check-in data this week. Check-in crons may not yet be delivering to Telegram.')
        lines.append('Verify: hermes cron list — all 4 activity-check crons should show deliver: origin')
    else:
        for block, s in block_stats.items():
            sent     = s['sent']
            recorded = s['recorded']
            pct_str  = f'{s["completion_pct"]}%' if s['completion_pct'] is not None else 'no responses yet'
            lines.append(
                f'{block.upper():12s} — {sent} check-ins sent | '
                f'{recorded} responses | completion: {pct_str}'
            )

    # --- Interruption patterns ---
    if reasons:
        lines += ['', 'WHAT INTERRUPTED YOU THIS WEEK:', '─' * 40]
        from collections import Counter
        for reason, count in Counter(reasons).most_common(5):
            lines.append(f'  [{count}x] {reason}')

    # --- Accountability cross-reference ---
    lines += ['', 'ACCOUNTABILITY LOG CROSS-REFERENCE', '─' * 40]
    if acct_summary['total_entries'] == 0:
        lines.append('No accountability entries this week.')
    else:
        lines.append(
            f'Entries: {acct_summary["total_entries"]} | '
            f'Wins: {acct_summary["wins"]} | '
            f'Gaps: {acct_summary["gaps"]}'
        )
        for pillar, counts in sorted(acct_summary['by_pillar'].items()):
            w = counts.get('wins', 0)
            g = counts.get('gaps', 0)
            lines.append(f'  {pillar:8s}: {w}W / {g}G')

        if acct_summary['flagged']:
            lines += ['', 'REPEATEDLY MISSED (3+ times this week):']
            for item, count in acct_summary['flagged'].items():
                lines.append(f'  [{count}x] {item} — flag for Testing Season review')

    # --- Suggestions (only after MIN_WEEKS of data) ---
    if data_weeks < MIN_WEEKS:
        lines += [
            '',
            f'ADAPTIVE SUGGESTIONS: Collecting data — {MIN_WEEKS - data_weeks} more week(s) until pattern analysis.',
            'Keep showing up. The picture gets clearer every week.',
        ]
    elif suggestions:
        lines += ['', 'ADAPTIVE OBSERVATIONS:', '─' * 40]
        for s in suggestions:
            lines.append(f'  • {s}')
        lines += [
            '',
            'Remember: the standard does not move. What adjusts is WHEN and HOW',
            'the work happens — not WHETHER it happens.',
        ]
    else:
        lines += [
            '',
            'ADAPTIVE STATUS: Patterns look healthy. No adjustments needed this week.',
        ]

    lines += [
        '',
        '=' * 40,
        'North Star: El Pabellón de Victoria — Hormigueros, PR',
        'The real DaNova shows up consistently. That is the data we are building.',
    ]

    print('\n'.join(lines))


if __name__ == '__main__':
    main()
