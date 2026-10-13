# MAN-501: RF Fixture Interface, Launch Pin Wear, and Contact Repeatability

- **Manual ID**: MAN-501
- **Prefix**: MAN-5
- **Category**: FIXTURE_CONTACT
- **Fault Family**: F3
- **Target Side**: MEASUREMENT_SYSTEM
- **Keywords**: reconnect, re-seat, repeatability, contact, fixture, pogo pin, launch interface, mechanical alignment

## 1. Overview and Operational Scope
This manual defines diagnostic workflows for intermittent or non-repeatable RF test failures linked to pneumatic test fixtures, pogo pin degradation, coaxial launch wear, and mechanical seating misalignment.

## 2. Measurement Signatures
- **High Intra-Run Repeatability Sigma**: Replicate sweeps without DUT movement demonstrate erratic variance ($\sigma > 0.30\text{ dB}$), especially above 4.0 GHz.
- **Reconnect Delta Shift**: Disengaging, re-seating, and re-engaging the DUT into the fixture yields large discontinuous measurement shifts ($> 0.80\text{ dB}$).
- **High Return Loss Degradation**: S11 return loss spikes toward 0 dB at higher frequencies while lower frequencies show marginal continuity.

## 3. Root Cause Analysis
1. Mechanical oxidation, solder flux buildup, or carbon contamination on spring-loaded RF probe tips.
2. Contact pin height non-coplanarity preventing full ground shield mating before center conductor engagement.
3. Misalignment of automated fixture clamp guides, causing uneven force distribution across the DUT landing pads.

## 4. Mandatory Corrective Action Protocol
1. **Fixture Cleanliness Inspection**: Inspect fixture RF launch pins and contact interfaces under 20x magnification for debris, bent tips, or flux contamination.
2. **Alcohol Swab & Decontamination**: Clean probe contacts using electronic-grade isopropyl alcohol (IPA) and lint-free micro-swabs.
3. **Repeatability Verification**: Perform a 5-cycle re-seat and reconnect repeatability test using a verification unit. Confirm sweep-to-sweep repeatability variance $\sigma < 0.05\text{ dB}$.
4. **Fixture Alignment & Clamping**: Adjust mechanical guides and verify clamping pressure conforms to production mechanical specifications before resuming testing.