import subprocess
import re
import csv
import threading
from typing import Optional
import matplotlib.pyplot as plt

import logger
log = logger.setup_logger(file_name='pkt_gen_benchmark.log')


def run_pkt_gen(mode: str, interface: str, num_packets: Optional[int] = None):
    import pdb
    pdb.set_trace()
    if mode not in ['tx', 'rx']:
        raise ValueError("Mode must be either 'tx' or 'rx'")
    elif mode == 'rx' and num_packets is None:
        raise ValueError(
            "Number of packets must be specified when running in rx mode")

    cmd = ['sudo', 'pkt-gen', '-i', interface, '-f', mode]

    if mode == 'rx':
        cmd.extend(['-n', str(num_packets)])

    result = subprocess.run(cmd, stdout=subprocess.PIPE,
                            stderr=subprocess.PIPE, text=True)
    return result.stdout


def parse_output(output):
    metrics = {}
    metrics['packets_per_sec'] = re.search(
        r'Speed: (\d+\.\d+) Mpps', output).group(1)
    metrics['throughput'] = re.search(
        r'Bandwidth: (\d+\.\d+) Gbps', output).group(1)
    metrics['average_batch'] = re.search(
        r'Average batch: (\d+\.\d+) pkts', output).group(1)
    return metrics


def main():
    total_experiment_iterations = 2  # Number of times to run pkt-gen
    processed_pkts_per_iteration = 100
    tx_interface = "vale118:01"
    rx_interface = "vale116:01"
    all_metrics = []

    for _ in range(total_experiment_iterations):
        log.info("Running iteration number {}".format(_))
        output = run_pkt_gen(mode='rx', interface=rx_interface,
                             num_packets=processed_pkts_per_iteration)
        metrics = parse_output(output)
        log.info(metrics)
        all_metrics.append(metrics)

    csv_file = 'pkt_gen_metrics.csv'

    # Write the metrics to the CSV file
    with open(csv_file, mode='w', newline='') as file:
        writer = csv.DictWriter(
            file, fieldnames=['packets_per_sec', 'throughput', 'average_batch'])
        writer.writeheader()
        writer.writerows(all_metrics)

    # Extract data for plotting
    packets_per_sec_data = [float(metrics['packets_per_sec'])
                            for metrics in all_metrics]
    throughput_data = [float(metrics['throughput']) for metrics in all_metrics]
    average_batch_data = [float(metrics['average_batch'])
                          for metrics in all_metrics]

    # Create a figure with subplots
    fig, axes = plt.subplots(3, 1, figsize=(10, 15))
    axes[0].plot(packets_per_sec_data, marker='o')
    axes[0].set_ylabel('Packets per Second')
    axes[0].set_title('Packets per Second')
    axes[1].plot(throughput_data, marker='o', color='orange')
    axes[1].set_ylabel('Throughput (Gbps)')
    axes[1].set_title('Throughput')
    axes[2].plot(average_batch_data, marker='o', color='green')
    axes[2].set_xlabel('Run')
    axes[2].set_ylabel('Average Batch Size')
    axes[2].set_title('Average Batch Size')
    plt.tight_layout()
    plt.savefig('pkt_gen_plots.pdf', format='pdf')


if __name__ == "__main__":
    main()
