import matplotlib
import matplotlib.pyplot as plt
import pandas as pd


def generate_images():
    matplotlib.use('agg', force=True)

    metrics_df = pd.read_csv(
        "metrics.csv",
        sep="\t",
        header=0,
        index_col=False,
        dtype={
          "epoch_time": int,
          "request_db_hash": str,
          "ad_db_hash": str,
          "markup_hash": str,
          "accuracy": float,
          "precision": float,
          "recall": float,
          "f1": float,
          "tp": int,
          "fp": int,
          "tn": int,
          "fn": int,
        },
    )
    metrics_df["ts"] = pd.to_datetime(metrics_df["epoch_time"], unit="s")

    plt.plot(metrics_df["ts"], metrics_df["f1"], label="F1", marker="o")
    plt.plot(metrics_df["ts"], metrics_df["accuracy"], label="Accuracy", marker="o")

    plt.title("History of Metrics in Search Pipeline")
    plt.legend(loc="lower right")
    plt.xticks(rotation=45)
    plt.tight_layout()
    plt.savefig("metrics_history.png")

    print(f"Images were generated")


if __name__ == "__main__":
    generate_images()
