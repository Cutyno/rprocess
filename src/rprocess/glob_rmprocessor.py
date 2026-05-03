"""Core utilities for rprocess."""

from glob import glob
from pickle import load, dump
from hashlib import sha256
from typing import AnyStr, Optional, Any, Union
from types import FunctionType
from os import PathLike
from multiprocessing import Pool


FileDescriptorOrPath = Union[
    int,
    str,
    bytes,
    PathLike[str],
    PathLike[bytes],
]
StrOrBytesPath = Union[str, bytes, PathLike[str], PathLike[bytes]]


def glob_rmprocessor(
        pathname: AnyStr,
        file_function: FunctionType,
        safepoint_path: FileDescriptorOrPath,
        cumulative_function: Optional[FunctionType] = None,
        processes: Optional[int] = None,
        root_dir: Optional[StrOrBytesPath] = None,
        dir_fd: Optional[int] = None,
        recursive: bool = False,
        verbose: bool = False) -> Optional[Any]:
    savepoint = {}
    curr_hash = []
    result = None
    try:
        with open(safepoint_path, 'rb') as f:
            savepoint = load(f)
        if verbose:
            print(f"Loaded savepoint with {len(savepoint)} entries.")
    except FileNotFoundError:
        if verbose:
            print("No savepoint found, starting from scratch.")
    changed_savepoint = False
    files = glob(
        pathname,
        root_dir=root_dir,
        dir_fd=dir_fd,
        recursive=recursive,
    )
    processed_files = 0
    pending_files = 0

    def error_callback(e):
        if verbose:
            print(f"\nError processing file: {e}")

    with Pool(processes=processes) as pool:
        working_files = {}
        for path in files:
            try:
                curr_result = None
                file_hash = None
                with open(path, 'rb') as f:
                    file_hash = sha256(f.read()).hexdigest()
                curr_hash.append(file_hash)
                if file_hash in savepoint:
                    curr_result = savepoint[file_hash]
                    processed_files += 1
                else:
                    pending_files += 1
                    working_files[file_hash] = pool.apply_async(
                        file_function,
                        args=(path,),
                        error_callback=lambda e: error_callback(e)
                    )
                    changed_savepoint = True
                if cumulative_function and curr_result is not None:
                    result = cumulative_function(result, curr_result)
                if verbose:
                    print(
                        f"Processing files... {processed_files}/{len(files)} processed, {pending_files} pending",
                        end='\r',
                    )
            except Exception as e:
                if verbose:
                    print(f"\nError processing file {path}: {e}")
        for file_hash, async_result in working_files.items():
            try:
                curr_result = async_result.get()
                savepoint[file_hash] = curr_result
                if cumulative_function:
                    result = cumulative_function(result, curr_result)
                processed_files += 1
                pending_files -= 1
                if verbose:
                    print(
                        f"Processing files... {processed_files}/{len(files)} processed, {pending_files} pending",
                        end='\r',
                    )
            except Exception as e:
                if verbose:
                    print(f"\nError processing file {path}: {e}")
    print("")
    for file_hash in list(savepoint.keys()):
        if file_hash not in curr_hash:
            if verbose:
                print(f"Removing savepoint for file hash {file_hash}.")
            del savepoint[file_hash]
            changed_savepoint = True
    if changed_savepoint:
        with open(safepoint_path, 'wb') as f:
            dump(savepoint, f)
    elif verbose:
        print("No changes to savepoint.")
    return result
