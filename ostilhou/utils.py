from typing import Union, List
import os

from colorama import Fore



def green(s:str) -> str:
    return Fore.GREEN + s + Fore.RESET

def yellow(s:str) -> str:
    return Fore.YELLOW + s + Fore.RESET

def red(s:str) -> str:
    return Fore.RED + s + Fore.RESET



def sec2hms(seconds, sep=' ', precision=0, h_unit='h', m_unit='\'', s_unit="''"):
    """Return a string of hours, minutes, seconds from a given number of seconds"""
    minutes, seconds = divmod(seconds, 60)
    hours, minutes = divmod(minutes, 60)
    parts = []
    if hours > 0:
        parts.append(f"{int(hours)}{h_unit}")
    if hours > 0 or minutes > 0:
        parts.append(f"{int(minutes)}{m_unit}")
    seconds = round(seconds, precision)
    parts.append(f"{seconds}{s_unit}")
    return sep.join(parts)



def list_files_with_extension(ext: Union[str, tuple, list], path, recursive=True) -> List[str]:
    """
    Recursively list all files of the given extension(s) in a folder

    Parameters
    ----------
        ext : str|list
            file extension, without the extension separator
        path : str
            path to a folder
    """
    extensions = [ext] if isinstance(ext, str) else ext
    file_list = []
    if os.path.isdir(path):
        for filename in os.listdir(path):
            filename = os.path.join(path, filename)
            if os.path.isdir(filename) and recursive:
                file_list.extend(list_files_with_extension(extensions, filename))
            else:
                file_ext = os.path.splitext(filename)[1].removeprefix(os.path.extsep)
                if file_ext and file_ext in extensions:
                    file_list.append(filename)
    return file_list



def read_file_drop_comments(path: str) -> List[str]:
    lines = []
    with open(path, 'r', encoding='utf-8') as f:
        for l in f.readlines():
            l = l.strip()
            if l and not l.startswith('#'):
                lines.append(l)
    return lines
