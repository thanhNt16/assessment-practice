# Generative AI Design — Patterns & Techniques

From [genai-design](16-genai-design.md). Name — when to use — how.

## Frameworks

- **Seven-step framework** — when: any GenAI design prompt; how: clarify requirements → frame as ML task → data prep → model dev → offline+online eval → overall system design → deployment + monitoring; drill once, reuse everywhere.
- **Compute-asymmetry reasoning** — when: build-vs-buy or adapt-vs-pretrain questions; how: pretraining = 1000s of GPUs for months, SFT/RLHF = 1-100 GPUs for days — never redo pretraining, decide only in cheap stages.
- **Two-stage training** — when: domain gap between generic and task data; how: unsupervised pretrain on generic text, then finetune on task corpus (Smart Compose: 1B email conversations).
- **RAG pipeline** — when: answers must cite sources, stay fresh, or fit no context window (GPT-4o = 128K tokens); how: parse → chunk (500 chars, 200 overlap) → embed → ANN index; retrieval top-k + prompt engineering into the LLM.
- **AI-based document parsing** — when: varied layouts break rule-based parsers; how: object detection → OCR → structured text/non-text blocks (Layout-Parser).
- **Index sizing math** — when: defending RAG at scale; how: 5M pages x (1500 chars, 3 images) → 500-char chunks + 3 image chunks/page = 40M chunks, +20%/yr.
- **Cross-modal alignment** — when: images must be retrievable by text; how: CLIP shared embedding space, or caption images first and embed captions as text.
- **ANN index choice** — when: corpus passes millions of items; how: pick from tree / LSH / clustering / graph (HNSW); clustering = inter-cluster centroid search then intra-cluster; FAISS/ScaNN/Elasticsearch ship it.
- **Finetune-last rule** — when: tempted to finetune for knowledge injection; how: exhaust retrieval + prompt engineering first; finetune only when retrieval is fixed and answers are still bad.
- **RAFT** — when: retrieval is noisy and cannot be fully cleaned; how: finetune the LLM on golden + distractor documents so it learns to ignore noise.
- **Precompute-and-cache** — when: embeddings/latents reused across epochs; how: cache caption embeddings (ch9) or video latents (ch11) before training.

## Modeling techniques

