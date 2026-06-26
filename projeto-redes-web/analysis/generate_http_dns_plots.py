# analysis/generate_http_dns_plots.py

import csv
from pathlib import Path
from collections import defaultdict

import matplotlib.pyplot as plt


INPUT_CSV = "data/results/http_dns_summary.csv"
OUTPUT_DIR = Path("data/results/plots")


def load_summary(path):
    rows = []

    with open(path, "r", encoding="utf-8") as file:
        reader = csv.DictReader(file)

        for row in reader:
            rows.append(row)

    return rows


def to_float(value):
    try:
        return float(value)
    except ValueError:
        return 0.0


def safe_filename(value):
    return (
        value.replace("/", "")
        .replace(".", "_")
        .replace(" ", "_")
        .replace("-", "_")
    )


def plot_throughput_by_file(rows):
    files = sorted(set(row["file_name"] for row in rows))

    for file_name in files:
        selected = [row for row in rows if row["file_name"] == file_name]

        labels = []
        values = []

        for row in selected:
            label = f"{row['protocol']}-{row['scenario']}"
            value = to_float(row["throughput_mbps_mean"])

            labels.append(label)
            values.append(value)

        plt.figure(figsize=(10, 5))
        plt.bar(labels, values)
        plt.title(f"Throughput médio - {file_name}")
        plt.xlabel("Protocolo e cenário")
        plt.ylabel("Throughput médio (Mbps)")
        plt.xticks(rotation=45)
        plt.tight_layout()

        output_path = OUTPUT_DIR / f"throughput_{safe_filename(file_name)}.png"
        plt.savefig(output_path)
        plt.close()

        print(f"[PLOTS] Gráfico salvo em: {output_path}")


def plot_total_time_by_file(rows):
    files = sorted(set(row["file_name"] for row in rows))

    for file_name in files:
        selected = [row for row in rows if row["file_name"] == file_name]

        labels = []
        values = []

        for row in selected:
            label = f"{row['protocol']}-{row['scenario']}"
            value_ms = to_float(row["total_time_ms_mean"])
            value_seconds = value_ms / 1000

            labels.append(label)
            values.append(value_seconds)

        plt.figure(figsize=(10, 5))
        plt.bar(labels, values)
        plt.title(f"Tempo total médio - {file_name}")
        plt.xlabel("Protocolo e cenário")
        plt.ylabel("Tempo total médio (s)")
        plt.xticks(rotation=45)
        plt.tight_layout()

        output_path = OUTPUT_DIR / f"tempo_total_{safe_filename(file_name)}.png"
        plt.savefig(output_path)
        plt.close()

        print(f"[PLOTS] Gráfico salvo em: {output_path}")


def plot_error_rate(rows):
    labels = []
    values = []

    for row in rows:
        label = f"{row['protocol']}-{row['scenario']}-{row['file_name'].replace('/arquivo_', '').replace('.bin', '')}"
        value = to_float(row["error_rate_percent"])

        labels.append(label)
        values.append(value)

    plt.figure(figsize=(14, 5))
    plt.bar(labels, values)
    plt.title("Taxa de erro por protocolo, cenário e arquivo")
    plt.xlabel("Grupo de teste")
    plt.ylabel("Taxa de erro (%)")
    plt.xticks(rotation=90)
    plt.tight_layout()

    output_path = OUTPUT_DIR / "taxa_erro.png"
    plt.savefig(output_path)
    plt.close()

    print(f"[PLOTS] Gráfico salvo em: {output_path}")


def main():
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    rows = load_summary(INPUT_CSV)

    if not rows:
        print("[PLOTS] Nenhum dado encontrado.")
        return

    plot_throughput_by_file(rows)
    plot_total_time_by_file(rows)
    plot_error_rate(rows)

    print("[PLOTS] Geração de gráficos finalizada.")


if __name__ == "__main__":
    main()
