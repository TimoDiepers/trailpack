"""Demo script to show data inconsistencies CSV export."""
import pandas as pd
from trailpack.validation import StandardValidator

# Create a DataFrame with mixed types
df = pd.DataFrame({
    'id': [1, 2, 3, 4, 5],
    'name': ['Alice', 123, 'Bob', 'Charlie', 456],  # Mixed string and int
    'value': [10.5, 20.3, 'not_a_number', 30.2, 40.1]  # Mixed float and string
})

# Define schema
schema = {
    'fields': [
        {
            'name': 'id',
            'type': 'integer',
            'description': 'Unique identifier',
            'unit': {'name': 'dimensionless', 'path': 'http://qudt.org/vocab/unit/NUM'}
        },
        {
            'name': 'name',
            'type': 'string',
            'description': 'Person name'
        },
        {
            'name': 'value',
            'type': 'number',
            'description': 'Numeric value',
            'unit': {'name': 'kg', 'path': 'http://qudt.org/vocab/unit/KiloGM'}
        }
    ]
}

# Validate
validator = StandardValidator()
result = validator.validate_data_quality(df, schema=schema)

# Print result
print(result)
print('\n' + '='*60)
print(f'Inconsistencies tracked: {len(result.inconsistencies)}')

if result.inconsistencies:
    print('\nFirst few inconsistencies:')
    for inc in result.inconsistencies[:5]:
        print(f"  Row {inc['row']}, Column '{inc['column']}': "
              f"value={inc['value']} (type={inc['actual_type']}, expected={inc['expected_type']})")
