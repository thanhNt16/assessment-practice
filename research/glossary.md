# Glossary — single source for terms + graph edges

## Format
- Term lines: `TERM :: one-sentence definition` (TERM is matched case-insensitively at word boundaries).
- Edge lines: `TERM_A > TERM_B :: why they're connected` (both must be defined).
- `##` headers are ignored (organization only).

## Core (data engineering)
Watermark :: Event-time progress marker; windows close and late data is judged against it.
Idempotency :: An operation safe to retry — same input, same final state, no duplicate effects.
Exactly-once :: Effect semantics built from at-least-once delivery + idempotent writes or transactional commits.
Medallion :: Bronze (raw) → silver (validated) → gold (business-ready) layering of lakehouse data.
RAG :: Retrieval-augmented generation — ground an LLM answer in retrieved documents.
Embedding :: Dense vector representation of text/image such that semantic similarity ≈ vector distance.
AQE :: Adaptive Query Execution — Spark re-plans joins/partitions at shuffle boundaries using runtime stats.
ISR :: In-sync replicas — Kafka followers caught up enough to acknowledge writes.
Parquet :: Columnar file format with per-column encoding and nested-type support.
CDC :: Change data capture — stream of row-level changes from an OLTP log.
SCD Type 2 :: Slowly changing dimension keeping history as new versioned rows.
Backfill :: Reprocessing historical data with new logic into the same destination.
Lambda architecture :: Batch + speed layers serving merged views; Kappa collapses both onto one stream.
Shuffle :: Redistributing data across partitions between stages; the dominant Spark cost.
Skew :: Uneven key distribution making one partition dominate stage time.
Checkpoint :: Durable snapshot of Flink state enabling exactly-once recovery.
Compaction :: Merging small files into fewer large ones to restore read performance.
Z-ordering :: Multi-column clustering of lakehouse files to prune scans on any column.
Distributed join strategy :: Broadcast vs sort-merge vs shuffle-hash — picked by size + skew stats.
Feature store :: Versioned repository of point-in-time-correct features for training and serving.

## Data platforms & modeling
Kafka :: Distributed log-based messaging system; topics are split into ordered, replicated partitions.
Spark :: Distributed compute engine executing a DAG of stages and tasks across executor JVMs.
Flink :: Streaming-first engine with event-time windows, keyed state, and checkpointed exactly-once pipelines.
Snowflake :: Fully managed cloud warehouse separating storage, virtual warehouses, and cloud services.
Databricks :: Lakehouse platform built on Spark with Delta Lake, collaborative notebooks, and managed ML tooling.
Delta Lake :: Open table format adding ACID transactions and a transaction log on top of Parquet.
Iceberg :: Open table format with hidden partitioning, snapshot metadata, and engine-neutral catalogs.
Hudi :: Open table format optimized for fast upserts and incremental pulls via merge-on-read or copy-on-write.
OLTP :: Row-oriented operational stores built for many short read/write transactions.
Lakehouse :: Lake storage plus ACID table formats and SQL engines — warehouse reliability at lake economics.
ELT :: Extract-load-transform; raw data lands first and transforms run inside the target engine.
ETL :: Extract-transform-load pipelines that shape data before it reaches the destination.
Window functions :: SQL functions computing aggregates over a row frame without collapsing rows (RANK, moving averages).
DAG :: Directed acyclic graph — Spark stages and orchestrator workflows are both modeled as DAGs.
Catalyst :: Spark's rule- and cost-based query optimizer producing the physical plan.
Driver :: The Spark JVM that builds the DAG, schedules tasks, and collects results.
Executor :: Worker JVM that runs Spark tasks on partitions and caches blocks.
Salting :: Adding a random prefix to hot keys so a skewed partition splits into manageable pieces.
Time travel :: Querying a table as of an earlier snapshot using table-format versioning.

