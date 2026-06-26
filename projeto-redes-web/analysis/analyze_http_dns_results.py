# analysis/analyze_http_dns_results.py

import csv
import argparse
from pathlib import Path
from statistics import mean, stdev


NUMERIC_COLUMNS = [
    "dns_time_ms",
    "http_time_ms",
    "total_time_ms",
    "throughput_mbps",
    "http_header_bytes",
    "http_body_bytes",
    "response_total_bytes",
    "retransmissions",
    "packets_sent",
    "acks_received",
]


def parse_bool(value: str) -> bool:
    return str(value).strip().lower() == "true"


def parse_float(value: str) -> float:
    try:
        return float(value)
    except ValueError:
        return 0.0


def load_csv(csv_path: str):
    rows = []

    with open(csv_path, "r", encoding="utf-8") as file:
        reader = csv.DictReader(file)

        for row in reader:
            rows.append(row)

    return rows


def group_rows(rows):
    groups = {}

    for row in rows:
        key = (
            row["protocol"],
            row["scenario"],
            row["file_name"],
        )

        if key not in groups:
            groups[key] = []

        groups[key].append(row)

    return groups


def calculate_stats(values):
    values = [float(v) for v in values]

    if not values:
        return {
            "mean": 0,
            "std": 0,
            "min": 0,
            "max": 0,
        }

    if len(values) == 1:
        std_value = 0
    else:
        std_value = stdev(values)

    return {
        "mean": mean(values),
        "std": std_value,
        "min": min(values),
        "max": max(values),
    }


def analyze_groups(groups):
    summary_rows = []

    for (protocol, scenario, file_name), rows in sorted(groups.items()):
        total_runs = len(rows)
        success_count = sum(1 for row in rows if parse_bool(row["success"]))
        error_count = total_runs - success_count

        error_rate_percent = (error_count / total_runs) * 100 if total_runs > 0 else 0

        base = {
            "protocol": protocol,
            "scenario": scenario,
            "file_name": file_name,
            "total_runs": total_runs,
            "success_count": success_count,
            "error_count": error_count,
            "error_rate_percent": error_rate_percent,
        }

        for column in NUMERIC_COLUMNS:
            values = [parse_float(row[column]) for row in rows]
            stats = calculate_stats(values)

            base[f"{column}_mean"] = stats["mean"]
            base[f"{column}_std"] = stats["std"]
            base[f"{column}_min"] = stats["min"]
            base[f"{column}_max"] = stats["max"]

        summary_rows.append(base)

    return summary_rows


def save_summary(summary_rows, output_path: str):
    if not summary_rows:
        print("[ANALYSIS] Nenhum dado encontrado para salvar.")
        return

    Path(output_path).parent.mkdir(parents=True, exist_ok=True)

    fieldnames = list(summary_rows[0].keys())

    with open(output_path, "w", newline="", encoding="utf-8") as file:
        writer = csv.DictWriter(file, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(summary_rows)

    print(f"[ANALYSIS] Resumo salvo em: {output_path}")


def print_summary(summary_rows):
    print()
    print("[ANALYSIS] Resumo estatístico")
    print("=" * 100)

    for row in summary_rows:
        print()
        print(
            f"Protocolo={row['protocol']} | "
            f"Cenário={row['scenario']} | "
            f"Arquivo={row['file_name']}"
        )
        print("-" * 100)
        print(f"Execuções: {row['total_runs']}")
        print(f"Sucessos: {row['success_count']}")
        print(f"Erros: {row['error_count']}")
        print(f"Taxa de erro: {row['error_rate_percent']:.2f}%")

        print(
            f"Throughput Mbps: "
            f"média={row['throughput_mbps_mean']:.6f}, "
            f"desvio={row['throughput_mbps_std']:.6f}, "
            f"mín={row['throughput_mbps_min']:.6f}, "
            f"máx={row['throughput_mbps_max']:.6f}"
        )

        print(
            f"Tempo total ms: "
            f"média={row['total_time_ms_mean']:.3f}, "
            f"desvio={row['total_time_ms_std']:.3f}, "
            f"mín={row['total_time_ms_min']:.3f}, "
            f"máx={row['total_time_ms_max']:.3f}"
        )

        print(
            f"Tempo DNS ms: "
            f"média={row['dns_time_ms_mean']:.3f}, "
            f"desvio={row['dns_time_ms_std']:.3f}, "
            f"mín={row['dns_time_ms_min']:.3f}, "
            f"máx={row['dns_time_ms_max']:.3f}"
        )

        print(
            f"Retransmissões: "
            f"média={row['retransmissions_mean']:.3f}, "
            f"desvio={row['retransmissions_std']:.3f}, "
            f"mín={row['retransmissions_min']:.3f}, "
            f"máx={row['retransmissions_max']:.3f}"
        )


def main():
    parser = argparse.ArgumentParser(
        description="Gera estatísticas do experimento HTTP + DNS TCP/R-UDP."
    )

    parser.add_argument(
        "--input",
        default="data/results/http_dns_results.csv",
        help="Caminho do CSV de entrada.",
    )

    parser.add_argument(
        "--output",
        default="data/results/http_dns_summary.csv",
        help="Caminho do CSV de saída com o resumo estatístico.",
    )

    args = parser.parse_args()

    if not Path(args.input).exists():
        raise FileNotFoundError(f"CSV de entrada não encontrado: {args.input}")

    rows = load_csv(args.input)

    if not rows:
        print("[ANALYSIS] CSV vazio.")
        return

    groups = group_rows(rows)
    summary_rows = analyze_groups(groups)

    save_summary(summary_rows, args.output)
    print_summary(summary_rows)


if __name__ == "__main__":
    main()

#python3 analysis/analyze_http_dns_results.py
#data/results/http_dns_summary.csv
#ls -lh data/results
#cat data/results/http_dns_summary.csv