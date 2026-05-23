#!/usr/bin/env python3
"""
IPO Researcher — Fetches upcoming IPOs from NASDAQ public calendar API.
Filters by price, date window, and Fidelity fractional eligibility.
Saves shortlist to ipo_cache.json for use by prayer_finance_engine.py

Usage:
  python3 ipo_researcher.py            # Run research, save ipo_cache.json
  python3 ipo_researcher.py --dry-run  # Print results without saving
"""
import json, sys, requests
from datetime import date, datetime, timedelta
from pathlib import Path

FINANCE_DIR = Path(__file__).parent
CACHE_FILE  = FINANCE_DIR / 'ipo_cache.json'
CONFIG_FILE = FINANCE_DIR / 'prayer_finance_config.json'

HEADERS = {
    'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36',
    'Accept': 'application/json, text/plain, */*',
    'Accept-Language': 'en-US,en;q=0.9',
}


def load_config():
    with open(CONFIG_FILE) as f:
        return json.load(f)


def fetch_nasdaq_ipos(year_month: str) -> dict:
    url = f'https://api.nasdaq.com/api/ipo/calendar/?date={year_month}'
    r = requests.get(url, headers=HEADERS, timeout=20)
    r.raise_for_status()
    return r.json()


def parse_price(price_str: str) -> tuple[float, float]:
    """Parse '$12.00-$14.00' or '$15.00' into (lo, hi)."""
    price_str = price_str.replace('$', '').replace(',', '').strip()
    if not price_str or price_str in ('-', 'N/A', ''):
        return 0.0, 0.0
    if '-' in price_str:
        parts = price_str.split('-')
        try:
            return float(parts[0].strip()), float(parts[1].strip())
        except ValueError:
            return 0.0, 0.0
    try:
        v = float(price_str)
        return v, v
    except ValueError:
        return 0.0, 0.0


def parse_ipo_date(date_str: str) -> date | None:
    """Parse date strings like '05/30/2026' or '2026-05-30'."""
    for fmt in ('%m/%d/%Y', '%Y-%m-%d', '%m/%d/%y'):
        try:
            return datetime.strptime(date_str.strip(), fmt).date()
        except (ValueError, AttributeError):
            continue
    return None


def score_mission(company: str, sector: str) -> int:
    text = (company + ' ' + sector).lower()
    if any(k in text for k in ['christian', 'faith', 'church', 'ministry', 'bible']):
        return 10
    if any(k in text for k in ['health', 'medical', 'pharma', 'bio', 'care']):
        return 8
    if any(k in text for k in ['tech', 'software', 'digital', 'cloud', 'ai', 'saas']):
        return 7
    if any(k in text for k in ['media', 'content', 'streaming', 'education']):
        return 6
    return 5


def score_momentum(price_lo: float, price_hi: float) -> int:
    if price_lo == 0:
        return 5
    spread = (price_hi - price_lo) / price_lo
    if spread <= 0.10:
        return 9
    if spread <= 0.20:
        return 7
    if spread <= 0.30:
        return 5
    return 3


def parse_candidates(data: dict, max_price: float, today: date, cutoff: date) -> list:
    candidates = []
    d = data.get('data', {})
    # Upcoming: data.upcoming.upcomingTable.rows
    upcoming = ((d.get('upcoming') or {}).get('upcomingTable') or {}).get('rows') or []
    # Priced: data.priced.rows
    priced   = ((d.get('priced') or {}).get('rows')) or []

    for row in upcoming + priced:
        try:
            ticker  = (row.get('proposedTickerSymbol') or '').strip().upper()
            company = (row.get('companyName') or '').strip()
            if not ticker or not company:
                continue

            # Price is "6.00-7.00" or "10.00" (no $ sign from this endpoint)
            raw_price = (row.get('proposedSharePrice') or row.get('pricedSharePrice') or '0')
            price_lo, price_hi = parse_price(raw_price)
            if price_hi == 0 or price_hi > max_price:
                continue

            raw_date = (row.get('expectedPriceDate') or row.get('pricedDate') or '')
            ipo_date = parse_ipo_date(raw_date)
            if ipo_date is None:
                ipo_date = today + timedelta(days=7)
            if not (today <= ipo_date <= cutoff):
                continue

            # Derive sector from exchange + company name (no sector field in API)
            exchange  = (row.get('proposedExchange') or '').strip()
            sector    = 'Unknown'
            m_score   = score_mission(company, '')
            mom_score = score_momentum(price_lo, price_hi)
            price_mid = (price_lo + price_hi) / 2

            candidates.append({
                'ticker':              ticker,
                'company':             company,
                'ipo_date':            ipo_date.isoformat(),
                'price_range':         f'${price_lo:.2f}-${price_hi:.2f}',
                'price_mid':           round(price_mid, 2),
                'exchange':            exchange,
                'sector':              sector,
                'fractional_eligible': True,
                'stability_score':     5,
                'mission_score':       m_score,
                'momentum_score':      mom_score,
                'rationale':           (
                    f'{exchange} IPO opening at ${price_lo:.2f}-${price_hi:.2f}. '
                    f'Fidelity fractional eligible. Kingdom seed opportunity.'
                ),
            })
        except (ValueError, TypeError, KeyError):
            continue
    return candidates


def composite_score(c: dict) -> float:
    return (c['stability_score'] * 0.25 + c['mission_score'] * 0.25
            + (10 if c['fractional_eligible'] else 3) * 0.20
            + c['momentum_score'] * 0.30)


def run(dry_run: bool = False) -> dict:
    config    = load_config()
    max_price = config['filters']['max_price']
    today     = date.today()
    cutoff    = today + timedelta(days=config['filters'].get('window_days', 14))

    months = [today.strftime('%Y-%m')]
    if today.day > 20:
        nxt = (today.replace(day=28) + timedelta(days=4))
        months.append(nxt.strftime('%Y-%m'))

    candidates = []
    for ym in months:
        try:
            data  = fetch_nasdaq_ipos(ym)
            batch = parse_candidates(data, max_price, today, cutoff)
            candidates.extend(batch)
            print(f'  NASDAQ {ym}: {len(batch)} candidates')
        except Exception as e:
            print(f'  NASDAQ fetch failed ({ym}): {e}', file=sys.stderr)

    # Deduplicate by ticker
    seen, unique = set(), []
    for c in candidates:
        if c['ticker'] not in seen:
            seen.add(c['ticker'])
            unique.append(c)

    unique.sort(key=composite_score, reverse=True)

    result = {
        'research_date':   today.isoformat(),
        'window':          f'{today.isoformat()} to {cutoff.isoformat()}',
        'candidate_count': len(unique),
        'candidates':      unique[:10],
    }

    if not dry_run:
        with open(CACHE_FILE, 'w') as f:
            json.dump(result, f, indent=2)

    print(f'\nIPO Research complete — {len(unique)} candidates in next 14 days')
    for c in unique[:5]:
        print(f'  [{composite_score(c):.1f}] {c["ticker"]} — {c["company"]} — {c["ipo_date"]} — {c["price_range"]}')

    if not unique:
        print('  No qualifying IPOs found. Consider holding $1 seed for next week.')

    return result


if __name__ == '__main__':
    dry = '--dry-run' in sys.argv
    run(dry_run=dry)
