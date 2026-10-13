# MAN-801: Product Hardware Revision and Test Limit Matrix Synchronization

- **Manual ID**: MAN-801
- **Prefix**: MAN-8
- **Category**: SPEC_OR_REVISION_MISMATCH
- **Fault Family**: F5
- **Target Side**: SPECIFICATION
- **Keywords**: limits, revision, product revision, spec mismatch, test limits, sequence version

## 1. Overview and Operational Scope
This procedure addresses apparent false test failures arising from testing new hardware product revisions (e.g., REV_B) against legacy test limits (e.g., REV_A).

## 2. Measurement Signatures
- **Controlled Parametric Shift**: The target device exhibits deliberate engineering design differences (e.g., lower insertion loss nominal of $-1.40\text{ dB}$) that violate tighter legacy limits (e.g., upper limit $-2.00\text{ dB}$).
- **Healthy Repeatability and Golden Runs**: Golden reference units pass with high precision; multi-station runs on the target DUT are completely repeatable.
- **Revision Ledger Discrepancy**: The DUT metadata product revision does not match the active test limit sheet revision.

## 3. Root Cause Analysis
1. Test sequencer executing legacy limit configuration file during pilot introduction of updated hardware revisions.
2. Engineering change order (ECO) limits not updated in the production test database.
3. Operator selection of incorrect product profile in the station user interface.

## 4. Mandatory Corrective Action Protocol
1. **Verify Unit Hardware Revision**: Inspect physical serial number and QR barcode to establish true product revision status.
2. **Audit Limits Version**: Review `limits.csv` against current Engineering Change Notices (ECN).
3. **Align Test Limit Matrix**: Load corresponding limit set for the target product revision (e.g., activate `LIM_V2.0` for `REV_B`).
4. **Re-execute Sequence**: Re-run testing under matched limits to confirm compliant parametric performance.