# SplintFit development rules

For every meaningful source, geometry, UI, test, configuration or documentation change:

1. Add or update a specific dated entry in LAB_NOTES using its template. Record what changed, why, validation performed, observed results, limitations and the next experiment.
2. Before committing, finish the note and set status to complete. That status means the record is complete; it does not mean the device is validated.
3. Link changed files and tests. Preserve earlier notes. Never backdate a note or invent a test, scan, print, Fusion conversion or clinical result.
4. Mark reconstructed history as retrospective, with the source version and checksum.
5. Keep geometric validity, mechanical performance, usability and clinical evidence separate.
6. Keep original scans and exported files in the same documented millimetre coordinate frame. Do not silently repair missing anatomy.
7. No patient/volunteer identifying files, raw scans, credentials or local runtime environments in Git. Only explicitly labelled synthetic examples belong in this repository by default.
8. Record uncertain claims as proposals. Do not call the perforation pattern mechanically optimized until load cases, constraints, material model and validation support that statement.

Use tools/new_lab_note.py to start an entry and tools/check_lab_notes.py --staged before a commit. See CONTRIBUTING.md.
