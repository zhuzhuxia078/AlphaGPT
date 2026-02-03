# AlphaGPT

> [!IMPORTANT]
> GitHub 的 issue 并非被设计为打卡工具！仅用于「打卡」「留名」的 issue 将会被直接删除。若您需要社群，请考虑QQ群组 1082630631。

> [!IMPORTANT]
> 若您在加密市场进行交易，另可参考 [Defense in Predatory Markets: A Differential Game Framework for AMM Liquidity via Uniswap V4 Hooks](https://github.com/imbue-bit/no_JIT) 进行做市。笔者懒得向会议投稿了。若有疑问，请联系 imbue2025@outlook.com. BTW，对该仓库代码进行 live trading 前作适当的修改可能会出现意想不到的业绩。

## What happened？

目前双方已达成和解。

## 去中心化

目前双方已达成和解。

## 责任免除

目前双方已达成和解。

## Abstract

目前双方已达成和解。

## Motivation

目前双方已达成和解。

## This was their money-making machine. Now it's your public library.

目前双方已达成和解。

## OH! NO!

目前双方已达成和解。

## Star History

[![Star History Chart](https://api.star-history.com/svg?repos=imbue-bit/AlphaGPT&type=date&legend=top-left)](https://www.star-history.com/#imbue-bit/AlphaGPT&type=date&legend=top-left)



## Run Checklist (从零到跑通的最小路线)

- Python 环境：在仓库根目录建虚拟环境并装依赖
  - python -m venv .venv && source .venv/bin/activate
  - pip install -r requirements.txt
- 配置 .env（仓库未提供）
  - 数据库：DB_USER/DB_PASSWORD/DB_HOST/DB_PORT/DB_NAME
  - 数据源：BIRDEYE_API_KEY（必填），可选 USE_DEXSCREENER 相关开关在 config.py。
  - 执行层：SOLANA_RPC_URL、JUPITER_BASE_URL（如有）、WALLET_PRIVATE_KEY 或助记词。
  - 网络选择：CHAIN=solana（默认），TIMEFRAME=1m 或 15min。
- 准备数据库
  - 启动 Postgres/Timescale，建库名与 .env 对应。
  - 如需要 hypertable/索引，检查 db_manager.py 里是否自动建表；若无，手动创建后再跑管线。
- 拉取历史数据（写库）
  - 运行 python -m data_pipeline.run_pipeline，它会用 DataManager 调 pipeline_sync_daily() 把近 HISTORY_DAYS（默认 7 天）的代币列表与 OHLCV 写入 DB。
  - 首跑关注日志里是否报缺密钥或 4xx/429；必要时降低 CONCURRENCY。
- 训练/生成策略公式
  -  入口：alphagpt.py（训练生成器）、engine.py（执行/评估）、backtest.py（回测评分函数）。
  - 典型流程：用 data_loader.py 读库 → engine.py 调用 Transformer 生成公式 → backtest.py 评分 → 输出高分公式文件（例如 best_meme_strategy.json）到根目录或 model_core/。
- 回测与验证
  - 在相同数据集上用生成的公式跑一次独立回测（walk-forward 优先），确认收益/回撤/滑点假设；相关代码集中在 backtest.py、vm.py（执行公式）。
- 策略运行（建议先 dry run）
  - 入口：runner.py。它会读取公式文件、对候选代币打分、调用 risk.py 过滤，再把信号交给执行层。
  - Dry run：让 execution 部分只写本地 portfolio.json（看 config.py/portfolio.py 的写盘路径），先不签名上链。
- 实盘执行
  - 配置 config.py 中的 RPC/Jupiter，解锁私钥。
  - 运行时监控滑点、余额、黑名单合约；出错要自动重试或降级。
- 看板
  - <entry>.py（查看 dashboard 下的具体脚本）读取本地 portfolio 和市场快照，便于观察。

如果你希望我补一个 .env.example 或找出 runner 的具体命令行参数，我可以直接在仓库里查文件并给出可复制的命令。


训练/生成公式的最小步骤（先纸面版）：

1. 确认数据够用
- 你的库已有最近几天 1m/15m K 线即可先跑；越多历史回测越稳。
2. 进入虚拟环境
`source .venv/bin/activate`

3. 直接跑训练引擎

在仓库根执行：
  `python -m model_core.engine`

- 默认使用 CPU/GPU 自动检测；CPU 会比较慢（几千步可能要十几分钟+）。
- 训练过程中会在终端打印 “New King” 的最佳分公式。
4. 产出文件
训练结束会在根目录生成：
- best_meme_strategy.json（公式 token 序列）
- training_history.json（奖励曲线等）
5. 若要调整（可选）

- 配置：config.py（如训练步数 TRAIN_STEPS、批大小、设备）。
- 回测参数：backtest.py（仓位/滑点/惩罚）。
- 数据加载：data_loader.py 使用 DB_DSN 连接当前数据库；如需不同时间窗口，可在这里或 Config 中改。
6. 验证回测
训练后可再写一个小脚本/调用 AlphaEngine 的回测部分，对 best_meme_strategy.json 在同一数据上重跑，观察收益、回撤、交易次数。

跑完把终端输出或生成的文件路径告诉我，我再帮你看效果或给 dry run 策略配置。


一些实用的docker postgres command：
在终端里用 docker 自带的 psql 就行，无需 UI。按顺序操作：

进入交互式 psql：
docker exec -it alphagpt-pg psql -U postgres -d crypto_quant

进到 psql 后常用命令：

列表表：\dt
看 tokens 表前几行：select * from tokens limit 5;
看 ohlcv 行数与时间范围：select count(*) rows, min(time), max(time) from ohlcv;
查看最新 K 线：select time, address, open, high, low, close, volume from ohlcv order by time desc limit 5;
退出：\q
如果只想跑一条 SQL 不进交互：
docker exec -it alphagpt-pg psql -U postgres -d crypto_quant -c "select count(*) from ohlcv;"