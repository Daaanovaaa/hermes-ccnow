#!/bin/bash
# CCN! Container Health Check
VAULT="/root/obsidian-vault"
DATE=$(date +%Y-%m-%d\ %H:%M)
REPORT="$VAULT/00-INBOX/HEALTH_$(date +%Y-%m-%d).md"

EXPECTED="paperclip paperclip-db temporal temporal-postgresql \
  temporal-admin-tools temporal-ui postiz postiz-postgres \
  postiz-redis n8n actual-budget spotlight"

echo "# Health Check — $DATE" > "$REPORT"
echo "" >> "$REPORT"

ALL_OK=true
for NAME in $EXPECTED; do
  STATUS=$(docker inspect --format='{{.State.Status}}' "$NAME" 2>/dev/null)
  if [ "$STATUS" = "running" ]; then
    echo "- ✅ $NAME — running" >> "$REPORT"
  else
    echo "- ❌ $NAME — $STATUS" >> "$REPORT"
    ALL_OK=false
  fi
done

echo "" >> "$REPORT"
FREE=$(free -h | awk '/^Mem:/{print $4}')
DISK=$(df -h / | awk 'NR==2{print $4}')
echo "RAM free: $FREE | Disk free: $DISK" >> "$REPORT"

if [ "$ALL_OK" = false ]; then
  echo "" >> "$REPORT"
  echo "⚠️ ACTION REQUIRED — One or more containers are down." >> "$REPORT"
fi
