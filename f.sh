#!/bin/bash

# Loop 1000 times
for ((i=1; i<=1000; i++))
do
  echo "Running iteration $i"
  python3 manage.py fetch_crypto_data
  sleep 10
done
