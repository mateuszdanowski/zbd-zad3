#!/bin/bash

# First, setup data
./setup.sh

# Create 20 elf-simulators
NUMBER_OF_ELFS=20

START=1
END=$NUMBER_OF_ELFS

# Create file with results
> elfs-results

echo -e "\nRUNNER: starting simulation...\n"
for elf_no in $(eval echo "{$START..$END}"); do
    echo -e "\nRUNNER: starting elf $elf_no...\n"
    python3 elf-simulator.py "$elf_no" &
done

echo -e "\nRUNNER: Waiting for simulations to end...\n"
wait

sort -o elfs-results elfs-results 

echo -e "\nRUNNER: Simulation done\n"

python3 count-stats.py