import re
from datetime import datetime
from pathlib import Path

import matplotlib.pyplot as plt
from dataclasses import dataclass

@dataclass
class Brennerdaten:
    dates: list[int]
    min_date: str
    max_date: str
    minutes : list[int]
    

# Datei mit den Daten
DATEI = "summary.txt"

def get_min(min_date, current_date):
    
    if min_date is None:
        return current_date
    elif current_date < min_date:
        return current_date
    else:
        return min_date
    
def get_max(max_date, current_date):
    
    if max_date is None:
        return current_date
    elif current_date > max_date:
        return current_date
    else:
        return max_date

def parse_summary(DATEI):
    
    daten = []
    minutenwerte = []
    min_date = None
    max_date = None

    # Datei einlesen
    with open(DATEI, "r", encoding="utf-8") as f:
        for zeile in f:
        # Beispiel:
        # 31.05.2025: 0002 -> 00:00:02
            match = re.search(r"(\d{2}\.\d{2}\.\d{4}):\s*(\d+)", zeile)

            if match:
                datum_str = match.group(1)
                sekunden = int(match.group(2))

            # Datum umwandeln
                datum = datetime.strptime(datum_str, "%d.%m.%Y")
                
                max_date = get_max(max_date, datum)
                min_date = get_min(min_date, datum)

            # Sekunden -> Minuten
                minuten = sekunden / 60

                daten.append(datum)
                minutenwerte.append(minuten)
                
    return Brennerdaten(daten, 
                        min_date, 
                        max_date, 
                        minutenwerte)
    
@dataclass
class Wetterdaten:
    dates: list
    temperatures: list[float]

def parse_wetterdaten(file_path: str, min_date, max_date):
    
    import pandas as pd
    ID_COL_DATE = "JJJJMMDD"
    ID_COL_TEMPERATURE = "TM"

    # Read the CSV file
    df = pd.read_csv(file_path, sep=r"\s+", skiprows=3)
    df[ID_COL_DATE] = pd.to_datetime(df[ID_COL_DATE], format="%Y%m%d")
    
    # if any()
    # min_dt = datetime.strptime(min_date, "%d.%m.%Y")
    # max_dt = datetime.strptime(max_date, "%d.%m.%Y")

    df = df[df[ID_COL_DATE] >= min_date]
    df = df[df[ID_COL_DATE] <= max_date]
    
    return Wetterdaten(
        dates = df[ID_COL_DATE].to_list(),
        temperatures= df[ID_COL_TEMPERATURE].to_list()
    )
    
def plot_wetter_und_brenner(
    wetter: Wetterdaten,
    brenner: Brennerdaten,
    outfile: str = "summary.png"
):
    from datetime import datetime
    import matplotlib.pyplot as plt

    # Datumswerte umwandeln
    wetter_dates = [
        datetime.strptime(str(d), "%Y%m%d")
        if not isinstance(d, datetime)
        else d
        for d in wetter.dates
    ]

    brenner_dates = [
        datetime.strptime(str(d), "%Y%m%d")
        if not isinstance(d, datetime)
        else d
        for d in brenner.dates
    ]

    # Zwei Subplots untereinander
    fig, (ax1, ax2) = plt.subplots(
        2,
        1,
        figsize=(12, 8),
        sharex=True
    )

    # Temperaturplot
    ax1.plot(
        wetter_dates,
        wetter.temperatures,
        color="blue",
        label="Temperatur"
    )

    ax1.set_ylabel("Temperatur (°C)", color="black")
    ax1.tick_params(axis="both", colors="black")
    ax1.grid(True, color="lightgray")
    ax1.legend(loc="upper right")

    # Brennerlaufzeitplot
    ax2.plot(
        brenner_dates,
        brenner.minutes,
        color="black",
        label="Laufzeit"
    )

    ax2.set_ylabel("Laufzeit (Minuten)", color="black")
    ax2.set_xlabel("Datum", color="black")
    ax2.tick_params(axis="both", colors="black")
    ax2.grid(True, color="lightgray")
    ax2.legend(loc="upper right")

    # Schwarze Achsen
    for ax in [ax1, ax2]:
        for spine in ax.spines.values():
            spine.set_color("black")

    # Datum lesbar machen
    fig.autofmt_xdate()

    plt.tight_layout()
    # plt.show()
    plt.savefig(Path(__file__).parent / outfile)
  
if __name__ == "__main__":
    brenner: Brennerdaten = parse_summary(Path(__file__).parent / "summary.txt")

    wetter: Wetterdaten = parse_wetterdaten(Path(__file__).parent / "wetterdaten.csv",
                    brenner.min_date, 
                    brenner.max_date)
    
    plot_wetter_und_brenner(wetter, brenner)