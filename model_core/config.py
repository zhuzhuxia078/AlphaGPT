import torch
import os
from urllib.parse import quote_plus
from dotenv import load_dotenv

# Load environment variables from project .env
load_dotenv()

class ModelConfig:
    DEVICE = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    DB_USER = os.getenv('DB_USER', 'postgres')
    DB_PASSWORD = os.getenv('DB_PASSWORD', 'password')
    DB_HOST = os.getenv('DB_HOST', 'localhost')
    DB_PORT = os.getenv('DB_PORT', '5432')  # Supabase pooler uses 6543
    DB_NAME = os.getenv('DB_NAME', 'crypto_quant')
    DB_SSLMODE = os.getenv('DB_SSLMODE', 'require')

    _ssl_suffix = f"?sslmode={DB_SSLMODE}" if DB_SSLMODE else ""
    _safe_pwd = quote_plus(DB_PASSWORD)
    DB_URL = (
        f"postgresql://{DB_USER}:{_safe_pwd}@{DB_HOST}:{DB_PORT}/{DB_NAME}{_ssl_suffix}"
    )
    # Reduce batch to fit 24GB GPU
    BATCH_SIZE = 8192
    TRAIN_STEPS = 1000
    MAX_FORMULA_LEN = 12
    TRADE_SIZE_USD = 1000.0
    MIN_LIQUIDITY = 5000.0 # 低于此流动性视为归零/无法交易
    BASE_FEE = 0.005 # 基础费率 0.5% (Swap + Gas + Jito Tip)
    INPUT_DIM = 6
