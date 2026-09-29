---
trigger: always_on
---

1. Inspect the repository before implementation.

2. Search for existing functionality before creating anything.

3. Before coding, identify:
   - reusable components
   - reusable hooks
   - services
   - utilities
   - types
   - constants
   - existing styles

4. Before implementing a medium or large feature, show the proposed:
   - folder structure
   - files to create
   - files to modify
   - existing components to reuse

5. Do not implement a large feature in a single file.

6. React components should normally remain below approximately 200 lines.

7. If a component approaches 200 lines, evaluate whether responsibilities should be extracted.

8. Never intentionally create a 500+ line component when the code can reasonably be modularized.

9. Do not split files artificially just to satisfy a line limit.

10. Prefer composition over duplication.

11. When modifying an existing large file, refactor it instead of adding more unrelated logic.

12. After implementation, verify:
    - existing functionality still works
    - no duplicate components were introduced
    - reusable components were actually reused
    - business logic is separated from UI
    - imports are clean
    - no unnecessary files were created