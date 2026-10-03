#!/bin/bash
D=$(cd "$(dirname "$0")" && pwd); cd $D
K=$(python3 -c "import re,os;print(re.search(r'api_?[kK]ey\s*=\s*[\"\']?([^\"\'\n]+)',open(os.path.expanduser('~/.runpod/config.toml')).read()).group(1))")
BAL0=$(cat balance_start.txt)
for i in $(seq 1 15); do
  for inst in cpu3c-32-64 cpu5c-32-64 cpu3c-16-32 cpu5c-16-32; do
    q="{\"query\":\"mutation { deployCpuPod(input: {cloudType: SECURE, instanceId: \\\"$inst\\\", templateId: \\\"runpod-ubuntu-2204\\\", name: \\\"pptc-doe\\\", containerDiskInGb: 40, startSsh: true, ports: \\\"22/tcp\\\"}) { id costPerHr } }\"}"
    out=$(curl -s -m 60 https://api.runpod.io/graphql -H "Content-Type: application/json" -H "Authorization: Bearer $K" -d "$q")
    id=$(echo "$out" | python3 -c "import json,sys
try: print(json.load(sys.stdin)['data']['deployCpuPod']['id'])
except Exception: print('')")
    if [ -n "$id" ]; then
      echo $id > pod_id.txt; echo $inst > pod_inst.txt
      nohup bash costguard_doe.sh $id auto 9.70 $BAL0 > costguard_doe.out 2>&1 &
      echo "DEPLOYED $id $inst attempt $i"; exit 0
    fi
  done
  echo "attempt $i: none available $(date '+%T')"; sleep 60
done
echo "GAVE UP"
