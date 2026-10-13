# MAN-701: RF Instrumentation Metrology, Calibration Expiry, and Reference Drift

- **Manual ID**: MAN-701
- **Prefix**: MAN-7
- **Category**: INSTRUMENT_CALIBRATION
- **Fault Family**: F4
- **Target Side**: MEASUREMENT_SYSTEM
- **Keywords**: calibration, golden, reference check, overdue, metrology, drift, vector network analyzer, signal generator

## 1. Overview and Operational Scope
This protocol governs situations where automated test stations experience systematic metrology drift due to expired factory calibration intervals or defective internal reference standards.

## 2. Measurement Signatures
- **Expired Calibration Interval**: Maintenance ledger indicates station instrument calibration is overdue by more than 30 days.
- **Multi-Parameter Measurement Shift**: Correlated drift observed across independent measurement domains (e.g., simultaneous shifts in insertion loss, phase noise, and power calibration).
- **Station-Specific Drift Pattern**: Discrepancies persist across all DUTs run on the overdue station, while calibrated stations produce consistent nominal readings.

## 3. Root Cause Analysis
1. Vector network analyzer (VNA) or spectrum analyzer internal reference oscillator drift exceeding factory specifications.
2. Expired calibration certificates without recertification against NIST-traceable standards.
3. Internal instrument temperature compensation hardware degradation.

## 4. Mandatory Corrective Action Protocol
1. **Immediate Station Tag-Out**: Tag-out the expired test station from active production lines.
2. **Metrology Recertification**: Transfer the instrument to the site metrology laboratory for full annual calibration against certified standards.
3. **Reference Verification Check**: Following return from metrology, perform a certified golden reference check across full frequency bands.
4. **Update Station Ledger**: Record new calibration dates and certificates in the `station_history.csv` ledger before returning to service.