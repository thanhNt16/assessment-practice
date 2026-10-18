# Generative AI Design — Cheatsheet

From [genai-design](16-genai-design.md).

## Model choice by requirement

| If requirement | Then |
|---|---|
| One-pass latency, attribute manipulation | GAN (structured latent space) |
| Fast + stable training, compression OK | VAE |
| Ceiling image quality, flexible speed/quality dial | Diffusion |
| High-res synthesis at scale | Autoregressive over VQ-VAE discrete tokens |
| Video generation economics | Latent diffusion (LDM, 512x compression) |
| Best fidelity + flexible control, latency tolerable | Autoregressive |
| Simple to implement/train, quality secondary | Autoregressive |

## Adaptation / knowledge approach

| If requirement | Then |
|---|---|
| Must cite sources, fresh data, or docs overflow context (128K) | RAG |
| RAG answers still bad, retrieval already fixed | Finetune the LLM |
| Retrieval is noisy and unfixable | RAFT (golden + distractor docs) |
| Personalization, model discarded after generation | DreamBooth (best identity, ~15 min, fits 1-h SLA) |
| Personalized models must persist | LoRA (MBs vs GBs) |
| Personalization from 1 image, weakest is fine | Textual inversion |
| Adapt a foundation model | Never redo pretraining — SFT/RLHF/LoRA in cheap stages (1-100 GPUs, days) |

## Metric choice by claim

| If claim | Then |
|---|---|
| Semantic alignment (text-image) | CLIPScore / CLIP similarity |
| Visual detail | DINO (flags what CLIP forgives) |
| Identity | Face-recognition model (CLIP+DINO can both pass on different people) |
| Image quality/diversity | FID / IS |
| Video quality incl. flicker | FVD (I3D features) |
| Caption quality | CIDEr |
| Translation quality | BLEU / METEOR / WER |
| RAG quality | IR measures + Ragas / ARES |
| Business value | CTR, conversion, adoption |
| GenAI cost health | Average cost per user per month (seed re-rolls burn GPU money) |

## GAN failure modes

| If symptom | Then fix |
|---|---|
| Vanishing gradients (discriminator too good) | Modified minimax loss or WGAN critic |
| Mode collapse (one image forever) | WGAN, unrolled GAN |
| Failure to converge (D accuracy → 50%) | Normalization, different learning rates |

## Scaling levers

| If bottleneck | Then |
|---|---|
| Diffusion too slow for video | Latent diffusion (8x spatial + 8x temporal compression) |
| Resolution below target | Spatial super-resolution cascade (64→256→1024; 720p→1080p/4K) |
| FPS below target | Temporal SR: generate 12 FPS, interpolate to 24 |
| Diffusion too many steps | DDIM (1000 → ~20) + classifier-free guidance for adherence |
| Retrieval scan too slow | ANN index (tree / LSH / clustering / HNSW graph) |
| Training data-starved embeddings/latents | Precompute + cache before training |

## Quick rules

- Skeleton for every prompt: clarify requirements → ML task → data prep → model dev → offline+online eval → system design → deployment + monitoring.
- Data prep shift: feature engineering → vast collection, quality/safety, storage + retrieval. Scale anchor: Llama 3 = 15T tokens ≈ 50TB.
- RAG sizing: 5M pages x (1500 chars, 3 images) → 40M chunks @ 500 chars / 200 overlap, +20%/yr.
- Discrete tokens are the universal interface: BPE (text), codebook (images), compressed latents (video) — one decoder-only Transformer underneath.
- Retrieval ceiling: a better LLM cannot fix bad chunks; finetune last.
- GAN training = keeping two networks balanced; BatchNorm stabilizes and permits higher LRs.
- At deployment discard the VQ-VAE encoder — only the decoder serves; generation and decoding run as separate services.
- Posterior collapse: decoder too powerful ignores latent → discretize (VQ) or constrain capacity.
- Personalization without overfitting: rare-token identifier + class-specific prior preservation loss.
- Always pair offline metrics with online business metrics — naming both unprompted is the scoring behavior.
- Pipeline cost shock to quote: 5s @ 24FPS 720p = 120 frames; pixel diffusion ≈ 7 min vs latent diffusion on one H100.
- Safety chain: prompt auto-complete → safety classifier → prompt enhancement → generation → harm detection → cascade SR.
