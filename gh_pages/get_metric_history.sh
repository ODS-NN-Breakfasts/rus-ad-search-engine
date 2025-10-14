#!/bin/bash

echo -e "epoch_time\trequest_db_hash\tad_db_hash\tmarkup_hash\taccuracy\tprecision\trecall\tf1\ttp\tfp\ttn\tfn" > metrics.csv

git log --follow --name-only --oneline --pretty=format:"%H %at" -- ../metrics.json | awk 'BEGIN {n=0} {if (n==0) {s[n]=$1; date=$2} else s[n]=$0; n++; if (n%3==0) {printf("%s:%s %s\n", s[0], s[1], date); n=0}} END {if (n==2) printf("%s:%s %s\n", s[0], s[1], date)}' | while IFS='$\n' read -r params; do IFS=' ' read -a p <<< $params; echo ${p[1]} `git show ${p[0]}` | python -c "import sys, json, numpy as np; s=sys.stdin.read().strip().split(' ', 1); acc=json.loads(s[1]); cm=acc.get(\"conf_matr\", {}); dh=acc.get(\"data_hashes\", {}); print(f'{s[0]}\t{dh.get(\"request_db\")}\t{dh.get(\"ad_db\")}\t{dh.get(\"markup\")}\t{acc.get(\"accuracy\", np.nan)}\t{acc.get(\"precision\", np.nan)}\t{acc.get(\"recall\", np.nan)}\t{acc.get(\"f1\", np.nan)}\t{cm.get(\"TP\")}\t{cm.get(\"FP\")}\t{cm.get(\"TN\")}\t{cm.get(\"FN\")}')" >> metrics.csv; done
