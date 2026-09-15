import pandas as pd
import json
from pathlib import Path

def main():
    print("Reading a small chunk of train.parquet to calculate realistic metrics...")
    df = pd.read_parquet("data/processed/train.parquet", columns=["time", "HeatingEquipmentStage1_RunTime", "CoolingEquipmentStage1_RunTime", "Fan_RunTime"])
    
    # We will compute daily aggregates
    df["date"] = pd.to_datetime(df["time"]).dt.date
    daily = df.groupby("date").agg({
        "HeatingEquipmentStage1_RunTime": "sum",
        "CoolingEquipmentStage1_RunTime": "sum",
        "Fan_RunTime": "sum"
    }).reset_index()
    
    # Convert runtime to approximate "Energy kWh" (Mock conversion factor)
    daily["Energy (kWh)"] = (daily["HeatingEquipmentStage1_RunTime"] * 0.05) + (daily["CoolingEquipmentStage1_RunTime"] * 0.08)
    daily["Cost ($)"] = daily["Energy (kWh)"] * 0.15 # $0.15 per kWh
    
    # Sort and take last 30 days for the chart
    daily = daily.sort_values("date").tail(30)
    
    metrics_data = {
        "dates": [d.strftime("%Y-%m-%d") for d in daily["date"]],
        "energy_kwh": daily["Energy (kWh)"].round(2).tolist(),
        "cost_usd": daily["Cost ($)"].round(2).tolist(),
        "heating_time": daily["HeatingEquipmentStage1_RunTime"].tolist(),
        "cooling_time": daily["CoolingEquipmentStage1_RunTime"].tolist()
    }
    
    out_path = Path("data/processed/metrics.json")
    with open(out_path, "w") as f:
        json.dump(metrics_data, f)
        
    print(f"Metrics saved to {out_path}")

if __name__ == "__main__":
    main()
