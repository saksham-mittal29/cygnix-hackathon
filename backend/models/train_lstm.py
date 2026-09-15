import torch
import torch.nn as nn
import torch.optim as optim
from torch.utils.data import DataLoader
from dataset import WispDataset
from lstm_state_space import NeuralStateSpaceModel
from pathlib import Path
import numpy as np

def main():
    print("Setting up datasets...")
    # Use just 5% of data (approx 2 weeks) to drastically cut training time while retaining enough physics to learn
    train_ds = WispDataset("../data/processed/train.parquet", fraction=0.05)
    # Validate on the entire untouched validation set
    val_ds = WispDataset("../data/processed/validation.parquet")
    
    # Increase batch size from 256 to 1024 to speed up gradient descent computation
    train_loader = DataLoader(train_ds, batch_size=1024, shuffle=True, num_workers=0)
    val_loader = DataLoader(val_ds, batch_size=1024, shuffle=False, num_workers=0)
    
    # Calculate dimensions
    state_dim = train_ds.states.shape[-1]
    action_dim = train_ds.actions.shape[-1]
    dist_dim = train_ds.dists.shape[-1]
    
    print(f"State Dim: {state_dim}, Action Dim: {action_dim}, Dist Dim: {dist_dim}")
    
    device = torch.device("cuda" if torch.cuda.is_available() else "mps" if torch.backends.mps.is_available() else "cpu")
    print(f"Using device: {device}")
    
    model = NeuralStateSpaceModel(state_dim, action_dim, dist_dim).to(device)
    
    criterion = nn.MSELoss()
    optimizer = optim.Adam(model.parameters(), lr=1e-3)
    
    epochs = 3 # Keeping it short for the hackathon iteration speed
    best_val_loss = float('inf')
    
    model_dir = Path("saved_models")
    model_dir.mkdir(exist_ok=True)
    
    for epoch in range(epochs):
        model.train()
        train_loss = 0
        print(f"Starting Epoch {epoch + 1} / {epochs}")
        
        for batch_idx, (s, a, d, y) in enumerate(train_loader):
            s, a, d, y = s.to(device), a.to(device), d.to(device), y.to(device)
            
            optimizer.zero_grad()
            y_pred = model(s, a, d)
            
            # Mask out NaNs
            mask = ~torch.isnan(y)
            
            loss = criterion(y_pred[mask], y[mask])
            loss.backward()
            optimizer.step()
            
            train_loss += loss.item()
            
            if batch_idx % 200 == 0:
                print(f"  Batch {batch_idx}/{len(train_loader)} | Loss: {loss.item():.4f}")
                
        avg_train_loss = train_loss / len(train_loader)
        
        # Validation
        model.eval()
        val_loss = 0
        all_residuals = []
        print(f"Validating Epoch {epoch + 1}...")
        with torch.no_grad():
            for s, a, d, y in val_loader:
                s, a, d, y = s.to(device), a.to(device), d.to(device), y.to(device)
                y_pred = model(s, a, d)
                mask = ~torch.isnan(y)
                if mask.any():
                    loss = criterion(y_pred[mask], y[mask])
                    val_loss += loss.item()
                    
                    # Calculate and store absolute residuals for ACI
                    res = torch.abs(y_pred[mask] - y[mask]).cpu().numpy()
                    all_residuals.extend(res)
                
        avg_val_loss = val_loss / len(val_loader)
        print(f"Epoch {epoch+1} Complete | Train Loss: {avg_train_loss:.4f} | Val Loss: {avg_val_loss:.4f}")
        
        if avg_val_loss < best_val_loss:
            best_val_loss = avg_val_loss
            torch.save(model.state_dict(), model_dir / "best_lstm_model.pth")
            # Save residuals for the best model to be used by the backend ACI engine
            np.save(model_dir / "validation_residuals.npy", np.array(all_residuals))
            print("Saved new best model and validation residuals!")
            
if __name__ == "__main__":
    main()
