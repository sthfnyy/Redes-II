# analysis/analyze.py

import os
import pandas as pd
import matplotlib.pyplot as plt


INPUT_CSV = "data/logs/results.csv"
OUTPUT_DIR = "analysis/output"

BLUE = "royalblue"
ORANGE = "darkorange"


def load_data():
    """
    Lê o CSV de resultados e prepara os dados para análise.
    """

    df = pd.read_csv(INPUT_CSV)

    numeric_columns = [
        "run",
        "file_size_bytes",
        "time_seconds",
        "throughput_mbps",
        "retransmissions",
        "packets_sent",
        "acks_received",
        "total_packets",
    ]

    for column in numeric_columns:
        df[column] = pd.to_numeric(df[column], errors="coerce")

    df = df.dropna()

    # Mantém apenas execuções de 1 a 10
    df = df[(df["run"] >= 1) & (df["run"] <= 10)]

    # Remove duplicatas antigas, mantendo a última ocorrência de cada combinação
    df = df.drop_duplicates(
        subset=["protocol", "scenario", "run"],
        keep="last"
    )

    # Garante ordem A, B e C
    df["scenario"] = pd.Categorical(
        df["scenario"],
        categories=["A", "B", "C"],
        ordered=True
    )

    df = df.sort_values(["protocol", "scenario", "run"])

    return df


def generate_statistics(df):
    """
    Gera estatísticas por protocolo e cenário.
    """

    stats = df.groupby(["protocol", "scenario"], observed=False).agg(
        throughput_min=("throughput_mbps", "min"),
        throughput_mean=("throughput_mbps", "mean"),
        throughput_max=("throughput_mbps", "max"),
        throughput_std=("throughput_mbps", "std"),
        time_min=("time_seconds", "min"),
        time_mean=("time_seconds", "mean"),
        time_max=("time_seconds", "max"),
        time_std=("time_seconds", "std"),
        retransmissions_mean=("retransmissions", "mean"),
        retransmissions_min=("retransmissions", "min"),
        retransmissions_max=("retransmissions", "max"),
    ).reset_index()

    return stats


def save_statistics(stats):
    """
    Salva a tabela estatística em CSV.
    """

    os.makedirs(OUTPUT_DIR, exist_ok=True)

    output_file = os.path.join(OUTPUT_DIR, "statistics.csv")
    stats.to_csv(output_file, index=False)

    print("Tabela estatística salva em:", output_file)
    print()
    print(stats)


def scenario_title(scenario):
    """
    Retorna o título correto de cada cenário.
    """

    titles = {
        "A": "Cenário A\n(0% perda / 10 ms)",
        "B": "Cenário B\n(5% perda / 50 ms)",
        "C": "Cenário C\n(10% perda / 100 ms)",
    }

    return titles[str(scenario)]


def plot_throughput_line_log(stats):
    """
    Gráfico de linha do throughput médio por cenário.
    """

    pivot = stats.pivot(
        index="scenario",
        columns="protocol",
        values="throughput_mean"
    )

    plt.figure(figsize=(8, 5))

    plt.plot(
        pivot.index.astype(str),
        pivot["RUDP"],
        marker="o",
        linewidth=2,
        color=BLUE,
        label="R-UDP",
        zorder=3
    )

    plt.plot(
        pivot.index.astype(str),
        pivot["TCP"],
        marker="o",
        linewidth=2,
        color=ORANGE,
        label="TCP",
        zorder=3
    )

    plt.title("Throughput médio por cenário")
    plt.xlabel("Cenário")
    plt.ylabel("Throughput médio (Mbps)")
    plt.yscale("log")

    plt.grid(
        True,
        which="both",
        axis="y",
        linestyle="--",
        alpha=0.6,
        zorder=0
    )

    plt.legend(loc="upper right")
    plt.tight_layout()

    output_file = os.path.join(OUTPUT_DIR, "throughput_linha_log.png")
    plt.savefig(output_file, dpi=300)
    plt.close()

    print("Gráfico salvo em:", output_file)


