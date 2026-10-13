# MAN-901: Inconclusive Evidence Triage and Missing Baseline Protocol

- **Manual ID**: MAN-901
- **Prefix**: MAN-9
- **Category**: INSUFFICIENT_EVIDENCE
- **Fault Family**: AMB
- **Target Side**: UNDETERMINED
- **Keywords**: golden, repeat, configuration revision, missing, baseline, data gap, inconclusive, escalation

## 1. Overview and Operational Scope
This manual establishes the handling protocol when test data packages exhibit inconclusive evidence, missing baseline golden reference runs, unrecorded calibration dates, or single-sweep marginal failures.

## 2. Measurement Signatures
- **Missing Golden Reference Baseline**: The measurement package contains zero golden unit verification runs to establish station ground truth.
- **Missing Maintenance Ledger Records**: Calibration due dates or last reference check timestamps are blank in `station_history.csv`.
- **Marginal Single-Sweep Violation**: A parameter slightly exceeds limits on only 1 of multiple repeated sweeps, while other sweeps pass comfortably.
- **Status Determination**: Evaluation requires `NEEDS_MORE_DATA`.

## 3. Root Cause Analysis
1. Incomplete test package export or test abort prior to executing scheduled golden verification runs.
2. Maintenance logging bypassed during urgent test runs, leaving station calibration state unverified.
3. Statistical ambiguity preventing reliable root-cause differentiation between measurement system and DUT.

## 4. Mandatory Corrective Action Protocol
1. **Halt Automated Disposition**: Do not scrap the DUT and do not disassemble the test station.
2. **Execute Golden Verification Campaign**: Immediately insert and measure a verified golden reference standard on the station across all frequency points.
3. **Audit Station Configuration and History**: Audit station calibration records, verify station configuration revision status, and manually record missing calibration dates into the tracking system.
4. **Multi-Sweep Repeat Test**: Perform a full 5-sweep repeat test of the target unit across both stations to establish statistical significance.
5. **Re-triage Package**: Re-submit the completed test package through TestTrace Guard once baseline data is restored.