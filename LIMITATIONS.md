# System Limitations & Deployment Prerequisites Report

This document outlines the operational scope, technical assumptions, prototype constraints, and real-world deployment prerequisites for the **Disaster Response Crowd-Report Verification & Confidence Dashboard**.

---

## 1. Prototype Assumptions & Constraints

### 1. Synthetic Disaster Dataset
The system operates on a synthetic dataset of 1,200 simulated disaster reports. While spatial coordinates, description templates, and incident distributions mimic real-world municipal hazards, the data does not represent live emergency events.

### 2. Simulated Ground Truth
Ground truth indicators (`TRUE`, `FALSE`, `UNKNOWN`) are embedded in the synthetic dataset solely to evaluate system precision, recall, and false positive rates. Ground truth is strictly internal and is never exposed to dispatchers as live operational knowledge.

### 3. Rule-Based Heuristic Scoring
Confidence (0–100) and Priority (0–100) scores are calculated using transparent, deterministic rule-based weighted formulas. They are heuristic decision-support metrics and **must not be interpreted as calibrated statistical probabilities**.

### 4. Heuristic Corroboration & Duplicate Clustering
Geographic proximity, timestamp overlap, and text similarity are used to group near-duplicate reports into correlation clusters. While this discounts duplicate reports from inflating independent corroboration, spatial/textual clustering remains an approximation.

### 5. Simulated Baseline & Dashboard Timing
Baseline review speed (simulated at 3.0 minutes per report) and dashboard time-to-surface metrics are prototype simulation assumptions and proxy measurements. They do not represent measured real-world field dispatch speeds.

### 6. Simulated/Proxy Validation Study
Validation metrics (task completion rates, average task times, confusion scores) are derived from a simulated proxy validation study evaluating 3 operational role profiles. They do not represent findings from a formal human-participant IRB user study.

### 7. Append-Only Audit Log
Human verification actions create append-only audit records in `data/verification_audit.json` for prototype accountability. This JSON audit log is intended for local demonstration and does not provide production-grade tamper-proof cryptographic security or immutable hardware storage.

---

## 2. Privacy & Responsible AI Safeguards

The system strictly enforces the following non-negotiable safety and privacy boundaries:

- ❌ **No Citizen Reputation Scoring:** All citizen reports receive the exact same baseline source reliability weight (0.40).
- ❌ **No Individual Profiling:** No user profiling, social credit scoring, or personal identity tracking is implemented.
- ❌ **No IP Tracking or Device Fingerprinting:** Duplicate clustering uses spatial and temporal report metadata only.
- ❌ **No Continuous Location Tracking:** Citizens are never continuously tracked or monitored.
- ❌ **No Automatic Enforcement or Deployment:** Emergency dispatch, permit rejection, and resource allocation actions are 100% human-authorized.

---

## 3. Real-World Deployment Prerequisites

Deploying this system in an actual municipal emergency operations center would require:

1. **Authentication & Role-Based Access Control (RBAC):** Multi-factor authentication (MFA) and strict role permissions for dispatchers, responders, and city officials.
2. **Encrypted Communications & Secure Storage:** SSL/TLS in-transit encryption and encrypted database storage for live report data.
3. **Enterprise Audit Trail:** Immutable, tamper-evident audit logging integrated with enterprise SIEM systems.
4. **Integration with Official Emergency Dispatch (CAD):** Bi-directional APIs connecting with Computer-Aided Dispatch (CAD) systems (e.g., 911/112 networks).
5. **Rigorous Security Testing & Penetration Audits:** Comprehensive vulnerability assessments and data governance approval.
6. **Mandatory Human-in-the-Loop Policy:** Formal operational protocols ensuring that automated scores serve strictly as decision-support signals, with final deployment authority resting with certified human dispatchers.
