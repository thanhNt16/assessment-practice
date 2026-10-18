## Machine Learning System Design — Cheatsheet

From [ml-design](17-ml-design.md). Decision tables + quick rules.

### Architecture chooser

| If | Then |
|---|---|
| accuracy beats latency, training data bounded | two-stage detector (R-CNN family); RPN + classifier |
| latency or data volume grows | one-stage detector (YOLO/SSD) |
| billions of items to search | precompute embeddings → ANN (Faiss/ScaNN) |
| small candidate pool | exact NN, no ANN needed |
| ID interactions only, serving must be fast | matrix factorization + WALS (precomputed dot products) |
| rich user/item features or new items frequent | two-tower NN; heavier scorer downstream |
| next-click from a short session, no attributes | session-based embeddings (word2vec-style + negative sampling) |
| ephemeral items, "will user attend" | pointwise LTR classifier + focal/class-balanced loss |
| high-cardinality sparse CTR features | LR baseline → DCN/DeepFM by experiment |
| link recommendation on a social graph | GNN edge prediction; dot product = edge probability |
| modalities harmful only combined (memes) | early fusion; multi-task NN, one head per policy |
| one input, many per-item decisions | multi-task NN: shared layers + per-task heads |
| metrics decay within minutes | continual learning (fine-tune → eval → deploy-if-better); no GBDT |
| no-ML text search good enough | inverted index (Elasticsearch); fuse with ANN via weighted-sum re-rank |
| 1B candidates per user impractical | friends-of-friends narrowing (1B → 1M); batch predict + store |
| new user/item with no interactions | demographics / heuristics → collect interactions → fine-tune |
| CPU-bound + GPU-bound stages | separate services, scale independently |
| non-ML rules (filters, business, freshness) | re-ranking stage, never inside the model |

### Metric chooser

| If relevance is... | Use |
|---|---|
| exactly one relevant item, rank matters | MRR (recall@k = hit-rate 0/1, precision@10 caps at 0.1) |
| millions of relevant / continuous scores | nDCG (MRR ignores post-first hits, recall drowns, precision rank-blind) |
| detection boxes + classes | AP over IOU thresholds, mAP over classes |
| binary connect-or-not ranking | ROC-AUC (model) + mAP (ranking) |
| imbalanced per-policy / per-reaction flags | PR-AUC + ROC-AUC per policy/reaction |
| pCTR vs naive baseline | CE + NCE (NCE < 1 = beating background CTR) |
| recsys beyond accuracy | diversity + recall offline; CTR, session book rate, time spent online |

### Labeling chooser

| If | Then |
|---|---|
| billions of examples, no labels | self-supervision via augmentation (free, clean) |
| clicks available | free but noisy, sparse — secondary signal |
| humans can label | accurate, expensive (~10K/day vs 500M posts) → eval only |
| click logs | visible-without-click = negative; click within t sec = positive |
| random negatives too easy | hard negatives: same-region listings, user-reported misses |

### Quick rules

- Business goal → trainable ML objective first ("engagement" → "maximize watch time").
- Name 2–3 candidate objectives with failure modes before choosing — signals senior judgment.
- Seven steps every design: clarify → frame → data → model → evaluate → deploy/serve → monitor.
- Model ladder: popularity/simple baseline → LR → DNN → ensemble only if needed.
- Loss over observed pairs only collapses to all-ones embeddings — always weight unobserved pairs (WALS).
- Re-ranking is the dumping ground for non-ML logic — never bake business rules into the model.
- Static features batch-computed into a feature store; dynamic computed at query time.
- Everything expensive (embeddings, whole lists) precomputed and cached before the request.
- Every metric choice needs a written elimination chain — state why the alternatives fail.
- Wrong computation mode is a design bug: blurring = batch, ads = minutes, PYMK batch = accepted 80% waste.
- Positional bias and feedback loops distort click data — correct in training/eval.
- The models are the easy 20%; seniority lives in data engineering (labeling, negatives, feature stores, batch-vs-online).
