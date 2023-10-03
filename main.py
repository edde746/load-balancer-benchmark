TESTS = [
    { "port": 9001, "name": "nginx" },
    { "port": 9002, "name": "haproxy" },
    { "port": 9004, "name": "traefik" },
    { "port": 9005, "name": "caddy" },
]

REQUESTS = 100_000

import subprocess,re
if subprocess.call(["hey", "-h"], stderr=subprocess.DEVNULL) != 2:
    raise Exception("hey is not installed")

def parse_output(output):
    parsed_data = {}
    
    summary_regex = re.compile(r"Summary:\s+Total:\s+(?P<total>\S+ secs)\s+Slowest:\s+(?P<slowest>\S+ secs)\s+"
                               r"Fastest:\s+(?P<fastest>\S+ secs)\s+Average:\s+(?P<average>\S+ secs)\s+"
                               r"Requests/sec:\s+(?P<req_per_sec>\S+)", re.DOTALL)
    
    data_regex = re.compile(r"Total data:\s+(?P<total_data>\S+ bytes)\s+Size/request:\s+(?P<size_per_request>\S+ bytes)", re.DOTALL)
    latency_regex = re.compile(r"Latency distribution:(.*?)(?=\n\n|\Z)", re.DOTALL)
    latency_percentiles_regex = re.compile(r"\s*(\d+)% in (\S+ secs)")
    details_regex = re.compile(r"Details \(average, fastest, slowest\):\s+(.*?)$", re.DOTALL)
    details_times_regex = re.compile(r"\s*(\S+):\s+(\S+ secs), (\S+ secs), (\S+ secs)")
    status_code_regex = re.compile(r"\[200\]\s+(\d+) responses")

    summary_match = summary_regex.search(output)
    data_match = data_regex.search(output)
    latency_match = latency_regex.search(output)
    details_match = details_regex.search(output)
    status_code_match = status_code_regex.search(output)

    if summary_match: parsed_data.update(summary_match.groupdict())  
    if data_match: parsed_data.update(data_match.groupdict())
    if status_code_match: parsed_data["status_code_distribution"] = {"200": int(status_code_match.group(1))}
    
    if latency_match:
        latencies = latency_percentiles_regex.findall(latency_match.group(1))
        parsed_data["latency_distribution"] = {f"{perc}%": time for perc, time in latencies}
    
    if details_match:
        details_times = details_times_regex.findall(details_match.group(1))
        parsed_data["details"] = {name: {"average": avg, "fastest": fastest, "slowest": slowest} 
                                  for name, avg, fastest, slowest in details_times}

    return parsed_data

tests = []
for test in TESTS:
    print(f"Testing {test['name']}")
    output = subprocess.check_output(["hey", "-n", str(REQUESTS), f"http://localhost:{test['port']}"])
    tests.append((test['name'], parse_output(output.decode("utf-8"))))

import plotly.express as px
import plotly.io as pio
import pandas as pd
from plotly.subplots import make_subplots

latency_data = []
for [name, output] in tests:
    for percentile, latency in output['latency_distribution'].items():
        latency_value = float(latency.split()[0])  # Extract numerical value from string
        latency_data.append({'Output': name, 'Percentile': percentile, 'Latency': latency_value})

time_data = []
for [name, output] in tests:
    for metric in ['average', 'fastest', 'slowest']:
        time_value = float(output[metric].split()[0])  # Extract numerical value from string
        time_data.append({'Output': name, 'Metric': metric.capitalize(), 'Time': time_value})

req_sec_data = []
for [name, output] in tests:
    req_sec_data.append({'Output': name, 'Requests/Sec': float(output['req_per_sec'])})

# Create DataFrames
latency_df = pd.DataFrame(latency_data)
time_df = pd.DataFrame(time_data)
req_sec_df = pd.DataFrame(req_sec_data)

# Create plots
fig_latency = px.bar(latency_df, x='Percentile', y='Latency', color='Output', barmode='group', title='Latency Distribution Comparison among Outputs')
fig_time = px.bar(time_df, x='Metric', y='Time', color='Output', barmode='group', title='Time Metrics (Average, Fastest, Slowest) Comparison among Outputs')
fig_req_sec = px.bar(req_sec_df, x='Output', y='Requests/Sec', title='Requests per Second Comparison among Outputs')

fig = make_subplots(rows=3, cols=1, subplot_titles=('Latency Distribution', 'Time Metrics Comparison', 'Requests per Second'), shared_xaxes=False, vertical_spacing=0.08)

for trace in fig_latency['data']: fig.add_trace(trace, row=1, col=1)
for trace in fig_time['data']: fig.add_trace(trace, row=2, col=1)
for trace in fig_req_sec['data']: fig.add_trace(trace, row=3, col=1)
    
fig.update_layout(height=1200, width=1000, title_text="Comparison Plots")

pio.write_html(fig, file='comparison.html', auto_open=True)