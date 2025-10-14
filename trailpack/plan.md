# Development Plan: Step 3 Column Mapping Enhancement

## check if value in column is numeric then suggest to choose a label and unit for it.
## drop immediate suggestions, and provide only search field.
## 3 + 4 steps together

## Goal
Implement/enhance the mapping interface on Step 3 of the Streamlit UI to map Excel column names to PyST concept suggestions.

## Current State Analysis

###  Already Implemented
1. Column names are retrieved from selected sheet via `st.session_state.df.columns`
2. PyST API client is called for each column name
3. Suggestions are cached in `st.session_state.suggestions_cache`
4. Dropdown lists display suggestions with "(No mapping)" option
5. Currently shows **10 suggestions** per column (line 81 in streamlit_app.py)

### = Modifications Required
1. Reduce suggestions from 10 to 5 per dropdown
2. Verify proper integration of excel/reader.py columns with PyST suggestions
3. Ensure proper error handling for missing suggestions

---

## Step-by-Step Implementation Tasks

  Task 1: ✅ COMPLETED

  Changes Made in ui/streamlit_app.py:

  1. Line 298 (Page 3): Changed from df.columns.tolist() to:
  columns = st.session_state.reader.columns(st.session_state.selected_sheet)
  2. Line 104 (generate_view_object()): Added explicit column retrieval from ExcelReader:
  columns = st.session_state.reader.columns(st.session_state.selected_sheet)
  3. Line 262 (Page 2 metrics): Changed column count from len(df.columns) to:
  column_count = len(st.session_state.reader.columns(selected_sheet))

  Result:

  - ✅ ExcelReader is now the single source of truth for both sheets AND columns
  - ✅ Consistent data flow: ExcelReader → column names → PyST suggestions
  - ✅ pandas DataFrame still used for data preview and sample values
  - ✅ Memory efficient (ExcelReader only loads structure, not full data)

---

### Task 2: Configure PyST API Client for Suggestions
**Status:**  Already implemented

**Components:**
- [x] `get_suggest_client()` returns singleton client
- [x] `fetch_suggestions_async()` calls `client.suggest(column_name, language)`
- [x] `fetch_suggestions_sync()` wraps async call with `asyncio.run()`

**Current Implementation:**
```python
# Lines 76-89 in streamlit_app.py
async def fetch_suggestions_async(column_name: str, language: str):
    client = get_suggest_client()
    suggestions = await client.suggest(column_name, language)
    return suggestions[:10]  # Currently 10
```

**Action Required:** Change line 81 from `[:10]` to `[:5]`

---

### Task 3: Reduce Suggestions from 10 to 5
**Status:** =DONE

**Changes Required:**
1. Update `fetch_suggestions_async()` to return only 5 suggestions
2. Update inline comment

**File:** `trailpack/ui/streamlit_app.py`

**Change:**
```python
# Line 81 - BEFORE:
return suggestions[:10]  # Limit to top 10

# Line 81 - AFTER:
return suggestions[:5]  # Limit to top 5
```

---

### Task 4: Implement Dropdown List with Suggestions
**Status:**  Already implemented

**Current Implementation:**
- Lines 327-343 in streamlit_app.py
- Uses `st.selectbox()` with dynamic options
- Format: `"Label (ID: id_value)"`
- Includes "(No mapping)" option at index 0

**Verification Points:**
- [x] Dropdown shows "(No mapping)" as first option
- [x] Each suggestion displays as "Label (ID: id)"
- [x] Selected value is stored in `st.session_state.column_mappings`
- [x] Selection persists across re-runs

**Action:** No changes needed - already working correctly

---

### Task 5: Cache Suggestions for Performance
**Status:**  Already implemented

**Current Implementation:**
- Lines 297-307 in streamlit_app.py
- Suggestions cached in `st.session_state.suggestions_cache`
- Progress bar shows loading status
- Only fetches if cache is empty

**Cache Structure:**
```python
{
  "column_name_1": [{"id": "...", "label": "..."}, ...],
  "column_name_2": [{"id": "...", "label": "..."}, ...],
}
```

**Action:** No changes needed - already working correctly

---

### Task 6: Handle Edge Cases and Errors
**Status:**  Partially implemented

**Current Error Handling:**
- `fetch_suggestions_async()` catches exceptions and shows warning
- Returns empty list `[]` on failure

**Edge Cases to Verify:**
- [ ] No suggestions available for a column � Shows "No suggestions available" warning
- [ ] PyST API timeout � Caught by exception handler
- [ ] PyST API authentication failure � Caught by exception handler
- [ ] Empty/null column names � Should handle gracefully

