#!/usr/bin/env python3
"""
Prayer Witness ID Generator
Generates unique PW-IDs and faith declarations for kingdom seed investments.

Format: PW-YYYYMMDD-TICKER

Usage:
  python3 pw_id_generator.py TICKER COMPANY [REASON]
"""
import sys
from datetime import date

PRAYER_VERSE = (
    'Mark 4:26-29 — "So is the kingdom of GOD, as if a man should cast seed '
    'into the ground; And should sleep, and rise night and day, and the seed '
    'should spring and grow up, he knoweth not how."'
)


def generate_pw_id(ticker: str, investment_date: date = None) -> str:
    d = investment_date or date.today()
    return f'PW-{d.strftime("%Y%m%d")}-{ticker.upper().strip()}'


def generate_declaration(ticker: str, company: str, reason: str,
                          pw_id: str = None) -> str:
    if pw_id is None:
        pw_id = generate_pw_id(ticker)
    return (
        f'PRAYER WITNESS DECLARATION\n'
        f'PW-ID: {pw_id}\n\n'
        f'I, Carlos DaNova Villanueva, declare before GOD and the host of heaven:\n'
        f'This $1.00 fractional share in {company} ({ticker.upper()}) is a kingdom seed.\n'
        f'Reason: {reason}\n\n'
        f'We declare this investment covered in prayer, protected from every loss,\n'
        f'and positioned for divine multiplication according to covenant promise.\n\n'
        f'{PRAYER_VERSE}\n\n'
        f'In the name of JESUS. Amen.\n'
    )


def format_saturday_message(ticker: str, company: str, price_range: str,
                              ipo_date: str, reason: str,
                              pw_id: str = None) -> str:
    if pw_id is None:
        pw_id = generate_pw_id(ticker)
    return (
        f'🙏 PW-ID: {pw_id}\n'
        f'Today\'s IPO: {company} ({ticker.upper()}) — opens {ipo_date} at {price_range}\n'
        f'Recommendation: BUY $1 fractional in Fidelity NOW\n'
        f'WHY: {reason}\n\n'
        f'Reply with your Fidelity confirmation number to log this act of faith.'
    )


if __name__ == '__main__':
    if len(sys.argv) < 3:
        print('Usage: pw_id_generator.py TICKER COMPANY [REASON]')
        sys.exit(1)
    ticker  = sys.argv[1]
    company = sys.argv[2]
    reason  = sys.argv[3] if len(sys.argv) > 3 else 'Kingdom seed investment'
    pw_id   = generate_pw_id(ticker)
    print(generate_declaration(ticker, company, reason, pw_id))
