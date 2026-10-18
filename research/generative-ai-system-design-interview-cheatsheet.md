## Cheatsheet — Generative AI System Design Interview

### Decision table — If / Then

| If | Then |
|---|---|
| Latency <1s AND latent manipulation is a stretch goal | GAN — one forward pass, structured latent space (StyleGAN); accept unstable training ([face-gen](22-face-generation.md)) |
| Quality beats latency (~10s OK, max 1024²) | Diffusion over autoregressive — superior fine detail, tunable sampling steps; pay implementation complexity ([t2i](24-text-to-image.md)) |
| High-res image gen (1024²+) at seconds latency | Autoregressive over chunk tokens (VQ-VAE tokenizer + decoder-only Transformer): 256 steps vs ~1M pixel steps ([hires](23-high-resolution-image-synthesis.md)) |
| Diffusion at 1024² output | Base model at low res + super-resolution cascade (64→256→1024); diffusion can't hit high res directly ([t2i](24-text-to-image.md)) |
| VAE/GAN at ≥512px | Posterior collapse — discrete quantizer (VQ-VAE codebook) forces decoder to use latents ([hires](23-high-resolution-image-synthesis.md)) |
| Text-to-video | Latent diffusion (not pixel: 7 min/video) + DiT + spatial SR (4×) + temporal SR (12→24 FPS) ([t2v](26-text-to-video.md)) |
| Context window 4096 tokens | RoPE positional encoding; absolute breaks when trained at 512 ([chatbot](19-chatbot-assistant.md)) |
| Decoding for open-ended chat | Top-p (nucleus) + tuned temperature (0.1–1.5); deterministic search = repetition loops ([chatbot](19-chatbot-assistant.md)) |
| Decoding for typed-text completion / translation / captions | Deterministic: beam search — consistency wanted, diversity unwanted ([smart-compose](17-ml-design.md), [mt](18-machine-translation.md), [captioning](20-image-captioning.md)) |
| Output is new content, text modality | Autoregressive decoder-only; encoder-only = understanding, encoder-decoder = output transforms input ([smart-compose](17-ml-design.md)) |
| Seq2seq with variable-length I/O (translation, captioning) | Encoder-decoder: bidirectional encoder + causally-masked decoder + cross-attention ([mt](18-machine-translation.md), [captioning](20-image-captioning.md)) |
| Pretraining an encoder-decoder | MLM objective, not next-token — full-sentence input lets the encoder "cheat" ([mt](18-machine-translation.md)) |
| Knowledge changes (~20%/yr) AND answers must cite sources | RAG; finetuning only for behavior/style, never facts, never citations ([rag](21-rag.md)) |
| 40M+ vectors to search | ANN (clustering/LSH/HNSW), never exact O(N×D) — accept approximate recall ([rag](21-rag.md)) |
| Mixed-layout PDF corpus | AI-based parsing (layout detection + OCR); rule-based breaks on varied columns ([rag](21-rag.md)) |
| Chatbot hallucinates | Decompose with the RAG triad first: retrieval miss (context relevance) vs LLM ignoring context (faithfulness) — fixes differ ([rag](21-rag.md)) |
| Annotating chatbot preference data | Rank, don't score — absolute scores drift between annotators ([chatbot](19-chatbot-assistant.md)) |
| Personalization where identity fidelity is the product, models discarded after use | DreamBooth (full finetune, ~15 min); switch to LoRA if models must persist ([headshot](25-headshot-personalization.md)) |
| Personalization storage/concurrency constraint | LoRA — MB adapters, base model untouched; textual inversion only when budget is tiny ([headshot](25-headshot-personalization.md)) |
| Identity check on generated faces | Face recognition model — CLIP/DINO score different faces as similar ([headshot](25-headshot-personalization.md)) |
| Dataset demographically skewed | Classifier-tagged rebalance before training — dataset bias becomes output bias ([face-gen](22-face-generation.md)) |
| Caption–image pairs at scale, weak captions | CLIP-score gating + BLIP recaptioning; misaligned pairs teach the model to ignore text ([captioning](20-image-captioning.md), [t2i](24-text-to-image.md)) |
| Safety in a generative product | Two gates: prompt safety before compute + harm detection after generation — one gate misses model-generated harm ([chatbot](19-chatbot-assistant.md), [t2i](24-text-to-image.md), [t2v](26-text-to-video.md)) |
| Two coupled models with distinct latency/resource profiles | Split services, scale independently; deploy only the needed halves (tokenizer decoder only, encoder never ships) ([hires](23-high-resolution-image-synthesis.md)) |
| Architecture detail question (diffusion backbone, positional encoding) | Name the trade-off, pick, and say what you'd validate empirically — no universal best ([t2i](24-text-to-image.md), [captioning](20-image-captioning.md), [t2v](26-text-to-video.md)) |

