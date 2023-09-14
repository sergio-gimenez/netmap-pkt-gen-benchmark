import argparse
import subprocess
import re
import csv
from typing import Optional
import uuid
import matplotlib.pyplot as plt

import logger
log = logger.setup_logger(file_name='pkt_gen_benchmark.log')
log.setLevel(logger.logging.DEBUG)

ETH_MINIMUM_PKT_SIZE_WITHOUT_CRC = 60


def run_pkt_gen_rx(interface: str, num_packets: int):
    cmd = ['sudo', 'pkt-gen', '-i', interface,
           '-f', 'rx', '-n', str(num_packets)]
    result = subprocess.run(cmd, stdout=subprocess.PIPE,
                            stderr=subprocess.PIPE, text=True)
    return result.stdout


def run_pkt_gen_tx(interface: str, pkt_size: int = ETH_MINIMUM_PKT_SIZE_WITHOUT_CRC):
    cmd = ['sudo', 'pkt-gen', '-i', interface, '-f', '-l', str(
        pkt_size), '-f', 'tx']
    pkt_gen_tx_pid = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    return pkt_gen_tx_pid


def kill_pkt_gen_tx(pkt_gen_tx_pid):
    pkt_gen_tx_pid.kill()


def parse_output(output: str):
    metrics = {}
    speed_match = re.search(r'Speed: (\d+\.\d+) (\w+)pps', output)
    throughput_match = re.search(r'Bandwidth: (\d+\.\d+) (\w+)', output)
    metrics['packets_per_sec'] = speed_match.group(1)
    metrics['speed_units'] = speed_match.group(2)
    metrics['throughput'] = throughput_match.group(1)
    metrics['throughput_units'] = throughput_match.group(2)
    metrics['average_batch'] = re.search(r'Average batch: (\d+\.\d+) pkts', output).group(1)
    return metrics


def dump_metrics_into_csv(all_metrics: list, pkt_size: int = ETH_MINIMUM_PKT_SIZE_WITHOUT_CRC, parallel_id: Optional[int] = None):
    if parallel_id is None:
        csv_file = '{}_pkt_gen_metrics_{}.csv'.format(uuid.uuid4(), pkt_size)
    else:
        csv_file = '{}_pkt_gen_metrics_{}_{}.csv'.format(uuid.uuid4(), parallel_id, pkt_size)

    # Extract units from the first metric (assuming all metrics have the same units)
    speed_units = all_metrics[0]['speed_units']
    throughput_units = all_metrics[0]['throughput_units']

   # Write the metrics to the CSV file
    with open(csv_file, mode='w', newline='') as file:
        fieldnames = ['packets_per_sec', 'speed_units', 'throughput', 'throughput_units', 'average_batch']
        writer = csv.DictWriter(file, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(all_metrics)

    # Extract data for plotting
    packets_per_sec_data = [float(metrics['packets_per_sec']) for metrics in all_metrics]
    throughput_data = [float(metrics['throughput']) for metrics in all_metrics]
    average_batch_data = [float(metrics['average_batch']) for metrics in all_metrics]

    return packets_per_sec_data, speed_units, throughput_data, throughput_units, average_batch_data


def run_experiment(total_experiment_iterations: int,
                   tx_interface: str,
                   rx_interface: str,
                   processed_pkts_per_iteration: int,
                   pkt_size: int = ETH_MINIMUM_PKT_SIZE_WITHOUT_CRC,
                   parallel_id: Optional[int] = None):
    all_metrics = []
    pkt_gen_tx_pid = run_pkt_gen_tx(interface=tx_interface, pkt_size=pkt_size)
    for _ in range(total_experiment_iterations):
        log.info("Running iteration number {}".format(_))
        output = run_pkt_gen_rx(interface=rx_interface, num_packets=processed_pkts_per_iteration)
        log.debug(output)
        metrics = parse_output(output)
        log.info(metrics)
        all_metrics.append(metrics)
    kill_pkt_gen_tx(pkt_gen_tx_pid)
    metrics = dump_metrics_into_csv(all_metrics=all_metrics, pkt_size=pkt_size, parallel_id=parallel_id)
    return metrics


def draw_plots_in_pdf(packets_per_sec_data, speed_units, throughput_data, throughput_units, average_batch_data):
    # Create a figure with subplots
    fig, axes = plt.subplots(3, 1, figsize=(10, 15))
    axes[0].plot(packets_per_sec_data, marker='o')
    axes[0].set_ylabel('Packets per Second')
    axes[0].set_title('Packets per Second')
    axes[1].plot(throughput_data, marker='o', color='orange')
    axes[1].set_ylabel(f'Throughput ({throughput_units})')
    axes[1].set_title('Throughput')
    axes[2].plot(average_batch_data, marker='o', color='green')
    axes[2].set_xlabel('Run')
    axes[2].set_ylabel('Average Batch Size')
    axes[2].set_title('Average Batch Size')
    plt.tight_layout()
    plt.savefig('pkt_gen_plots.pdf', format='pdf')


def parse_arguments():
    parser = argparse.ArgumentParser(
        description="Your script's description here")

    parser.add_argument("-it", "--iterations", type=int, default=30, help="Total iterations of the experiment")
    parser.add_argument("-n", "--pkts-per-iteration", type=int, default=100,
                        help="Total amount of processed packets per iteration")
    parser.add_argument("-s", "--pkt-size", type=int, default=ETH_MINIMUM_PKT_SIZE_WITHOUT_CRC, help="Packet size")
    parser.add_argument("-txi", "--tx-interface", type=str, help="TX interface")
    parser.add_argument("-txr", "--rx-interface", type=str, help="RX interface")
    parser.add_argument("-d", "--draw-plots", action="store_true", default=False, help="Draw plots in a PDF file")
    parser.add_argument("-p", "--parallel-id", type=int, default=None, help="Parallel ID")

    return parser.parse_args()


def main():
    args = parse_arguments()
    metrics = run_experiment(total_experiment_iterations=args.iterations,
                             tx_interface=args.tx_interface,
                             rx_interface=args.rx_interface,
                             processed_pkts_per_iteration=args.pkts_per_iteration,
                             pkt_size=args.pkt_size,
                             parallel_id=args.parallel_id)

    if args.draw_plots:
        packets_per_sec_data, speed_units, throughput_data, throughput_units, average_batch_data = metrics
        draw_plots_in_pdf(packets_per_sec_data, speed_units, throughput_data, throughput_units, average_batch_data)


if __name__ == "__main__":
    main()
