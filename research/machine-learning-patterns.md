## Machine Learning System Design — Patterns

From [ml-design](17-ml-design.md): framework, technique, and anti-pattern cards. Format: name — when to use — how.

### Model frameworks

- Two-stage detector (R-CNN family) — accuracy trumps latency, training data doesn't punish slowness — RPN proposes boxes, per-box classifier refines; MSE for boxes + λ-balanced cross-entropy for classes.
- One-stage detector (YOLO/SSD) — latency or data volume grows beyond two-stage's sweet spot — single-pass bbox + class prediction.
- Multi-task multimodal NN — one input needs many per-policy decisions — shared layers (DistilmBERT text encoder) + one binary head per policy.
- Matrix factorization + WALS — ID interactions only, precomputed serving acceptable — factorize interaction matrix with a loss weighted over observed + unobserved pairs.
- Two-tower NN — CF needs rich user/item features or new-item support — separate encoders meet at a dot product; heavier content-based scorer ranks the survivors.
- Session-based embeddings — next-click prediction from short sessions, interactions only, no attributes — word2vec-style sliding window over session sequences, negative sampling.
- Pointwise LTR — ranking reduces to per-item binary classification — train "will this user attend/click" classifier, rank by score.
- GNN edge prediction — link recommendation where social context separates plausible from implausible pairs — GNN node embeddings, dot product = edge probability; train on graph snapshot t, label = edge at t+1.
- Multi-task DNN for reactions — engagement objective blends many implicit/explicit signals — shared trunk, per-reaction binary heads, probabilities × weights = score.
- DeepFM — high-cardinality sparse CTR features needing low+high-order interactions — FM and DNN share embeddings; beats DCN in competitions but slows continual learning.
- DCN — feature crosses should be learned, not manual — cross layers multiply features automatically; pick after LR baseline by experiment.
- FM — pairwise interactions without manual crossing — LR + learned pairwise embedding interactions.
- GBDT / GBDT+LR — tabular features, no continual-learning requirement — boosted trees; tree leaves as features into LR.

### Techniques

- Objective translation — always the first move — turn business goal into trainable ML objective ("increase engagement" → "maximize watch time"); name 2–3 candidates with failure modes before choosing.
- Contrastive representation learning — similarity retrieval without a ranker — similar pairs close in embedding space: dot product/cosine → softmax → cross-entropy.
- Self-supervision via augmentation — labeling at billions of examples — generate positives by augmenting source images; free and clean vs human judgment (expensive) or clicks (noisy).
- Negative sampling — embedding training at scale — central vs context positive, central vs random negative.
- Hard negative mining — random negatives trivially separable (across regions users never compare) — same-region listings; user-reported missed faces feeding retraining.
- Focal loss / class-balanced loss — extreme class imbalance (rare attendance) — down-weight easy negatives or rebalance class weights.
- Feature crossing — expose feature interactions — manual explodes sparsity; let DCN/DeepFM learn crosses from shared embeddings.
- Feature hashing — unseen/viral hashtags must not break the model — hash into fixed-size space, no vocabulary retrain.
- Viterbi tokenization — concatenated hashtags need splitting — segment into words before TF-IDF/word2vec (skip Transformers: hashtags carry no context worth the cost).
- Decay-weighted streaming features — recency matters (events) — weight recent interactions with an exponential decay factor.
- Time-discounted mutual connections — PYMK features — down-weight old network growth; recent growth signals openness to connect.
- Attribute standardization — messy free-text ("CS" vs "computer science") — predefined lists, heuristics, or clustering.
- Quantization — billion-scale embedding memory — compress vectors in the precompute indexing pipeline.
- Continual-learning pipeline — performance decays within minutes (ads) — fine-tune → evaluate → deploy only if metrics improve.
- Impression-based labeling — click logs are biased — visible-without-click = negative, click within t seconds = positive.
- Early fusion — modalities harmful only in combination (memes) — concatenate modality representations early so interactions are captured.
- Late fusion — independent per-modality models — separate models merged at output; misses cross-modal interactions, rejected for memes.
- Weighted multi-reaction score — implicit signals data-rich but noisy, explicit clean but scarce — per-reaction probabilities × weights (click 1 … share 20, hide −20, block −50).

### Serving patterns

- Retrieval → ranking → re-ranking skeleton — default shape for search/rec/feed/ads/PYMK — candidate generation (ANN/index/FoF/filters) → heavy scorer over survivors → filters, diversity, freshness, business rules.
- ANN retrieval — past millions of candidates — precompute embeddings, index tree/LSH/clustering (Faiss/ScaNN); exact search only for small pools.
- Inverted-index retrieval — zero-ML-cost text search — Elasticsearch; fuse with ANN results via weighted-sum re-rank (over a trained fusion model).
- Feature-store split — static vs dynamic features — batch-compute static offline, compute dynamic at query time.
- Precompute-and-cache — per-request inference infeasible at scale — index all embeddings offline; batch-predict whole PYMK lists, refresh every 7 days (1 for new users), over-generate, hide already-seen.
- Batch vs online computation — match the latency tolerance — blurring tolerates batch; ad models must refresh within minutes; PYMK batch wastes 80% of compute — an accepted, stated trade.
- Friends-of-friends narrowing — scoring 1B embeddings per user impractical — restrict to FoF (1000² = 1M); 92% of new friendships form within FoF.
- Cold-start ladder — new users/items lack interactions — demographic features / heuristics (nearest geographic embedding) → collect interactions → fine-tune.
- Rule-based pre-filtering — candidate pool must shrink before the model — city/time rules cut 1M events to hundreds, then the model ranks.
- Resource-aligned services — stages have different hardware bottlenecks — CPU-bound preprocessing separate from GPU-bound blurring; scale independently.

### Anti-patterns

- All-ones embeddings — loss over observed pairs only reaches zero with degenerate embeddings — weight unobserved pairs (WALS); walk the loss reasoning aloud.
- Uncalibrated probabilities — pCTR feeds downstream bidding — miscalibration breaks the auction; calibrate before serving.
- Clickbait optimization — maximizing clicks or raw reactions rewards clickbait — weight negative signals, prefer relevance-aware objectives.
- Biased negatives — unclicked ≠ uninterested when the user scrolled past — impression-based labels; same-region hard negatives.
- Positional bias — top ranks collect clicks regardless of quality — correct for position in training/evaluation.
- Feedback-loop bias — frequent users over-recommended, then over-represented in logs — monitor and dampen recommendation frequency.
- GBDT in continual-learning systems — cannot fine-tune; retrains from scratch at scale — use fine-tunable NNs.
- Business rules inside the model — re-ranking is the dumping ground for non-ML logic — keep the model pure; apply filters/diversity/rules after.
- Wrong metric by default — precision@10 caps at 0.1 with one relevant item; recall@k drowns at millions; precision@k is rank-blind — run a written elimination chain to nDCG/MRR/mAP/NCE per task.