### Quick rules

- Answer skeleton: 2–3 clarifying questions (business goal, scale, quality-vs-speed) → modality → algorithm family, in the first 5 minutes ([overview](16-genai-design.md)).
- Scaling laws are the justification: scaling beats arch tweaks (OpenAI 2020); data ~linear with params (DeepMind 2022); budget test-time compute as a quality lever ([overview](16-genai-design.md)).
- Cost math aloud: ops × params ÷ GPU TFLOP/s → GPU-years; converts hand-wave into a number ([overview](16-genai-design.md)).
- Tokenization: always subword (BPE/SentencePiece), use existing libraries, never hand-roll; char-level ~100 vocab performs poorly, word-level 300K+ vocab is impractical ([smart-compose](17-ml-design.md), [mt](18-machine-translation.md)).
- Never train from scratch on task data: pretrain on general text → finetune on task data; or start from public checkpoints (T5/BART/GPT-2/Llama) to skip pretraining cost ([smart-compose](17-ml-design.md), [mt](18-machine-translation.md), [captioning](20-image-captioning.md)).
- Three-stage LLM training, data quality inverts: trillions of low-quality tokens → 10K–100K demonstrations → 100K–1M comparisons; pretraining is the only expensive stage ([chatbot](19-chatbot-assistant.md)).
- Deploying the base model = it continues your prompt instead of answering; SFT turns continuer into responder, RLHF aligns ([chatbot](19-chatbot-assistant.md)).
- Embed prompt context as tagged sequence via template (subject, recipient, history) — not just body ([smart-compose](17-ml-design.md)).
- Legacy text preprocessing (lowercasing, stop-words, stemming) is dead — drop it; keep placeholder-substitution for named entities, restore after decode ([mt](18-machine-translation.md)).
- Data cleaning constant across designs: language ID → NSFW/harm removal → PII anonymize → dedup (perceptual hash / CLIP) → quality filter → BPE ([chatbot](19-chatbot-assistant.md), [captioning](20-image-captioning.md), [t2v](26-text-to-video.md)).
- Dedup is load-bearing: duplicates overexpose the model → overfitting, bias toward frequent images and samey outputs ([chatbot](19-chatbot-assistant.md), [t2i](24-text-to-image.md)).
- Positional encoding: fixed sine-cosine for short sequences (Smart Compose), RoPE for long context (chat, video); ViT uses learnable 1D; no universal best — test ([smart-compose](17-ml-design.md), [chatbot](19-chatbot-assistant.md), [captioning](20-image-captioning.md), [t2v](26-text-to-video.md)).
- Diffusion training in 4 steps: sample t ∈ 1..1000 → add noise → condition (text + timestep) → predict ε with MSE; predict ε, never x₀ ([t2i](24-text-to-image.md)).
- Diffusion sampling fixes: CFG for prompt alignment + DDIM (1000 → as few as 20 steps) for latency — volunteer both ([t2i](24-text-to-image.md)).
- VQ-VAE tokenizer losses: reconstruction + quantization (stop-gradient) + perceptual (VGG) + adversarial (patch-based); MSE-only shows artifacts at high res ([hires](23-high-resolution-image-synthesis.md)).
- Pixel normalization must match final activation: -1..1 → Tanh; 0..1 for diffusion ([face-gen](22-face-generation.md), [hires](23-high-resolution-image-synthesis.md)).
- GAN discipline: alternate freeze-train G/D; the three failures are discriminator-too-good (vanishing gradients → WGAN), mode collapse (Wasserstein/unrolled), D at ~50% accuracy (stop, monitor D accuracy) ([face-gen](22-face-generation.md)).
- GAN sampling: random latent sampling by default — diversity matters for faces; truncated sampling trades diversity for realism ([face-gen](22-face-generation.md)).
- DreamBooth identifier token: rare vocabulary tokens only — common words carry prior meaning, random strings fragment in the tokenizer ([headshot](25-headshot-personalization.md)).
- Two-loss personalization: α × reconstruction (identity) + β × class-specific prior preservation (keep the generic class) — "learn the instance without destroying the class" ([headshot](25-headshot-personalization.md)).
- Failed identity check → regenerate same prompt, different seed; quality gate is a loop, not a report ([headshot](25-headshot-personalization.md)).
- RAG chunk math drives capacity: page count × chunks-per-page × growth ≈ index size; size the index before picking the vector store ([rag](21-rag.md)).
- Shared embedding space is the RAG invariant: same text encoder for docs and queries; images enter via CLIP or caption-then-embed ([rag](21-rag.md)).
- Captioning encoder granularity: token sequence (per-patch), not single global vector — attention wants sequences, detail matters ([captioning](20-image-captioning.md)).
- Multi-reference captions for training and eval — robust to phrasing variety, fairer evaluation ([captioning](20-image-captioning.md)).
- Confidence gating at serving: beam-search cumulative probability below threshold → disable suggestion for ambiguous inputs ([captioning](20-image-captioning.md), [smart-compose](17-ml-design.md)).
- Pretrain latents, don't encode per step: run frames through the VAE once, cache — per-iteration VAE stalls training ([t2v](26-text-to-video.md)).
- Video = image cost × frame count; collapse the multiplier with latent compression + low-res/low-FPS generation + spatial/temporal SR ([t2v](26-text-to-video.md)).
- Video–text data scarcity: fold image–text pairs in as single-frame videos (one stage) or pretrain image → finetune video — state the trade-off ([t2v](26-text-to-video.md)).
- FID lower = better; IS higher = better; neither replaces pairwise human evaluation — Inception/ImageNet artifacts misalign with judgment ([face-gen](22-face-generation.md)).
- Metric coverage: FID/IS = frame quality, FVD = temporal consistency, CLIPScore = text alignment — no single metric covers the others; use the RAG triad (context relevance, faithfulness, answer relevance, correctness) for RAG ([t2v](26-text-to-video.md), [rag](21-rag.md)).
- Watch cost per generation / cost per user, not just latency — unhappy users re-roll seeds, dissatisfaction compounds into compute spend ([t2i](24-text-to-image.md), [hires](23-high-resolution-image-synthesis.md)).
- Non-functional requirements (latency, fairness, safety) drive tuning, rarely initial architecture — but name them early ([overview](16-genai-design.md)).
- Honest scope cuts read senior: "PPO/DPO internals beyond this round; loop is generate → score → update" ([chatbot](19-chatbot-assistant.md)).