- **Parallel loss computation** — when: pretraining affordability; how: compute losses for all token lengths of a sequence in parallel — one forward pass per sequence, not sequential generation.
- **BPE subword tokenization** — when: rare/unseen words; how: iteratively merge most frequent symbol pairs until vocab target.
- **ViT image encoder** — when: captioning needs long-range dependencies and detail; how: patchify (256x256 → 64x64 patches) + learnable 1D positional encoding; sequence-of-tokens output + decoder-only text head.
- **Beam search over sampling** — when: quality, determinism, coherence required (same image → same caption); how: decode with beam search instead of stochastic sampling.
- **Caption cleaning** — when: noisy web pairs; how: dedup via perceptual hashing / CLIP similarity, drop below CLIP relevance 0.25, LLM-summarize long captions, BPE-tokenize.
- **Image cleaning** — when: mixed-quality corpus; how: drop <256x256, quality-score (LAION Aesthetics Predictor), resize-then-center-crop to preserve aspect ratio.
- **GAN architecture** — when: one-pass latency plus attribute manipulation; how: generator = transposed conv → BatchNorm → ReLU (Tanh output for [-1,1]); discriminator = strided Conv2D + sigmoid; freeze-and-train alternately, keep balanced.
- **GAN failure-mode fixes** — when: adversarial training misbehaves; how: vanishing gradients → modified minimax loss or WGAN critic; mode collapse → WGAN, unrolled GAN; non-convergence (D acc → 50%) → normalization, different learning rates.
- **Retraining loop on user-approved images** — when: production generative system with feedback signal; how: ship generator + training + evaluation + deployment services; approved outputs feed retraining.
- **VQ-VAE tokenizer + AR generator** — when: high-res synthesis at scale (VAE/GAN posterior collapse >=512x512, diffusion O(TN²)); how: CNN encoder → codebook quantizer → decoder; train tokenizer, cache images as token sequences, train generator with next-token prediction + cross-entropy.
- **Tokenizer loss stack** — when: high-res artifacts; how: weighted sum of reconstruction MSE + quantization loss + perceptual (VGG) + patch-adversarial losses.
- **Encoder-discard deployment** — when: serving a two-stage AR system; how: discard tokenizer encoder, serve only decoder; run generation and decoding as separate services (different compute profiles).
- **U-Net + cross-attention** — when: text-conditioned diffusion; how: queries from image features, keys/values from text embeddings at every block; DiT (patchify → transformer → unpatchify) as alternative.
- **Closed-form noise training** — when: diffusion training; how: sample timestep t, add noise via closed-form schedule, predict ε from noisy image + t + text, loss = MSE(ε, ε̂).
- **Classifier-free guidance + DDIM** — when: diffusion sampling; how: CFG for prompt adherence, DDIM cuts 1000 steps to ~20.
- **Cascade super-resolution** — when: diffusion can't emit high-res directly; how: generate 64 → 256 → 1024 in stages.
- **Inference safety chain** — when: public text-to-image; how: prompt auto-complete → safety classifier → prompt enhancement → generation → harm detection on output → cascade SR.
- **Adaptation spectrum** — when: personalization; how: textual inversion (1 image, weakest) → LoRA (freeze W, ΔW=AB, MBs) → DreamBooth (finetune all, best identity, GBs); pick by storage + SLA, not leaderboard.
- **Anti-forgetting mechanics** — when: finetuning on 10-20 subject images; how: rare-token identifier ("[V]"/"SKS") + class-specific prior preservation loss (α x subject reconstruction + β x generic-face prior).
- **Identity metric triad** — when: claiming "same person"; how: CLIP = semantics, DINO = visual detail, face-recognition model = identity — CLIP+DINO can score high on two different people.
- **Quality-service regeneration** — when: personalized output can fail; how: check face similarity, regenerate with different initial noise on failure.
- **Latent diffusion for video** — when: pixel-space diffusion too slow (5s 720p ≈ 7 min); how: VAE compression 8x spatial + 8x temporal = 512x smaller, diffuse latents, decode pixels last.
- **Image-video joint training** — when: paired video-text data scarce; how: train DiT treating images as single-frame videos, or pretrain on images, finetune on video.
- **Resolution/FPS cascade** — when: base model can't hit 1080p/24FPS; how: spatial SR (720p→1080p/4K) + temporal SR (12 FPS interpolated to 24), à la Imagen Video.
- **FVD over per-frame FID** — when: video quality claims; how: Fréchet distance over I3D features captures flicker per-frame metrics miss.

## Anti-patterns

- **Finetuning first for knowledge injection** — when: model lacks facts; avoid: can't cite sources, constant retraining, expensive, data-hungry — retrieve instead.
- **Blaming the LLM for bad chunks** — when: RAG answers poor; avoid: response quality is highly dependent on retrieval relevance — a better LLM cannot fix bad chunks.
- **Exact nearest-neighbor at scale** — when: O(N x D) scan; avoid: 40M comparisons per query is infeasible — ANN is mandatory past millions.
- **Unbalanced adversarial training** — when: one network dominates; avoid: vanishing gradients, mode collapse, coin-flip feedback — the balance IS the training.
- **Posterior collapse in deep decoders** — when: powerful decoder ignores latent, diversity dies; avoid via discrete latents (VQ) or capacity constraints.
- **Diffusion cost blindness** — when: users re-roll seeds on failed generations; avoid: unmonitored re-rolls quietly multiply GPU spend — track average cost per user per month.
- **Storing full personalized models** — when: GBs per subject; avoid: does not scale — LoRA's MBs win whenever models must persist.
- **Wrong similarity metric for the claim** — when: proposing "similarity"; avoid: semantic ≠ visual ≠ identity — name the instrument.
- **Overfitting to the subject** — when: finetuning on 10-20 images; avoid: without generic-data mixing and prior-preservation loss, class diversity is destroyed.
