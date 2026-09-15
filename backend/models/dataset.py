import pandas as pd
import numpy as np
import torch
from torch.utils.data import Dataset
from pathlib import Path

class WispDataset(Dataset):
    def __init__(self, parquet_path, history_len=12, max_rows=None, fraction=1.0):
        print(f"Loading {parquet_path}...")
        self.df = pd.read_parquet(parquet_path)
            
        if max_rows is not None and len(self.df) > max_rows:
            self.df = self.df.iloc[:max_rows]
        self.history_len = history_len
        
        self.state_cols = ["Indoor_AverageTemperature", "Indoor_Humidity", "Thermostat_DetectedMotion"]
        self.action_cols = ["HeatingEquipmentStage1_RunTime", "CoolingEquipmentStage1_RunTime", "Fan_RunTime", "Indoor_HeatSetpoint", "Indoor_CoolSetpoint"]
        self.dist_cols = ["Outdoor_Temperature", "Outdoor_Humidity", "hour_sin", "hour_cos", "day_sin", "day_cos"]
        
        print("Computing valid sliding windows...")
        seq_ids = self.df["sequence_id"].values
        valid_mask = np.zeros(len(self.df), dtype=bool)
        if len(self.df) >= history_len:
            # A window ending at i is valid if the sequence ID at i is the same as the sequence ID at i - history_len + 1
            valid_mask[history_len - 1:] = (seq_ids[history_len - 1:] == seq_ids[:-history_len + 1])
            
        self.valid_indices = np.where(valid_mask)[0]
        
        # Subsample valid indices evenly across the entire dataset to preserve all weather patterns!
        if fraction < 1.0:
            step = int(1.0 / fraction)
            self.valid_indices = self.valid_indices[::step]
            print(f"Uniformly subsampled valid sequences to {fraction*100:.1f}% (spanning all seasons!) -> {len(self.valid_indices)} sequences.")
        
        # Filter existing columns
        self.state_cols = [c for c in self.state_cols if c in self.df.columns]
        self.action_cols = [c for c in self.action_cols if c in self.df.columns]
        self.dist_cols = [c for c in self.dist_cols if c in self.df.columns]
        
        self.states = torch.tensor(self.df[self.state_cols].fillna(0).values, dtype=torch.float32)
        self.actions = torch.tensor(self.df[self.action_cols].fillna(0).values, dtype=torch.float32)
        self.dists = torch.tensor(self.df[self.dist_cols].fillna(0).values, dtype=torch.float32)
        
        target_cols = [
            "target_Indoor_Temperature_plus_5m", "target_Indoor_Humidity_plus_5m",
            "target_Indoor_Temperature_plus_15m", "target_Indoor_Humidity_plus_15m",
            "target_Indoor_Temperature_plus_30m", "target_Indoor_Humidity_plus_30m"
        ]
        self.target_cols = [c for c in target_cols if c in self.df.columns]
        self.targets = torch.tensor(self.df[self.target_cols].fillna(0).values, dtype=torch.float32)
        
        print(f"Dataset ready: {len(self.valid_indices)} valid sequences.")

    def __len__(self):
        return len(self.valid_indices)
        
    def __getitem__(self, idx):
        end_idx = self.valid_indices[idx]
        start_idx = end_idx - self.history_len + 1
        
        hist_s = self.states[start_idx:end_idx+1]
        hist_a = self.actions[start_idx:end_idx+1]
        hist_d = self.dists[start_idx:end_idx+1]
        
        targets = self.targets[end_idx]
        
        return hist_s, hist_a, hist_d, targets
