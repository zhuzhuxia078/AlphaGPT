import pandas as pd
import torch
import sqlalchemy
from .config import ModelConfig
from .factors import FeatureEngineer

class CryptoDataLoader:
    def __init__(self):
        self.engine = sqlalchemy.create_engine(ModelConfig.DB_URL)
        self.feat_tensor = None
        self.raw_data_cache = None
        self.target_ret = None
        
    def load_data(self, limit_tokens=500):
        print("Loading data from SQL...")
        top_query = f"""
        SELECT address FROM tokens 
        LIMIT {limit_tokens} 
        """
        addrs = pd.read_sql(top_query, self.engine)['address'].tolist()
        if not addrs: raise ValueError("No tokens found.")
        # Log which tokens are selected for training (preview first 10)
        preview = ", ".join(addrs[:10])
        suffix = " ..." if len(addrs) > 10 else ""
        print(f"Selected tokens ({len(addrs)}): {preview}{suffix}")
        addr_str = "'" + "','".join(addrs) + "'"
        time_filter = ""
        if ModelConfig.LOOKBACK_DAYS > 0:
            time_filter = f" AND time >= NOW() - INTERVAL '{ModelConfig.LOOKBACK_DAYS} days'"

        data_query = f"""
        SELECT time, address, open, high, low, close, volume, liquidity, fdv
        FROM ohlcv
        WHERE address IN ({addr_str}) {time_filter}
        ORDER BY time ASC
        """
        df = pd.read_sql(data_query, self.engine)
        # Logging: how many candles and time span are loaded
        if not df.empty:
            print(f"Loaded {len(df)} candles for {len(addrs)} tokens "
                  f"from {df['time'].min()} to {df['time'].max()} "
                  f"(lookback={ModelConfig.LOOKBACK_DAYS} days)")
        else:
            print(f"No data loaded (lookback={ModelConfig.LOOKBACK_DAYS} days).")
        def to_tensor(col):
            pivot = df.pivot(index='time', columns='address', values=col)
            pivot = pivot.fillna(method='ffill').fillna(0.0)
            return torch.tensor(pivot.values.T, dtype=torch.float32, device=ModelConfig.DEVICE)
        self.raw_data_cache = {
            'open': to_tensor('open'),
            'high': to_tensor('high'),
            'low': to_tensor('low'),
            'close': to_tensor('close'),
            'volume': to_tensor('volume'),
            'liquidity': to_tensor('liquidity'),
            'fdv': to_tensor('fdv')
        }
        self.feat_tensor = FeatureEngineer.compute_features(self.raw_data_cache)
        op = self.raw_data_cache['open']
        t1 = torch.roll(op, -1, dims=1)
        t2 = torch.roll(op, -2, dims=1)
        self.target_ret = torch.log(t2 / (t1 + 1e-9))
        self.target_ret[:, -2:] = 0.0
        print(f"Data Ready. Shape: {self.feat_tensor.shape}")
