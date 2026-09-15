import torch
from torch.utils.data import DataLoader
from dataset import WispDataset
from lstm_state_space import NeuralStateSpaceModel
from pathlib import Path
import numpy as np
import sys

def main():
    print("Loading existing model to extract validation residuals...")
    val_ds = WispDataset("../data/processed/validation.parquet", fraction=0.05)
    val_loader = DataLoader(val_ds, batch_size=1024, shuffle=False, num_workers=0)
    
    state_dim = val_ds.states.shape[-1]
    action_dim = val_ds.actions.shape[-1]
    dist_dim = val_ds.dists.shape[-1]
    
    device = torch.device("cuda" if torch.cuda.is_available() else "mps" if torch.backends.mps.is_available() else "cpu")
    model = NeuralStateSpaceModel(state_dim, action_dim, dist_dim).to(device)
    
    model_dir = Path("saved_models")
    model_path = model_dir / "best_lstm_model.pth"
    if not model_path.exists():
        print("No saved model found.")
        sys.exit(1)
        
    model.load_state_dict(torch.load(model_path, map_location=device))
    model.eval()
    
    all_residuals = []
    print("Running validation pass...")
    with torch.no_grad():
        for s, a, d, y in val_loader:
            s, a, d, y = s.to(device), a.to(device), d.to(device), y.to(device)
            y_pred = model(s, a, d)
            mask = ~torch.isnan(y)
            if mask.any():
                res = torch.abs(y_pred[mask] - y[mask]).cpu().numpy()
                all_residuals.extend(res)
                
    np.save(model_dir / "validation_residuals.npy", np.array(all_residuals))
    print(f"Saved {len(all_residuals)} validation residuals!")

if __name__ == "__main__":
    main()
