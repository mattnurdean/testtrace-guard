# MAN-601: DUT Internal RF Defect Isolation and Shielding Quarantine

- **Manual ID**: MAN-601
- **Prefix**: MAN-6
- **Category**: DUT_DEFECT
- **Fault Family**: F2
- **Target Side**: DUT
- **Keywords**: isolation, shield, LO, leakage, DUT, defect, active component, harmonic distortion

## 1. Overview and Operational Scope
This standard provides instructions for isolating intrinsic device-under-test (DUT) hardware defects, including internal local oscillator (LO) leakage, defective RF cavity shielding, and active component failure.

## 2. Measurement Signatures
- **Multi-Station Spec Failure**: The target DUT fails specification limits identically on Station A and Station B.
- **Healthy Golden Verification**: Golden reference standards pass with zero deviations on all test stations, confirming the measurement system is healthy.
- **Specific Defect Fingerprint**: Excessive LO leakage (e.g., measured $-34.0\text{ dBm}$ against a $-40.0\text{ dBm}$ upper limit) or anomalous harmonic distortion (H2/H3) with normal linear S-parameters.

## 3. Root Cause Analysis
1. Insufficient physical solder joint wetting on internal RF shield lids, allowing radiated LO leakage into adjacent receiver stages.
2. Mixer or oscillator active circuit bias point shift due to out-of-spec passive component placement.
3. Defective internal decoupling capacitors causing ground bounce at RF frequencies.

## 4. Mandatory Corrective Action Protocol
1. **DUT Quarantine**: Quarantine the failing device immediately to inspect for internal LO leakage defects. Do not adjust test station configuration or test limits.
2. **Cross-Station Replication**: Confirm identical failure behavior on a secondary calibrated station to rule out fixture artifacts.
3. **Physical Shield Inspection**: Route the quarantined DUT to failure analysis (FA). Inspect RF shielding cans, solder joints, and ground vias using X-ray imaging.
4. **Internal Isolation Audit**: Measure radiated emissions using an RF near-field sniffer probe to locate the precise source of internal isolation breakdown and LO leakage.