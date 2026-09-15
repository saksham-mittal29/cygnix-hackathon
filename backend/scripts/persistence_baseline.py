import pandas as pd
import numpy as np
from pathlib import Path
import joblib

PROCESSED_DATA_DIR = Path("../data/processed")

def evaluate_persistence(split):
    print(f"\n======================================")
    print(f"Evaluating Persistence Baseline on {split.upper()} set")
    print(f"======================================")
    
    file_path = PROCESSED_DATA_DIR / f"{split}.parquet"
    if not file_path.exists():
        print(f"Error: {file_path} not found.")
        return None
        
    df = pd.read_parquet(file_path)
    scaler = joblib.load(PROCESSED_DATA_DIR / "scaler.pkl")
    
    # Scale column indices (as defined in build script)
    # 0: Indoor_AverageTemperature, 1: Indoor_Humidity
    temp_idx = 0
    hum_idx = 1
    
    temp_mean = scaler.mean_[temp_idx]
    temp_std = scaler.scale_[temp_idx]
    hum_mean = scaler.mean_[hum_idx]
    hum_std = scaler.scale_[hum_idx]
    
    # Inverse transform current state (which is the persistence prediction)
    current_temp = (df["Indoor_AverageTemperature"] * temp_std) + temp_mean
    current_hum = (df["Indoor_Humidity"] * hum_std) + hum_mean if "Indoor_Humidity" in df.columns else None
    
    metrics = []
    
    for mins in [5, 15, 30]:
        t_col = f'target_Indoor_Temperature_plus_{mins}m'
        if t_col in df.columns:
            # Unscale true future targets
            true_temp = (df[t_col] * temp_std) + temp_mean
            
            # Mask out NaNs
            valid = ~np.isnan(true_temp) & ~np.isnan(current_temp)
            
            mae_t = np.mean(np.abs(true_temp[valid] - current_temp[valid]))
            rmse_t = np.sqrt(np.mean((true_temp[valid] - current_temp[valid])**2))
            metrics.append({"Horizon (min)": mins, "Variable": "Temperature", "MAE": mae_t, "RMSE": rmse_t})
            
        h_col = f'target_Indoor_Humidity_plus_{mins}m'
        if h_col in df.columns and current_hum is not None:
            # Unscale true future targets
            true_hum = (df[h_col] * hum_std) + hum_mean
            
            # Mask out NaNs
            valid = ~np.isnan(true_hum) & ~np.isnan(current_hum)
            
            mae_h = np.mean(np.abs(true_hum[valid] - current_hum[valid]))
            rmse_h = np.sqrt(np.mean((true_hum[valid] - current_hum[valid])**2))
            metrics.append({"Horizon (min)": mins, "Variable": "Humidity", "MAE": mae_h, "RMSE": rmse_h})
            
    res_df = pd.DataFrame(metrics)
    print(res_df.to_string(index=False))
    
    out_csv = PROCESSED_DATA_DIR / f"persistence_baseline_{split}.csv"
    res_df.to_csv(out_csv, index=False)
    print(f"\nSaved metrics to {out_csv}")
    
    return res_df

if __name__ == "__main__":
    evaluate_persistence("validation")
    evaluate_persistence("test")
