"""Parquet export service."""
import pandas as pd
import io
from typing import List, Dict, Any
from app.models.schemas import ColumnMapping, ExportConfig


class ExportService:
    """Service for exporting data to Parquet format."""
    
    @staticmethod
    def export_to_parquet(
        data_dict: Dict[str, Any],
        mappings: List[ColumnMapping],
        config: ExportConfig
    ) -> bytes:
        """
        Export mapped data to Parquet format.
        
        Args:
            data_dict: Original Excel data as dictionary
            mappings: Column mappings to PyST concepts
            config: Export configuration
            
        Returns:
            Parquet file as bytes
        """
        # Create DataFrame from mappings
        mapped_data = {}
        metadata = {}
        
        for mapping in mappings:
            if mapping.pystConcept:
                # Use PyST concept ID as column name
                concept_id = mapping.pystConcept.id
                mapped_data[concept_id] = data_dict.get(mapping.excelColumn, [])
                
                # Store metadata
                metadata[concept_id] = {
                    'original_column': mapping.excelColumn,
                    'concept_name': mapping.pystConcept.name,
                    'concept_description': mapping.pystConcept.description or '',
                    'concept_category': mapping.pystConcept.category or '',
                }
        
        # Create DataFrame
        df = pd.DataFrame(mapped_data)
        
        # Determine compression
        compression_map = {
            'snappy': 'snappy',
            'gzip': 'gzip',
            'none': None
        }
        compression = compression_map.get(config.compressionType, 'snappy')
        
        # Export to Parquet
        buffer = io.BytesIO()
        df.to_parquet(
            buffer,
            engine='pyarrow',
            compression=compression,
            index=False
        )
        
        return buffer.getvalue()


# Singleton instance
export_service = ExportService()
