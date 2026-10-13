# MAN-401: Station Configuration and Cable Loss Compensation Diagnostics

- **Manual ID**: MAN-401
- **Prefix**: MAN-4
- **Category**: STATION_CONFIGURATION
- **Fault Family**: F1
- **Target Side**: MEASUREMENT_SYSTEM
- **Keywords**: golden, reference path, cable loss, compensation, configuration, S21, station offset

## 1. Overview and Operational Scope
This procedure governs investigations when an RF automated test station exhibits systematic insertion loss (S21) or scalar power measurement offsets following software, hardware, or calibration table updates.

## 2. Measurement Signatures
- **Golden Standard Deviation**: The golden reference verification unit fails insertion loss limits exclusively on the modified test station (e.g., ST-A), while passing within normal tolerance on sister stations (e.g., ST-B).
- **Broadband Uniform Attenuation**: Measurement deltas across multi-gigahertz frequency sweeps show uniform or frequency-proportional negative shifts (e.g., -0.8 dB to -2.4 dB).
- **Sister Station Discrepancy**: Cross-station Welch's t-test indicates significant mean shifts ($p < 0.01$) on identical DUTs tested across stations.

## 3. Root Cause Analysis
1. Corrupted, uncalibrated, or default cable loss compensation tables loaded into the station sequence configuration.
2. Inadvertent insertion of uncharacterized RF adapters or directional couplers in the reference path without updating de-embedding S-parameter files.
3. Configuration version desynchronization between instrument driver state and line test limits.

## 4. Mandatory Corrective Action Protocol
1. **Immediate Line Halt**: Immediately quarantine and halt the suspect station to prevent false DUT rejections.
2. **Audit Configuration Delta**: Review recent configuration version commits, audit station cable loss compensation, and inspect `cable_loss_compensation_table` entries against the golden calibration ledger.
3. **Reference Path Verification**: Inspect the physical reference path, RF jumper cables, and torque all SMA/3.5mm connectors to 8 in-lbs (0.9 N-m).
4. **Golden Re-characterization**: Re-run the golden reference standard across all sweeps. Verify measured insertion loss agrees with nominal reference values to within +/-0.30 dB.
5. **Configuration Baseline Restoration**: Restore the last verified baseline configuration table before releasing the station to production.