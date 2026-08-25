"""
BIDS-EEG Export Module — NeuroSim 2.0
Exports session data to BIDS (Brain Imaging Data Structure) format for interoperability
with EEGLAB, MNE-Python, FieldTrip, and other neuroscience tools.

BIDS-EEG Specification: https://bids-specification.readthedocs.io/en/stable/modality-specific-files/electroencephalography.html
"""

import os
import json
from datetime import datetime
from typing import Dict, Any, List, Optional


class BIDSEXporter:
    """
    Exports NeuroSim session data to BIDS-EEG format.
    Creates proper directory structure, metadata files, and data files.
    """
    
    def __init__(self, output_dir: str = "bids_exports"):
        self.output_dir = output_dir
        os.makedirs(output_dir, exist_ok=True)
    
    def export_session(self, session_data: Dict[str, Any], bids_root: Optional[str] = None) -> str:
        """Export a single session to BIDS format."""
        if bids_root is None:
            subject_id = session_data.get('user_id', 'anonymous')
            session_id = session_data.get('session_id', '001')
            bids_root = os.path.join(
                self.output_dir,
                f"sub-{subject_id}",
                f"ses-{session_id}"
            )
        
        eeg_dir = os.path.join(bids_root, "eeg")
        os.makedirs(eeg_dir, exist_ok=True)
        
        subject = session_data.get('user_id', 'anonymous').replace('_', '-')
        session = session_data.get('session_id', '001').replace('_', '-')
        base_filename = f"sub-{subject}_ses-{session}_task-eeg_eeg"
        
        self._write_eeg_data(session_data, eeg_dir, base_filename)
        self._write_eeg_sidecar(session_data, eeg_dir, base_filename)
        self._write_channels_info(session_data, eeg_dir, base_filename)
        self._write_events(session_data, eeg_dir, base_filename)
        self._write_dataset_description(os.path.dirname(os.path.dirname(bids_root)))
        self._write_participants(session_data, os.path.dirname(os.path.dirname(bids_root)))
        self._write_readme(session_data, bids_root)
        
        return bids_root
    
    def _write_eeg_data(self, session_data: Dict[str, Any], eeg_dir: str, base_filename: str):
        """Write EEG time series data to TSV file."""
        filepath = os.path.join(eeg_dir, f"{base_filename}.tsv")
        sampling_rate = session_data.get('sampling_rate', 250)
        duration = session_data.get('duration', 60.0)
        channel_count = session_data.get('channel_count', 8)
        eeg_data = session_data.get('eeg_data', None)
        
        with open(filepath, 'w') as f:
            channels = session_data.get('channel_names', [f'EEG{i:03d}' for i in range(1, channel_count + 1)])
            header = '\t'.join(['timestamp'] + channels)
            f.write(header + '\n')
            
            if eeg_data:
                import numpy as np
                eeg_array = np.array(eeg_data)
                n_samples = eeg_array.shape[0] if eeg_array.ndim > 1 else len(eeg_array)
                for i in range(n_samples):
                    timestamp = i / sampling_rate
                    if eeg_array.ndim > 1:
                        values = '\t'.join([f"{v:.6f}" for v in eeg_array[i]])
                    else:
                        values = f"{eeg_array[i]:.6f}"
                    f.write(f"{timestamp:.6f}\t{values}\n")
            else:
                f.write(f"# Placeholder: {int(duration * sampling_rate)} samples expected\n")
    
    def _write_eeg_sidecar(self, session_data: Dict[str, Any], eeg_dir: str, base_filename: str):
        """Create EEG sidecar JSON with required BIDS metadata."""
        filepath = os.path.join(eeg_dir, f"{base_filename}.json")
        sidecar = {
            "TaskName": session_data.get('protocol_name', 'eeg'),
            "Manufacturer": session_data.get('manufacturer', 'NeuroSim'),
            "SamplingFrequency": float(session_data.get('sampling_rate', 250)),
            "PowerLineFrequency": session_data.get('power_line_freq', 50),
            "EEGChannelCount": session_data.get('channel_count', 8),
            "EEGReference": session_data.get('reference', 'Cz'),
            "RecordingType": session_data.get('recording_type', 'continuous'),
        }
        with open(filepath, 'w') as f:
            json.dump(sidecar, f, indent=2)
    
    def _write_channels_info(self, session_data: Dict[str, Any], eeg_dir: str, base_filename: str):
        """Create channels TSV file."""
        filepath = os.path.join(eeg_dir, f"{base_filename}_channels.tsv")
        channel_count = session_data.get('channel_count', 8)
        channel_names = session_data.get('channel_names', [f'EEG{i:03d}' for i in range(1, channel_count + 1)])
        
        with open(filepath, 'w') as f:
            f.write("name\ttype\tunits\tx\ty\tz\treference\n")
            for ch_name in channel_names:
                f.write(f"{ch_name}\tEEG\tµV\t0.0\t0.0\t0.0\tCz\n")
    
    def _write_events(self, session_data: Dict[str, Any], eeg_dir: str, base_filename: str):
        """Create events TSV file."""
        filepath = os.path.join(eeg_dir, f"{base_filename}_events.tsv")
        events = session_data.get('events', [])
        
        with open(filepath, 'w') as f:
            f.write("onset\tduration\tvalue\tsample\ttrial_type\n")
            for event in events:
                onset = event.get('onset', 0.0)
                f.write(f"{onset:.6f}\t0.0\t{event.get('value', '')}\t{event.get('sample', 0)}\t{event.get('trial_type', 'marker')}\n")
    
    def _write_dataset_description(self, bids_root: str):
        """Create dataset_description.json."""
        filepath = os.path.join(bids_root, "dataset_description.json")
        description = {
            "Name": "NeuroSim EEG Research Dataset",
            "BIDSVersion": "1.8.0",
            "DatasetType": "raw",
            "License": "CC0",
            "Authors": ["NeuroSim Research Team"],
        }
        with open(filepath, 'w') as f:
            json.dump(description, f, indent=2)
    
    def _write_participants(self, session_data: Dict[str, Any], bids_root: str):
        """Create participants.tsv file."""
        filepath = os.path.join(bids_root, "participants.tsv")
        subject_id = session_data.get('user_id', 'anonymous')
        write_header = not os.path.exists(filepath)
        
        with open(filepath, 'a') as f:
            if write_header:
                f.write("participant_id\tage\tsex\thandedness\n")
            f.write(f"sub-{subject_id}\tN/A\tN/A\tN/A\n")
    
    def _write_readme(self, session_data: Dict[str, Any], bids_root: str):
        """Create README file."""
        filepath = os.path.join(bids_root, "README")
        content = f"""# NeuroSim BIDS Export
Subject: sub-{session_data.get('user_id', 'anonymous')}
Session: ses-{session_data.get('session_id', '001')}
Date: {session_data.get('timestamp', 'N/A')}
Channels: {session_data.get('channel_count', 8)}
Sampling Rate: {session_data.get('sampling_rate', 250)} Hz
"""
        with open(filepath, 'w') as f:
            f.write(content)
    
    def validate_bids_structure(self, bids_root: str) -> Dict[str, Any]:
        """Validate BIDS directory structure."""
        results = {'valid': True, 'errors': [], 'warnings': [], 'files_found': []}
        
        required_files = [
            os.path.join(os.path.dirname(os.path.dirname(bids_root)), "dataset_description.json"),
            os.path.join(os.path.dirname(os.path.dirname(bids_root)), "participants.tsv"),
        ]
        
        eeg_dir = os.path.join(bids_root, "eeg")
        if os.path.exists(eeg_dir):
            files = os.listdir(eeg_dir)
            results['files_found'].extend([os.path.join(eeg_dir, f) for f in files])
            if not any(f.endswith('.json') for f in files):
                results['warnings'].append("Missing EEG sidecar JSON")
        else:
            results['errors'].append("Missing eeg/ directory")
            results['valid'] = False
        
        for req in required_files:
            if os.path.exists(req):
                results['files_found'].append(req)
            else:
                results['errors'].append(f"Missing: {req}")
                results['valid'] = False
        
        return results
