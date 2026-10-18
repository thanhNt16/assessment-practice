## Patterns — Generative AI System Design Interview

Cross-note index of every framework, technique, and anti-pattern named in the 11 chapter notes (16–26). Sweep before a design round: each row maps one pattern to the note that owns it.

## Frameworks

| Pattern | When to use | One-line how | Ref |
|---|---|---|---|
| 7-step design framework | Every "design X" opener | Clarify → frame as ML task → data → model → evaluation → system design → deployment; user feedback loops back to data | [genai-overview](16-genai-overview.md) |
| Modality-first task framing | Step 2 of any design | Define input/output modality, then split: class/value → discriminative; new content → pick family by output modality (text: autoregressive; image/video/audio: diffusion, AR, VAE, GAN, flow) | [genai-overview](16-genai-overview.md) |
| Discriminative vs generative selection | Framing the ML task | P(Y\|X) classify/predict vs P(X)/P(X,Y) sample; generative trades cheap eval for new content | [genai-overview](16-genai-overview.md) |
| Scaling-law justification | "Why is this model good enough?" | OpenAI 2020: scaling beats arch tweaks; DeepMind 2022: data scales ~linearly with params; post-o1: budget test-time compute | [genai-overview](16-genai-overview.md) |
| Two-stage transfer training | Small task dataset | Pretrain on general text (next-token, cross-entropy) → finetune on task data (same objective); pretraining cost paid once, regularization free | [smart-compose](17-smart-compose.md), [machine-translation](18-machine-translation.md), [image-captioning](20-image-captioning.md) |
| Three-stage LLM training | Any LLM product round | Pretraining (trillions tokens, 1000s GPUs, months) → SFT (10–100K demos) → reward modeling (100K–1M comparisons) → PPO/DPO alignment | [chatbot-assistant](19-chatbot-assistant.md), [genai-overview](16-genai-overview.md) |
| Four-layer evaluation | LLM quality questions | Perplexity baseline → task benchmarks (MMLU, HumanEval, GSM8K) → safety benchmarks (toxicity, bias, truthfulness) → human + online (Arena) | [chatbot-assistant](19-chatbot-assistant.md) |
| Two-sided inference safety gates | Any generative serving path | Input safety filter rejects harmful prompts; output harm detector blocks unsafe generations; rejection generator handles both refusal paths | [chatbot-assistant](19-chatbot-assistant.md), [text-to-image](24-text-to-image.md), [text-to-video](26-text-to-video.md) |
| Encoder-decoder seq2seq split | Input/output different lengths | Bidirectional encoder builds source context; causally-masked decoder emits target via cross-attention into encoder output | [machine-translation](18-machine-translation.md) |
| Smart Compose serving pipeline | Keystroke-triggered LLM feature | Triggering service (min context + throttle) → phrase generator (beam top-k) → confidence/length filters → bias/NSFW post-processing → display | [smart-compose](17-smart-compose.md) |
| Captioning serving pipeline | Ambiguity-prone generation | Preprocess → beam-search generator → confidence-threshold gate disables suggestion → bias replacement/offense disable → output | [image-captioning](20-image-captioning.md) |
| RAG two-pipeline shape | Knowledge changes, citations needed | Offline: parse → chunk → embed → index; online: query → embed → ANN → prompt assembly → LLM | [rag](21-rag.md) |
| RAG triad evaluation | "The bot hallucinates" | Decompose: context relevance (hit rate, MRR, NDCG) → faithfulness (grounded in context) → answer relevance → answer correctness; fix differs per leg | [rag](21-rag.md) |
| LLM customization decision | "Why not finetune on our docs?" | Finetuning = style/terminology, no citations, retraining cost; prompt engineering = cheap, context-window-capped; RAG = current + citable; pick by knowledge volatility | [rag](21-rag.md) |
| Generative approach selection | Unconditional image generation | Score VAE/GAN/AR/diffusion on quality, speed, stability, control, latent manipulability vs requirements (latency SLA, attribute control) | [face-generation](22-face-generation.md) |
| Alternating freeze-train G/D loop | GAN training | Freeze G, train D a few iters on real+fake → freeze D, train G to fool it → repeat; imbalance is root of all three classic failures | [face-generation](22-face-generation.md) |
| Train→gate→deploy→retrain loop | Production generative service | Training service retrains periodically on user-approved outputs → evaluation service gates on predefined metrics → low-downtime deployment → monitor | [face-generation](22-face-generation.md) |
| Tokenizer + generator split | High-res AR generation | Stage I: VQ-VAE tokenizer (reconstruction losses); Stage II: decoder-only Transformer on cached token sequences; composed at inference | [high-res-synthesis](23-high-resolution-image-synthesis.md) |
| Split serving services | Two models, distinct resource profiles | Generation service (Transformer → tokens), decoding service (tokenizer decoder only), optional SR service — each scales independently | [high-res-synthesis](23-high-resolution-image-synthesis.md) |
| Diffusion 4-step training loop | Diffusion model training | Sample t uniformly from 1..1000 → noise x₀ per schedule → condition on text + timestep → predict noise ε → MSE vs true ε | [text-to-image](24-text-to-image.md) |
| Super-resolution cascade | Diffusion can't hit target resolution natively | Train base at low res (e.g. 64²), chain SR models to target (64→256→1024; spatial 4× + temporal 2× for video) | [text-to-image](24-text-to-image.md), [high-res-synthesis](23-high-resolution-image-synthesis.md), [text-to-video](26-text-to-video.md) |
| Data flywheel | Deployed generative product | Fold user prompts, generated images, and feedback back into the training set; retrain through the eval gate | [text-to-image](24-text-to-image.md) |
| Personalization method selection | "Personalize a foundation model" | Tuning-based (per-user finetune: TI / LoRA / DreamBooth scorecard) vs tuning-free (shared visual encoder); decide by identity fidelity + per-user cost + storage fate | [headshot-personalization](25-headshot-personalization.md) |
| Regenerate-on-failure loop | Identity/quality-critical generation | Generate → verify (face recognition vs user's real images) → re-sample with different initial noise on failure; gate, not post-hoc report | [headshot-personalization](25-headshot-personalization.md) |
| Bilingual vs multilingual decision | Multi-language pairs | One model per pair (accuracy, N-pair ops cost) vs one multilingual model (cheap ops, cross-pair interference); state pick with justification | [machine-translation](18-machine-translation.md) |
| Video three-axis evaluation | Any video generator | Frame quality (FID/IS) + temporal consistency (FVD) + alignment (CLIP); none covers the others; plus pairwise human eval | [text-to-video](26-text-to-video.md) |
| Image-as-foreign-language framing | Captioning/multimodal design | Treat image as source "language": image encoder → embedding sequence → decoder-only Transformer → caption token by token | [image-captioning](20-image-captioning.md) |
| Positional-encoding decision table | Context length changes | Absolute (short, fixed) vs relative (better distances, loses linear-attention tricks) vs RoPE (geometric relative position, generalizes to unseen) — driven by token budget, not fashion | [chatbot-assistant](19-chatbot-assistant.md) |

## Techniques

| Pattern | When to use | One-line how | Ref |
|---|---|---|---|
| Cleaning pipeline (harm/NSFW/quality/dedup) | Internet-scale corpora | Harm detection, NSFW removal, low-quality filtering, deduplication before training | [genai-overview](16-genai-overview.md) |
| Synthetic training data | Real data limited/imbalanced | Generate model-made samples for diversity; screen for inherited bias and distribution gaps | [genai-overview](16-genai-overview.md) |
| Distributed storage + retrieval efficiency | Petabyte corpora | HDFS/S3 + Parquet/ORC; sharding, Lucene/Elasticsearch indexing, caching | [genai-overview](16-genai-overview.md) |
| Scaled dot-product self-attention | Any Transformer answer | softmax(QKᵀ/√d_K)V with projected Q/K/V; multi-head attends in parallel subspaces | [genai-overview](16-genai-overview.md) |
| Gradient checkpointing | GPU memory bound | Save subset of activations, recompute in backward pass | [genai-overview](16-genai-overview.md) |
| Mixed precision (AMP) | Speed + memory without accuracy loss | Most math 16-bit, sensitive ops 32-bit | [genai-overview](16-genai-overview.md), [text-to-image](24-text-to-image.md) |
| Data parallelism | Model fits one device | Full copy per device, split data; sync = consistent but waits for slowest, async = stale versions | [genai-overview](16-genai-overview.md) |
| Pipeline parallelism | Very deep models | Split layers across devices (inter-layer) | [genai-overview](16-genai-overview.md) |
| Tensor parallelism | One layer exceeds device memory | Split single layer's ops column/row-wise (intra-layer) | [genai-overview](16-genai-overview.md) |
| Hybrid + ZeRO/FSDP | Largest models | Combine pipeline+tensor; shard optimizer state to cut redundancy | [genai-overview](16-genai-overview.md), [text-to-image](24-text-to-image.md) |
| FLOP cost math aloud | Cost questions | ops × params ÷ GPU TFLOP/s → GPU-years; converts hand-wave into a number | [genai-overview](16-genai-overview.md) |
| Subword tokenization (BPE/SentencePiece) | Any text model | ~50–150K vocab, unseen words decompose into known pieces; use Tiktoken/SentencePiece, don't hand-roll | [smart-compose](17-smart-compose.md), [machine-translation](18-machine-translation.md), [chatbot-assistant](19-chatbot-assistant.md) |
| BPE `</w>` boundary token | Explaining BPE mechanics | Start from characters, iteratively merge most frequent adjacent pair; `</w>` marks full-word vs prefix | [machine-translation](18-machine-translation.md) |
| Token ↔ ID vocab table | Tokenization step | Build vocabulary table mapping tokens to integer IDs | [smart-compose](17-smart-compose.md) |
| Confidential-content placeholdering | Email/private text corpora | Replace names/URLs/emails/phones with placeholders (`john@gmail.com` → `##@gmail.com`) | [smart-compose](17-smart-compose.md) |
| Format normalization | Inconsistent input formats | e.g. `(123) 456-7890` / `123-456-7890` → `1234567890` | [smart-compose](17-smart-compose.md) |
| PII anonymization in corpus prep | Privacy-law compliance | Anonymize PII across all crawled sources before training | [chatbot-assistant](19-chatbot-assistant.md) |
| Web corpus prep pipeline | Training on crawled data | Content extraction (Beautiful Soup, boilerplate detection) → URL/domain allow-blocklists → language ID (fastText) → quality filtering (readability, spam, ML) | [chatbot-assistant](19-chatbot-assistant.md) |
| Entity placeholders (ENTITY_1) | Named entities break generation | Substitute entities pre-translation, reinsert after decoding | [machine-translation](18-machine-translation.md) |
| Drop legacy NLP preprocessing | Modern Transformer input prep | No lowercasing, stop-word removal, stemming — they destroy grammatical/case signal | [machine-translation](18-machine-translation.md) |
| Language ID filtering (FastText) | Language-scoped models | Classify and keep only target-language text | [smart-compose](17-smart-compose.md), [chatbot-assistant](19-chatbot-assistant.md) |
| Perceptual-hash / CLIP dedup | Large image or video sets | Duplicate images via perceptual hashing or CLIP image encoder; duplicate captions via exact match or CLIP text-encoder similarity | [image-captioning](20-image-captioning.md), [text-to-image](24-text-to-image.md), [text-to-video](26-text-to-video.md) |
| CLIP relevance scoring (~0.25 threshold) | Noisy image–caption pairs | Pretrained CLIP scores pair relevance; drop pairs below threshold | [image-captioning](20-image-captioning.md) |
| LLM caption summarization | Captions longer than use case allows | Summarize long captions with an LLM (Llama) — training length imitates output length | [image-captioning](20-image-captioning.md) |
| CLIP-gated recaptioning (BLIP-3) | Raw web captions misaligned | CLIP-score each pair; replace weak captions with auto-generated; drop still-below-threshold pairs | [text-to-image](24-text-to-image.md) |
| Video caption re-captioning | Noisy/missing video captions | Generate missing, re-caption existing with video captioners (LLaVa, LLaMa3-Video); precompute caption embeddings | [text-to-video](26-text-to-video.md) |
| Aesthetics/quality model filtering | Ugly/blurry images poison quality | Drop blurry/over-/underexposed images scored by LAION Aesthetics Predictor; drop <min resolution | [image-captioning](20-image-captioning.md), [text-to-image](24-text-to-image.md) |
| Movie Gen video filtering | Video corpora | Drop low-res, short, slow-motion, compression-artifact clips | [text-to-video](26-text-to-video.md) |
| Video standardization | Heterogeneous video sources | Split into 5 s clips, re-encode to 24 FPS, resize/crop to target | [text-to-video](26-text-to-video.md) |
| Precompute + cache latents | Diffusion training on video | Run all videos through VAE once (~200 TB for 100M), skip per-step encoding | [text-to-video](26-text-to-video.md) |
| Cache token/embedding artifacts | Two-stage or encoder-heavy pipelines | Tokenize all images post-Stage-I (23); precompute T5 caption embeddings (24) | [high-res-synthesis](23-high-resolution-image-synthesis.md), [text-to-image](24-text-to-image.md) |
| Resize + center-crop | Uniform input dims, keep aspect ratio | Resize smaller side to target, center-crop the long side | [image-captioning](20-image-captioning.md), [text-to-image](24-text-to-image.md) |
| Classifier-tagged dataset rebalancing | Diversity requirement | Classifiers tag gender/age/attributes; rebalance before training — dataset bias becomes output bias | [face-generation](22-face-generation.md) |
| Image augmentation | Tiny finetune sets (10–20 images) | Mirror, slight rotations, scaling for artificial expansion | [face-generation](22-face-generation.md), [headshot-personalization](25-headshot-personalization.md) |
| Generic-face data mixing | Per-subject finetune | Mix pretrained-model-generated generic faces to prevent identity overfit and class forgetting | [headshot-personalization](25-headshot-personalization.md) |
| Upload data-quality gate | User-supplied training images | Face detection, blur/quality/expression assessors reject bad uploads; ask user rather than train anyway | [headshot-personalization](25-headshot-personalization.md) |
| Pixel-range normalization matched to output activation | Image model input/output contract | Normalize to [-1,1] with Tanh output (GAN) or [0,1] — mismatch breaks training | [face-generation](22-face-generation.md), [text-to-image](24-text-to-image.md) |
| LAION-400M augmentation | Self-supervised tokenizer training | Augment in-house images with LAION-400M for a richer codebook | [high-res-synthesis](23-high-resolution-image-synthesis.md) |
| Prompt template for multi-field context | Structured inputs beyond body text | Tag and concatenate subject/recipient/previous emails into one sequence; decouples architecture from input structure | [smart-compose](17-smart-compose.md) |
| Decoder-only for generation | Text/image generation tasks | Pick architecture by generation-vs-understanding: encoder-only = understanding, decoder-only = generation, enc-dec = transformation | [smart-compose](17-smart-compose.md), [image-captioning](20-image-captioning.md) |
| Cross-attention conditioning | Output steered by another sequence | Decoder attends to encoder output (translation) or text embeddings (U-Net: queries from image, K/V from text encoder) | [machine-translation](18-machine-translation.md), [text-to-image](24-text-to-image.md) |
| Causal masking in decoder | Any autoregressive decoder | Mask future tokens so generation sees only already-generated prefixes | [machine-translation](18-machine-translation.md) |
| MLM pretraining for encoder-decoder | Encoder-decoder pretraining | Mask input tokens, decoder predicts them — next-token lets encoder leak the answer | [machine-translation](18-machine-translation.md) |
| Start from public checkpoints | Skip pretraining cost | Initialize from T5/BART (enc-dec), GPT-2/Llama (decoder), CLIP/ViT (encoder) | [machine-translation](18-machine-translation.md), [image-captioning](20-image-captioning.md) |
| Fixed sine-cosine positional encoding | Fixed/short contexts, generalization wanted | No extra params, maps any position; Smart Compose's pick over learned | [smart-compose](17-smart-compose.md) |
| RoPE | Long context (≥4096) | Rotate embeddings by position-derived angle; relative position encoded geometrically, generalizes to unseen positions | [chatbot-assistant](19-chatbot-assistant.md), [text-to-video](26-text-to-video.md) |
| 1D vs 2D image positional encoding | Patch-based vision models | 1D = sequence position (ViT), 2D = row+col preserving spatial layout; no universal best — test combinations | [image-captioning](20-image-captioning.md) |
| Patchify | Image/video as token sequence | Divide into fixed patches → flatten → linearly project (3D patches for video DiT); ViT 256²/64² → 16 patches | [image-captioning](20-image-captioning.md), [text-to-image](24-text-to-image.md), [text-to-video](26-text-to-video.md) |
| Token-sequence encoder output | Detail-rich images | Emit per-patch token sequence, not one global vector — feeds attention, preserves local detail | [image-captioning](20-image-captioning.md) |
| ViT over CNN encoder | Long-range image dependencies | Self-attention over patch embeddings captures global relations conv receptive fields miss | [image-captioning](20-image-captioning.md) |
| Encoder-only classifier head | Sequence classification (language ID) | Average-pool token outputs or last-token representation → prediction head over classes | [machine-translation](18-machine-translation.md) |
| VQ-VAE codebook quantization | AR image generation, posterior collapse | Replace each latent with nearest codebook entry → integer token IDs; discretization forces decoder use and shrinks prediction space | [high-res-synthesis](23-high-resolution-image-synthesis.md) |
| Straight-through gradient | Quantizer in the loop | Copy decoder-input gradient directly to encoder output — nearest-neighbor lookup has no gradient | [high-res-synthesis](23-high-resolution-image-synthesis.md) |
| Stage-I loss quartet | High-res tokenizer | λrec·MSE + λquant·(stop-grad) + λperc·(VGG features) + λadv·(patch-based discriminator), weights tuned per goal | [high-res-synthesis](23-high-resolution-image-synthesis.md) |
| Perceptual loss | High-res artifacts under MSE-only | Distance between pretrained-VGG layer features of original vs reconstruction | [high-res-synthesis](23-high-resolution-image-synthesis.md) |
| Chunk-token autoregression | AR image generation latency bound | 64×64 px per token → 256 sequential steps for 1024² instead of ~1M pixel steps | [high-res-synthesis](23-high-resolution-image-synthesis.md) |
| Transposed convolution | Learned upsampling | Insert zeros between pixels then convolve; `ConvTranspose2d`; final block Tanh for [-1,1] | [face-generation](22-face-generation.md), [high-res-synthesis](23-high-resolution-image-synthesis.md) |
| Normalization layer selection | GAN/vision training stability | Batch (deep CNNs, G generators), Layer (small batches, Transformers), Instance (style transfer), Group (tiny batches) | [face-generation](22-face-generation.md) |
| GAN discriminator design | Binary real-vs-fake | Stride-2 Conv2D downsampling + BatchNorm + ReLU; FC head → sigmoid realness probability | [face-generation](22-face-generation.md) |
| Modified minimax loss | Vanishing gradients | Generator maximizes log D(G(z)) instead of minimizing -log D(G(z)) | [face-generation](22-face-generation.md) |
| Wasserstein loss (WGAN) | Mode collapse / vanishing gradients | Critic outputs realness score; loss = D(x) − D(G(z)) | [face-generation](22-face-generation.md) |
| Unrolled GAN | Mode collapse | Look ahead at discriminator updates when training generator | [face-generation](22-face-generation.md) |
| G/D imbalance mitigations | Non-convergence | Normalization, different learning rates for G/D, weight decay, noise into discriminator inputs | [face-generation](22-face-generation.md) |
| Minimax objective framing | GAN loss answer | D minimizes BCE; G minimizes -log D(G(z)); unified minimax — D maximizes, G minimizes | [face-generation](22-face-generation.md) |
| Random vs truncated latent sampling | GAN inference diversity dial | Standard Gaussian over full space = diversity; high-probability region = realism at diversity's cost; random default for faces | [face-generation](22-face-generation.md) |
| StyleGAN latent adjustment | Deferred attribute control | Adjust latent vector per age/gender/expression in the structured latent space | [face-generation](22-face-generation.md) |
| Latent diffusion (LDM) | Pixel-space too expensive | Denoise VAE-compressed latents; 8×8×8 factor → 512× cheaper for 720p×120f | [text-to-image](24-text-to-image.md), [text-to-video](26-text-to-video.md) |
| Noise prediction (ε, not x₀) | Diffusion training objective | Predict the noise added; predicting clean image directly underperforms | [text-to-image](24-text-to-image.md) |
| Noise schedule + reparameterization | Diffusion forward process | β_t grows with t; closed-form jump from x₀ to any x_t without iterating | [text-to-image](24-text-to-image.md) |
| Classifier-free guidance | Prompt alignment | Train with and without prompt; at sampling amplify conditioned mode, shrink unconditioned | [text-to-image](24-text-to-image.md), [headshot-personalization](25-headshot-personalization.md) |
| DDIM | Latency SLA | Cut diffusion steps 1,000 → as few as 20 at minimal quality cost | [text-to-image](24-text-to-image.md) |
| Distillation / quantization / parallel sampling | Per-step inference cost | Compress or parallelize billion-parameter denoiser steps to meet SLA | [text-to-image](24-text-to-image.md) |
| Rank-don't-score annotation | Preference data collection | Annotators rank response pairs (absolute scores drift between annotators); rankings become (prompt, winning, losing) pairs | [chatbot-assistant](19-chatbot-assistant.md) |
| Margin ranking loss | Reward model training | Penalize when score(win) − score(lose) < margin m; optimizer pushes the gap open | [chatbot-assistant](19-chatbot-assistant.md) |
| Reward model architecture | RLHF stage 3 | Transformer + scalar head, typically SFT-model copy; size has no consistent pattern (6B for 175B LM) | [chatbot-assistant](19-chatbot-assistant.md) |
| PPO/DPO loop | Alignment optimization | Generate multiple responses → reward model scores → update toward high-scoring; internals out of scope, say so | [chatbot-assistant](19-chatbot-assistant.md) |
| Top-p/nucleus decoding | Open-ended generation default | Smallest set with cumulative probability > p — adaptive to sharp vs flat distributions | [chatbot-assistant](19-chatbot-assistant.md), [high-res-synthesis](23-high-resolution-image-synthesis.md) |
| Temperature tuning | Output randomness dial | T scales logits pre-softmax; 0.1–1.5 modern practice, tune per task; T=0 deterministic | [chatbot-assistant](19-chatbot-assistant.md), [high-res-synthesis](23-high-resolution-image-synthesis.md) |
| Repetition penalty knobs | Repetitive outputs | `no_repeat_ngram_size` (HF), `frequency_penalty` (ChatGPT API) | [chatbot-assistant](19-chatbot-assistant.md) |
| Beam search | Short, consistency-critical outputs | Track top-k sequences, prune by cumulative probability, stop at EOS; deterministic — same input, same output | [smart-compose](17-smart-compose.md), [machine-translation](18-machine-translation.md), [image-captioning](20-image-captioning.md) |
| Multi-candidate sampling + selection | Quality-critical dialogue | Sample multiple responses, pick best by predefined criteria | [chatbot-assistant](19-chatbot-assistant.md) |
| Hand-engineered prompt set | Users give no prompts | One curated prompt per output template ("A professional headshot of [V] smiling...") | [headshot-personalization](25-headshot-personalization.md) |
| Textual inversion | Tiny budget, text-driven identity | Train one token embedding `S*` only; model/text encoder frozen; minimal storage, weak detail | [headshot-personalization](25-headshot-personalization.md) |
| LoRA | Low storage, fast adaptation | Freeze W, learn low-rank ΔW = AB; params drop from d_in×d_out to r×(d_in+d_out); MBs per adapter | [headshot-personalization](25-headshot-personalization.md) |
| DreamBooth | Max identity fidelity | Finetune all diffusion params on subject images; ~15 min; GB storage per subject (void if models discarded) | [headshot-personalization](25-headshot-personalization.md) |
| Rare-token identifier | DreamBooth subject marker | `[V]` from rare vocabulary tokens: distinct yet tokenizer-cohesive; frequency-distribution scan → generate → decode ("SKS", "XyZ") | [headshot-personalization](25-headshot-personalization.md) |
| Class-specific prior preservation loss | Full-parameter finetune | α·reconstruction + β·prior-preservation keeps the generic class intact while learning the instance | [headshot-personalization](25-headshot-personalization.md) |
| Tuning-free personalization | One shared model, per-image identity | Finetune base + visual encoder once; encoder injects reference-image features without per-user weights (Imagine Yourself, InstantID) | [headshot-personalization](25-headshot-personalization.md) |
| Joint image+video training | Scarce video–text pairs | Treat every image as a single-frame video; one training stage (vs pretrain-image → finetune-video) | [text-to-video](26-text-to-video.md) |
| Temporal attention + temporal convolution | Extending image U-Net to video | Interleave across-frame attention and 3D conv into every down/up block | [text-to-video](26-text-to-video.md) |
| DiT for video | New video-generation builds | 3D patchify → positional encoding → Transformer w/ text cross-attention → unpatchify; scales with data+compute (Sora, Movie Gen) | [text-to-video](26-text-to-video.md) |
| Spatial + temporal SR | Target resolution/FPS beyond generator | Generate low-res/low-FPS latents → spatial SR (720p→1080p/4K) + temporal SR (12→24 FPS interpolation) | [text-to-video](26-text-to-video.md) |
| Efficient attention + MoE | Attention cost at video scale | Near-linear attention (HyperAttention); sparse expert compute; tensor parallelism across devices | [text-to-video](26-text-to-video.md) |
| Triggering service | Keystroke-triggered suggestions | Activate only with enough context ("I hope" yes, "I" no); throttle suggestion frequency | [smart-compose](17-smart-compose.md) |
| Confidence/length filters | Suggestion candidates | Drop long and low-confidence beam candidates before display; guards trust and acceptance rate | [smart-compose](17-smart-compose.md) |
| Confidence-threshold gate | Ambiguous inputs | Disable suggestion when cumulative beam probability falls below threshold — design the skip path | [image-captioning](20-image-captioning.md) |
| Rule-based bias post-processing | Explicit fairness requirement | Pronoun neutralization (he/she→they), gender-neutral terms (chairman→chairperson), flagged-term lexical analysis, NSFW keywords; full disable on offense | [smart-compose](17-smart-compose.md), [image-captioning](20-image-captioning.md) |
| Prompt enhancer | Sparse user prompts | Expand acronyms, fix typos, add context before the LLM — cheap quality win | [chatbot-assistant](19-chatbot-assistant.md), [text-to-image](24-text-to-image.md), [text-to-video](26-text-to-video.md) |
| Session management | Follow-up turns | Feed chat history with the enhanced prompt — the whole mechanism for follow-up coherence | [chatbot-assistant](19-chatbot-assistant.md) |
| Rejection response generator | Unsafe input or output | Polite refusal path wired to both input filter and output evaluator | [chatbot-assistant](19-chatbot-assistant.md) |
| AI-based document parsing | Mixed/varied layouts | Layout detection (object-detection boxes) → per-box OCR in reading order → structured blocks (LayoutParser, Dedoc, Document AI) | [rag](21-rag.md) |
| Structure-aware chunking | Meaningful retrieval units | `MarkdownHeaderTextSplitter`/`HTMLHeaderTextSplitter` preserve hierarchy; length-based splitters need `chunk_size` + `overlap` | [rag](21-rag.md) |
| Chunk math capacity planning | Index sizing | pages × chunks-per-page × growth: 5M × (1500/(500−200) + 3) ≈ 40M chunks, +20%/yr | [rag](21-rag.md) |
| ANN over exact search | Tens of millions of vectors | Clustering-based (FAISS/ScaNN), LSH, graph-based HNSW, tree-based; ~O(log(N)×D) vs O(N×D); exact stays as correctness benchmark | [rag](21-rag.md) |
| Shared embedding space | Retrieval invariant | Same text encoder embeds docs and queries; images aligned via CLIP or caption-then-embed | [rag](21-rag.md) |
| Query expansion | Retrieval misses | Rewrite query (fix typos, broaden scope) before embedding (Query2doc) | [rag](21-rag.md) |
| CoT / few-shot / role / user-context prompting | Generation quality levers | CoT for multi-hop across docs; few-shot sets format; expert persona; user profile with "use only if relevant" | [rag](21-rag.md) |
| Citation-format prompting | RAG trust requirement | "Answer sentences end with `[1]`", no References section; assembled with role + retrieved context + user context | [rag](21-rag.md) |
| RAFT (distractor-penalty finetuning) | Noisy retrieval is unavoidable | Label retrieved docs golden vs distractor; finetune LLM with loss penalizing distractor use — after fixing retrieval + prompts first | [rag](21-rag.md) |
| Perplexity | LLM offline baseline | exp of avg negative log-likelihood; lower = better next-token prediction; never sufficient alone | [smart-compose](17-smart-compose.md), [chatbot-assistant](19-chatbot-assistant.md) |
| ExactMatch@N | Suggestion quality offline | % of generations matching first N ground-truth words, averaged across lengths | [smart-compose](17-smart-compose.md) |
| BLEU / ROUGE / METEOR trio | Seq2seq offline metrics | BLEU = precision + brevity penalty; ROUGE = recall; METEOR = harmonic mean w/ synonym/stem matching (best human correlation, slow) | [machine-translation](18-machine-translation.md) |
| CIDEr | Captioning evaluation | TF-IDF vectors → cosine similarity vs each reference → mean; consensus-based, knows word-order and novelty blind spots | [image-captioning](20-image-captioning.md) |
| Multi-reference validation data | Subjective outputs | Several annotators caption each held-out image — robust to phrasing variety, fairer evaluation | [image-captioning](20-image-captioning.md) |
| IS / FID / KID | Image generation offline | IS: peaked per-image + uniform marginal (higher better); FID: Fréchet distance of Inception features (lower better); KID kernel distance | [face-generation](22-face-generation.md), [high-res-synthesis](23-high-resolution-image-synthesis.md), [text-to-image](24-text-to-image.md) |
| FVD | Video temporal consistency | I3D features → Fréchet distance between generated vs real video distributions; lower better | [text-to-video](26-text-to-video.md) |
| CLIPScore | Image–text alignment | Cosine similarity of CLIP text/image embeddings | [text-to-image](24-text-to-image.md), [headshot-personalization](25-headshot-personalization.md) |
| DINO vs CLIP axis selection | Image-to-image vs image-to-text scoring | DINO captures fine visual detail (jacket color); CLIP captures semantics; pick by comparison type | [headshot-personalization](25-headshot-personalization.md) |
| Facial similarity score | Identity verification | Pretrained face-recognition model — CLIP/DINO score different faces as similar; all three metrics combined = full coverage | [headshot-personalization](25-headshot-personalization.md) |
| Safety benchmark suites | LLM safety evaluation | RealToxicityPrompts/PerspectiveAPI, ToxiGen, HateCheck; CrowS-Pairs, BBQ, BOLD; TruthfulQA, PrivacyQA, AdvGLUE, TextFooler | [chatbot-assistant](19-chatbot-assistant.md) |
| Pairwise human evaluation | Metrics miss photorealism/aesthetics | Users pick the more realistic of two outputs; most reliable signal despite metric disagreements with Inception-based scores | [face-generation](22-face-generation.md), [text-to-video](26-text-to-video.md), [text-to-image](24-text-to-image.md) |
| Curated prompt benchmarks | Standardized offline eval | DrawBench (composition/interaction); VBench, Movie Gen Bench (motion coherence, temporal consistency) | [text-to-image](24-text-to-image.md), [text-to-video](26-text-to-video.md) |
| LLM-as-judge + Ragas/ARES | Faithfulness at scale | Automated fact-checking and consistency checks across queries; LLM compares Q&A for relevance | [rag](21-rag.md) |
| LMSYS Chatbot Arena | Online LLM ranking | Ranks on 800K+ crowdsourced pairwise comparisons | [chatbot-assistant](19-chatbot-assistant.md) |
| Online business metrics | Product-value proof | Acceptance rate, completion time, response latency (17); CTR/conversion/churn (16, 24); satisfaction 1–5 + paid conversion (25) | [smart-compose](17-smart-compose.md), [genai-overview](16-genai-overview.md), [headshot-personalization](25-headshot-personalization.md) |
| Cost-per-user monitoring | Dissatisfaction proxy | Unhappy users re-roll prompts with new seeds; spend compounds — watch monthly cost per user | [text-to-image](24-text-to-image.md) |
| Ops cost metrics | Unit economics | Time per image + cost per generation alongside latency budget | [high-res-synthesis](23-high-resolution-image-synthesis.md) |

## Anti-patterns

| Anti-pattern | Symptom | Fix | Ref |
|---|---|---|---|
| Model = whole system | No answer to "how does this ship to millions safely?" | Design safety filters, eval, monitoring, feedback loops as components | [genai-overview](16-genai-overview.md) |
| Synthetic data without scrutiny | Degraded output diversity | Screen source-model bias/errors and real-world distribution gaps | [genai-overview](16-genai-overview.md) |
| Scaling params without data | Bigger model, no loss improvement | Compute-optimal: data scales ~linearly with params | [genai-overview](16-genai-overview.md) |
| Confusing parameters with FLOPs | Wrong optimization target when cost-constrained | Run the FLOP math; dense layers cost more compute than sparse at equal params | [genai-overview](16-genai-overview.md) |
| Deferring non-functional requirements | Architecture rework during tuning | Identify latency/throughput/fairness/security early; they drive performance work | [genai-overview](16-genai-overview.md) |
| Single-metric generative evaluation | One FID score misses prompt alignment, safety, bias | Assess multiple angles: quality, alignment, safety, bias | [genai-overview](16-genai-overview.md) |
| Sync data parallelism at scale | Every step waits for the slowest device | Async parallelism (accepting stale-parameter inconsistency) | [genai-overview](16-genai-overview.md) |
| From-scratch training on task data | Great on training emails, poor generalization | Pretrain on general data → finetune on task data | [smart-compose](17-smart-compose.md) |
| Body-only input | Never suggests "John" after "Dear" — useless greetings | Prompt-template the full context: subject, recipient, sender, previous emails | [smart-compose](17-smart-compose.md) |
| No positional encoding | Bag-of-words behavior, order-blind predictions | Add positional encoding — attention is permutation-invariant without it | [smart-compose](17-smart-compose.md) |
| Greedy search in production | Repetitive degenerate loops ("I'm not sure if I'll ever...") | Beam search for short consistency-critical outputs | [smart-compose](17-smart-compose.md) |
| Learned positional encoding on varied lengths | Overfits training lengths, degrades on others | Fixed sine-cosine | [smart-compose](17-smart-compose.md) |
| Character- or word-level tokenization | Poor performance, or a 300K+ vocab making training slow/costly | Subword BPE/SentencePiece | [smart-compose](17-smart-compose.md), [machine-translation](18-machine-translation.md) |
| Skipping confidence/length filters | Users see long, half-confident guesses — trust collapses, acceptance drops | Filter beam candidates by length and score | [smart-compose](17-smart-compose.md) |
| No post-processing | Biased or NSFW suggestions reach users | Rule-based bias control + NSFW keyword filtering | [smart-compose](17-smart-compose.md) |
| Encoder "cheating" in pretraining | Full-sentence input + next-token objective leaks the answer | MLM pretraining — masked tokens never visible during encoding | [machine-translation](18-machine-translation.md) |
| Named entities mistranslated/dropped | Models choke on uncommon proper nouns | Placeholder-substitute (ENTITY_1), reinsert after decoding | [machine-translation](18-machine-translation.md) |
| Unmasked decoder self-attention | Decoder attends to future positions, breaks generation | Causal masking — mandatory | [machine-translation](18-machine-translation.md) |
| Trusting BLEU alone | Correct-but-different wording punished | Pair with METEOR + human/user feedback | [machine-translation](18-machine-translation.md) |
| Stochastic sampling in translation | Inconsistent translations for identical input | Beam search — determinism is the feature | [machine-translation](18-machine-translation.md), [smart-compose](17-smart-compose.md), [image-captioning](20-image-captioning.md) |
| Wrong language detected → wrong model routed | Detector failure silently degrades output | Treat the language detector as a load-bearing classifier | [machine-translation](18-machine-translation.md) |
| Bilingual fleet sprawl | N-pair models multiply train/deploy/maintain cost | Choose deliberately via accuracy-vs-ops table; multilingual (mT5/mBART) is closing the gap | [machine-translation](18-machine-translation.md) |
| Deploying the base model | Chatbot completes sentences, never responds | SFT — turns text-continuer into responder | [chatbot-assistant](19-chatbot-assistant.md) |
| Stopping at SFT | Plausible but unhelpful/unsafe answers | RLHF alignment stage (reward model + PPO/DPO) | [chatbot-assistant](19-chatbot-assistant.md) |
| Deterministic decoding for dialogue | Repetition loops, generic text | Stochastic top-p + tuned temperature | [chatbot-assistant](19-chatbot-assistant.md) |
| Raw multinomial sampling | Flat distributions → incoherent output | Top-k or top-p truncation; multinomial rarely used | [chatbot-assistant](19-chatbot-assistant.md) |
| Top-k with fixed k | Sharp distributions lose the 89%-obvious token; flat ones get capped variety | Top-p/nucleus — adaptive set size | [chatbot-assistant](19-chatbot-assistant.md) |
| Temperature mis-set | Too high → erratic/off-topic; too low → repetition | Tune 0.1–1.5 per task; both extremes are tuning signals, not model bugs | [chatbot-assistant](19-chatbot-assistant.md) |
| Absolute positional encoding at long context | Trained at 512, breaks at 4096 | RoPE-style relative encoding | [chatbot-assistant](19-chatbot-assistant.md) |
| Scoring instead of ranking annotations | Numeric scores drift between annotators | Rank-don't-score; convert rankings to preference pairs | [chatbot-assistant](19-chatbot-assistant.md) |
| Skipping dedup | Duplicate articles overexpose the model | Deduplicate during corpus prep | [chatbot-assistant](19-chatbot-assistant.md), [text-to-image](24-text-to-image.md) |
| Training on raw noisy pairs | Off-language or wrong captions at inference | Run the filter pipeline: language, dedup, CLIP relevance, summarization | [image-captioning](20-image-captioning.md) |
| Skipping long-caption summarization | Verbose outputs unusable as name suggestions | LLM-summarize captions to target length | [image-captioning](20-image-captioning.md) |
| Single-token encoder for detail-rich images | Generic captions missing objects/actions | Per-patch token sequence from the encoder | [image-captioning](20-image-captioning.md) |
| CNN encoder despite long-range needs | Captions describe parts in isolation | Transformer/ViT encoder | [image-captioning](20-image-captioning.md) |
| Trusting CIDEr alone | Penalizes novel-but-correct captions; "coffee on table" ≈ "table on coffee" | Pair with human review | [image-captioning](20-image-captioning.md) |
| Serving without confidence gating | Ambiguous images get confidently wrong suggestions | Gate on cumulative beam probability | [image-captioning](20-image-captioning.md) |
| Serving without bias/offense post-processing | Biased terms or offensive words reach users | Neutral-term replacement; disable service on offense | [image-captioning](20-image-captioning.md) |
| Rule-based parser on mixed layouts | Garbled text/reading order → answers cite content in no doc | AI-based parsing when formats vary | [rag](21-rag.md) |
| Indexing whole documents as one vector | Gist only, misses details; busts token limits | Chunk first | [rag](21-rag.md) |
| Naive length chunking | Sentences/sections split mid-thought → fragmented chunks | Overlap or structure-aware splitters | [rag](21-rag.md) |
| Exact NN at 40M scale | 40M comparisons per query — latency/cost blowup | ANN (clustering/LSH/HNSW); accept approximate recall | [rag](21-rag.md) |
| Trusting retrieval blindly | Distractor docs mislead the LLM | RAFT-style training or better ranking | [rag](21-rag.md) |
| Prompt engineering as the whole solution | Works until external knowledge exceeds context window | RAG — retrieval is non-negotiable at scale | [rag](21-rag.md) |
| Low faithfulness | Plausible answers ungrounded in retrieved context | Detect via the triad, not end-to-end vibes; fix retrieval vs generation separately | [rag](21-rag.md) |
| Discriminator dominates | Vanishing gradients; generator loss flatlines early | Modified minimax or WGAN critic | [face-generation](22-face-generation.md) |
| Mode collapse | Near-identical faces despite diverse latent samples | Wasserstein loss, unrolled GAN | [face-generation](22-face-generation.md) |
| Training past the usefulness point | D accuracy → 50% coin-flip, feedback becomes noise, quality degrades | Monitor D accuracy; stop at balance | [face-generation](22-face-generation.md) |
| Skewed dataset | Demographic skew in generated outputs | Classifier-tagged rebalancing before training | [face-generation](22-face-generation.md) |
| Pixel-range mismatch | [-1,1] normalization paired with ReLU output | Tanh final activation matching the normalization | [face-generation](22-face-generation.md) |
| Trusting automated metrics alone | Good FID, unhappy users — ImageNet artifact misalignment | Pairwise human evaluation | [face-generation](22-face-generation.md) |
| Posterior collapse | Outputs converge to near-identical images; decoder ignores latents | Discretize latents with a quantizer (VQ-VAE) | [high-res-synthesis](23-high-resolution-image-synthesis.md) |
| Pixel-level autoregression | ~1M sequential steps at 1024² — blows the latency budget | Chunk tokens: 64×64 px/token → 256 steps | [high-res-synthesis](23-high-resolution-image-synthesis.md) |
| MSE-only tokenizer at high resolution | Pixel error looks fine, images show artifacts | Add perceptual + adversarial losses | [high-res-synthesis](23-high-resolution-image-synthesis.md) |
| Assuming the quantizer backpropagates | Encoder training silently stalls — no gradient through nearest-neighbor lookup | Straight-through gradient copy | [high-res-synthesis](23-high-resolution-image-synthesis.md) |
| Deploying the tokenizer encoder | Wasted inference compute — it is training-only | Ship the decoder only | [high-res-synthesis](23-high-resolution-image-synthesis.md) |
| Monolithic generation+decoding service | Distinct latency/resource profiles make independent scaling impossible | Split services | [high-res-synthesis](23-high-resolution-image-synthesis.md) |
| Ignoring cost per generation | Latency-only monitoring misses revenue impact | Track cost alongside time-per-image | [high-res-synthesis](23-high-resolution-image-synthesis.md) |
| Skipping dedup at image scale | Overfits repeated images → bias toward frequent subjects, same compositions across prompts | Perceptual dedup before training | [text-to-image](24-text-to-image.md) |
| Trusting raw web captions | Good images, wrong content — poorly matched pairs dilute prompt-image alignment | CLIP-score gating + BLIP-3 recaptioning | [text-to-image](24-text-to-image.md) |
| Naive diffusion sampling | Prompt fidelity and latency both fail | Volunteer CFG + DDIM | [text-to-image](24-text-to-image.md) |
| Generating at 1024 directly | Diffusion can't do high-res natively — SLA blown | Super-resolution cascade | [text-to-image](24-text-to-image.md) |
| One safety gate only | Model-generated harm slips past prompt filtering (benign-ish prompt → unsafe image) | Two gates: prompt classifier + output harm detection | [text-to-image](24-text-to-image.md), [text-to-video](26-text-to-video.md) |
| Predicting x₀ instead of ε | Harder task, worse convergence | Predict noise ε — the one non-negotiable training detail | [text-to-image](24-text-to-image.md) |
| Common-word identifier ("special") | Established meaning fights the new subject binding | Rare-token identifier | [headshot-personalization](25-headshot-personalization.md) |
| Random-string identifier ("xxy5syt00") | Tokenizer fragments it; outputs contaminated by fragment meanings | Rare-token identifier — distinct yet cohesive | [headshot-personalization](25-headshot-personalization.md) |
| Finetuning on user images alone | Overfits identity, forgets generic face class — can't render "a person" | Generic face data + class-specific prior preservation loss | [headshot-personalization](25-headshot-personalization.md) |
| Trusting CLIP/DINO for identity | Two different faces score high | Face-recognition model as the identity gate | [headshot-personalization](25-headshot-personalization.md) |
| Ignoring bad uploads | Dark or face-less images poison finetuning | Gate at ingestion; ask user for better images | [headshot-personalization](25-headshot-personalization.md) |
| Skipping the regeneration loop | Failed identity check ships anyway — user-visible deepfake-quality bug | Re-sample with different initial noise on QA failure | [headshot-personalization](25-headshot-personalization.md) |
| Pixel-space diffusion at 720p/120 frames | ~7 min per video on an H100 — compute budget blown before scale-up | LDM: denoise 512× smaller latents | [text-to-video](26-text-to-video.md) |
| Encoding latents on the fly during training | Diffusion training dominated by per-step VAE preprocessing | Precompute + cache all latents (~200 TB) | [text-to-video](26-text-to-video.md) |
| Judging videos by FID/IS alone | Flickery videos pass — sharp frames, jerky motion | Add FVD for temporal consistency | [text-to-video](26-text-to-video.md) |
| Reusing image U-Net unchanged | Inconsistent motion across frames — layers are within-frame only | Interleave temporal attention + temporal convolution | [text-to-video](26-text-to-video.md) |
| Training only on video–text pairs | Paired video data scarce → undertrained visual foundation | Fold in image–text data as single-frame videos | [text-to-video](26-text-to-video.md) |
| Training DiT at target resolution | 1080p/4K multiplies cost | Generate low-res/low-FPS; restore with spatial + temporal SR | [text-to-video](26-text-to-video.md) |
| Trusting noisy/short source captions | Misaligned conditioning degrades text alignment | Re-caption with LLaVA/LLaMa3-Video | [text-to-video](26-text-to-video.md) |