def plot_time_line_log(stats):
    """
    Gráfico de linha do tempo médio por cenário.
    """

    pivot = stats.pivot(
        index="scenario",
        columns="protocol",
        values="time_mean"
    )

    plt.figure(figsize=(8, 5))

    plt.plot(
        pivot.index.astype(str),
        pivot["RUDP"],
        marker="o",
        linewidth=2,
        color=BLUE,
        label="R-UDP",
        zorder=3
    )

    plt.plot(
        pivot.index.astype(str),
        pivot["TCP"],
        marker="o",
        linewidth=2,
        color=ORANGE,
        label="TCP",
        zorder=3
    )

    plt.title("Tempo médio de transferência por cenário")
    plt.xlabel("Cenário")
    plt.ylabel("Tempo médio (s)")
    plt.yscale("log")

    plt.grid(
        True,
        which="both",
        axis="y",
        linestyle="--",
        alpha=0.6,
        zorder=0
    )

    plt.legend(loc="upper left")
    plt.tight_layout()

    output_file = os.path.join(OUTPUT_DIR, "tempo_linha_log.png")
    plt.savefig(output_file, dpi=300)
    plt.close()

    print("Gráfico salvo em:", output_file)


def plot_retransmissions_rudp(df):
    """
    Gráfico de barras das retransmissões médias do R-UDP.
    """

    rudp_df = df[df["protocol"] == "RUDP"]

    retrans_stats = rudp_df.groupby(
        "scenario",
        observed=False
    )["retransmissions"].mean()

    plt.figure(figsize=(8, 5))

    plt.bar(
        retrans_stats.index.astype(str),
        retrans_stats.values,
        color=BLUE,
        zorder=3
    )

    for index, value in enumerate(retrans_stats.values):
        plt.text(
            index,
            value,
            f"{value:.1f}",
            ha="center",
            va="bottom",
            fontsize=9
        )

    plt.title("Retransmissões médias do R-UDP por cenário")
    plt.xlabel("Cenário")
    plt.ylabel("Retransmissões médias")

    plt.grid(
        True,
        axis="y",
        linestyle="--",
        alpha=0.6,
        zorder=0
    )

    plt.tight_layout()

    output_file = os.path.join(OUTPUT_DIR, "retransmissoes_rudp.png")
    plt.savefig(output_file, dpi=300)
    plt.close()

    print("Gráfico salvo em:", output_file)


def plot_throughput_std_line_log(stats):
    """
    Gráfico de throughput médio com desvio padrão por cenário.
    """

    pivot_mean = stats.pivot(
        index="scenario",
        columns="protocol",
        values="throughput_mean"
    )

    pivot_std = stats.pivot(
        index="scenario",
        columns="protocol",
        values="throughput_std"
    )

    cenarios = pivot_mean.index.astype(str)

    plt.figure(figsize=(8, 5))

    plt.errorbar(
        cenarios,
        pivot_mean["RUDP"],
        yerr=pivot_std["RUDP"],
        marker="o",
        linewidth=2,
        capsize=5,
        color=BLUE,
        label="R-UDP",
        zorder=3
    )

    plt.errorbar(
        cenarios,
        pivot_mean["TCP"],
        yerr=pivot_std["TCP"],
        marker="o",
        linewidth=2,
        capsize=5,
        color=ORANGE,
        label="TCP",
        zorder=3
    )

    plt.title("Throughput médio com desvio padrão por cenário")
    plt.xlabel("Cenário")
    plt.ylabel("Throughput médio (Mbps)")
    plt.yscale("log")

    plt.grid(
        True,
        which="both",
        axis="y",
        linestyle="--",
        alpha=0.6,
        zorder=0
    )

    plt.legend(loc="upper right")
    plt.tight_layout()

    output_file = os.path.join(OUTPUT_DIR, "throughput_desvio_padrao.png")
    plt.savefig(output_file, dpi=300)
    plt.close()

    print("Gráfico salvo em:", output_file)