## Streaming & distributed systems
CAP theorem :: Under a network partition, a distributed store must sacrifice either consistency or availability.
Quorum :: Majority acknowledgment rule (R+W greater than N) keeping reads and writes consistent through failures.
Consensus :: Getting nodes to agree on one value or log despite crashes and partitions.
Raft :: Leader-based consensus protocol replicating a log — the readable alternative to Paxos.
Replication :: Keeping copies of data on multiple nodes for durability and read scale.
Partitioning :: Splitting a dataset across nodes or partitions for parallel storage and processing.
Event time :: The timestamp embedded in a record (when it happened) — the basis for correct windowing.
Late data :: Records arriving after their window closed, handled via watermarks and allowed lateness.
Micro-batch :: Processing a stream as small bounded batches — Spark Structured Streaming's original model.
Structured Streaming :: Spark's streaming API that treats a stream as an unbounded table queried incrementally.
Kappa architecture :: Serving batch and realtime needs from one log-based stream pipeline.
Backpressure :: Flow control where slow consumers make upstream slow down instead of buffering without bound.
Consumer group :: Set of Kafka consumers that splits a topic's partitions among its members.
Offset :: Per-partition position marker recording how far a consumer has read.
Retention :: How long a log or topic keeps records before deletion — time- or size-based.
Outbox pattern :: Writing events to an outbox table in the same transaction as state, then CDC-publishing them.
Rebalancing :: Reassigning partitions when consumers join or leave a group (or when Flink rescales operators).
Schema evolution :: Changing record structure over time under backward/forward/full compatibility rules.
Data contracts :: Explicit producer-consumer agreements on schema, semantics, and SLOs for a dataset.
SLO :: Service level objective — the reliability or freshness target a pipeline commits to.

## ML foundations
LLM :: Large language model — a transformer trained on next-token prediction over massive corpora.
Transformer :: Neural architecture built on self-attention instead of recurrence.
Attention :: Mechanism letting each token weigh every other token's representation — parallel and context-aware.
Tokenization :: Splitting text into subword units the model embeds and predicts.
BPE :: Byte-pair encoding — builds the subword vocabulary by iteratively merging frequent symbol pairs.
Prompt :: Input text conditioning the model; its design (instructions, few-shot examples) drives output quality.
Context window :: Maximum number of tokens a model can attend to in one request.
Temperature :: Sampling knob scaling logits — low is deterministic, high is diverse.
Fine-tuning :: Continued training of a pretrained model on task data to change its behavior.
LoRA :: Parameter-efficient fine-tuning that learns low-rank delta weights instead of updating the base model.
RLHF :: Reinforcement learning from human feedback — a reward model learned from preference rankings aligns an LLM.
word2vec :: Classic static embedding method trained with sliding-window prediction and negative sampling.
BERT :: Encoder-only transformer producing contextual text embeddings.
GNN :: Graph neural network producing node embeddings; dot products estimate edge likelihoods.
Autoregressive model :: Generates output token-by-token, each step conditioned on what came before.

## Retrieval, ranking & recsys
ANN :: Approximate nearest-neighbor search — sublinear retrieval over embeddings by trading exactness for speed.
HNSW :: Hierarchical graph ANN index; the default in most vector search engines.
Quantization :: Compressing vectors to fewer bits per dimension so indexes fit in memory.
Chunking :: Splitting documents into retrieval-sized passages for embedding and indexing.
Hallucination :: Fluent model output unsupported by sources or training facts.
Guardrails :: Policy layer filtering or constraining model inputs and outputs for safety and compliance.
Candidate generation :: First serving stage narrowing millions of items to hundreds for the ranker.
Collaborative filtering :: Recommending from interaction patterns alone; discovers well, suffers cold start.
Cold start :: No interaction history for new users or items; handled with content features and heuristics.
WALS :: Weighted alternating least squares — matrix-factorization solver that weights unobserved pairs.
FoF :: Friends-of-friends — social-graph candidate source for people recommendations.
DCN :: Deep and Cross Network — learns feature crosses explicitly instead of manual crossing.
DeepFM :: Factorization machine plus shared-embedding DNN — the classic CTR model.
GBDT :: Gradient-boosted decision trees — strong tabular baseline but hard to fine-tune continually.
CTR :: Click-through rate — probability a shown item is clicked; the core ads prediction.
Re-ranking :: Final serving stage applying business logic and filters the model should not own.
Continual learning :: Continuous finetune-evaluate-deploy loop, shipped only on metric improvement.

