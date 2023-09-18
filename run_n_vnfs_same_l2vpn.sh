#!/bin/bash

# Display help message if not enough arguments are provided
if [ "$#" -lt 6 ]; then
    echo "Usage: $0 <total_parallel_executions> <iterations> <pkts_per_iteration> <pkt_size> <tx_interface> <rx_interface>"
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

total_parallel_executions=$1
iterations=$2
pkts_per_iteration=$3
pkt_size=$4
tx_interface=$5
rx_interface=$6

source .venv/bin/activate
for ((i = 1; i <= total_parallel_executions; i++)); do
    # Replace last character of interfaces with $i
    tx_interface=${tx_interface%?}$i
    rx_interface=${rx_interface%?}$i
    arguments="--iterations $iterations --pkts-per-iteration $pkts_per_iteration --pkt-size $pkt_size --tx-interface $tx_interface --rx-interface $rx_interface --parallel-id $i"
    echo "Running iteration $i with arguments: $arguments"
    python3 rina_netmap_benchmark.py $arguments &
done

# Wait for all background processes to finish
wait
