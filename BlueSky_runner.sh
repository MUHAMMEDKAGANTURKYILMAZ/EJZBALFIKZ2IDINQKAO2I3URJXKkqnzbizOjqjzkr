#!/bin/bash
# ~/bluesky_runner.sh

BOT_YOLU="Write_your_own_bot_path_here"
[ -z "$ILK" ] && { ILK=1; python3 "$BOT_YOLU" & PID=$!; sleep 15; kill $PID 2>/dev/null; }

while true; do
    BEKLEME=$((RANDOM % 1501 + 2700)); echo "$(date '+%H:%M:%S'): $((BEKLEME/60)) dk bekleniyor..."
    sleep $BEKLEME

    echo "$(date '+%H:%M:%S'): Bot başlatılıyor..."
    timeout 15 python3 "$BOT_YOLU"

    echo "$(date '+%H:%M:%S'): Bot durduruldu, yeniden başlanıyor..."
    echo "---"
done
