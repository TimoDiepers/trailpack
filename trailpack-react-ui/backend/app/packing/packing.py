"""
Module for writing and reading pandas DataFrames with datapackage metadata 
into Parquet files using PyArrow.
"""

import pandas as pd
from pyarrow import Table, parquet
import json
import os
from typing import Tuple, Dict, Any


class Packing:
    """Class to handle packing and unpacking of pandas DataFrames with metadata into Parquet files.
    
    Attributes:
        data (pd.DataFrame): The pandas DataFrame to be packed or unpacked.
        meta_data (dict): The metadata dictionary to be embedded in the Parquet file.
    
    Methods:
        write_parquet(path): Writes the DataFrame and metadata to a Parquet file.
        read_parquet(path): Reads a Parquet file and extracts the DataFrame and metadata.
    """
    
    def __init__(
        self,
        data: pd.DataFrame = pd.DataFrame(),
        meta_data: dict = {}
    ) -> None:
        # Do data type checks
        self.__check_data_types__(data, meta_data)
        
        self.data = data
        self.meta_data = meta_data
    
    def write_parquet(self, path: str) -> None:
        """Write the DataFrame to a Parquet file with embedded metadata.
        
        Args:
            path (str): The file path where the Parquet file will be saved. 
                       Including file name 'file.parquet'.
        
        Returns:
            None
        """
        # Ensure the directory exists
        dir_path = os.path.dirname(path)
        if dir_path and not os.path.exists(dir_path):
            os.makedirs(dir_path, exist_ok=True)
        
        # Convert pandas DataFrame to Arrow Table
        table = Table.from_pandas(self.data)
        
        # Convert to JSON string for Arrow metadata (Arrow metadata must be bytes)
        json_metadata = json.dumps(self.meta_data)
        # Explicitly encode to bytes
        arrow_metadata = {"datapackage.json": json_metadata.encode('utf-8')}
        
        # Create schema with metadata
        schema_with_metadata = table.schema.with_metadata(arrow_metadata)
        
        table = table.cast(schema_with_metadata)
        
        # Write to Parquet with metadata
        parquet.write_table(table, path)
    
    def write_parquet_to_bytes(self) -> bytes:
        """Write the DataFrame to Parquet format as bytes with embedded metadata.
        
        Returns:
            bytes: Parquet file content as bytes
        """
        import io
        
        # Convert pandas DataFrame to Arrow Table
        table = Table.from_pandas(self.data)
        
        # Convert to JSON string for Arrow metadata (Arrow metadata must be bytes)
        json_metadata = json.dumps(self.meta_data)
        # Explicitly encode to bytes
        arrow_metadata = {"datapackage.json": json_metadata.encode('utf-8')}
        
        # Create schema with metadata
        schema_with_metadata = table.schema.with_metadata(arrow_metadata)
        
        table = table.cast(schema_with_metadata)
        
        # Write to bytes buffer
        buffer = io.BytesIO()
        parquet.write_table(table, buffer)
        
        return buffer.getvalue()
    
    def read_parquet(self, path: str) -> Tuple[pd.DataFrame, dict]:
        """Read a Parquet file and extract the DataFrame and embedded metadata.
        
        Args:
            path (str): The file path of the Parquet file to read.
        
        Returns:
            Tuple[pd.DataFrame, dict]: DataFrame and metadata dictionary
        """
        df, meta_data = read_parquet(path)
        
        self.data = df
        self.meta_data = meta_data
        
        return df, meta_data
    
    def __check_data_types__(self, data: pd.DataFrame, meta_data: dict) -> None:
        """Check that self.data is a pandas DataFrame and self.meta_data is a dictionary."""
        # Check that self.data is a pandas DataFrame
        if not isinstance(data, pd.DataFrame):
            raise TypeError("data must be a pandas DataFrame")
        # Check that self.meta_data is a dictionary
        if not isinstance(meta_data, dict):
            raise TypeError("meta_data must be a dictionary")


def read_parquet(source_path: str) -> Tuple[pd.DataFrame, Dict[str, Any]]:
    """Read a Parquet file and extract the DataFrame and embedded metadata.
    
    Args:
        source_path (str): The file path of the Parquet file to read.
    
    Returns:
        Tuple[pd.DataFrame, dict]: A tuple containing the DataFrame and metadata dictionary.
    """
    if not os.path.exists(source_path):
        raise FileNotFoundError(f"The file {source_path} does not exist.")
    
    # Read the Parquet file
    table = parquet.read_table(source_path)
    
    # Extract metadata
    metadata = table.schema.metadata
    if metadata and b"datapackage.json" in metadata:
        json_metadata = metadata[b"datapackage.json"].decode('utf-8')
        meta_data = json.loads(json_metadata)
    else:
        meta_data = {}
    
    # Convert Arrow Table back to pandas DataFrame
    df = table.to_pandas()
    
    return df, meta_data
