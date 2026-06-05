import os
import pandas as pd


RESULTS_CSV = "data/logs/results.csv"
STATS_CSV = "analysis/output/statistics.csv"
OUTPUT_DIR = "analysis/output"


def main():
    os.makedirs(OUTPUT_DIR, exist_ok=True)

    if not os.path.exists(RESULTS_CSV):
        print(f"Arquivo não encontrado: {RESULTS_CSV}")
        print("Rode primeiro: ./scripts/run_all_tests.sh 10")
        return

    if not os.path.exists(STATS_CSV):
        print(f"Arquivo não encontrado: {STATS_CSV}")
        print("Rode primeiro: python3 -m analysis.analyze")
        return

    results = pd.read_csv(RESULTS_CSV)
    stats = pd.read_csv(STATS_CSV)

    tabela_estatistica = stats[
        [
            "protocol",
            "scenario",
            "throughput_min",
            "throughput_mean",
            "throughput_max",
            "throughput_std",
            "time_min",
            "time_mean",
            "time_max",
            "time_std",
        ]
    ].round(4)

    rudp = results[results["protocol"] == "RUDP"]

    tabela_rudp = rudp.groupby("scenario").agg(
        retransmissoes_media=("retransmissions", "mean"),
        retransmissoes_min=("retransmissions", "min"),
        retransmissoes_max=("retransmissions", "max"),
        pacotes_enviados_media=("packets_sent", "mean"),
        acks_recebidos_media=("acks_received", "mean"),
        total_pacotes_media=("total_packets", "mean"),
    ).reset_index().round(2)

    tabela_comparativa = stats[
        [
            "protocol",
            "scenario",
            "throughput_mean",
            "time_mean",
            "retransmissions_mean",
        ]
    ].round(4)

    output_file = os.path.join(OUTPUT_DIR, "tabelas_relatorio.md")

    with open(output_file, "w", encoding="utf-8") as file:
        file.write("# Tabelas para o relatório\n\n")

        file.write("## Tabela 1 — Estatísticas de throughput e tempo\n\n")
        file.write(tabela_estatistica.to_markdown(index=False))
        file.write("\n\n")

        file.write("## Tabela 2 — Retransmissões do R-UDP\n\n")
        file.write(tabela_rudp.to_markdown(index=False))
        file.write("\n\n")

        file.write("## Tabela 3 — Comparação resumida TCP vs R-UDP\n\n")
        file.write(tabela_comparativa.to_markdown(index=False))
        file.write("\n")

    print(f"Tabelas geradas em: {output_file}")


if __name__ == "__main__":
    main()
