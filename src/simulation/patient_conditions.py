"""
Clinical Patient Condition Simulations Module
Defines 35 high-fidelity clinical and electrophysiological patient scenarios with
distinct biopotential frequency characteristics, diagnostic interpretations, and tailored action plans.
"""

from typing import Dict, Any, List

PATIENT_CONDITIONS: Dict[str, Dict[str, Any]] = {
    "case_01_resting_baseline": {
        "id": "case_01_resting_baseline",
        "patient_id": "PT-2026-001",
        "patient_name": "Elena Vance (Age 32, F)",
        "category": "Neurological & Neurodegenerative Disorders",
        "name": "Normal Wakeful Baseline (Eyes Closed 10.2 Hz Alpha)",
        "dominant_freq": 10.2,
        "bands": {"delta": 12.0, "theta": 14.0, "alpha": 58.0, "beta": 16.0},
        "stress_index": 0.28,
        "tbr": 0.88,
        "abr": 3.62,
        "cognitive_load": "LOW",
        "patient_condition": (
            "Posterior dominant rhythm at 10.2 Hz with prominent sinusoidal alpha spindles and characteristic "
            "anterior attenuation upon eyes closed. Normal cortical idling in relaxed wakefulness without focal or generalized slowing."
        ),
        "patient_action_plan": [
            "Maintain standard clinical recording conditions with intermittent photic stimulation and hyperventilation protocol.",
            "Document baseline posterior alpha reactivity upon eye opening (Berger effect) to confirm intact thalamocortical gating.",
            "Clear subject for baseline neurocognitive reference profiling; no pharmacological or clinical intervention indicated."
        ],
        "wave_params": {
            "base_freq": 10.2, "alpha_amp": 32.0, "beta_amp": 6.0, "theta_amp": 5.0, "delta_amp": 4.0, "noise": 2.5
        }
    },
    "case_02_deep_nrem_sleep": {
        "id": "case_02_deep_nrem_sleep",
        "patient_id": "PT-2026-002",
        "patient_name": "Marcus Chen (Age 45, M)",
        "category": "Sleep & Circadian Disorders",
        "name": "Deep NREM Stage 3 / SWS Restorative Slow-Wave Sleep (Delta > 70%)",
        "dominant_freq": 1.2,
        "bands": {"delta": 74.0, "theta": 16.0, "alpha": 6.0, "beta": 4.0},
        "stress_index": 0.05,
        "tbr": 4.00,
        "abr": 1.50,
        "cognitive_load": "LOW",
        "patient_condition": (
            "High-amplitude (>75 μV), low-frequency polymorphic delta waves (0.8–2.0 Hz) comprising >70% of the epoch. "
            "Synchronous slow-wave oscillations indicate restorative neurocellular clearance and diminished external sensory responsiveness."
        ),
        "patient_action_plan": [
            "Preserve undisturbed sleep architecture; minimize ambient acoustic and optical arousals to maintain restorative delta sleep.",
            "Monitor for pathological slow-wave fragmentation, nocturnal myoclonus, or respiratory micro-arousals.",
            "Continue continuous polysomnographic biopotential tracking across sleep cycles N2 -> N3 -> REM."
        ],
        "wave_params": {
            "base_freq": 1.2, "alpha_amp": 3.0, "beta_amp": 2.0, "theta_amp": 12.0, "delta_amp": 85.0, "noise": 3.0
        }
    },
    "case_03_cognitive_overload": {
        "id": "case_03_cognitive_overload",
        "patient_id": "PT-2026-003",
        "patient_name": "Sarah Jenkins (Age 29, F)",
        "category": "Psychiatric & Behavioral Disorders",
        "name": "Acute Cognitive Overload & Executive Exhaustion (Beta > 60%)",
        "dominant_freq": 24.5,
        "bands": {"delta": 6.0, "theta": 12.0, "alpha": 18.0, "beta": 64.0},
        "stress_index": 2.13,
        "tbr": 0.19,
        "abr": 0.28,
        "cognitive_load": "HIGH",
        "patient_condition": (
            "Prominent desynchronized high-frequency beta oscillations (20-28 Hz) across prefrontal and central leads with marked alpha suppression. "
            "Significant elevation in the Spectral Stress Index (2.13) indicative of acute neurocognitive saturation and imminent mental burnout."
        ),
        "patient_action_plan": [
            "Mandate an immediate 15-minute sensory attenuation pause away from high-density visual displays.",
            "Administer guided 0.1 Hz resonant frequency breathing (6 breaths/minute) to elevate vagal parasympathetic modulation.",
            "Restructure high-stakes analytical tasks into segregated 25-minute Pomodoro intervals to prevent executive cognitive collapse.",
            "Re-evaluate biopotential stress index prior to resuming mission-critical cognitive responsibilities."
        ],
        "wave_params": {
            "base_freq": 24.5, "alpha_amp": 6.0, "beta_amp": 38.0, "theta_amp": 4.0, "delta_amp": 3.0, "noise": 5.0
        }
    },
    "case_04_adhd_inattention": {
        "id": "case_04_adhd_inattention",
        "patient_id": "PT-2026-004",
        "patient_name": "Lucas Rodriguez (Age 14, M)",
        "category": "Psychiatric & Behavioral Disorders",
        "name": "Attention Deficit Hyperactivity Disorder (Elevated Frontal TBR = 5.17)",
        "dominant_freq": 5.8,
        "bands": {"delta": 10.0, "theta": 62.0, "alpha": 16.0, "beta": 12.0},
        "stress_index": 0.15,
        "tbr": 5.17,
        "abr": 1.33,
        "cognitive_load": "LOW",
        "patient_condition": (
            "Frontal midline theta excess (4.5–6.5 Hz) with pronounced suppression of fast beta rhythm, yielding an abnormal "
            "Theta/Beta Ratio (TBR = 5.17 > 3.0 age-adjusted threshold). Indicates cortical hypo-arousal and executive inattention."
        ),
        "patient_action_plan": [
            "Initiate 20-session neurofeedback training targeting frontal theta down-training (4-7 Hz) and sensorimotor beta up-training (12-15 Hz).",
            "Introduce structured behavioral scaffolding with sensory modulation and externalized executive task cues.",
            "Clinical consultation for evaluating dopaminergic/noradrenergic pharmacological optimization (e.g., methylphenidate titration).",
            "Enforce regular 20-minute movement intervals and minimize sustained uninterrupted low-engagement tasks."
        ],
        "wave_params": {
            "base_freq": 5.8, "alpha_amp": 8.0, "beta_amp": 4.0, "theta_amp": 42.0, "delta_amp": 8.0, "noise": 3.5
        }
    },
    "case_05_focal_epileptiform": {
        "id": "case_05_focal_epileptiform",
        "patient_id": "PT-2026-005",
        "patient_name": "David Thorne (Age 38, M)",
        "category": "Neurological & Neurodegenerative Disorders",
        "name": "Focal Temporal Interictal Epileptiform Discharges (IEDs 150 μV)",
        "dominant_freq": 9.5,
        "bands": {"delta": 32.0, "theta": 28.0, "alpha": 22.0, "beta": 18.0},
        "stress_index": 0.36,
        "tbr": 1.56,
        "abr": 1.22,
        "cognitive_load": "HIGH",
        "patient_condition": (
            "Episodic sharp waves and spike-and-slow-wave complexes (120–180 μV amplitude, duration 80-140 ms) arising from temporal montages "
            "with subsequent phase-reversal. Morphologically diagnostic of focal cortical hyper-excitability and epileptiform irritability."
        ),
        "patient_action_plan": [
            "Urgent neurological consult for high-resolution 3T epilepsy-protocol brain MRI and 24-hour ambulatory video-EEG monitoring.",
            "Assess therapeutic serum levels of anti-seizure medications (e.g., Levetiracetam, Lamotrigine) or initiate trial if treatment-naive.",
            "Institute seizure safety precautions: driving restriction, avoidance of unmonitored swimming, and sleep deprivation mitigation.",
            "Prescribe rescue intranasal midazolam with explicit caregiver status epilepticus action plan."
        ],
        "wave_params": {
            "base_freq": 9.5, "alpha_amp": 16.0, "beta_amp": 8.0, "theta_amp": 18.0, "delta_amp": 20.0, "noise": 4.0, "spike_amp": 150.0
        }
    },
    "case_06_absence_3hz": {
        "id": "case_06_absence_3hz",
        "patient_id": "PT-2026-006",
        "patient_name": "Chloe Dupont (Age 9, F)",
        "category": "Neurological & Neurodegenerative Disorders",
        "name": "Childhood Absence Seizure (Classic 3 Hz Spike-and-Wave Paroxysms)",
        "dominant_freq": 3.0,
        "bands": {"delta": 52.0, "theta": 24.0, "alpha": 14.0, "beta": 10.0},
        "stress_index": 0.16,
        "tbr": 2.40,
        "abr": 1.40,
        "cognitive_load": "HIGH",
        "patient_condition": (
            "Paroxysmal, generalized, synchronous 3.0 Hz spike-and-slow-wave complexes with abrupt onset and sudden termination "
            "against a normal background. Characteristic electrographic pattern of childhood absence epilepsy (petit mal)."
        ),
        "patient_action_plan": [
            "First-line pharmacological management: Initiate Ethosuximide (or Valproate if concomitant generalized tonic-clonic risk).",
            "Avoid sodium channel blockers (Carbamazepine, Phenytoin) which may paradoxically exacerbate 3 Hz spike-wave absence paroxysms.",
            "Advise school and family regarding brief staring spells, micro-unresponsiveness, and cognitive lapses during schoolwork.",
            "Repeat hyperventilation EEG activation study at 6-week follow-up to confirm electrographic remission."
        ],
        "wave_params": {
            "base_freq": 3.0, "alpha_amp": 8.0, "beta_amp": 4.0, "theta_amp": 16.0, "delta_amp": 70.0, "noise": 3.0, "absence_spike": True
        }
    },
    "case_07_anxiety_panic": {
        "id": "case_07_anxiety_panic",
        "patient_id": "PT-2026-007",
        "patient_name": "Amina Patel (Age 26, F)",
        "category": "Psychiatric & Behavioral Disorders",
        "name": "Severe Generalized Anxiety & Acute Panic Agitation (Beta Buzz 26 Hz)",
        "dominant_freq": 26.2,
        "bands": {"delta": 4.0, "theta": 10.0, "alpha": 14.0, "beta": 72.0},
        "stress_index": 3.60,
        "tbr": 0.14,
        "abr": 0.19,
        "cognitive_load": "HIGH",
        "patient_condition": (
            "Diffuse, pervasive 22–32 Hz fast beta activity ('beta buzz') with profound suppression of synchronizing alpha mechanisms. "
            "Autonomic biometric channels indicate acute hyper-sympathetic activation, tachycardia, and heightened somatic arousal."
        ),
        "patient_action_plan": [
            "Immediate clinician-facilitated Grounding & Somatosensory Regulation (5-4-3-2-1 sensory orientation and 4-7-8 breathing).",
            "Rule out acute physiological etiologies: check bedside glucose, cardiac ECG rhythm strip, and pulse oximetry.",
            "Consider short-term anxiolytic or beta-adrenergic blockade (e.g., Propranolol 10-20 mg) for sympathetic tremor and tachycardia.",
            "Enroll in Cognitive Behavioral Therapy (CBT) with heart rate variability (HRV) biofeedback stabilization."
        ],
        "wave_params": {
            "base_freq": 26.2, "alpha_amp": 5.0, "beta_amp": 45.0, "theta_amp": 4.0, "delta_amp": 2.0, "noise": 6.0
        }
    },
    "case_08_meditative_flow": {
        "id": "case_08_meditative_flow",
        "patient_id": "PT-2026-008",
        "patient_name": "Tenzin Gyatso (Age 52, M)",
        "category": "Neuromodulation & Brain Stimulation",
        "name": "Deep Meditative Flow State (Zen / Frontal Midline Theta + Alpha)",
        "dominant_freq": 6.2,
        "bands": {"delta": 10.0, "theta": 42.0, "alpha": 38.0, "beta": 10.0},
        "stress_index": 0.13,
        "tbr": 4.20,
        "abr": 3.80,
        "cognitive_load": "LOW",
        "patient_condition": (
            "High-amplitude coherent frontal midline theta (Fmθ 5.5–6.5 Hz) synchronized with abundant posterior alpha. "
            "Indicates profound internalized sustained attention, emotional serenity, and decreased default mode network (DMN) rumination."
        ),
        "patient_action_plan": [
            "Continue contemplative mindfulness practice session without external cognitive interference.",
            "Record neuroplastic biopotential markers for longitudinal meditation neuro-phenotyping study.",
            "Transition gently into active mental tasks to maintain post-meditative cognitive clarity and vagal tone."
        ],
        "wave_params": {
            "base_freq": 6.2, "alpha_amp": 26.0, "beta_amp": 5.0, "theta_amp": 28.0, "delta_amp": 6.0, "noise": 1.5
        }
    },
    "case_09_chronic_burnout": {
        "id": "case_09_chronic_burnout",
        "patient_id": "PT-2026-009",
        "patient_name": "Robert Sterling (Age 42, M)",
        "category": "Artifacts & Pharmacological Effects",
        "name": "Chronic Occupational Burnout & Cognitive Fatigue (Disorganized Alpha)",
        "dominant_freq": 8.4,
        "bands": {"delta": 18.0, "theta": 40.0, "alpha": 24.0, "beta": 18.0},
        "stress_index": 0.35,
        "tbr": 2.22,
        "abr": 1.33,
        "cognitive_load": "FATIGUE",
        "patient_condition": (
            "Disorganized background rhythms with low-voltage theta intrusion during active executive tasks and blunted alpha reactivity. "
            "Reflects neuro-endocrine allostatic load, diminished attentional stamina, and central cognitive exhaustion."
        ),
        "patient_action_plan": [
            "Implement mandatory clinical duty-hour restrictions and enforced circadian sleep schedule (minimum 8 hours nocturnal sleep).",
            "Comprehensive endocrine panel: morning serum cortisol curve, thyroid panel (TSH, free T4), vitamin D, and ferritin.",
            "Workplace ergonomic and schedule restructuring; limit continuous screen time to under 4 hours without cognitive respite.",
            "Neuro-rehabilitation coaching with progressive physical exercise and restorative mindfulness interventions."
        ],
        "wave_params": {
            "base_freq": 8.4, "alpha_amp": 14.0, "beta_amp": 10.0, "theta_amp": 24.0, "delta_amp": 12.0, "noise": 4.5
        }
    },
    "case_10_mild_cognitive_impairment": {
        "id": "case_10_mild_cognitive_impairment",
        "patient_id": "PT-2026-010",
        "patient_name": "Eleanor Wright (Age 71, F)",
        "category": "Neurological & Neurodegenerative Disorders",
        "name": "Mild Cognitive Impairment (Slowed Posterior Dominant Rhythm 7.8 Hz)",
        "dominant_freq": 7.8,
        "bands": {"delta": 24.0, "theta": 44.0, "alpha": 22.0, "beta": 10.0},
        "stress_index": 0.15,
        "tbr": 4.40,
        "abr": 2.20,
        "cognitive_load": "LOW",
        "patient_condition": (
            "Pathological slowing of the posterior dominant rhythm down to 7.8 Hz with diffuse temporo-parietal theta intrusion during resting conditions. "
            "Consistent with early neurodegenerative biomarker changes and synaptic transmission slowing."
        ),
        "patient_action_plan": [
            "Formal neurocognitive battery assessment: MoCA (Montreal Cognitive Assessment) and detailed neuropsychological memory subtests.",
            "Order volumetric brain MRI with NeuroQuant hippocampal atrophy quantification and vascular white matter burden scoring.",
            "Initiate lifestyle multimodal intervention: Mediterranean-DASH neuroprotective diet, cardiovascular exercise, and structured cognitive stimulation.",
            "Screen for reversible metabolic contributors (serum B12, methylmalonic acid, TSH, and sleep apnea polysomnography)."
        ],
        "wave_params": {
            "base_freq": 7.8, "alpha_amp": 12.0, "beta_amp": 5.0, "theta_amp": 28.0, "delta_amp": 16.0, "noise": 3.0
        }
    },
    "case_11_metabolic_encephalopathy": {
        "id": "case_11_metabolic_encephalopathy",
        "patient_id": "PT-2026-011",
        "patient_name": "Arthur Pendelton (Age 64, M)",
        "category": "Acute Critical Care Pathologies",
        "name": "Toxic-Metabolic Encephalopathy (FIRDA & Bilateral Triphasic Waves)",
        "dominant_freq": 1.8,
        "bands": {"delta": 58.0, "theta": 28.0, "alpha": 10.0, "beta": 4.0},
        "stress_index": 0.06,
        "tbr": 7.00,
        "abr": 2.50,
        "cognitive_load": "HIGH",
        "patient_condition": (
            "Frontal Intermittent Rhythmic Delta Activity (FIRDA 1.5–2.5 Hz) with bilateral, synchronous triphasic waves exhibiting anterior-posterior lag. "
            "Characteristic of toxic, hepatic, or uremic encephalopathy with widespread cortical dysfunction."
        ),
        "patient_action_plan": [
            "STAT laboratory evaluation: Arterial blood ammonia, comprehensive metabolic panel (BUN, creatinine, electrolytes), hepatic enzymes, and arterial blood gas.",
            "Review active medication chart for nephrotoxic, hepatotoxic, or centrally sedating compounds; immediately withhold offending agents.",
            "For hepatic etiology: Initiate lactulose titration (20-30 g q6h) and rifaximin 550 mg BID; consider nephrology consultation for uremic hemodialysis.",
            "Continuous neurological observation for fluctuating delirium, asterixis, and progressive obtundation."
        ],
        "wave_params": {
            "base_freq": 1.8, "alpha_amp": 5.0, "beta_amp": 2.0, "theta_amp": 20.0, "delta_amp": 65.0, "noise": 4.0, "firda": True
        }
    },
    "case_12_post_concussion": {
        "id": "case_12_post_concussion",
        "patient_id": "PT-2026-012",
        "patient_name": "Tyler Brooks (Age 22, M)",
        "category": "Acute Critical Care Pathologies",
        "name": "Post-Concussion Syndrome / Mild TBI (Focal Delta-Theta Slowing)",
        "dominant_freq": 6.8,
        "bands": {"delta": 34.0, "theta": 36.0, "alpha": 18.0, "beta": 12.0},
        "stress_index": 0.20,
        "tbr": 3.00,
        "abr": 1.50,
        "cognitive_load": "MODERATE",
        "patient_condition": (
            "Asymmetric focal polymorphic delta and theta slowing over lateral fronto-temporal regions with attenuated background alpha amplitude. "
            "Typical electrophysiological correlate of localized axonal shear injury and neurotrauma."
        ),
        "patient_action_plan": [
            "Enforce graduated return-to-play / return-to-learn protocol; absolute restriction from contact sports and physical exertion until symptom-free.",
            "Vestibular-ocular motor screening (VOMS) with specialized physical therapy for post-traumatic dizziness and saccadic dysmetria.",
            "Non-contrast head CT or 3T brain MRI with SWI (susceptibility-weighted imaging) to exclude microhemorrhages or subdural hematoma.",
            "Structured sleep hygiene and avoidance of prolonged blue-light screen exposure during early axonal recovery."
        ],
        "wave_params": {
            "base_freq": 6.8, "alpha_amp": 10.0, "beta_amp": 6.0, "theta_amp": 26.0, "delta_amp": 24.0, "noise": 4.0
        }
    },
    "case_13_narcolepsy_hypnagogic": {
        "id": "case_13_narcolepsy_hypnagogic",
        "patient_id": "PT-2026-013",
        "patient_name": "Chloe Kim (Age 24, F)",
        "category": "Sleep & Circadian Disorders",
        "name": "Narcolepsy Type 1 (Sleep-Onset SOREMP & Vertex Sharp Waves)",
        "dominant_freq": 5.2,
        "bands": {"delta": 26.0, "theta": 46.0, "alpha": 18.0, "beta": 10.0},
        "stress_index": 0.16,
        "tbr": 4.60,
        "abr": 1.80,
        "cognitive_load": "LOW",
        "patient_condition": (
            "Abrupt daytime sleep-onset REM period (SOREMP) within 3 minutes of eyes-closed recording, accompanied by high-amplitude vertex sharp transients "
            "and loss of submental muscle tone. Highly specific for central hypersomnolence / narcolepsy."
        ),
        "patient_action_plan": [
            "Schedule overnight diagnostic polysomnogram (PSG) followed by next-day Multiple Sleep Latency Test (MSLT; 5 nap opportunities).",
            "Assess for cataplexy episodes, sleep paralysis, and hypnagogic hallucinations; consider CSF orexin/hypocretin-1 diagnostic assay.",
            "Pharmacotherapy evaluation: Wake-promoting agents (Modafinil/Armodafinil or Solriamfetol) and nocturnal sodium oxybate.",
            "Enforce scheduled 20-minute daytime prophylactic naps and strict road safety driving precautions."
        ],
        "wave_params": {
            "base_freq": 5.2, "alpha_amp": 10.0, "beta_amp": 5.0, "theta_amp": 32.0, "delta_amp": 18.0, "noise": 3.0, "vertex_waves": True
        }
    },
    "case_14_depression_frontal_asymmetry": {
        "id": "case_14_depression_frontal_asymmetry",
        "patient_id": "PT-2026-014",
        "patient_name": "Claire Montgomery (Age 36, F)",
        "category": "Psychiatric & Behavioral Disorders",
        "name": "Major Depressive Disorder (Frontal Alpha Asymmetry FAA)",
        "dominant_freq": 9.8,
        "bands": {"delta": 16.0, "theta": 24.0, "alpha": 48.0, "beta": 12.0},
        "stress_index": 0.17,
        "tbr": 2.00,
        "abr": 4.00,
        "cognitive_load": "LOW",
        "patient_condition": (
            "Prominent Frontal Alpha Asymmetry (FAA) characterized by elevated left frontal alpha power relative to right frontal leads. "
            "Reflects relative left prefrontal hypo-activation, decreased approach motivation, and depressive withdrawal tendency."
        ),
        "patient_action_plan": [
            "Administer validated mood metrics: PHQ-9 (Patient Health Questionnaire) and HAM-D depression rating scale.",
            "Consider 10 Hz repetitive Transcranial Magnetic Stimulation (rTMS) targeted to the left dorsolateral prefrontal cortex (DLPFC).",
            "Psychiatric evaluation for SSRI/SNRI pharmacotherapy combined with evidence-based cognitive behavioral therapy.",
            "Inquire regarding sleep architecture disruptions (early morning awakening) and assess clinical suicidality risk protocol."
        ],
        "wave_params": {
            "base_freq": 9.8, "alpha_amp": 28.0, "beta_amp": 6.0, "theta_amp": 14.0, "delta_amp": 8.0, "noise": 2.5, "asymmetry": 1.4
        }
    },
    "case_15_elite_athlete_zone": {
        "id": "case_15_elite_athlete_zone",
        "patient_id": "PT-2026-015",
        "patient_name": "Jonas Lindqvist (Age 28, M)",
        "category": "Neuromodulation & Brain Stimulation",
        "name": "Olympic Marksman Peak Performance Zone (SMR 12-15 Hz)",
        "dominant_freq": 13.5,
        "bands": {"delta": 8.0, "theta": 16.0, "alpha": 46.0, "beta": 30.0},
        "stress_index": 0.48,
        "tbr": 0.53,
        "abr": 1.53,
        "cognitive_load": "MODERATE",
        "patient_condition": (
            "Distinctive burst of Sensorimotor Rhythm (SMR 12-15 Hz) over central rolandic electrodes with concurrent occipital alpha synchronization. "
            "Reflects motionless motor readiness, suppressed somatosensory distraction, and peak performance flow."
        ),
        "patient_action_plan": [
            "Reinforce pre-performance neuro-cognitive routine and kinesthetic motor imagery visualization.",
            "Maintain SMR biofeedback conditioning to sustain peak motor cortex quietude prior to trigger pull / kinetic execution.",
            "Optimize autonomic nervous system coherence with targeted heart rate variability (HRV) sync protocols.",
            "Archive biopotential epoch as subject's idiosyncratic baseline for competitive mental performance profiling."
        ],
        "wave_params": {
            "base_freq": 13.5, "alpha_amp": 26.0, "beta_amp": 18.0, "theta_amp": 8.0, "delta_amp": 4.0, "noise": 2.0
        }
    },
    "case_16_myogenic_bruxism": {
        "id": "case_16_myogenic_bruxism",
        "patient_id": "PT-2026-016",
        "patient_name": "Alexander Vance (Age 34, M)",
        "category": "Artifacts & Pharmacological Effects",
        "name": "Severe Myogenic Bruxism & Temporalis Jaw Clenching Artifact (30-80 Hz EMG)",
        "dominant_freq": 45.0,
        "bands": {"delta": 8.0, "theta": 8.0, "alpha": 12.0, "beta": 72.0},
        "stress_index": 3.60,
        "tbr": 0.11,
        "abr": 0.17,
        "cognitive_load": "HIGH",
        "patient_condition": (
            "Massive high-amplitude (50-120 μV), high-frequency continuous sharp interference (30-80 Hz) completely obscuring underlying cortical biopotentials. "
            "Characteristic myogenic (EMG) artifact from masseter and temporalis muscle contraction."
        ),
        "patient_action_plan": [
            "Instruct patient to gently part teeth, relax jaw muscles, and drop the tongue from the roof of the mouth to eliminate EMG artifact.",
            "Dental evaluation for nocturnal custom occlusal splint (nightguard) to prevent enamel wear and TMJ arthralgia.",
            "Consider bilateral masseter therapeutic botulinum toxin injections if severe chronic myofascial clenching persists.",
            "Apply digital 30 Hz low-pass filter to inspect underlying residual cerebral rhythms once muscle relaxation is achieved."
        ],
        "wave_params": {
            "base_freq": 45.0, "alpha_amp": 6.0, "beta_amp": 12.0, "theta_amp": 4.0, "delta_amp": 4.0, "noise": 55.0, "emg_burst": True
        }
    },
    "case_17_ocular_blink_artifacts": {
        "id": "case_17_ocular_blink_artifacts",
        "patient_id": "PT-2026-017",
        "patient_name": "Sophia Martinez (Age 21, F)",
        "category": "Artifacts & Pharmacological Effects",
        "name": "High-Frequency Ocular Saccades & Bell's Blink Transients (Frontal Dipoles)",
        "dominant_freq": 1.0,
        "bands": {"delta": 68.0, "theta": 16.0, "alpha": 10.0, "beta": 6.0},
        "stress_index": 0.07,
        "tbr": 2.67,
        "abr": 1.67,
        "cognitive_load": "LOW",
        "patient_condition": (
            "Periodic high-amplitude monophasic positive deflections (80-220 μV, duration 200-400 ms) maximal at frontal leads. "
            "Caused by electro-retinal dipole rotation during Bell's phenomenon and involuntary eye blinks."
        ),
        "patient_action_plan": [
            "Guide patient to fixate eyes gently on a stationary central cross-hair target 1.5 meters away to minimize blink rate.",
            "Engage Independent Component Analysis (ICA) or automated EOG regression artifact subtraction in preprocessing pipeline.",
            "Check ophthalmic tear film stability; provide lubricating preservative-free artificial tears if dry eye irritations provoke blinks.",
            "Verify differential montage polarity (E1 - E2) to isolate true frontal cortical rhythms from corneal-retinal dipoles."
        ],
        "wave_params": {
            "base_freq": 1.0, "alpha_amp": 14.0, "beta_amp": 4.0, "theta_amp": 8.0, "delta_amp": 12.0, "noise": 2.5, "eog_blink": True
        }
    },
    "case_18_drowsiness_microsleep": {
        "id": "case_18_drowsiness_microsleep",
        "patient_id": "PT-2026-018",
        "patient_name": "Dmitri Volkov (Age 49, M)",
        "category": "Sleep & Circadian Disorders",
        "name": "Commercial Driver Somnolence & 3-Second Microsleep Lapses",
        "dominant_freq": 4.5,
        "bands": {"delta": 36.0, "theta": 48.0, "alpha": 10.0, "beta": 6.0},
        "stress_index": 0.09,
        "tbr": 8.00,
        "abr": 1.67,
        "cognitive_load": "FATIGUE",
        "patient_condition": (
            "Intermittent dropouts of posterior alpha rhythm replaced by diffuse, slow rolling eye movements and 2–4 second epochs of diffuse 4–6 Hz theta intrusion. "
            "Electrographic markers of stage N1 sleep transition and dangerous micro-sleep lapses."
        ),
        "patient_action_plan": [
            "Immediate safety override: Sound audible wakefulness alert and mandate immediate cessation of vehicle/machinery operation.",
            "Require minimum 20-30 minute restorative nap followed by 100-200 mg caffeine administration before resuming travel.",
            "Occupational health screening for obstructive sleep apnea (STOP-BANG questionnaire) and shift-work sleep disorder.",
            "Install in-cab gaze-tracking and biopotential somnolence monitors for safety-critical transportation operations."
        ],
        "wave_params": {
            "base_freq": 4.5, "alpha_amp": 6.0, "beta_amp": 3.0, "theta_amp": 34.0, "delta_amp": 26.0, "noise": 3.5, "microsleep": True
        }
    },
    "case_19_pharmacological_benzo": {
        "id": "case_19_pharmacological_benzo",
        "patient_id": "PT-2026-019",
        "patient_name": "Patricia Moore (Age 58, F)",
        "category": "Artifacts & Pharmacological Effects",
        "name": "Pharmacological Benzodiazepine Effect ('Beta Buzz' 18-26 Hz)",
        "dominant_freq": 21.0,
        "bands": {"delta": 8.0, "theta": 14.0, "alpha": 18.0, "beta": 60.0},
        "stress_index": 1.88,
        "tbr": 0.23,
        "abr": 0.30,
        "cognitive_load": "MODERATE",
        "patient_condition": (
            "Generalized, high-voltage rhythmic fast activity (18–26 Hz beta buzz, 25-45 μV) prominent over fronto-central derivations without subjective anxiety. "
            "Classic neuropharmacological signature of GABA-A receptor positive allosteric modulation."
        ),
        "patient_action_plan": [
            "Reconcile current pharmacological regimen: document specific agent, dosage, and last administration time (e.g., Lorazepam/Clonazepam).",
            "Counsel patient on additive sedative risks with alcohol, antihistamines, or opioid compounds and avoid machinery operation.",
            "If discontinuing, design a gradual tapering schedule (10-25% reduction every 1-2 weeks) to prevent rebound insomnia or withdrawal seizures.",
            "Note drug-induced fast activity in clinical report to avoid misinterpreting beta excess as psychological panic or hyperarousal."
        ],
        "wave_params": {
            "base_freq": 21.0, "alpha_amp": 10.0, "beta_amp": 36.0, "theta_amp": 7.0, "delta_amp": 4.0, "noise": 3.0
        }
    },
    "case_20_cerebral_hypoxia": {
        "id": "case_20_cerebral_hypoxia",
        "patient_id": "PT-2026-020",
        "patient_name": "Harold Simmons (Age 68, M)",
        "category": "Acute Critical Care Pathologies",
        "name": "Acute Cerebral Hypoxia / Ischemia (Severe Voltage Suppression < 15 μV)",
        "dominant_freq": 1.5,
        "bands": {"delta": 78.0, "theta": 14.0, "alpha": 6.0, "beta": 2.0},
        "stress_index": 0.03,
        "tbr": 7.00,
        "abr": 3.00,
        "cognitive_load": "HIGH",
        "patient_condition": (
            "Severe generalized voltage attenuation (<15 μV) across all electrode leads with intermittent polymorphic slow delta burst suppression. "
            "High-acuity finding indicating critical cerebral perfusion deficiency and cellular metabolic compromise."
        ),
        "patient_action_plan": [
            "EMERGENCY MEDICAL RESPONSE: Activate Rapid Response / Code Blue team; verify airway patency, 100% supplemental oxygen, and hemodynamic stability.",
            "Check arterial blood pressure, end-tidal CO2, and core body temperature; optimize mean arterial pressure (MAP > 75 mmHg).",
            "STAT arterial blood gas, cardiac troponin, bedside echocardiogram, and urgent neurological critical care consultation.",
            "Institute continuous qEEG monitoring for burst suppression ratio (BSR) tracking and neuroprotective hypothermia/normothermia protocol."
        ],
        "wave_params": {
            "base_freq": 1.5, "alpha_amp": 2.0, "beta_amp": 1.0, "theta_amp": 4.0, "delta_amp": 8.0, "noise": 1.0, "hypoxia": True
        }
    },
    "case_21_alzheimers_dementia": {
        "id": "case_21_alzheimers_dementia",
        "patient_id": "PT-2026-021",
        "patient_name": "Arthur Pendelton (Age 76, M)",
        "category": "Neurological & Neurodegenerative Disorders",
        "name": "Alzheimer's Disease / Dementia (Severe Diffuse Slowing & Alpha Disappearance)",
        "dominant_freq": 5.2,
        "bands": {"delta": 42.0, "theta": 40.0, "alpha": 12.0, "beta": 6.0},
        "stress_index": 0.14,
        "tbr": 6.67,
        "abr": 2.00,
        "cognitive_load": "HIGH",
        "patient_condition": (
            "Severe generalized slowing with progressive loss of posterior alpha rhythm replaced by diffuse 4-6 Hz theta and polymorphic delta waves. "
            "Prominent anteriorization of background activity reflecting cortical degeneration, synaptic loss, and severe executive-memory impairment."
        ),
        "patient_action_plan": [
            "Initiate cholinesterase inhibitor optimization (donepezil or rivastigmine) and consider NMDA receptor antagonist (memantine).",
            "Schedule high-resolution volumetric 3T MRI to quantify hippocampal and entorhinal cortex atrophy.",
            "Implement structured neuro-supportive cognitive stimulation routines and fall-prevention environmental modifications.",
            "Enroll caregiver in respite assistance and conduct periodic quantitative EEG tracking of theta/alpha slowing ratios."
        ],
        "wave_params": {
            "base_freq": 5.2, "alpha_amp": 5.0, "beta_amp": 3.0, "theta_amp": 28.0, "delta_amp": 32.0, "noise": 3.5
        }
    },
    "case_22_parkinsons_resting_tremor": {
        "id": "case_22_parkinsons_resting_tremor",
        "patient_id": "PT-2026-022",
        "patient_name": "Evelyn Wright (Age 64, F)",
        "category": "Neurological & Neurodegenerative Disorders",
        "name": "Parkinson's Disease (4-6 Hz Basal Ganglia-Cortical Tremor Coupling & Beta Deficit)",
        "dominant_freq": 4.8,
        "bands": {"delta": 18.0, "theta": 48.0, "alpha": 22.0, "beta": 12.0},
        "stress_index": 0.25,
        "tbr": 4.00,
        "abr": 2.18,
        "cognitive_load": "MODERATE",
        "patient_condition": (
            "Rhythmic 4-6 Hz central theta-delta slow waves with intermittent harmonic myogenic tremor artifact phase-locked to contralateral pill-rolling resting tremor. "
            "Suppression of sensorimotor rhythm (SMR) and excessive pathological beta synchrony bursts indicating dopaminergic basal ganglia dysfunction."
        ),
        "patient_action_plan": [
            "Review dopaminergic titration (Levodopa/Carbidopa or dopamine agonists) targeting motor 'off' time reduction.",
            "Conduct dual EMG-EEG coherence mapping to assess subthalamic nucleus oscillatory entrainment.",
            "Screen for Deep Brain Stimulation (DBS) candidacy targeting STN or GPi if motor fluctuations become medically refractory.",
            "Prescribe specialized physical and occupational therapy focusing on gait cadence, balance, and cueing strategies."
        ],
        "wave_params": {
            "base_freq": 4.8, "alpha_amp": 12.0, "beta_amp": 8.0, "theta_amp": 32.0, "delta_amp": 14.0, "noise": 4.0, "tremor_hz": 5.0
        }
    },
    "case_23_creutzfeldt_jakob": {
        "id": "case_23_creutzfeldt_jakob",
        "patient_id": "PT-2026-023",
        "patient_name": "Heinrich Hoffman (Age 62, M)",
        "category": "Neurological & Neurodegenerative Disorders",
        "name": "Prion Encephalopathy / Creutzfeldt-Jakob Disease (Periodic Sharp Wave Complexes 1.0 Hz)",
        "dominant_freq": 1.0,
        "bands": {"delta": 62.0, "theta": 24.0, "alpha": 10.0, "beta": 4.0},
        "stress_index": 0.06,
        "tbr": 6.00,
        "abr": 2.40,
        "cognitive_load": "HIGH",
        "patient_condition": (
            "Bilateral, synchronous, bisynchronous periodic sharp wave complexes (PSWC) recurring rhythmically every 0.8-1.2 seconds (approx 1.0 Hz) over a slow and suppressed background rhythm. "
            "Pathognomonic biopotential hallmark of rapid cortical neurodegeneration and prion pathology."
        ),
        "patient_action_plan": [
            "URGENT NEUROLOGICAL ADMISSION: Initiate isolation barrier precautions and expedited diagnostic workup for rapidly progressive dementia.",
            "Perform lumbar puncture for CSF RT-QuIC (real-time quaking-induced conversion) assay and 14-3-3 protein analysis.",
            "Order emergency diffusion-weighted MRI (DWI) to detect cortical ribboning and basal ganglia hyperintensities (hockey-stick sign).",
            "Engage palliative care team and family counseling for comprehensive supportive management and comfort measures."
        ],
        "wave_params": {
            "base_freq": 1.0, "alpha_amp": 4.0, "beta_amp": 2.0, "theta_amp": 14.0, "delta_amp": 45.0, "noise": 3.0, "pswc_period": 1.0, "pswc_amp": 90.0
        }
    },
    "case_24_status_epilepticus": {
        "id": "case_24_status_epilepticus",
        "patient_id": "PT-2026-024",
        "patient_name": "Amara Diallo (Age 38, F)",
        "category": "Acute Critical Care Pathologies",
        "name": "Non-Convulsive Status Epilepticus (NCSE Continuous 2.5 Hz Spike-Wave Discharge)",
        "dominant_freq": 2.5,
        "bands": {"delta": 54.0, "theta": 30.0, "alpha": 10.0, "beta": 6.0},
        "stress_index": 0.20,
        "tbr": 5.00,
        "abr": 3.00,
        "cognitive_load": "HIGH",
        "patient_condition": (
            "Continuous, generalized, rhythmic 2.5-3.0 Hz spike-and-slow-wave discharges exceeding 100 μV lasting without interictal recovery in a patient with altered mental status. "
            "Confirms non-convulsive status epilepticus requiring immediate emergent pharmacological termination."
        ),
        "patient_action_plan": [
            "CRITICAL MEDICAL EMERGENCY: Administer first-line IV benzodiazepine (IV Lorazepam 4 mg or Midazolam 10 mg IM STAT).",
            "Immediately load second-line non-sedating antiepileptic therapy (IV Levetiracetam 60 mg/kg or Fosphenytoin 20 mg PE/kg).",
            "Prepare for ICU endotracheal intubation and continuous anesthetic infusion (Propofol or Midazolam) if electrographic discharges persist beyond 30 min.",
            "Establish continuous qEEG telemetry to titrate pharmacotherapy toward electrographic burst-suppression."
        ],
        "wave_params": {
            "base_freq": 2.5, "alpha_amp": 6.0, "beta_amp": 8.0, "theta_amp": 24.0, "delta_amp": 50.0, "noise": 3.0, "ncse_spike": True
        }
    },
    "case_25_severe_tbi_burst_suppression": {
        "id": "case_25_severe_tbi_burst_suppression",
        "patient_id": "PT-2026-025",
        "patient_name": "Jack Sterling (Age 23, M)",
        "category": "Acute Critical Care Pathologies",
        "name": "Severe Traumatic Brain Injury & Coma (Burst-Suppression Pattern)",
        "dominant_freq": 0.8,
        "bands": {"delta": 82.0, "theta": 12.0, "alpha": 4.0, "beta": 2.0},
        "stress_index": 0.02,
        "tbr": 6.00,
        "abr": 3.00,
        "cognitive_load": "HIGH",
        "patient_condition": (
            "Alternating sequence of high-voltage (75-150 μV) mixed delta-theta polyspike bursts lasting 1-3 seconds followed by generalized isoelectric flatline suppression (<5 μV) lasting 4-10 seconds. "
            "Reflects critical cerebral metabolic depression, severe structural brain injury, or deep therapeutic anesthesia."
        ),
        "patient_action_plan": [
            "NEURO-ICU CRITICAL MANAGEMENT: Maintain continuous multimodality neuromonitoring (ICP bolt, cerebral perfusion pressure CPP > 60 mmHg, PbtO2).",
            "Calculate real-time Burst Suppression Ratio (BSR %) to titrate neuroprotective barbiturate or propofol coma.",
            "Monitor serial pupillometry and repeat emergent non-contrast head CT for herniation, midline shift, or expanding contusion.",
            "Optimize arterial normocapnia (PaCO2 35-40 mmHg) and strict normothermia (36.0-37.0 °C)."
        ],
        "wave_params": {
            "base_freq": 0.8, "alpha_amp": 1.0, "beta_amp": 1.0, "theta_amp": 4.0, "delta_amp": 12.0, "noise": 1.0, "burst_suppression": True
        }
    },
    "case_26_intracranial_hypertension": {
        "id": "case_26_intracranial_hypertension",
        "patient_id": "PT-2026-026",
        "patient_name": "Victoria Zhao (Age 51, F)",
        "category": "Acute Critical Care Pathologies",
        "name": "Acute Intracranial Hypertension (Generalized Monomorphic Delta Slowing)",
        "dominant_freq": 1.6,
        "bands": {"delta": 68.0, "theta": 22.0, "alpha": 7.0, "beta": 3.0},
        "stress_index": 0.04,
        "tbr": 7.33,
        "abr": 3.14,
        "cognitive_load": "HIGH",
        "patient_condition": (
            "Generalized, continuous, monomorphic delta slowing (1.2-2.0 Hz) without normal sleep architecture or alpha reactivity, accompanied by blunted cortical responsiveness to external auditory stimuli. "
            "Suggests acute intracranial mass effect, severe edema, or elevated ICP > 25 mmHg."
        ),
        "patient_action_plan": [
            "URGENT NEUROSURGICAL PROTOCOL: Elevate head of bed to 30 degrees and maintain neutral neck alignment to optimize jugular venous drainage.",
            "Administer hyperosmolar therapy STAT (Hypertonic Saline 3% 250 mL IV or Mannitol 1 g/kg IV).",
            "Prepare emergency CT head and neurosurgical operating room for possible emergent decompressive craniectomy or EVD ventriculostomy.",
            "Institute continuous arterial line blood pressure monitoring and avoid hypotonic intravenous fluids."
        ],
        "wave_params": {
            "base_freq": 1.6, "alpha_amp": 3.0, "beta_amp": 2.0, "theta_amp": 16.0, "delta_amp": 60.0, "noise": 3.0
        }
    },
    "case_27_bipolar_mania": {
        "id": "case_27_bipolar_mania",
        "patient_id": "PT-2026-027",
        "patient_name": "Liam Gallagher (Age 27, M)",
        "category": "Psychiatric & Behavioral Disorders",
        "name": "Bipolar I Disorder / Acute Mania (Hyper-Synchronous Beta-Gamma Activation 32 Hz)",
        "dominant_freq": 31.5,
        "bands": {"delta": 5.0, "theta": 10.0, "alpha": 15.0, "beta": 70.0},
        "stress_index": 2.80,
        "tbr": 0.14,
        "abr": 0.21,
        "cognitive_load": "HIGH",
        "patient_condition": (
            "Extreme cortical hyper-excitability characterized by persistent, diffuse high-frequency beta and low gamma synchronization (28-36 Hz) with complete loss of eyes-closed posterior alpha rhythm. "
            "Reflects severe psychomotor agitation, racing thoughts, insomnia, and noradrenergic-dopaminergic hyperactivity."
        ),
        "patient_action_plan": [
            "Ensure secure, low-stimulus psychiatric inpatient environment to de-escalate psychomotor agitation and sensory overload.",
            "Initiate or optimize mood stabilizer therapy (Lithium or Valproate) co-administered with a rapid-acting atypical antipsychotic (e.g., Olanzapine or Quetiapine).",
            "Conduct comprehensive toxicology screen to exclude secondary stimulant-induced or substance-induced manic states.",
            "Track circadian sleep patterns and biopotential fast-frequency spectral power reduction across pharmacological stabilization."
        ],
        "wave_params": {
            "base_freq": 31.5, "alpha_amp": 4.0, "beta_amp": 45.0, "theta_amp": 3.0, "delta_amp": 2.0, "noise": 6.0
        }
    },
    "case_28_schizophrenia_gamma_deficit": {
        "id": "case_28_schizophrenia_gamma_deficit",
        "patient_id": "PT-2026-028",
        "patient_name": "Tariq Mansoor (Age 24, M)",
        "category": "Psychiatric & Behavioral Disorders",
        "name": "Schizophrenia / First-Episode Psychosis (Attenuated 40 Hz Auditory Gamma Evoked Synchrony)",
        "dominant_freq": 6.2,
        "bands": {"delta": 22.0, "theta": 46.0, "alpha": 20.0, "beta": 12.0},
        "stress_index": 0.26,
        "tbr": 3.83,
        "abr": 2.30,
        "cognitive_load": "MODERATE",
        "patient_condition": (
            "Attenuated evoked 40 Hz gamma-band phase locking following auditory steady-state stimulation combined with diffuse baseline theta excess and fragmented alpha rhythm. "
            "Indicates parvalbumin GABAergic interneuron hypo-functioning and disrupted thalamocortical microcircuit gating."
        ),
        "patient_action_plan": [
            "Comprehensive psychiatric evaluation with PANSS scoring for positive, negative, and cognitive symptom dimensions.",
            "Initiate evidence-based second-generation antipsychotic therapy (e.g., Aripiprazole, Risperidone) with metabolic profile monitoring.",
            "Perform 40 Hz Auditory Steady-State Response (ASSR) test to objectively index cortical auditory circuit integrity.",
            "Integrate cognitive behavioral therapy for psychosis (CBTp) and supportive family psychoeducation programs."
        ],
        "wave_params": {
            "base_freq": 6.2, "alpha_amp": 10.0, "beta_amp": 7.0, "theta_amp": 28.0, "delta_amp": 16.0, "noise": 4.5, "gamma_deficit": True
        }
    },
    "case_29_rem_sleep_behavior_disorder": {
        "id": "case_29_rem_sleep_behavior_disorder",
        "patient_id": "PT-2026-029",
        "patient_name": "Gunnar Lindholm (Age 67, M)",
        "category": "Sleep & Circadian Disorders",
        "name": "REM Sleep Behavior Disorder / RBD (REM Without Atonia & Submentalis Hypertonia)",
        "dominant_freq": 6.8,
        "bands": {"delta": 18.0, "theta": 44.0, "alpha": 22.0, "beta": 16.0},
        "stress_index": 0.36,
        "tbr": 2.75,
        "abr": 2.00,
        "cognitive_load": "MODERATE",
        "patient_condition": (
            "Desynchronized, mixed low-voltage theta/alpha cortical activity typical of REM sleep accompanied by abnormal persistent, high-amplitude submentalis and limb EMG muscle bursts ('REM sleep without atonia' - RSWA). "
            "Associated with violent dream enactment behavior and alpha-synucleinopathy risk."
        ),
        "patient_action_plan": [
            "Implement immediate bedroom safety modifications (bed rails, removing nightstands/sharp objects, floor mattress padding).",
            "Initiate first-line pharmacotherapy with low-dose Clonazepam (0.5-1.0 mg at bedtime) or high-dose oral Melatonin (3-12 mg).",
            "Counsel patient on long-term neurological surveillance for emerging neurodegenerative synucleinopathies (Parkinson's disease, DLB).",
            "Conduct annual UPDRS motor and cognitive MoCA screening."
        ],
        "wave_params": {
            "base_freq": 6.8, "alpha_amp": 12.0, "beta_amp": 10.0, "theta_amp": 26.0, "delta_amp": 12.0, "noise": 4.0, "emg_artifact": True
        }
    },
    "case_30_severe_obstructive_sleep_apnea": {
        "id": "case_30_severe_obstructive_sleep_apnea",
        "patient_id": "PT-2026-030",
        "patient_name": "Bruce MacIntyre (Age 53, M)",
        "category": "Sleep & Circadian Disorders",
        "name": "Severe Obstructive Sleep Apnea (AHI > 45, Cyclic Delta Slowing & Cortical Arousals)",
        "dominant_freq": 3.2,
        "bands": {"delta": 50.0, "theta": 28.0, "alpha": 12.0, "beta": 10.0},
        "stress_index": 0.35,
        "tbr": 2.80,
        "abr": 2.33,
        "cognitive_load": "MODERATE",
        "patient_condition": (
            "Cyclic electroencephalographic pattern consisting of 20-40 second periods of progressive delta-theta slowing during obstructive hypopnea/apnea abruptly terminated by sudden 3-10 second burst of fast alpha-beta activity and muscle artifact corresponding to sympathetic cortical arousal."
        ),
        "patient_action_plan": [
            "Immediate initiation of nocturnal Positive Airway Pressure (CPAP / Auto-PAP) therapy with telemetry compliance tracking.",
            "Comprehensive sleep clinic consultation for mask fitting, humidification optimization, and positional therapy.",
            "Cardiovascular risk evaluation: 24-hour ambulatory blood pressure monitoring and nocturnal pulse oximetry titration.",
            "Weight management, metabolic screening, and occupational driving safety restriction pending CPAP adherence."
        ],
        "wave_params": {
            "base_freq": 3.2, "alpha_amp": 8.0, "beta_amp": 8.0, "theta_amp": 22.0, "delta_amp": 42.0, "noise": 4.0, "apnea_cycle": True
        }
    },
    "case_31_fatal_insomnia_thalamectomy": {
        "id": "case_31_fatal_insomnia_thalamectomy",
        "patient_id": "PT-2026-031",
        "patient_name": "Miriam Adler (Age 48, F)",
        "category": "Sleep & Circadian Disorders",
        "name": "Severe Chronic Insomnia Disorder (Complete Loss of Delta Slow Waves & Spindle Depletion)",
        "dominant_freq": 18.5,
        "bands": {"delta": 8.0, "theta": 16.0, "alpha": 26.0, "beta": 50.0},
        "stress_index": 1.92,
        "tbr": 0.32,
        "abr": 0.62,
        "cognitive_load": "MODERATE",
        "patient_condition": (
            "Marked nocturnal electrographic hyperarousal: profound depletion of stage N2 sleep spindles (12-14 Hz) and total absence of synchronized slow delta sleep (<10%), replaced by unrelenting low-voltage fast beta activity and autonomic micro-arousals throughout the night."
        ),
        "patient_action_plan": [
            "Prescribe Cognitive Behavioral Therapy for Insomnia (CBT-I) as the first-line intervention.",
            "Consider Dual Orexin Receptor Antagonists (DORA, e.g., Suvorexant, Lemborexant) to selectively promote sleep drive without GABAergic distortion.",
            "Strict circadian realignment: light therapy in early morning and complete blue-light filtering 2 hours prior to scheduled sleep.",
            "Perform polysomnography and neuroendocrine screening (24-hour salivary cortisol and thyroid panel)."
        ],
        "wave_params": {
            "base_freq": 18.5, "alpha_amp": 14.0, "beta_amp": 32.0, "theta_amp": 10.0, "delta_amp": 5.0, "noise": 3.0
        }
    },
    "case_32_tms_entrainment_10hz": {
        "id": "case_32_tms_entrainment_10hz",
        "patient_id": "PT-2026-032",
        "patient_name": "Jonathan Cruz (Age 35, M)",
        "category": "Neuromodulation & Brain Stimulation",
        "name": "Transcranial Magnetic Stimulation (Phase-Locked 10.0 Hz rTMS Alpha Entrainment)",
        "dominant_freq": 10.0,
        "bands": {"delta": 8.0, "theta": 12.0, "alpha": 68.0, "beta": 12.0},
        "stress_index": 0.17,
        "tbr": 1.00,
        "abr": 5.67,
        "cognitive_load": "LOW",
        "patient_condition": (
            "High-amplitude, highly coherent 10.0 Hz sinusoidal oscillations across left dorsolateral prefrontal cortex (DLPFC) induced by repetitive TMS neuromodulation. "
            "Evidences successful thalamocortical alpha resonance entrainment and enhanced neuroplastic plasticity."
        ),
        "patient_action_plan": [
            "Verify coil positioning via stereotactic neuronavigation over F3 (left DLPFC) at 120% motor threshold.",
            "Administer standardized 3,000-pulse therapeutic protocol (75 trains of 40 pulses at 10 Hz with 26-second inter-train intervals).",
            "Record post-treatment resting EEG to evaluate durability of frontal alpha coherence and mood elevation.",
            "Monitor for scalp discomfort, transient headache, and screen meticulously for contraindications (metallic implants, history of seizures)."
        ],
        "wave_params": {
            "base_freq": 10.0, "alpha_amp": 48.0, "beta_amp": 8.0, "theta_amp": 7.0, "delta_amp": 5.0, "noise": 2.0, "rtms_burst": True
        }
    },
    "case_33_tdcs_anodal_prefrontal": {
        "id": "case_33_tdcs_anodal_prefrontal",
        "patient_id": "PT-2026-033",
        "patient_name": "Chloe Moreau (Age 31, F)",
        "category": "Neuromodulation & Brain Stimulation",
        "name": "Anodal transcranial Direct Current Stimulation (tDCS Prefrontal Excitability & Beta Power)",
        "dominant_freq": 22.0,
        "bands": {"delta": 10.0, "theta": 15.0, "alpha": 25.0, "beta": 50.0},
        "stress_index": 1.25,
        "tbr": 0.30,
        "abr": 1.67,
        "cognitive_load": "MODERATE",
        "patient_condition": (
            "Prefrontal cortical excitability elevation induced by 2.0 mA anodal tDCS over F3/Fp1. Characterized by localized enhancement of 18-24 Hz beta power and reduction in slow-frequency delta/theta power, indicative of enhanced working memory encoding and cognitive control."
        ),
        "patient_action_plan": [
            "Confirm electrode impedance < 5 kΩ using isotonic saline sponge electrodes before ramping up current.",
            "Deliver 2.0 mA constant direct current for 20 minutes concurrent with working memory n-back training tasks.",
            "Check skin beneath electrode pads pre- and post-stimulation for irritation or electrochemical burns.",
            "Log subjective cognitive workload and track sustained enhancement of executive attention on objective test batteries."
        ],
        "wave_params": {
            "base_freq": 22.0, "alpha_amp": 16.0, "beta_amp": 34.0, "theta_amp": 9.0, "delta_amp": 6.0, "noise": 3.0
        }
    },
    "case_34_psychedelic_psilocybin_entropy": {
        "id": "case_34_psychedelic_psilocybin_entropy",
        "patient_id": "PT-2026-034",
        "patient_name": "Dante Rossi (Age 40, M)",
        "category": "Neuromodulation & Brain Stimulation",
        "name": "Serotonergic Psychedelic State (Psilocybin Induced Alpha Collapse & High Neural Entropy)",
        "dominant_freq": 7.4,
        "bands": {"delta": 24.0, "theta": 42.0, "alpha": 14.0, "beta": 20.0},
        "stress_index": 0.47,
        "tbr": 2.10,
        "abr": 0.33,
        "cognitive_load": "HIGH",
        "patient_condition": (
            "Profound suppression and disintegration of posterior alpha power (REBUS model) coupled with expanded broadband high-entropy oscillatory dynamics (theta-gamma cross-frequency decoupling). "
            "Reflects 5-HT2A receptor activation, dissolution of Default Mode Network (DMN) rigidity, and heightened cortical entropy."
        ),
        "patient_action_plan": [
            "Provide calm, continuous psychotherapeutic guiding presence in a controlled, supportive sensory room.",
            "Monitor non-invasive biometrics (blood pressure, ECG rhythm, and galvanic skin response) every 30 minutes.",
            "Maintain low ambient lighting, curated acoustic support, and non-judgmental reassurance during peak conscious dissolution.",
            "Schedule post-session integration therapy 24 hours post-administration to translate neuroplastic insights into durable behavior change."
        ],
        "wave_params": {
            "base_freq": 7.4, "alpha_amp": 8.0, "beta_amp": 14.0, "theta_amp": 26.0, "delta_amp": 16.0, "noise": 6.5, "entropy": True
        }
    },
    "case_35_acute_cannabinoid_intoxication": {
        "id": "case_35_acute_cannabinoid_intoxication",
        "patient_id": "PT-2026-035",
        "patient_name": "Keanu Reeves (Simulation Proxy) (Age 28, M)",
        "category": "Artifacts & Pharmacological Effects",
        "name": "Acute Cannabinoid CB1 Modulation (Frontal Theta Shift, Alpha Attenuation & Temporal Distortion)",
        "dominant_freq": 5.5,
        "bands": {"delta": 20.0, "theta": 50.0, "alpha": 18.0, "beta": 12.0},
        "stress_index": 0.24,
        "tbr": 4.17,
        "abr": 0.36,
        "cognitive_load": "LOW",
        "patient_condition": (
            "Prominent increase in fronto-central theta power (4-7 Hz) accompanied by moderate reduction in posterior alpha peak frequency and amplitude. "
            "Signature of retrograde endocannabinoid CB1 receptor agonism, causing impaired short-term memory encoding, spatial disorientation, and subjective temporal elongation."
        ),
        "patient_action_plan": [
            "Observe in quiet recovery suite until acute psychoactive peak subsides (typically 2-4 hours post-exposure).",
            "Advise absolute prohibition of motor vehicle driving or operating safety-critical equipment for a minimum of 8-12 hours.",
            "Offer oral hydration and reassurance in case of transient cannabis-induced anxiety or orthostatic tachycardia.",
            "Conduct follow-up cognitive evaluation for cannabis use disorder screening if repeated intoxication episodes occur."
        ],
        "wave_params": {
            "base_freq": 5.5, "alpha_amp": 11.0, "beta_amp": 8.0, "theta_amp": 32.0, "delta_amp": 14.0, "noise": 3.5
        }
    }
}

def get_all_conditions() -> Dict[str, Dict[str, Any]]:
    """Return all 35 patient condition definitions."""
    return PATIENT_CONDITIONS

def get_condition(condition_id: str) -> Dict[str, Any]:
    """Retrieve condition by ID, fallback to resting baseline if not found."""
    return PATIENT_CONDITIONS.get(condition_id, PATIENT_CONDITIONS["case_01_resting_baseline"])

