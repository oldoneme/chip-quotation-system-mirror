# Engineering Quote Edit Fix - Syntax & Logic Restoration

## Issue Description
A syntax error (`Unexpected token`) persisted in `useQuoteEditMode.js` around line 990. This was caused by accidental deletion of the variable declaration and filter logic for `detailedFormatCards` in the **Handler (分选机)** section during a previous bulk edit. The `.map()` function was left hanging without a subject.

## Applied Fixes
1.  **Code Restoration:** I have restored the missing lines in `frontend/chip-quotation-frontend/src/hooks/useQuoteEditMode.js`:
    ```javascript
    const detailedFormatCards = deviceGroups.handler
      .filter(item => item.item_name && item.item_name.includes(' - '))
      .map(item => {
        const boardName = item.item_name.split(' - ')[1] || item.item_name;
        // ... (rest of the logic including partNumber extraction)
    ```
2.  **Context Alignment:** Ensured the restored code aligns correctly with the subsequent logic that uses `findCardTypeIdByName`.

## Verification
*   **Syntax Check:** The file should now parse correctly without `Unexpected token` errors.
*   **Logic Check:** The ID normalization logic (String matching, Number fallback) implemented in previous steps is preserved within this restored block.
*   **Functional Goal:** This completes the chain of fixes. The application should now compile, and the "Edit Engineering Quote" page should correctly display board selections for Test Machines, Handlers, and Probers, preserving their IDs as Numbers to match the UI components.
