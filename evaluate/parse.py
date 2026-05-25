from pathlib import Path
import logging
import argparse
from datetime import datetime
from typing import Tuple, Dict
from utils import get_git_dir, get_file_path, setup_logging

def setup_parser():
    parser = argparse.ArgumentParser(
        description="Take a logfile from a given path (heating times) and analze it"
    )
    git_dir = get_git_dir()

    parser.add_argument("-ip", "--input_path", 
                        required=True,
                        default=f"{str(git_dir)}/evaluate/data",
                        type=str,
                        help="Input path to the file to be analzed")
    
    parser.add_argument("-if", "--input_file", 
                        required=True,
                        default="brennerlaufzeiten.log",
                        type=str,
                        help="File to be analzed")

    parser.add_argument("-op", "--output_path", 
                        required=False,
                        default=f"{str(git_dir)}/evaluate/result",
                        type=str,
                        help="Output to the logfile to be analzed")
    
    parser.add_argument("-of", "--output_file", 
                        required=False,
                        default="summary.txt",
                        type=str,
                        help="Summary file")    
    
    logging.info(f"Setup argparser done")
    return parser
    
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
    
def create_dictionary_entry():
    logging.info("Creating new dictionary entry")

    return {
        "times": [],
        "overall_time": 0
    }

def main():
    setup_logging()
    argparser = setup_parser().parse_args()
    
    logging.info(f"Input path:  {argparser.input_path=}")
    logging.info(f"Input file:  {argparser.input_file=}")
    logging.info(f"Ouput path:  {argparser.output_path=}")
    logging.info(f"Output file: {argparser.output_file=}")
    
    input_file_path: Path = get_file_path(argparser.input_path, argparser.input_file)
    
    if not input_file_path:
        logging.error(f"Input file path does not exist!")
        return 0
    
    from collections import defaultdict
    brenner_dict = defaultdict(create_dictionary_entry)
    
    with Path(input_file_path).open("r") as f:
        
        for line in f.readlines():
            
            # Parse the current line into its information values            
            match parse_line(line):
                
                case (False, ()):
                    logging.info(f"Line \"{line}\" could not be parsed")
                    continue
                case (True, (date, time, measured_time)):
                    entry = brenner_dict[date]
                    entry["times"].append(time)
                    entry["overall_time"]+= measured_time
                    logging.info(f"For {date=}, add elements {time=} and {measured_time=} -- Sum: {entry["overall_time"]}")
    
    with (Path(argparser.output_path) / Path(argparser.output_file)).open("w") as results:
    
        for key, item in brenner_dict.items():
            hours, minutes, seconds  = seconds_to_readable_time(item["overall_time"])
            # print(f"Zeit in Minuten: {item['overall_time']//60}")
            results.write(f"{key}: {item["overall_time"]:0>4} -> {hours:0>2}:{minutes:0>2}:{seconds:0>2}\n")

if __name__ == "__main__":
    main()