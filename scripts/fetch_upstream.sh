#!/usr/bin/env bash
# Fetch official evaluators and data at the commits pinned in src/nrqa/datasets.py.
set -euo pipefail
cd "$(dirname "$0")/.."
fetch() { # name url commit
  local dir="third_party/$1"
  [ -d "$dir/.git" ] && { echo "have $1"; return; }
  mkdir -p "$dir"
  git -C "$dir" init -q
  git -C "$dir" remote add origin "$2"
  git -C "$dir" fetch -q --depth 1 origin "$3"
  git -C "$dir" -c advice.detachedHead=false checkout -q FETCH_HEAD
  echo "fetched $1 $(git -C "$dir" rev-parse HEAD)"
}
fetch FinQA       https://github.com/czyssrs/FinQA        0f16e2867befa6840783e58be38c9efb9229d742
fetch TAT-QA      https://github.com/NExTplusplus/TAT-QA  870accc41953dcde885aabeb963d94aabdc0fbc3
fetch ConvFinQA   https://github.com/czyssrs/ConvFinQA    cf3eed2d5984960bf06bb8145bcea5e80b0222a6
fetch HybridQA    https://github.com/wenhuchen/HybridQA   db22fda8c5951438fade3c69d75b350335ba93b3
fetch TAT-HQA     https://github.com/NExTplusplus/TAT-HQA 8b821d89f0fbfeceea07e4f5faf46b33150fee07
fetch MultiHiertt https://github.com/psunlpgroup/MultiHiertt 45bd9ccdf3142ea059bd5e69c0afb83437fa539c
[ -d data/WikiTables-WithLinks ] || git clone -q --depth 1 https://github.com/wenhuchen/WikiTables-WithLinks data/WikiTables-WithLinks
