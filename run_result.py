import os
import glob
import shutil
import subprocess
from pathlib import Path

import pandas as pd
import matplotlib.pyplot as plt

SCHEMES = ["vivace", "bbr", "cubic"]

NETWORK_PROFILES = {
    "A": {
        "delay": 5,
        "downlink": "mahimahi/traces/TMobile-LTE-driving.down",
        "uplink": "mahimahi/traces/TMobile-LTE-driving.up"
    },
    "B": {
        "delay": 200,
        "downlink": "mahimahi/traces/TMobile-LTE-short.down",
        "uplink": "mahimahi/traces/TMobile-LTE-short.up"
    }
}

def execute_experiments():
    for profile_name, settings in NETWORK_PROFILES.items():
        print(f"\n>>> Running Profile {profile_name} experiments")
        for scheme in SCHEMES:
            results_path = f"results/profile_{profile_name}/{scheme}"
            os.makedirs(results_path, exist_ok=True)

            cmd = (
                f"mm-delay {settings['delay']} "
                f"mm-link {settings['downlink']} {settings['uplink']} -- "
                f"bash -c 'python3 tests/test_schemes.py --schemes \"{scheme}\" > {results_path}/log.txt 2>&1'"
            )

            try:
                subprocess.run(cmd, shell=True, check=True)
                print(f"[✓] {scheme} completed on Profile {profile_name}")
            except subprocess.CalledProcessError:
                print(f"[✗] {scheme} failed on Profile {profile_name}")

            # Copy latest log to results folder
            logs = sorted(glob.glob(f"logs/metrics_{scheme}_*.csv"), key=os.path.getmtime, reverse=True)
            if logs:
                shutil.copy(logs[0], os.path.join(results_path, f"{scheme}_cc_log.csv"))
            else:
                print(f"[!] No metrics log found for {scheme} in Profile {profile_name}")

def read_all_logs():
    logs = []
    for profile in NETWORK_PROFILES:
        for scheme in SCHEMES:
            csv_file = f"results/profile_{profile}/{scheme}/{scheme}_cc_log.csv"
            if os.path.exists(csv_file):
                df = pd.read_csv(csv_file)
                df['scheme'] = scheme
                df['profile'] = profile
                df['timestamp'] = range(len(df))
                logs.append(df)
            else:
                print(f"[!] Missing: {csv_file}")
    return pd.concat(logs, ignore_index=True) if logs else pd.DataFrame()

def save_throughput_graph(df):
    for profile in df['profile'].unique():
        plt.figure()
        for scheme in df['scheme'].unique():
            sub = df[(df['scheme'] == scheme) & (df['profile'] == profile)]
            plt.plot(sub['timestamp'], sub['throughput'], label=scheme)
        plt.title(f'Throughput Over Time - Profile {profile}')
        plt.xlabel('Time (s)')
        plt.ylabel('Throughput (Mbps)')
        plt.legend()
        plt.grid()
        plt.savefig(f'graphs/throughput_profile_{profile}.png')
        plt.close()

def save_loss_graph(df):
    for profile in df['profile'].unique():
        plt.figure()
        for scheme in df['scheme'].unique():
            sub = df[(df['scheme'] == scheme) & (df['profile'] == profile)]
            plt.plot(sub['timestamp'], sub['loss_rate'], label=scheme)
        plt.title(f'Loss Rate Over Time - Profile {profile}')
        plt.xlabel('Time (s)')
        plt.ylabel('Loss Rate')
        plt.legend()
        plt.grid()
        plt.savefig(f'graphs/loss_profile_{profile}.png')
        plt.close()

def export_rtt_summary(df):
    summary = []
    for profile in df['profile'].unique():
        for scheme in df['scheme'].unique():
            subset = df[(df['scheme'] == scheme) & (df['profile'] == profile)]
            if not subset.empty:
                summary.append([
                    scheme, profile,
                    subset['rtt'].mean(),
                    subset['rtt'].quantile(0.95)
                ])
    pd.DataFrame(summary, columns=['Scheme', 'Profile', 'Avg RTT', '95th RTT']) \
        .to_csv('graphs/rtt_summary.csv', index=False)

def plot_rtt_vs_throughput(df):
    plt.figure()
    for profile in df['profile'].unique():
        for scheme in df['scheme'].unique():
            sub = df[(df['scheme'] == scheme) & (df['profile'] == profile)]
            if not sub.empty:
                plt.scatter(sub['rtt'].mean(), sub['throughput'].mean(), label=f'{scheme}-{profile}')
                plt.annotate(f'{scheme}-{profile}', (sub['rtt'].mean(), sub['throughput'].mean()))
    plt.title('Average Throughput vs Average RTT')
    plt.xlabel('RTT (ms)')
    plt.ylabel('Throughput (Mbps)')
    plt.grid()
    plt.legend()
    plt.savefig('graphs/rtt_vs_throughput.png')
    plt.close()

def barplot_avg_and_95th_rtt(df):
    if 'rtt' not in df.columns:
        print("[!] 'rtt' column missing in DataFrame.")
        return

    summary = []

    for profile in df['profile'].unique():
        for scheme in df['scheme'].unique():
            subset = df[(df['scheme'] == scheme) & (df['profile'] == profile)]
            if not subset.empty:
                avg_rtt = subset['rtt'].mean()
                p95_rtt = subset['rtt'].quantile(0.95)
                summary.append({
                    'Scheme-Profile': f'{scheme}-{profile}',
                    'Avg RTT': avg_rtt,
                    '95th RTT': p95_rtt
                })

    summary_df = pd.DataFrame(summary)

    # Plotting
    labels = summary_df['Scheme-Profile']
    x = range(len(labels))
    width = 0.35

    plt.figure(figsize=(12, 6))
    plt.bar(x, summary_df['Avg RTT'], width=width, label='Average RTT', color='skyblue')
    plt.bar([i + width for i in x], summary_df['95th RTT'], width=width, label='95th Percentile RTT', color='salmon')

    plt.xlabel('Scheme-Profile')
    plt.ylabel('RTT (ms)')
    plt.title('Average vs 95th Percentile RTT per Scheme/Profile')
    plt.xticks([i + width / 2 for i in x], labels, rotation=45, ha='right')
    plt.legend()
    plt.tight_layout()
    plt.grid(axis='y')
    plt.savefig('graphs/barplot_avg_and_95th_rtt.png')
    plt.close()



def main():
    os.makedirs('graphs', exist_ok=True)
    os.makedirs('results', exist_ok=True)

    execute_experiments()
    data = read_all_logs()

    if data.empty:
        print("No logs found. Exiting.")
        return

    save_throughput_graph(data)
    save_loss_graph(data)
    export_rtt_summary(data)
    plot_rtt_vs_throughput(data)
    barplot_avg_and_95th_rtt(data)


    print("All plots and summaries saved.")

if __name__ == '__main__':
    main()