### Numbers table

| Number | Meaning | Ref |
|---|---|---|
| 15T tokens (~50 TB) | Llama 3 training data — self-supervised scale ([overview](16-genai-design.md)) |
| 1.8B image–text pairs | Flamingo training data ([overview](16-genai-design.md)) |
| 540B / 175B / 405B / 80B / 2B params | PaLM / GPT-3 / Llama 3 / Flamingo / Imagen ([overview](16-genai-design.md)) |
| 10²² FLOPs | PaLM-2 training compute ([overview](16-genai-design.md)) |
| ~5.5 years | One H100 (60 TFLOP/s ≈ 5.18 EFLOP/day) on PaLM-2's budget → thousands of GPUs ([overview](16-genai-design.md)) |
| >$100M | GPT-4 training cost ([overview](16-genai-design.md)) |
| 21 FLOPs | Fully connected 4→3 layer (3×(4+3)) — FLOP warm-up math ([overview](16-genai-design.md)) |
| ~100 ms | Smart Compose latency budget (imperceptible) ([smart-compose](17-ml-design.md)) |
| 1B emails | Smart Compose finetuning corpus ([smart-compose](17-ml-design.md)) |
| 1.8B users, ≤500 emails/day each | Smart Compose scale requirement ([smart-compose](17-ml-design.md)) |
| ~100 / 300K+ (267,735) / 50K–150K | Vocab size: char / word (Transformer-XL) / subword ([smart-compose](17-ml-design.md)) |
| O(n²) | Self-attention cost in sequence length → Flash Attention motivation ([smart-compose](17-ml-design.md)) |
| 4 languages, 1,000-word inputs, 300M sentence pairs | MT scope + training data ([mt](18-machine-translation.md)) |
| ≥4096 tokens | Chatbot context window requirement → RoPE ([chatbot](19-chatbot-assistant.md)) |
| 80,000 (instruction, answer) examples | Chatbot SFT dataset size from requirements ([chatbot](19-chatbot-assistant.md)) |
| ~1.4T tokens, 7 corpora | Llama-1 pretraining (Common Crawl, C4, GitHub, Wikipedia, Books, ArXiv, StackExchange) ([chatbot](19-chatbot-assistant.md)) |
| 10K–100K demos / 100K–1M comparisons / 10K–100K prompts | SFT / reward model / RLHF data scales ([chatbot](19-chatbot-assistant.md)) |
| 1000s GPUs·months vs 1–100 GPUs·days | Pretraining vs SFT/RM/RL compute ([chatbot](19-chatbot-assistant.md)) |
| 6B RM per 175B LM; 10B–52B | OpenAI / Anthropic reward model sizes — no consistent pattern ([chatbot](19-chatbot-assistant.md)) |
| T range 0–2; practice 0.1–1.5 | Temperature; T=0 deterministic, T=1 normal ([chatbot](19-chatbot-assistant.md)) |
| 1,800 prompts, 12 use cases | Llama 3 human eval protocol ([chatbot](19-chatbot-assistant.md)) |
| ~100K prompts | RealToxicityPrompts safety benchmark ([chatbot](19-chatbot-assistant.md)) |
| 9 categories / 23,679 prompts, 5 domains | CrowS-Pairs / BOLD bias benchmarks ([chatbot](19-chatbot-assistant.md)) |
| 800K+ pairwise comparisons | LMSYS Chatbot Arena rankings ([chatbot](19-chatbot-assistant.md)) |
| 400M image–caption pairs | Captioning training data ([captioning](20-image-captioning.md)) |
| 1–2 s | Captioning latency budget — beam search affordable ([captioning](20-image-captioning.md)) |
| 256×256 | Captioning min resolution + resize/crop target ([captioning](20-image-captioning.md)) |
| 0.25 | CLIP image–caption relevance threshold — drop below ([captioning](20-image-captioning.md)) |
| 64×64 patches → 16 patches, 4096-dim each | Captioning patchify example, 256×256 image ([captioning](20-image-captioning.md)) |
| 0.570 | CIDEr worked example: (0.688+0.257+0.766)/3 over 3 refs ([captioning](20-image-captioning.md)) |
| 5M PDF pages → 40M chunks | RAG corpus: 1500 chars/page, chunk 500 + overlap 200 → 5 text + 3 image chunks/page ([rag](21-rag.md)) |
| +20%/yr | RAG document growth — justifies scalable vector index ([rag](21-rag.md)) |
| 128K | GPT-4o context window — full docs still don't fit; chunk ([rag](21-rag.md)) |
| O(N×D) vs ~O(log(N)×D) | Exact NN (40M comparisons/query) vs ANN ([rag](21-rag.md)) |
| 1024×1024, <1 s | Face-gen resolution + latency SLA — kills autoregressive + diffusion ([face-gen](22-face-generation.md)) |
| 70,000 | Licensed face images ([face-gen](22-face-generation.md)) |
| 100-dim noise, pixels -1..1 → Tanh | GAN generator input + output activation pairing ([face-gen](22-face-generation.md)) |
| ~50% | Discriminator accuracy at convergence — past this, feedback is noise; stop ([face-gen](22-face-generation.md)) |
| 5M images, 1024²–2048², ~5 s | High-res synthesis requirements ([hires](23-high-resolution-image-synthesis.md)) |
| 64×64 px/token → 256 tokens | Token math: 1024² image = 256 sequential AR steps ([hires](23-high-resolution-image-synthesis.md)) |
| ~1M pixel steps | Naive pixel AR at 1024² — blows 5 s budget ([hires](23-high-resolution-image-synthesis.md)) |
| O(T·N²), minutes | Diffusion at high res — growing T with resolution ([hires](23-high-resolution-image-synthesis.md)) |
| ≥512px | Posterior collapse onset for VAE/GAN decoders ([hires](23-high-resolution-image-synthesis.md)) |
| LAION-400M | Augmenting self-supervised tokenizer training ([hires](23-high-resolution-image-synthesis.md)) |
| 2× | Super-resolution upscale for 2048² requests (RCAN/ESRGAN) ([hires](23-high-resolution-image-synthesis.md)) |
| 1024×1024, ~10 s, 128-word prompts, ~500M pairs | T2I requirements ([t2i](24-text-to-image.md)) |
| 3.5B params | DALL-E 2 — why OOM/latency problems exist ([t2i](24-text-to-image.md)) |
| t ∈ 1..1000; DDIM 1000 → 20 steps | Diffusion timesteps; DDIM speedup at minimal quality cost ([t2i](24-text-to-image.md)) |
| <64×64 dropped; shorter side → 128 | T2I image filtering + standardization ([t2i](24-text-to-image.md)) |
| 64 → 256 → 1024 | T2I super-resolution cascade ([t2i](24-text-to-image.md)) |
| 100/50/0 | Human eval scoring: yes/somewhat/no text alignment ([t2i](24-text-to-image.md)) |
| 10–20 user images, 50 outputs, <1 h, ~15 min finetune | Headshot requirements + DreamBooth fit ([headshot](25-headshot-personalization.md)) |
| >15 high-quality uploads | Data-pipeline gate before training ([headshot](25-headshot-personalization.md)) |
| d_in×d_out → r×(d_in+d_out) | LoRA trainable-param reduction ([headshot](25-headshot-personalization.md)) |
| 1–5 rating | Post-delivery satisfaction metric; conversion = new paying ÷ engaged ([headshot](25-headshot-personalization.md)) |
| 5 s @ 24 FPS = 120 frames, 720p (1280×720) | T2V output spec ([t2v](26-text-to-video.md)) |
| ~100M pairs, >6000 H100s | T2V data + compute budget ([t2v](26-text-to-video.md)) |
| ~7 min | 5 s 720p video in pixel space on H100 (512² image ≈ 1 s; 720p frame ~3.6× pixels) → LDM mandatory ([t2v](26-text-to-video.md)) |
| 512× smaller | Factor-8 spatial+temporal latent compression: 1280×720×120 (110,592,000 px) → 160×90×15 (216,000 px) ([t2v](26-text-to-video.md)) |
| 1000 MB → 2 MB latent; ~200 TB total | Precomputed latent cache for 100M videos ([t2v](26-text-to-video.md)) |
| 60 @ 12 FPS → 120 @ 24 FPS; spatial SR 4× | Temporal + spatial super-resolution chain: 40×23×8 latents → 320×180×60 → 1280×720×120 ([t2v](26-text-to-video.md)) |

