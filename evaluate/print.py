import re
from datetime import datetime
from pathlib import Path
from typing import Optional, Callable
import argparse
from functools import partial
import logging
import yaml
import matplotlib.pyplot as plt
from matplotlib.ticker import MultipleLocator
from dataclasses import dataclass
from utils import get_git_dir, setup_logging

@dataclass
class Brennerdaten:
    dates: list[int]
    min_date: str
    max_date: str
    minutes : list[int]
    

# Datei mit den Daten
DATEI = "summary.txt"

@dataclass
class Configuration:
    weather_input: Path
    data_input: Path
    output: Path

def get_yaml_config(config_path: str="config.yaml"):
        
    # Reading YAML data from file
    with open(config_path, 'r') as f:
        yaml_data = yaml.safe_load(f)
        
    return yaml_data

def get_sanitized_config(yaml_data) -> Configuration:
    paths = {}
    
    # Input paths to check
    for key in ["weather_input", "data_input"]:
        input_file_path = (Path(yaml_data[key]["dir"]) / Path(yaml_data[key]["file"])).resolve()
        
        if not input_file_path.is_file():
            raise FileNotFoundError(f"File \"{input_file_path}\" does not exist")
        
        paths[key] = input_file_path
        
    # Output path to check
    output_dir_path = Path(yaml_data["output"]["dir"]).resolve()
    
    if not output_dir_path.is_dir():
        raise Exception(f"Ouput directory \"{output_dir_path}\" does not exist")

    paths["output"] = output_dir_path / yaml_data["output"]["file"]
    return Configuration(**paths)

def setup_parser():
    parser = argparse.ArgumentParser(
        description="Take a logfile from a given path (heating times) and print it"
    )
    git_dir = get_git_dir()

    parser.add_argument("-c", "--config_file_path", 
                        required=False,
                        default=f"{str(git_dir)}/config.yaml",
                        type=str,
                        help="Input path for the config file")
    
    return parser

def get_config_file_path():
    argparser = setup_parser().parse_args() 
    yaml_config_path = Path(argparser.config_file_path)
    
    if not yaml_config_path.is_file():
        raise FileNotFoundError(f"Configuration file \"{yaml_config_path}\" does not exist.")
    return yaml_config_path


Number = float | int

def is_valid_instance(d: Optional[Number]):
    """ Check if data is either of type 'float' or 'int' """
    return isinstance(d, datetime)

def get_best(compare_func : Callable[[Number, Number], Number],
             best_date: Optional[Number], 
             current_date: Optional[Number]):

    # Check if current_date is 'None'
    if current_date is None:
        raise TypeError("Passed parameter is of type None")
    
    if not is_valid_instance(current_date):
        raise TypeError("Passed parameter is of wrong type. Expect type datetime.")
    
    # Return the current_date if best_date is not yet initialized
    if best_date is None:
        return current_date
    
    if not is_valid_instance(best_date):
        raise TypeError("Passed parameter is of wrong type. Expect datetime.")    
    
    # Finally, call the compare function
    if not callable(compare_func):
        raise TypeError("Function not callable")
    
    return compare_func(best_date, current_date)

get_max = partial(get_best, max)
get_min = partial(get_best, min)

def parse_summary(input_file: Path):
    
    daten = []
    minutenwerte = []
    min_date = None
    max_date = None
    
    # Datei einlesen
    with input_file.open("r", encoding="utf-8") as f:
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
    outfile: str|Path
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
    ax2.yaxis.set_major_locator(MultipleLocator(60))
    ax2.grid(True, color="lightgray")
    ax2.legend(loc="upper right")

    # Schwarze Achsen
    for ax in [ax1, ax2]:
        for spine in ax.spines.values():
            spine.set_color("black")

    # Datum lesbar machen
    fig.autofmt_xdate()

    plt.tight_layout()
    plt.savefig(outfile)

def main():
    setup_logging()
    
    # Get the configuartion file from the argparser
    config_file_path = get_config_file_path()
    
    # Read configuratino file and convert it into dataclass representation
    config = get_yaml_config(config_file_path)
    configuration = get_sanitized_config(config)
    
    # Evaluate brenner data set
    brenner: Brennerdaten = parse_summary(configuration.data_input)

    # Evaluate weather data set
    wetter: Wetterdaten = parse_wetterdaten(configuration.weather_input,
                    brenner.min_date,
                    brenner.max_date)
    
    plot_wetter_und_brenner(wetter, 
                            brenner, 
                            configuration.output)

if __name__ == "__main__":
    main()