## Generative models
Diffusion :: Generative model that iteratively denoises random noise toward data, guided by conditioning.
U-Net :: Conv downsampling and upsampling denoiser backbone where cross-attention injects the prompt.
Cross-attention :: Attention where queries come from image features and keys and values from text embeddings.
VAE :: Variational autoencoder — encoder-decoder latent generative model; fast and stable, lower fidelity.
VQ-VAE :: Discrete tokenizer — CNN encoder, codebook quantization, decoder; turns images into tokens.
LDM :: Latent diffusion model — diffusion run in a VAE-compressed latent space for tractability.
DiT :: Diffusion transformer — a transformer over latent patches replacing the U-Net denoiser.
DDIM :: Deterministic sampler cutting diffusion inference from 1000 steps to about 20.
Classifier-free guidance :: Sampling trick that strengthens prompt adherence without a separate classifier.
GAN :: Generator versus discriminator adversarial training — fast one-pass generation, unstable training.
StyleGAN :: GAN with a layered latent space enabling fine-grained facial attribute editing.
Mode collapse :: GAN failure where the generator produces one plausible output regardless of input.
ViT :: Vision transformer treating image patches as tokens.
CLIP :: Contrastively trained image-text encoder pair enabling zero-shot scoring and multimodal conditioning.
CLIPScore :: Cosine similarity of CLIP text and image embeddings; measures prompt-image alignment.
DINO :: Visual-detail similarity metric that flags changes CLIP forgives.
DreamBooth :: Full finetuning personalization — best identity preservation, heaviest per subject.
Latent space :: Learned continuous space where encodings live and interpolation or attribute editing happens.
Beam search :: Decoding that keeps the top partial sequences — deterministic, quality-leaning alternative to sampling.

## Evaluation & defense
FID :: Frechet inception distance — distributional image quality and diversity metric.
FVD :: Frechet video distance over I3D features — captures temporal coherence per-frame metrics miss.
BLEU :: N-gram precision metric for translation and captioning.
ROUGE :: N-gram recall metric for summarization.
METEOR :: Alignment-based translation metric adding recall and stemming to n-gram matching.
CIDEr :: TF-IDF-weighted n-gram consensus metric for captioning against multiple references.
mAP :: Mean average precision over classes or thresholds — standard detection and ranking metric.
nDCG :: Normalized discounted cumulative gain — ranking metric handling graded relevance.
MRR :: Mean reciprocal rank — for retrieval with exactly one relevant item.
Recall@k :: Fraction of relevant items present in the top k results.
ROC-AUC :: Threshold-independent ranking quality metric.
A3 defense :: EPAM committee-form system design defense probing objective framing, pipeline, and metric choices.

