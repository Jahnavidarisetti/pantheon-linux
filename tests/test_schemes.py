# test_schemes.py
#!/usr/bin/env python3

import os
import sys
import time
import csv
import signal
import random
import argparse
from datetime import datetime
from os import path

import context
from helpers import utils
from helpers.subprocess_wrappers import Popen, check_output, call


def generate_random_metrics():
    """Generates mock metrics for testing."""
    return (
        round(random.uniform(20, 100), 2),    # RTT (ms)
        round(random.uniform(0.5, 5.0), 2),   # Throughput (Mbps)
        round(random.uniform(0, 0.05), 4),    # Loss rate (%)
        round(random.uniform(10, 60), 2)      # Latency (ms)
    )


def initialize_csv_logger(scheme, port):
    """Creates a log file and CSV writer for metrics."""
    log_dir = 'logs'
    os.makedirs(log_dir, exist_ok=True)
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    filepath = path.join(log_dir, f'metrics_{scheme}_{port}_{timestamp}.csv')
    file = open(filepath, 'w', newline='')
    writer = csv.writer(file)
    writer.writerow(['time', 'rtt', 'throughput', 'loss_rate', 'latency'])
    return file, writer


def run_scheme_test(args):
    available_schemes = utils.parse_config()['schemes'].keys() if args.all else args.schemes.split()
    wrappers_dir = path.join(context.src_dir, 'wrappers')

    for scheme in available_schemes:
        print(f"Testing scheme: {scheme}", file=sys.stderr)
        scheme_script = path.join(wrappers_dir, f'{scheme}.py')

        role = check_output([scheme_script, 'run_first']).strip()
        counterpart = 'receiver' if role == 'sender' else 'sender'
        port = utils.get_open_port()

        p1 = Popen([scheme_script, role, port], preexec_fn=os.setsid)
        time.sleep(3)
        p2 = Popen([scheme_script, counterpart, '127.0.0.1', port], preexec_fn=os.setsid)

        log_file, csv_writer = initialize_csv_logger(scheme, port)

        try:
            start = time.time()
            while time.time() - start < 60:
                metrics = generate_random_metrics()
                csv_writer.writerow([datetime.now().strftime('%H:%M:%S')] + list(metrics))
                time.sleep(1)
        except Exception as e:
            sys.exit(f"Error during metrics logging: {e}")
        finally:
            log_file.close()

        signal.signal(signal.SIGALRM, utils.timeout_handler)
        signal.alarm(60)

        try:
            for proc in (p1, p2):
                proc.wait()
                if proc.returncode != 0:
                    sys.exit(f"Test failed for scheme: {scheme}")
        except utils.TimeoutError:
            pass
        except Exception as e:
            sys.exit(f"Unexpected error: {e}")
        else:
            signal.alarm(0)
            sys.exit("Test ended early")
        finally:
            utils.kill_proc_group(p1)
            utils.kill_proc_group(p2)


def main():
    parser = argparse.ArgumentParser()
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument('--all', action='store_true', help='Run tests for all configured schemes')
    group.add_argument('--schemes', help='Specify space-separated scheme names')
    args = parser.parse_args()

    try:
        run_scheme_test(args)
    except:
        cleanup()
        raise
    else:
        print("All scheme tests completed successfully.", file=sys.stderr)


def cleanup():
    cleanup_script = path.join(context.base_dir, 'tools', 'pkill.py')
    call([cleanup_script, '--kill-dir', context.base_dir])


if __name__ == '__main__':
    main()
