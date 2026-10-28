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

### 4. Heuristic Corroboration, Duplicate Clustering & Conflict Detection Thresholds
Geographic proximity, timestamp overlap, and text similarity are used to group near-duplicate reports into correlation clusters and identify conflicting observations. The backend implements specific, deterministic constants:
- **Duplicate Correlation Clustering:** Spatial threshold $\le 1.0\text{ km}$ (Haversine), text similarity $\ge 0.50$ (`SequenceMatcher`), and temporal window $\le 30\text{ min}$ (with composite score threshold $\ge 0.80$, plus near-identical relaxation $\le 0.20\text{ km}$ and $\ge 0.50$ text similarity). *Note: The operational constants are 1.0 km / 0.50 / 30 min, not the legacy prototype specifications of 0.5 km / 0.60 / 180 min.*
- **Spatial-Temporal Conflict Detection:** Spatial threshold $\le 1.0\text{ km}$ and temporal window $\le 30\text{ min}$. *Note: The operational conflict temporal window is 30 min, not 360 min.* This tighter 30-minute window prevents morning flooding reports from erroneously contradicting afternoon clearance reports as floodwaters naturally recede.
- **Empirical Results:** Across the 1,200 synthetic reports, these implemented constants identified **94 conflicting reports** (7.83%) and **802 duplicate reports** clustered into **67 correlation groups**, achieving 88.30% precision and zero high-priority missed incidents.

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

---

## 4. Areas to Improve & Next Steps

Based on empirical testing against the actual implemented constants, the following engineering and algorithmic next steps are identified:

1. **Dynamic Spatial-Temporal Windowing:**
   - *Current State:* Fixed constants ($1.0\text{ km}$, $30\text{ min}$) applied across all incident types.
   - *Next Step:* Adapt window parameters dynamically based on hazard propagation velocity (e.g., $15\text{ min}$ for rapid flash floods vs. $120\text{ min}$ for static structural collapses).

2. **Probabilistic Calibration of Scoring Heuristics:**
   - *Current State:* Rule-based linear weighted combination (Confidence and Priority on 0–100 scale).
   - *Next Step:* Implement Platt scaling or isotonic regression on historical validation outcomes to map heuristic confidence scores into calibrated empirical Bayesian probabilities.

3. **Geospatial Indexing for $O(\log N)$ Candidate Matching:**
   - *Current State:* Exhaustive pairwise comparison ($O(N^2)$) using vectorized Haversine distance, suitable for 1,200 reports.
   - *Next Step:* Implement an R-Tree / PostGIS spatial index (`ST_DWithin` and GiST index) to support live streaming datasets exceeding 50,000 reports/hour.

4. **Multilingual NLP & Semantic Embeddings:**
   - *Current State:* `difflib.SequenceMatcher` lexical string matching with a 0.50 threshold.
   - *Next Step:* Integrate multilingual sentence transformer embeddings (e.g., `all-MiniLM-L6-v2`) to capture semantic synonyms and multilingual reports across diverse municipal populations.

5. **Formal Human-in-the-Loop User Studies:**
   - *Current State:* Evaluated using simulated proxy personas (Responder, City Official, Coordinator).
   - *Next Step:* Conduct structured empirical trials with certified emergency dispatchers to measure cognitive load, alert fatigue, and real-world triage latency.
