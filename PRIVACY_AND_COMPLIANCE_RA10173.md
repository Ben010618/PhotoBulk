# Philippine Data Privacy Act of 2012 (RA 10173) Compliance & Privacy Governance Blueprint

**Document Version:** 1.0.0  
**Jurisdiction:** Republic of the Philippines  
**Regulator:** National Privacy Commission (NPC)  
**Applicability:** KameraPh Studio Suite, Partner Photography Studios, School Clients, and Student/Parent Data Subjects  

---

## 1. Executive Context & Legal Applicability
Under **Republic Act No. 10173 (Data Privacy Act of 2012)** and its **Implementing Rules and Regulations (IRR)**, photographic portraits and facial biometrics captured during school pictorials constitute **Personal Information** and **Sensitive Personal Information** (when linked to official student records, LRNs, and educational institutions).

KameraPh acts as a **Personal Information Processor (PIP)** when processing graduation photos on behalf of partner photography studios or educational institutions, and as a **Personal Information Controller (PIC)** for studio administrative accounts and direct student proofing portals.

---

## 2. Core Compliance Directives

### A. Principle of Transparency & Informed Consent
1. **Minor Consent (K-12 Students under 18 years old):**
   - Under Philippine Law (Family Code & RA 10173), minors cannot legally execute independent consent for commercial biometric processing.
   - Partner studios and schools must obtain an **Informed Parental/Guardian Consent Waiver** during annual school registration or prior to pictorial day.
   - The online proofing portal (`/proof/{student_id}`) includes a mandatory consent verification prompt before photos can be viewed, downloaded, or shared.
2. **Tertiary Students (18+ College & Graduate School):**
   - Direct digital consent check on first login / access to preview watermarked proofs.

### B. Principle of Legitimate Purpose
- Photographs are collected and processed **strictly** for:
  1. Inclusion in official school yearbooks, graduation programs, and commencement slides.
  2. Printing of official Philippine 2x2 identification cards (compliant with PRC, DFA, and DepEd/CHED guidelines).
  3. Delivery of commemorative studio print packages ordered by the student/family.
- Photos **shall never** be monetized, sold, or used to train third-party public AI models without explicit, separate written consent.

### C. Principle of Proportionality & Data Retention Policy
1. **Active Project Retention (90-Day Rule):**
   - High-resolution master files and batch exports are retained for **90 calendar days** following commencement exercises to fulfill re-print and yearbook correction requests.
2. **Automated Purge & Deletion:**
   - Following 90 days, raw and processed portrait images are permanently purged from active object storage (Cloudflare R2 / local disks).
   - Only non-identifiable financial transaction metadata (receipt numbers, payment references) is retained for 5 years to comply with Bureau of Internal Revenue (BIR) tax auditing requirements.

---

## 3. Security Measures & Technical Safeguards

1. **Storage & Encryption:**
   - All photos at rest are encrypted using AES-256 on Cloudflare R2 / secure volumes.
   - Data in transit is enforced via TLS 1.3 / HTTPS.
2. **Multi-Tenant Studio Isolation & Row-Level Security (RLS):**
   - Strict database row-level security ensures Studio A cannot access, query, or export batches belonging to Studio B.
3. **Watermarking & Screen Scraping Defense:**
   - Online proofs rendered to mobile devices carry diagonal studio watermarks and student identification cards to prevent unauthorized commercial printing prior to payment.

---

## 4. NPC Registration & Data Protection Officer (DPO) Requirements

### A. Mandatory NPC Registration Check (NPC Circular 2022-04)
Under Section 5 of NPC Circular No. 2022-04, mandatory registration with the National Privacy Commission is required if:
1. The organization employs at least two hundred fifty (250) persons; **OR**
2. The processing involves sensitive personal information of at least **one thousand (1,000) individuals**; **OR**
3. The processing is likely to pose a significant risk to the rights and freedoms of data subjects.

> **Legal Advisory:** Because high-volume graduation photography studios routinely capture between **2,000 and 50,000 student faces per academic graduation season**, partner studios and KameraPh cloud operators exceed the 1,000-subject threshold for sensitive personal data. **NPC Registration is legally mandatory.**

### B. Appointment of a Data Protection Officer (DPO)
- Every commercial studio and KameraPh operating entity must formally designate an internal or outsourced **Data Protection Officer (DPO)** registered with the NPC.
- The DPO's responsibilities:
  - Monitor local compliance with RA 10173.
  - Handle data subject inquiries and deletion requests within 15 business days.
  - Act as primary liaison to the National Privacy Commission.

### C. Mandatory 72-Hour Data Breach Notification
- In the event of a security incident involving unauthorized access or leak of student photos or personal identifiers, the DPO must formally report the breach to the NPC and affected schools/individuals **within seventy-two (72) hours** of discovery.

---

## 5. Model Privacy Notice for Studios (Ready for Deployment)

```markdown
### PRIVACY NOTICE TO STUDENTS AND PARENTS
In accordance with Republic Act No. 10173 (Data Privacy Act of 2012), [STUDIO NAME], in partnership with [SCHOOL NAME] and KameraPh AI Studio Suite, collects and processes your portrait photograph, student name, and section solely for graduation yearbook publication, school records, and studio print packages. 

Your photographs are processed securely with state-of-the-art encryption and will be retained for 90 days after graduation, after which raw master images will be permanently erased. We do not sell or distribute your biometric data to any third party.

To exercise your rights to access, inspect, or request deletion of your photographs, contact our Data Protection Officer at: dpo@[studiodomain].ph.
```
