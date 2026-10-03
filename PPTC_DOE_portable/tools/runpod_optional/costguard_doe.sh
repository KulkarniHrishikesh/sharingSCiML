#!/bin/bash
# Local cost guard for the DOE sweep. Stops the pod when total spend reaches LIMIT.
# Usage: costguard_doe.sh POD_ID HOST:PORT LIMIT_USD BALANCE_AT_START
# Spend = max(time x hourly rate, balance drop). Results are mirrored with rsync every 5 min
# (only new files), and once more before the pod is stopped.
DIR=$(cd "$(dirname "$0")" && pwd); POD=$1; HP=$2; LIMIT=$3; BAL0=$4
START=$(date +%s); mkdir -p $DIR/pulled
sync_results(){ hp=$(runpodctl ssh info $POD 2>/dev/null | python3 -c "import json,sys
try: d=json.load(sys.stdin); print(d['ip']+':'+str(d['port']))
except Exception: print('')"); [ -z "$hp" ] && return; H=${hp%:*}; PORT=${hp##*:}; rsync -az --timeout=120 -e "ssh -p $PORT -o StrictHostKeyChecking=no -o ConnectTimeout=15" root@$H:/workspace/pptc/results/ $DIR/pulled/ 2>/dev/null; }
i=0
while true; do
  r=$(runpodctl pod get $POD 2>/dev/null | python3 -c "import json,sys
try: d=json.load(sys.stdin); print(d.get('costPerHr') or 0, d.get('desiredStatus','?'))
except Exception: print('0 ?')"); RATE=${r% *}; ST=${r#* }
  bal=$(runpodctl user 2>/dev/null | python3 -c "import json,sys
try: print(json.load(sys.stdin)['clientBalance'])
except Exception: print('')")
  spent=$(python3 -c "print(round(max(($(date +%s)-$START)/3600*$RATE, $BAL0-float('${bal:-$BAL0}')),3))")
  echo "$(date '+%F %T') status=$ST rate=$RATE balance=$bal spent=$spent" >> $DIR/costguard_doe.log
  i=$((i+1)); [ $((i % 5)) -eq 0 ] && sync_results
  [ "$ST" = EXITED ] || [ "$ST" = TERMINATED ] && { echo "pod $ST; exit" >> $DIR/costguard_doe.log; exit 0; }
  if grep -q "sweep end" $DIR/pulled/progress.log 2>/dev/null; then sync_results; runpodctl pod stop $POD >> $DIR/costguard_doe.log 2>&1; echo "STOPPED: sweep done, spent $spent"; exit 0; fi
  if python3 -c "import sys; sys.exit(0 if $spent >= $LIMIT else 1)"; then sync_results; runpodctl pod stop $POD >> $DIR/costguard_doe.log 2>&1; echo "STOPPED: limit, spent $spent"; exit 0; fi
  sleep 60
done