## Edges
Databricks > Delta Lake :: Delta Lake is the platform's native table format.
Snowflake > Iceberg :: Snowflake reads and writes Iceberg tables for open interop.
Snowflake > Data contracts :: platform governance features publish contract-backed datasets.
Checkpoint > Exactly-once :: exactly-once recovery replays from durable state snapshots.
Medallion > Parquet :: lakehouse layers are stored in open columnar formats.
RAG > Embedding :: retrieval quality depends on embedding similarity.
AQE > Skew :: AQE detects and rewrites skewed joins at runtime.
Driver > Executor :: the driver schedules tasks; executors run them on partitions.
DAG > Shuffle :: stage boundaries in the DAG are exactly where shuffles happen.
Salting > Skew :: salted keys break up the hot partitions that skew stages.
Kafka > Offset :: consumer progress is tracked as per-partition offsets.
Kafka > Consumer group :: a group spreads a topic's partitions across its consumers.
Consumer group > Rebalancing :: membership changes trigger partition reassignment.
Outbox pattern > CDC :: the outbox table is the CDC source that publishes reliable domain events.
OLTP > CDC :: change capture streams the OLTP log into analytics.
Flink > Checkpoint :: barrier alignment snapshots operator state for consistent recovery.
Structured Streaming > Micro-batch :: Spark's streaming API began as micro-batches before continuous mode.
Kappa architecture > Lambda architecture :: kappa collapses the batch and speed layers onto one stream.
Backpressure > Flink :: credit-based flow control propagates slow-consumer pressure through Flink.
Lakehouse > Delta Lake :: ACID table formats are what turn a lake into a lakehouse.
Delta Lake > Time travel :: the transaction log keeps snapshots queryable as of any version.
Iceberg > Schema evolution :: hidden partitioning and schema evolution are first-class in Iceberg metadata.
SLO > Data contracts :: contracts pin the freshness and quality SLOs producers must meet.
Data contracts > Schema evolution :: contracts declare the compatibility rules schema changes must respect.
CAP theorem > Quorum :: quorum reads and writes are how stores navigate the consistency-availability tradeoff.
Raft > Consensus :: Raft is the replicable-log consensus protocol most systems cite.
Event time > Watermark :: watermarks track event-time progress and decide when windows close.
Watermark > Late data :: allowed lateness is judged against the watermark.
LLM > Transformer :: decoder-only transformers scaled up.
LLM > Autoregressive model :: LLMs generate token-by-token, each conditioned on the last.
Transformer > Attention :: self-attention replaces recurrence and enables parallel training.
Tokenization > BPE :: BPE builds the subword vocabulary tokenizers use.
LLM > Context window :: everything the model can use at inference must fit the window.
LLM > Prompt :: output quality is steered by instructions and few-shot examples.
LoRA > Fine-tuning :: low-rank adapters are the cheap fine-tuning path.
RLHF > LLM :: preference-trained alignment layered on pretrained LLMs.
BERT > Transformer :: encoder-only transformer for contextual embeddings.
word2vec > Embedding :: the classic static embedding baseline.
Embedding > ANN :: retrieval runs ANN over embedding indexes.
ANN > HNSW :: HNSW is the graph index most vector search engines ship.
RAG > Chunking :: retrieval quality starts with chunk granularity.
RAG > Re-ranking :: a cross-encoder rerank stage fixes first-stage retrieval noise.
RAG > Hallucination :: grounding in evidence reduces unsupported answers.
Guardrails > LLM :: the policy layer that wraps LLM inputs and outputs.
Candidate generation > ANN :: ANN narrows millions of items to hundreds.
Re-ranking > Candidate generation :: ranking refines what retrieval surfaces.
WALS > Collaborative filtering :: weighted ALS solves the matrix-factorization loss behind CF.
Collaborative filtering > Cold start :: CF has no signal for new users or items.
FoF > Candidate generation :: social hops are a cheap candidate source for people recommendations.
DCN > DeepFM :: both learn feature crosses over shared embeddings.
DeepFM > CTR :: the classic click-through-rate model pair.
Diffusion > U-Net :: the denoiser predicts noise at every step.
U-Net > Cross-attention :: the prompt enters the denoiser through cross-attention at every block.
Cross-attention > CLIP :: text embeddings from CLIP condition generation.
LDM > VAE :: latent diffusion runs in a VAE-compressed space.
LDM > Diffusion :: same denoising objective, executed in latent space.
DDIM > Diffusion :: fewer sampling steps along the same trajectory.
GAN > Mode collapse :: the generator loops on one plausible output.
StyleGAN > Latent space :: layered latent space enables attribute-level face editing.
ViT > Transformer :: image patches become tokens.
DreamBooth > Fine-tuning :: full per-subject finetuning buys identity preservation.
CLIPScore > CLIP :: cosine of CLIP embeddings scores prompt-image alignment.
DINO > CLIPScore :: DINO catches visual detail that CLIP forgives.
Beam search > Autoregressive model :: decoding over the partial sequences of AR models.
FID > GAN :: distributional quality metric born for GAN outputs.
FVD > FID :: adds temporal modeling that per-frame metrics miss.
Window functions > Catalyst :: Spark plans SQL window aggregates through the same Catalyst optimizer.
Iceberg > Parquet :: Iceberg tables store data as Parquet files behind the metadata tree.
Partitioning > Kafka :: Kafka partitions topics for parallel consumption the way compute partitions data.
mAP > Recall@k :: average precision aggregates precision across recall levels.
