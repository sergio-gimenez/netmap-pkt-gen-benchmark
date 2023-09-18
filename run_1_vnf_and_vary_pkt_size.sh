#!/bin/bash

# Display help message if not enough arguments are provided
if [ "$#" -lt 4 ]; then
    echo "Usage: $0 <iterations> <pkts_per_iteration> <tx_interface> <rx_interface>"
    exit 1
fi

# check whether user had supplied -h or --help . If yes display usage
if [[ ($# == "--help") || $# == "-h" ]]; then
    display_usage
    exit 0
fi

# display usage if the script is not run as root user
if [[ "$EUID" -ne 0 ]]; then
    echo "This script must be run as root!"
    exit 1
fi
iterations=$1
pkts_per_iteration=$2
tx_interface=$3
rx_interface=$4

source .venv/bin/activate
# Iterate through an array of pkt-size
declare pkt_sizes=(64 128 256 512 1024 1280 1500)
for pkt_size in "${pkt_sizes[@]}"; do
    arguments="--iterations $iterations --pkts-per-iteration $pkts_per_iteration --pkt-size $pkt_size --tx-interface $tx_interface --rx-interface $rx_interface"
    echo "Running experiments with $pkt_size bytes's sized packets: $arguments"
    python3 rina_netmap_benchmark.py $arguments
done