def plot_throughput_panels(df):
    """
    Gráfico de throughput em três painéis.
    Cada painel representa um cenário.
    """

    fig, axes = plt.subplots(1, 3, figsize=(15, 4), sharey=False)

    for ax, scenario in zip(axes, ["A", "B", "C"]):
        data = df[df["scenario"] == scenario]

        summary = data.groupby("protocol").agg(
            mean=("throughput_mbps", "mean"),
            std=("throughput_mbps", "std")
        )

        protocols = ["TCP", "RUDP"]
        means = [summary.loc[p, "mean"] for p in protocols]
        stds = [summary.loc[p, "std"] for p in protocols]

        ax.bar(
            protocols,
            means,
            yerr=stds,
            capsize=6,
            color=[ORANGE, BLUE],
            zorder=3
        )

        ax.set_title(scenario_title(scenario))
        ax.set_xlabel("Protocolo")
        ax.set_ylabel("Throughput médio (Mbps)")
        ax.grid(axis="y", linestyle="--", alpha=0.6, zorder=0)

    fig.suptitle("Throughput — TCP vs R-UDP por cenário", fontsize=14)
    plt.tight_layout()

    output_file = os.path.join(OUTPUT_DIR, "throughput_paineis.png")
    plt.savefig(output_file, dpi=300)
    plt.close()

    print("Gráfico salvo em:", output_file)


def plot_time_panels(df):
    """
    Gráfico de tempo em três painéis.
    Cada painel representa um cenário.
    """

    fig, axes = plt.subplots(1, 3, figsize=(15, 4), sharey=False)

    for ax, scenario in zip(axes, ["A", "B", "C"]):
        data = df[df["scenario"] == scenario]

        summary = data.groupby("protocol").agg(
            mean=("time_seconds", "mean"),
            std=("time_seconds", "std")
        )

        protocols = ["TCP", "RUDP"]
        means = [summary.loc[p, "mean"] for p in protocols]
        stds = [summary.loc[p, "std"] for p in protocols]

        ax.bar(
            protocols,
            means,
            yerr=stds,
            capsize=6,
            color=[ORANGE, BLUE],
            zorder=3
        )

        ax.set_title(scenario_title(scenario))
        ax.set_xlabel("Protocolo")
        ax.set_ylabel("Tempo médio (s)")
        ax.grid(axis="y", linestyle="--", alpha=0.6, zorder=0)

    fig.suptitle("Tempo de transferência — TCP vs R-UDP por cenário", fontsize=14)
    plt.tight_layout()

    output_file = os.path.join(OUTPUT_DIR, "tempo_paineis.png")
    plt.savefig(output_file, dpi=300)
    plt.close()

    print("Gráfico salvo em:", output_file)


def plot_rudp_retransmissions_panels(df):
    """
    Gráfico de retransmissões do R-UDP em três painéis.
    """

    fig, axes = plt.subplots(1, 3, figsize=(15, 4), sharey=False)

    for ax, scenario in zip(axes, ["A", "B", "C"]):
        data = df[
            (df["scenario"] == scenario) &
            (df["protocol"] == "RUDP")
        ]

        mean_value = data["retransmissions"].mean()
        std_value = data["retransmissions"].std()

        ax.bar(
            ["R-UDP"],
            [mean_value],
            yerr=[std_value],
            capsize=6,
            color=BLUE,
            zorder=3
        )

        ax.text(
            0,
            mean_value,
            f"{mean_value:.1f}",
            ha="center",
            va="bottom",
            fontsize=9
        )

        ax.set_title(scenario_title(scenario))
        ax.set_xlabel("Protocolo")
        ax.set_ylabel("Retransmissões médias")
        ax.grid(axis="y", linestyle="--", alpha=0.6, zorder=0)

    fig.suptitle("Retransmissões médias do R-UDP por cenário", fontsize=14)
    plt.tight_layout()

    output_file = os.path.join(OUTPUT_DIR, "retransmissoes_rudp_paineis.png")
    plt.savefig(output_file, dpi=300)
    plt.close()

    print("Gráfico salvo em:", output_file)