### Architecture cheat rows (reference)

| Need | Pick | Ref |
|---|---|---|
| Text generation | Decoder-only Transformer ([smart-compose](17-ml-design.md)) |
| Output transforms input (translation, captioning) | Encoder-decoder + cross-attention ([mt](18-machine-translation.md), [captioning](20-image-captioning.md)) |
| Understanding (classify, NER, language ID) | Encoder-only (BERT-style); language detector = encoder-only classifier ([smart-compose](17-ml-design.md), [mt](18-machine-translation.md)) |
| Image tokens ↔ image | VQ-VAE: CNN encoder + codebook quantizer + ConvTranspose decoder; deploy decoder only ([hires](23-high-resolution-image-synthesis.md)) |
| Denoising backbone | U-Net (Imagen, Stable Diffusion) or DiT (Sora, Movie Gen — newer bet, scales) ([t2i](24-text-to-image.md), [t2v](26-text-to-video.md)) |
| Faces, <1s, latent control | GAN + StyleGAN (ConvT generator, stride-2 discriminator, alternating freeze-train) ([face-gen](22-face-generation.md)) |
| Per-user identity | DreamBooth > LoRA > textual inversion, by fidelity/storage/resources ([headshot](25-headshot-personalization.md)) |

### Evaluation cheat rows (reference)

