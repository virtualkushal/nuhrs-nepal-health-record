#!/bin/bash
set -e
apt-get update -qq
apt-get install -y -qq graphviz libgraphviz-dev gcc > /dev/null
pip install --quiet eralchemy2 psycopg2-binary

declare -A MAP=(
  [national_db]=db-national
  [swastha_db]=db-swastha
  [mediciti_db]=db-mediciti
  [norvic_db]=db-norvic
  [lab_a_db]=db-lab-a
)
for db in "${!MAP[@]}"; do
  echo "Rendering $db from ${MAP[$db]}..."
  if eralchemy2 -i "postgresql://nuhrs:nuhrs@${MAP[$db]}:5432/$db" -o "/out/$db.png"; then
    echo "OK $db"
  else
    echo "FAIL $db"
  fi
done
