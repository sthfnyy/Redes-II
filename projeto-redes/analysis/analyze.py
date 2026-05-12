# analysis/analyze.py

import pandas as pd
import matplotlib.pyplot as plt
import os

INPUT_CSV = "data/logs/results.csv"
OUTPUT_DIR = "data/logs/graphs"

os.makedirs(OUTPUT_DIR, exist_ok=True)

df = pd.read_csv(INPUT_CSV)

summary = df.groupby(["protocol", "scenario"])["throughput_mbps"].agg([
    "min",
    "mean",
    "max",
    "std"
]).reset_index()

print(summary)

summary.to_csv("data/logs/summary.csv", index=False)

for scenario in ["A", "B", "C"]:
    subset = df[df["scenario"] == scenario]

    plt.figure()
    subset.boxplot(column="throughput_mbps", by="protocol")
    plt.title(f"Throughput TCP vs R-UDP - Cenário {scenario}")
    plt.suptitle("")
    plt.xlabel("Protocolo")
    plt.ylabel("Throughput Mbps")
    plt.savefig(f"{OUTPUT_DIR}/throughput_boxplot_{scenario}.png")
    plt.close()

avg = df.groupby(["scenario", "protocol"])["throughput_mbps"].mean().unstack()

plt.figure()
avg.plot(kind="bar")
plt.title("Throughput médio por cenário")
plt.xlabel("Cenário")
plt.ylabel("Throughput médio Mbps")
plt.savefig(f"{OUTPUT_DIR}/throughput_medio_por_cenario.png")
plt.close()