| Task | Offline metrics | Ref |
|---|---|---|
| Text generation | Perplexity, BLEU, METEOR, ROUGE, CIDEr; ExactMatch@N | [overview](16-genai-design.md), [smart-compose](17-ml-design.md), [captioning](20-image-captioning.md) |
| Machine translation | BLEU (precision+brevity), ROUGE (recall), METEOR (synonyms, best human correlation) | [mt](18-machine-translation.md) |
| Chatbot | 4 layers: perplexity → task benchmarks (MMLU, GSM8K, HumanEval) → safety (RealToxicityPrompts, CrowS-Pairs, TruthfulQA) → human + Arena | [chatbot](19-chatbot-assistant.md) |
| Image generation | FID (lower better), IS (higher better), KID, CLIPScore (alignment), DrawBench, pairwise human | [overview](16-genai-design.md), [face-gen](22-face-generation.md), [t2i](24-text-to-image.md) |
| RAG | Triad: context relevance (HitRate/MRR/NDCG/P@k), faithfulness (Ragas/ARES), answer relevance (LLM-judge), correctness (BLEU/ROUGE/METEOR) | [rag](21-rag.md) |
| Personalization | CLIPScore (text), FID/IS (quality), DINO + facial similarity (identity); DINO for img-img, CLIP for img-text | [headshot](25-headshot-personalization.md) |
| Text-to-video | FID/IS per-frame + FVD (temporal, lower better) + CLIP similarity (alignment) + VBench/Movie Gen Bench + pairwise human | [overview](16-genai-design.md), [t2v](26-text-to-video.md) |