**Recommendations:**
1. Add more specific error messages for different failure types
2. Consider retry logic for temporary failures
3. Log errors for debugging

---

### Task 7: Display Sample Values for Context
**Status:**  Already implemented

**Current Implementation:**
- Lines 318-321 in streamlit_app.py
- Shows first 3 non-null values from each column
- Format: "Sample: value1, value2, value3"

**Action:** No changes needed - working correctly

---

### Task 8: Generate View Object with Mappings
**Status:**  Already implemented

**Current Implementation:**
- `generate_view_object()` function (lines 92-138)
- Called on every render of page 3 (line 355)
- Stored in `st.session_state.view_object`

**View Object Structure:**
```json
{
  "sheet_name": "Sheet1",
  "dataset_name": "filename_Sheet1",
  "columns": {
    "column_name": {
      "values": ["sample1", "sample2", ...],
      "mapping_to_pyst": {
        "suggestions": [{"label": "...", "id": "..."}],
        "selected": {"label": "...", "id": "..."}
      }
    }
  }
}
```

**Action:** No changes needed - already working correctly

---

## Implementation Checklist

### Immediate Actions Required
- [ ] **Task 3:** Change suggestion limit from 10 to 5 in `fetch_suggestions_async()` (line 81)
- [ ] **Task 3:** Update comment to reflect "top 5" instead of "top 10"

### Verification Actions
- [ ] **Task 1:** Test with various Excel files and sheet structures
- [ ] **Task 4:** Verify dropdown displays exactly 5 suggestions + "(No mapping)"
- [ ] **Task 6:** Test error handling with invalid PyST credentials
- [ ] **Task 6:** Test with columns that have no matching PyST concepts
- [ ] **Task 8:** Verify view object is correctly generated with selected mappings

### Optional Enhancements
- [ ] Add tooltips showing full suggestion descriptions
- [ ] Implement search/filter within suggestion dropdown
- [ ] Add "Refresh suggestions" button for individual columns
- [ ] Show confidence scores if provided by PyST API
- [ ] Add ability to manually enter PyST concept ID
- [ ] Implement bulk mapping (apply same concept to multiple columns)
- [ ] Add export mappings to JSON/CSV for reuse

---

## Testing Plan

### Unit Tests
1. Test `fetch_suggestions_sync()` with various column names
2. Test `generate_view_object()` with different mapping states
3. Test error handling in `fetch_suggestions_async()`

### Integration Tests
1. Upload Excel file and verify columns are extracted correctly
2. Verify PyST API is called with correct parameters
3. Verify suggestions are cached and reused
4. Verify view object contains all required fields

### UI Tests
1. Test dropdown selection and persistence
2. Test "No mapping" option
3. Test navigation between pages preserves selections
4. Test with large Excel files (many columns)
5. Test with different languages

---

## Files to Modify

### Primary File
- `trailpack/ui/streamlit_app.py`
  - Line 81: Change `[:10]` to `[:5]`
  - Line 81: Update comment

### Supporting Files (No changes required)
- `trailpack/excel/reader.py` - Already working correctly
- `trailpack/pyst/api/client.py` - Already working correctly
- `trailpack/pyst/api/config.py` - Already configured

---

## Dependencies

### Required Packages (Already Installed)
- streamlit >= 1.28.0
- pandas >= 2.0.0
- openpyxl
- httpx
- python-dotenv
- langcodes
- pydantic

### Environment Variables Required
```bash
PYST_HOST=https://api.pyst.example.com
PYST_AUTH_TOKEN=your_token_here
```

---

## Success Criteria

The implementation is considered complete when:
1.  Column names from Excel sheet are correctly displayed
2. = Each column shows exactly **5 PyST concept suggestions** in dropdown
3.  User can select a suggestion or choose "No mapping"
4.  Selections are persisted in session state
5.  View object is generated with all mappings
6.  Error handling gracefully manages API failures
7.  Performance is acceptable for sheets with 50+ columns

---

## Timeline Estimate

- **Task 3 (Change limit):** 5 minutes
- **Verification Tasks:** 30 minutes
- **Testing:** 1 hour
- **Total:** ~1.5 hours

---

## Notes

- Current implementation already has most features working
- Main change needed: reduce suggestions from 10 to 5
- Consider future enhancement: make number of suggestions configurable
- PyST API response time may vary - caching is critical for UX
- Session state management is working well for multi-page workflow
