# Current Task
Update the `AlertQueue.jsx` component to support a new "Informational" severity tier.

## Requirements
1. Locate the `AlertQueue.jsx` file in `dashboard/src/components/`.
2. Add `'Informational'` to the `SEVERITIES` array.
3. Update the `SEVERITY_STYLES` dictionary to include a mapping for `Informational` with the background mapped to `#4B556322`, border to `#4B5563`, and color to `#9CA3AF`.
4. Ensure the filter bar correctly renders the new "Informational" button alongside the existing severity options.
5. Write or update a test in the frontend suite to verify the component renders the new severity filter and updates the active state when clicked without crashing.