from pathlib import Path
import logging

def setup_logging():
    logging.basicConfig(
        filename="./log_analyzer.log",
        filemode="a",
        format='%(asctime)s %(levelname)-8s %(message)s',
        level=logging.INFO,
        datefmt='%Y-%m-%d %H:%M:%S')

def get_git_dir():
    
    current_dir = Path().cwd()
    
    while current_dir != current_dir.parent:
        
        if (current_dir / ".git").is_dir():
            return str(current_dir)
        else:
            current_dir = current_dir.parent
        
    return None

def get_file_path(user_path: str, user_file: str) -> Path:
    
    file_path = Path(user_path) / Path(user_file)
    
    if file_path.is_file():
        return file_path
    else:
        return None