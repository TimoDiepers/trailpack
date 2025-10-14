"""
NumericValueGuesser: Detects numeric columns and suggests units/labels.

This module provides functionality to:
- Detect if a column contains numeric values
- Calculate statistics for numeric columns
- Suggest appropriate units based on column names and value ranges
- Determine if a column should be treated as numeric with unit selection
"""

import re
from typing import Dict, List, Optional, Tuple, Any
import pandas as pd
import numpy as np


class NumericValueGuesser:
    """
    Analyzes DataFrame columns to detect numeric data and suggest units.

    This class helps determine whether a column should be mapped to a PyST concept
    or treated as a numeric value with a unit and label.
    """

    # Common unit patterns in column names
    UNIT_PATTERNS = {
        # Energy
        'kwh': ['kwh', 'kilowatt-hour', 'kilowatt hour'],
        'mwh': ['mwh', 'megawatt-hour', 'megawatt hour'],
        'gwh': ['gwh', 'gigawatt-hour', 'gigawatt hour'],
        'kw': ['kw', 'kilowatt'],
        'mw': ['mw', 'megawatt'],
        'gw': ['gw', 'gigawatt'],
        'joule': ['j', 'joule', 'joules'],

        # Mass
        'kg': ['kg', 'kilogram', 'kilograms'],
        'g': ['g', 'gram', 'grams'],
        'ton': ['ton', 'tons', 'tonne', 'tonnes', 't'],
        'lb': ['lb', 'lbs', 'pound', 'pounds'],

        # Distance
        'km': ['km', 'kilometer', 'kilometers', 'kilometre', 'kilometres'],
        'm': ['m', 'meter', 'meters', 'metre', 'metres'],
        'mile': ['mile', 'miles', 'mi'],

        # Area
        'km2': ['km2', 'km²', 'square kilometer', 'square kilometre'],
        'm2': ['m2', 'm²', 'square meter', 'square metre'],
        'hectare': ['ha', 'hectare', 'hectares'],

        # Volume
        'l': ['l', 'liter', 'liters', 'litre', 'litres'],
        'ml': ['ml', 'milliliter', 'milliliters', 'millilitre', 'millilitres'],
        'm3': ['m3', 'm³', 'cubic meter', 'cubic metre'],

        # Time
        'year': ['year', 'years', 'yr', 'yrs', 'y'],
        'month': ['month', 'months', 'mo'],
        'day': ['day', 'days', 'd'],
        'hour': ['hour', 'hours', 'hr', 'hrs', 'h'],

        # Money
        'usd': ['usd', '$', 'dollar', 'dollars'],
        'eur': ['eur', '€', 'euro', 'euros'],
        'gbp': ['gbp', '£', 'pound', 'pounds'],

        # Percentage
        'percent': ['%', 'percent', 'percentage', 'pct'],

        # Carbon/Emissions
        'co2': ['co2', 'co₂', 'carbon dioxide'],
        'co2e': ['co2e', 'co₂e', 'carbon dioxide equivalent'],
        'mtco2': ['mtco2', 'mt co2', 'megatonne co2'],
    }

    def __init__(self, numeric_threshold: float = 0.8):
        """
        Initialize the NumericValueGuesser.

        Args:
            numeric_threshold: Minimum fraction of non-null values that must be
                             numeric for a column to be considered numeric (0-1)
        """
        self.numeric_threshold = numeric_threshold

    def is_numeric_column(self, series: pd.Series) -> bool:
        """
        Determine if a pandas Series should be treated as numeric.

        Args:
            series: Pandas Series to analyze

        Returns:
            True if the column contains primarily numeric values
        """
        if len(series) == 0:
            return False

        # Remove null values
        non_null = series.dropna()
        if len(non_null) == 0:
            return False

        # Check if pandas dtype is already numeric
        if pd.api.types.is_numeric_dtype(series):
            return True

        # Try to convert to numeric
        numeric_converted = pd.to_numeric(non_null, errors='coerce')
        numeric_count = numeric_converted.notna().sum()

        # Calculate percentage of numeric values
        numeric_ratio = numeric_count / len(non_null)

        return numeric_ratio >= self.numeric_threshold

    def get_numeric_stats(self, series: pd.Series) -> Optional[Dict[str, Any]]:
        """
        Calculate statistics for a numeric column.

        Args:
            series: Pandas Series to analyze

        Returns:
            Dictionary with statistics, or None if not numeric
        """
        if not self.is_numeric_column(series):
            return None

        # Convert to numeric
        numeric_series = pd.to_numeric(series, errors='coerce')
        numeric_series = numeric_series.dropna()

        if len(numeric_series) == 0:
            return None

        return {
            'count': len(numeric_series),
            'min': float(numeric_series.min()),
            'max': float(numeric_series.max()),
            'mean': float(numeric_series.mean()),
            'median': float(numeric_series.median()),
            'std': float(numeric_series.std()) if len(numeric_series) > 1 else 0.0,
            'has_negative': bool((numeric_series < 0).any()),
            'has_decimal': bool((numeric_series % 1 != 0).any()),
            'null_count': series.isna().sum(),
            'null_percentage': float(series.isna().sum() / len(series) * 100)
        }

    def guess_unit_from_name(self, column_name: str) -> List[str]:
        """
        Guess possible units based on the column name.

        Args:
            column_name: Name of the column

        Returns:
            List of possible unit names
        """
        column_lower = column_name.lower()
        matched_units = []

        for unit_name, patterns in self.UNIT_PATTERNS.items():
            for pattern in patterns:
                # Check if pattern appears as a word in the column name
                pattern_regex = r'\b' + re.escape(pattern) + r'\b'
                if re.search(pattern_regex, column_lower):
                    matched_units.append(unit_name)
                    break

        return matched_units

    def guess_unit_from_values(self, series: pd.Series) -> List[str]:
        """
        Guess possible units based on value ranges.

        Args:
            series: Pandas Series with numeric values

        Returns:
            List of possible unit names
        """
        stats = self.get_numeric_stats(series)
        if not stats:
            return []

        suggested_units = []
        min_val = stats['min']
        max_val = stats['max']

        # Percentage: values between 0-100 or 0-1
        if 0 <= min_val and max_val <= 100 and not stats['has_negative']:
            suggested_units.append('percent')
        elif 0 <= min_val <= 1 and 0 <= max_val <= 1:
            suggested_units.append('percent')

        # Year: values in year range
        if 1900 <= min_val and max_val <= 2100:
            suggested_units.append('year')

        # Large numbers might be money, energy, or mass
        if max_val >= 1000000:
            suggested_units.extend(['usd', 'mwh', 'ton'])

        return suggested_units

    def analyze_column(self, series: pd.Series, column_name: str) -> Dict[str, Any]:
        """
        Perform complete analysis of a column.

        Args:
            series: Pandas Series to analyze
            column_name: Name of the column

        Returns:
            Dictionary with analysis results
        """
        is_numeric = self.is_numeric_column(series)

        result = {
            'column_name': column_name,
            'is_numeric': is_numeric,
            'stats': None,
            'suggested_units': [],
            'should_map_to_pyst': True  # Default: map to PyST concept
        }

        if is_numeric:
            result['stats'] = self.get_numeric_stats(series)

            # Guess units from name and values
            units_from_name = self.guess_unit_from_name(column_name)
            units_from_values = self.guess_unit_from_values(series)

            # Combine and deduplicate
            all_units = list(set(units_from_name + units_from_values))
            result['suggested_units'] = all_units

            # If we have strong unit suggestions, recommend unit selection instead of PyST
            if units_from_name:  # Units in name = strong indicator
                result['should_map_to_pyst'] = False

        return result

    def analyze_dataframe(self, df: pd.DataFrame) -> Dict[str, Dict[str, Any]]:
        """
        Analyze all columns in a DataFrame.

        Args:
            df: Pandas DataFrame to analyze

        Returns:
            Dictionary mapping column names to analysis results
        """
        results = {}

        for column in df.columns:
            results[column] = self.analyze_column(df[column], str(column))

        return results

    def get_numeric_columns(self, df: pd.DataFrame) -> List[str]:
        """
        Get list of column names that are numeric.

        Args:
            df: Pandas DataFrame to analyze

        Returns:
            List of column names that contain numeric data
        """
        numeric_cols = []

        for column in df.columns:
            if self.is_numeric_column(df[column]):
                numeric_cols.append(column)

        return numeric_cols

    def should_use_unit_selection(self, series: pd.Series, column_name: str) -> bool:
        """
        Determine if a column should use unit selection instead of PyST mapping.

        Args:
            series: Pandas Series to analyze
            column_name: Name of the column

        Returns:
            True if unit selection should be used, False if PyST mapping
        """
        analysis = self.analyze_column(series, column_name)
        return analysis['is_numeric'] and not analysis['should_map_to_pyst']

    @staticmethod
    def format_stats(stats: Optional[Dict[str, Any]]) -> str:
        """
        Format statistics for display.

        Args:
            stats: Statistics dictionary from get_numeric_stats()

        Returns:
            Formatted string representation
        """
        if not stats:
            return "Not numeric"

        return (
            f"Count: {stats['count']:,} | "
            f"Range: [{stats['min']:.2f}, {stats['max']:.2f}] | "
            f"Mean: {stats['mean']:.2f} | "
            f"Median: {stats['median']:.2f}"
        )
