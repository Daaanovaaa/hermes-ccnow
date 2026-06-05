#!/usr/bin/env python3
"""
Wayback Machine crawler - DISABLED
faaate.com was taken over by Chinese gambling operators in 2021.
All historical snapshots after 2018 are contaminated.
The one clean 2018 snapshot is already in raw_text/.
This crawler is permanently disabled to prevent re-contamination.
"""

import logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def main():
    logger.warning("Wayback crawler DISABLED - faaate.com domain compromised by Chinese operators")
    logger.warning("Clean 2018 snapshot already preserved in raw_text/")
    logger.warning("Do not re-enable without manual review of target domain")

if __name__ == "__main__":
    main()
