import torch
import torch.nn as nn

class NeuralStateSpaceModel(nn.Module):
    def __init__(self, state_dim, action_dim, dist_dim, latent_dim=64):
        super().__init__()
        self.latent_dim = latent_dim
        self.input_dim = state_dim + action_dim + dist_dim
        
        # Encoder: Takes the history sequence and outputs a latent state
        self.encoder = nn.LSTM(input_size=self.input_dim, hidden_size=latent_dim, num_layers=1, batch_first=True)
        
        # Transition Model: Takes (z_t, u_t, d_t) and predicts z_{t+1}
        self.transition = nn.Sequential(
            nn.Linear(latent_dim + action_dim + dist_dim, latent_dim),
            nn.ReLU(),
            nn.Linear(latent_dim, latent_dim)
        )
        
        # Decoder: Maps latent state back to physical state (Temp, Humidity)
        self.decoder = nn.Sequential(
            nn.Linear(latent_dim, 32),
            nn.ReLU(),
            nn.Linear(32, 2) # Predicting Temp and Humidity
        )
        
    def encode(self, x):
        """
        x: (B, L, F)
        Returns latent state z_t: (B, latent_dim)
        """
        _, (h_n, _) = self.encoder(x)
        return h_n.squeeze(0)
        
    def step(self, z, u, d):
        """
        z: (B, latent_dim), u: (B, action_dim), d: (B, dist_dim)
        Returns z_{t+1}
        """
        x_trans = torch.cat([z, u, d], dim=-1)
        z_next = self.transition(x_trans)
        return z_next
        
    def decode(self, z):
        return self.decoder(z)
        
    def forward(self, hist_s, hist_a, hist_d):
        """
        Forward pass doing a multi-step rollout.
        Assumes the action u_t and disturbance d_t are held constant for the rollout.
        """
        # 1. Encode history to get current latent state z_t
        x_hist = torch.cat([hist_s, hist_a, hist_d], dim=-1)
        z_t = self.encode(x_hist)
        
        # Get the CURRENT action and disturbance (last element of history)
        u_t = hist_a[:, -1, :]
        d_t = hist_d[:, -1, :]
        
        predictions = []
        z = z_t
        
        # Roll out for 6 steps (30 minutes)
        for i in range(1, 7):
            z = self.step(z, u_t, d_t)
            
            # Save predictions for +5, +15, +30 (steps 1, 3, 6)
            if i in [1, 3, 6]:
                y_pred = self.decode(z)
                predictions.append(y_pred)
                
        # Concat predictions. Shape will be (B, 6)
        return torch.cat(predictions, dim=-1)
