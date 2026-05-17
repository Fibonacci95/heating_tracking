from pathlib import Path
import logging
import argparse
from datetime import datetime
from typing import Tuple, Dict

def setup_parser():
    parser = argparse.ArgumentParser(
        description="Take a logfile from a given path (heating times) and analze it"
    )

    parser.add_argument("-ip", "--input_path", 
                        required=True,
                        type=str,
                        help="Input path to the logfile to be analzed")

    parser.add_argument("-op", "--output_path", 
                        required=False,
                        type=str,
                        help="Output tpth to the logfile to be analzed")
    
    logging.info(f"Setup argparser done")
    return parser

def setup_logging():
    logging.basicConfig(
        filename="./log_analyzer.log",
        filemode="a",
        format='%(asctime)s %(levelname)-8s %(message)s',
        level=logging.INFO,
        datefmt='%Y-%m-%d %H:%M:%S')
    
def parse_line(line: str) -> Tuple[bool, Tuple[str, str, int]]:
    if "INFO" not in line:
        return False, ()

    try:
        elements = line.split()
        timestamp = " ".join(elements[0:2])
        dt = datetime.strptime(timestamp, "%d-%m-%Y %H:%M:%S")

        date = dt.strftime("%d.%m.%Y")
        time = dt.strftime("%H:%M:%S")
        measured_time = int(elements[-1].strip("[]"))

        return True, (date, time, measured_time)
        
    except (ValueError, IndexError):
        return False, ()
    
def seconds_to_readable_time(t_in_sec:int) -> Tuple[int,int,int]:
        seconds_per_hour = 3600
        seconds_per_minute = 60
        
        hours = t_in_sec // seconds_per_hour
        minutes = (t_in_sec - (hours*seconds_per_hour)) // seconds_per_minute
        seconds = (t_in_sec - (hours*seconds_per_hour) - (minutes*60))
        return hours, minutes, seconds  

def main():
    setup_logging()
    argparser = setup_parser().parse_args()
    input_path = Path(argparser.input_path)
    
    if not input_path.is_file():
        logging.error(f"File path {input_path} does not exist!")
        return 0
    
    # Explictitly write down the expected type of dictionary
    brenner_dict : Dict[str, Dict[str, list | int]] = {}
    
    with input_path.open("r") as f:
        
        lines = f.readlines()
        
        for line in lines:
            # Parse the current line into its information values
            parsing_ok, infos = parse_line(line)
            
            # Go to next iteration if parsing failed
            if not parsing_ok:
                continue

            # Decompose Tuple
            current_date, current_time, measured_time = infos
            
            # Add new entry to dict if it does not exist yet
            if current_date not in brenner_dict:
                brenner_dict[current_date] = {
                    "times": [measured_time],
                    "overall_time": int(measured_time)}
                logging.info(f"Adding value {measured_time} to new element {current_date}")
            else:
                brenner_dict[current_date]["times"].append(measured_time)
                brenner_dict[current_date]["overall_time"]+=int(measured_time)
                logging.info(f"Adding value {measured_time} to already existing element {current_date}")
    
    
    outfile = "summary.txt"
    cwd = Path(__file__).parent
    
    with (cwd / Path(outfile)).open("w") as results:
    
        for key, item in brenner_dict.items():
            hours, minutes, seconds  = seconds_to_readable_time(item["overall_time"])
            # print(f"Zeit in Minuten: {item['overall_time']//60}")
            results.write(f"{key}: {item["overall_time"]:0>4} -> {hours:0>2}:{minutes:0>2}:{seconds:0>2}\n")

if __name__ == "__main__":
    main()