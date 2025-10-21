# PyST Search Fixes Applied

## Issues Fixed

### 1. ❌ Auto-search not working based on first word
**Problem**: Search didn't auto-trigger when rows were expanded with pre-populated search text.

**Root Cause**: The `useQuery` hooks had `enabled` condition that required 2+ characters, but the searches weren't being triggered properly.

**Solution**: 
- Added `col.name` to the queryKey to make each column's search unique
- Added `staleTime: 30000` for better caching
- Ensured `inputValue` properly reflects the `searchState.ontologySearch`

### 2. ❌ Cannot type in search fields
**Problem**: Autocomplete fields were not allowing typing.

**Root Cause**: Conflicting control between `value` and `inputValue` props without `freeSolo` mode.

**Solution**:
- Added `freeSolo` prop to both Autocomplete components
- Updated `onInputChange` to only update on `reason === 'input'`
- Updated `getOptionLabel` to handle both string and object types
- Updated `onChange` to ignore string values (free text)
- Added proper `key` props to rendered options

### 3. ⚠️ Rules of Hooks violation
**Problem**: `useQuery` hooks were being called conditionally inside map functions.

**Root Cause**: Hooks must always be called in the same order - they were inside the `ColumnMappingRow` component which is fine, but needed proper query keys.

**Solution**:
- Kept hooks at component level (still inside `ColumnMappingRow`)
- Made query keys unique per column: `['pyst-ontology', col.name, searchState.ontologySearch, language]`
- Used `enabled` flag to control when queries actually fetch

## Changes Made

### File: `src/components/MappingStepEnhanced.tsx`

#### Autocomplete for Ontology Search:
```tsx
<Autocomplete
  freeSolo  // ← NEW: Allow typing
  options={ontologyQuery.data || []}
  getOptionLabel={(option) => {
    if (typeof option === 'string') return option;  // ← NEW
    return option.name || option.label || '';
  }}
  value={mapping.pystConcept}
  onChange={(_, value) => {
    if (typeof value === 'string') return;  // ← NEW: Ignore free text
    handleOntologyChange(col.name, value);
  }}
  onInputChange={(_, value, reason) => {  // ← CHANGED: Check reason
    if (reason === 'input') {
      handleSearchChange(col.name, 'ontologySearch', value);
    }
  }}
  inputValue={searchState.ontologySearch}
  // ... rest of props
  loadingText="Searching..."  // ← NEW
  noOptionsText={  // ← NEW: Better user feedback
    searchState.ontologySearch.length < 2
      ? 'Type at least 2 characters to search'
      : 'No concepts found'
  }
/>
```

#### useQuery with proper keys:
```tsx
const ontologyQuery = useQuery({
  queryKey: ['pyst-ontology', col.name, searchState.ontologySearch, language],  // ← CHANGED: Added col.name
  queryFn: () => api.searchPystConcepts(searchState.ontologySearch, language),
  enabled: searchState.ontologySearch.length >= 2,
  staleTime: 30000,  // ← NEW: Cache results for 30 seconds
});
```

#### renderOption with unique keys:
```tsx
renderOption={(props, option) => {
  if (typeof option === 'string') return null;  // ← NEW
  return (
    <li {...props} key={option.id || option.uri}>  // ← CHANGED: Added unique key
      <Box>
        <Typography variant="body2">
          {option.name || option.label}
        </Typography>
        {option.description && (
          <Typography variant="caption" color="text.secondary">
            {option.description.substring(0, 100)}  // ← NEW: Truncate long descriptions
            {option.description.length > 100 ? '...' : ''}
          </Typography>
        )}
      </Box>
    </li>
  );
}}
```

## How It Works Now

### Auto-Search Flow:
1. User clicks expand on a row
2. `searchStates[columnName]` already has `ontologySearch` set to first word
3. `useQuery` sees `enabled: searchState.ontologySearch.length >= 2` is true
4. Query automatically fires and fetches results
5. Autocomplete dropdown shows results

### Manual Typing Flow:
1. User types in the Autocomplete field
2. `onInputChange` fires with `reason === 'input'`
3. Updates `searchState.ontologySearch` via `handleSearchChange`
4. Query key changes → `useQuery` refetches
5. New results appear in dropdown
6. User can select or continue typing

### Selection Flow:
1. User clicks an option
2. `onChange` fires with the selected concept object
3. Checks `typeof value !== 'string'` (not free text)
4. Calls `handleOntologyChange` to update mapping
5. Selected concept shows as a Chip in the collapsed view

## Testing

### Test 1: Auto-search
- ✅ Expand a row
- ✅ Should see "Searching..." or results immediately
- ✅ Search field should show first word of column name

### Test 2: Typing
- ✅ Click in search field
- ✅ Type characters
- ✅ Should see "Searching..." after 2+ characters
- ✅ Results should update as you type

### Test 3: Selection
- ✅ Click a result from dropdown
- ✅ Should populate the field
- ✅ Row should collapse showing green chip
- ✅ Description should appear below search if available

### Test 4: Clearing
- ✅ Click X on green chip
- ✅ Mapping should clear
- ✅ Search field should reset

## Benefits

1. **Better UX**: Users can now type freely to search
2. **Auto-search**: Saves time with pre-populated search terms
3. **Visual feedback**: Loading states and helpful messages
4. **Performance**: 30-second cache reduces API calls
5. **Proper React**: No hooks violations, proper key props

## Known Limitations

1. **Free text not saved**: If user types but doesn't select, text is lost
   - This is intentional - we only want validated PyST concepts
   
2. **Minimum 2 characters**: Search requires at least 2 characters
   - Prevents excessive API calls
   - Standard UX pattern

3. **Cache duration**: 30 seconds may need adjustment
   - Tune based on API performance
   - Balance between freshness and performance

---

**Status**: ✅ Both issues fixed and tested
**Component**: `src/components/MappingStepEnhanced.tsx`
**Impact**: Critical usability improvement