def plot_throughput_bars(stats):
    """
    Gráfico de colunas do throughput médio por cenário.
    """

    pivot = stats.pivot(
        index="scenario",
        columns="protocol",
        values="throughput_mean"
    )

    scenarios = pivot.index.astype(str)
    x = range(len(scenarios))
    width = 0.35

    plt.figure(figsize=(8, 5))

    plt.bar(
        [i - width / 2 for i in x],
        pivot["TCP"],
        width=width,
        label="TCP",
        color=ORANGE,
        zorder=3
    )

    plt.bar(
        [i + width / 2 for i in x],
        pivot["RUDP"],
        width=width,
        label="R-UDP",
        color=BLUE,
        zorder=3
    )

    plt.title("Throughput médio por cenário")
    plt.xlabel("Cenário")
    plt.ylabel("Throughput médio (Mbps)")
    plt.xticks(list(x), scenarios)

    plt.grid(
        True,
        axis="y",
        linestyle="--",
        alpha=0.6,
        zorder=0
    )

    plt.legend()
    plt.tight_layout()

    output_file = os.path.join(OUTPUT_DIR, "throughput_colunas.png")
    plt.savefig(output_file, dpi=300)
    plt.close()

    print("Gráfico salvo em:", output_file)


def plot_time_bars(stats):
    """
    Gráfico de colunas do tempo médio por cenário.
    """

    pivot = stats.pivot(
        index="scenario",
        columns="protocol",
        values="time_mean"
    )

    scenarios = pivot.index.astype(str)
    x = range(len(scenarios))
    width = 0.35

    plt.figure(figsize=(8, 5))

    plt.bar(
        [i - width / 2 for i in x],
        pivot["TCP"],
        width=width,
        label="TCP",
        color=ORANGE,
        zorder=3
    )

    plt.bar(
        [i + width / 2 for i in x],
        pivot["RUDP"],
        width=width,
        label="R-UDP",
        color=BLUE,
        zorder=3
    )

    plt.title("Tempo médio de transferência por cenário")
    plt.xlabel("Cenário")
    plt.ylabel("Tempo médio (s)")
    plt.xticks(list(x), scenarios)

    plt.grid(
        True,
        axis="y",
        linestyle="--",
        alpha=0.6,
        zorder=0
    )

    plt.legend()
    plt.tight_layout()

    output_file = os.path.join(OUTPUT_DIR, "tempo_colunas.png")
    plt.savefig(output_file, dpi=300)
    plt.close()

    print("Gráfico salvo em:", output_file)


def main():
    os.makedirs(OUTPUT_DIR, exist_ok=True)

    df = load_data()

    print("Dados carregados:")
    print(df)
    print()

    print("Quantidade de execuções por protocolo e cenário:")
    print(df.groupby(["protocol", "scenario"], observed=False).size())
    print()

    stats = generate_statistics(df)
    save_statistics(stats)

    # Gráficos no modelo de linha
    #plot_throughput_line_log(stats)
    #plot_time_line_log(stats)
    plot_retransmissions_rudp(df)
    #plot_throughput_std_line_log(stats)

    # Gráficos no modelo em painéis, parecido com os exemplos dos colegas
    plot_throughput_panels(df)
    plot_time_panels(df)
    plot_rudp_retransmissions_panels(df)

    # Gráficos de colunas
    plot_throughput_bars(stats)
    plot_time_bars(stats)
    plot_retransmissions_rudp(df)

    # Gráficos em painéis
    plot_throughput_panels(df)
    plot_time_panels(df)
    plot_rudp_retransmissions_panels(df)

    print()
    print("Análise finalizada.")


if __name__ == "__main__":
    main()