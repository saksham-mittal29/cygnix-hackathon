import os
import glob
import xarray as xr
import pandas as pd
import numpy as np
from pathlib import Path
from sklearn.preprocessing import StandardScaler
import joblib

# Paths
CLEAN_DATA_DIR = Path("../clean_data")
PROCESSED_DATA_DIR = Path("../data/processed")
PROCESSED_DATA_DIR.mkdir(parents=True, exist_ok=True)

# Variables to keep
VARIABLES = [
    "Indoor_AverageTemperature", "Indoor_Humidity", 
    "Outdoor_Temperature", "Outdoor_Humidity",
    "Indoor_HeatSetpoint", "Indoor_CoolSetpoint",
    "HeatingEquipmentStage1_RunTime", "CoolingEquipmentStage1_RunTime", "Fan_RunTime",
    "Thermostat_DetectedMotion", "State"
]

SCALE_COLS = [
    "Indoor_AverageTemperature", "Indoor_Humidity", 
    "Outdoor_Temperature", "Outdoor_Humidity",
    "Indoor_HeatSetpoint", "Indoor_CoolSetpoint"
]

def process_month(file_path):
    print(f"Loading {file_path.name}...")
    ds = xr.open_dataset(file_path)
    
    # Filter variables to avoid loading huge unnecessary data
    vars_to_load = [v for v in VARIABLES if v in ds.variables]
    df = ds[vars_to_load].to_dataframe().reset_index()
    ds.close()
    
    if "Indoor_AverageTemperature" not in df.columns:
        return pd.DataFrame()
        
    # Drop rows where main state is missing
    df = df.dropna(subset=["Indoor_AverageTemperature"])
    
    # Sort temporally
    df = df.sort_values(["id", "time"]).reset_index(drop=True)
    
    # ----------------------------------------------------
    # Sequence Boundaries (Break if gap > 5 mins)
    # ----------------------------------------------------
    df['time_diff'] = df.groupby('id')['time'].diff()
    df['seq_break'] = (df['time_diff'] > pd.Timedelta(minutes=5)) | df['time_diff'].isna()
    df['seq_id'] = df.groupby('id')['seq_break'].cumsum()
    df['sequence_id'] = df['id'].astype(str) + "_" + df['seq_id'].astype(str)
    df = df.drop(columns=['time_diff', 'seq_break', 'seq_id'])
    
    # ----------------------------------------------------
    # Multi-horizon Targets (+5, +15, +30 mins)
    # ----------------------------------------------------
    for steps, mins in [(1, 5), (3, 15), (6, 30)]:
        df[f'target_Indoor_Temperature_plus_{mins}m'] = df.groupby('sequence_id')['Indoor_AverageTemperature'].shift(-steps)
        if "Indoor_Humidity" in df.columns:
            df[f'target_Indoor_Humidity_plus_{mins}m'] = df.groupby('sequence_id')['Indoor_Humidity'].shift(-steps)
        
    # ----------------------------------------------------
    # Temporal & Normalized Features
    # ----------------------------------------------------
    df['hour_sin'] = np.sin(2 * np.pi * df['time'].dt.hour / 24).astype(np.float32)
    df['hour_cos'] = np.cos(2 * np.pi * df['time'].dt.hour / 24).astype(np.float32)
    df['day_sin'] = np.sin(2 * np.pi * df['time'].dt.dayofweek / 7).astype(np.float32)
    df['day_cos'] = np.cos(2 * np.pi * df['time'].dt.dayofweek / 7).astype(np.float32)
    
    # Normalize runtime fraction [0, 1]
    for col in ["HeatingEquipmentStage1_RunTime", "CoolingEquipmentStage1_RunTime", "Fan_RunTime"]:
        if col in df.columns:
            df[col] = (df[col] / 300.0).astype(np.float32)
            
    # Convert numerical columns to float32 to save RAM
    num_cols = df.select_dtypes(include=['float64']).columns
    df[num_cols] = df[num_cols].astype(np.float32)
    
    return df

def main():
    print("Step 1: Processing files & calculating splits...")
    
    train_files = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep"]
    val_files = ["Oct", "Nov"]
    test_files = ["Dec"]
    
    scaler = StandardScaler()
    
    # We will process and write out to temporary parquet files first,
    # and fit the scaler iteratively to prevent OOM
    temp_dir = PROCESSED_DATA_DIR / "temp_chunks"
    temp_dir.mkdir(exist_ok=True)
    
    all_nc_files = sorted(CLEAN_DATA_DIR.glob("*_clean.nc"))
    
    chunk_meta = []
    
    for file in all_nc_files:
        month = file.stem.split('_')[0]
        
        if month in train_files:
            split = "train"
        elif month in val_files:
            split = "val"
        elif month in test_files:
            split = "test"
        else:
            continue
            
        df = process_month(file)
        if df.empty:
            continue
            
        if split == "train":
            # Partial fit the scaler
            valid_rows = df[SCALE_COLS].dropna()
            if len(valid_rows) > 0:
                scaler.partial_fit(valid_rows)
                
        # Save chunk
        out_path = temp_dir / f"{month}_{split}.parquet"
        df.to_parquet(out_path, index=False)
        chunk_meta.append((out_path, split))
        
    print("Step 2: Applying Scaler and assembling final datasets...")
    
    # Re-read, scale, and append to final parquet stores
    import pyarrow as pa
    import pyarrow.parquet as pq
    
    writers = {"train": None, "val": None, "test": None}
    
    for chunk_path, split in chunk_meta:
        print(f"Scaling and appending {chunk_path.name} to {split}...")
        df = pd.read_parquet(chunk_path)
        
        # Scale continuous features
        for col in SCALE_COLS:
            if col in df.columns:
                col_idx = SCALE_COLS.index(col)
                mean = scaler.mean_[col_idx]
                std = scaler.scale_[col_idx]
                df[col] = (df[col] - mean) / std
                
        # Scale targets using same temperature/humidity params
        temp_mean = scaler.mean_[SCALE_COLS.index("Indoor_AverageTemperature")]
        temp_std = scaler.scale_[SCALE_COLS.index("Indoor_AverageTemperature")]
        hum_mean = scaler.mean_[SCALE_COLS.index("Indoor_Humidity")] if "Indoor_Humidity" in SCALE_COLS else 0
        hum_std = scaler.scale_[SCALE_COLS.index("Indoor_Humidity")] if "Indoor_Humidity" in SCALE_COLS else 1
        
        for mins in [5, 15, 30]:
            t_col = f'target_Indoor_Temperature_plus_{mins}m'
            if t_col in df.columns:
                df[t_col] = (df[t_col] - temp_mean) / temp_std
            
            h_col = f'target_Indoor_Humidity_plus_{mins}m'
            if h_col in df.columns:
                df[h_col] = (df[h_col] - hum_mean) / hum_std
                
        table = pa.Table.from_pandas(df)
        
        if writers[split] is None:
            out_file = PROCESSED_DATA_DIR / f"{split if split != 'val' else 'validation'}.parquet"
            writers[split] = pq.ParquetWriter(out_file, table.schema)
            
        writers[split].write_table(table)
        
        # Cleanup temp file
        chunk_path.unlink()
        
    for w in writers.values():
        if w is not None:
            w.close()
            
    temp_dir.rmdir()
    
    # Save the scaler
    joblib.dump(scaler, PROCESSED_DATA_DIR / "scaler.pkl")
    print("Dataset generation complete! Files saved to data/processed/")

if __name__ == "__main__":
    main()
