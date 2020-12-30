#!/bin/bash   
  
# Init tables
psql -f init-tables.sql

# Generate data
python3 dataset-generator.py