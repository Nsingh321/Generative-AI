EVALUATION_MODEL = "deepseek-v4-pro" # deepseek-v4-pro

GENERATOR_PROVIDER = "fireworks"  # "ollama" (local), "together" (hosted), "deepseek", or "fireworks" (hosted)
GENERATOR_MODEL = "accounts/fireworks/models/gpt-oss-120b"  # size-tier ladder: ~20B, OpenAI open-weight, verified live 2026-08-22
# completed: google/gemma-4-31B-it (~30B, Together) -> Entity-EX 65%, Strict-EX 50%
# size-tier ladder, still to test: Qwen/Qwen2.5-7B-Instruct-Turbo (~9B, Together),
#   meta-llama/Llama-3.3-70B-Instruct-Turbo (~70B, Together), moonshotai/Kimi-K2.7-Code (large code-specialist,
#   Together or accounts/fireworks/models/kimi-k2p7-code), Qwen/Qwen3.8-2.4T-A95B (flagship - already tested)
# note: classic dense 12-30B coder-branded models (Qwen2.5-Coder, StarCoder2, DeepSeek-Coder-V2-Lite, Devstral)
#   are NOT reachable via cheap serverless on Together, Fireworks, or DeepInfra as of 2026-08-22 - all require
#   GPU-hour-billed dedicated/on-demand deployment. gpt-oss-20b/120b substitute for the dense coder tier.
# local ollama models tested previously: gemma4:12b-it-q4_K_M, granite4.1:8b, mistral-nemo:12b

conn_str = (
        "Driver={ODBC Driver 18 for SQL Server};"
        "Server=localhost\\SQLEXPRESS;"  # server name/instance
        "Database=AdventureWorks2025;" # DB name
        "Trusted_Connection=yes;"
        "Encrypt=no;" # Crucial for local dev environments to avoid SSL cert errors
    )

