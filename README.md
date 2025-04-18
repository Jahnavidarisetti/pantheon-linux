Pantheon Congestion Control Evaluation

This repository contains scripts and configurations for evaluating different congestion control algorithms using the Pantheon framework with MahiMahi network emulation.

Overview

The project evaluates the performance of three congestion control algorithms (TCP Cubic, BBR, and Vivace) under different network conditions using the Pantheon testing framework. The scripts automate the process of running experiments, collecting data, and generating visualizations for analysis.

Prerequisites

Ubuntu 20.04 or later (tested on Ubuntu 22.04)
Python 3.8 or later
Git


Installation

1. Clone this repository

git clone https://github.com/Jahnavidarisetti/pantheon-linux.git
cd pantheon

2. Install dependencies

Install all the dependencies for Pantheon and Mahimahi

3. Running Experiments:

python3 run_tests.py

4. Output Files

After running the experiments, the following output will be generated:

1. logs: /pantheon/logs/

2. graphs: /pantheon/graphs/

3. CSV Results:
	a. Profile A: /pantheon/results/profileA/
	b. Profile B: /pantheon/results/profileB/

