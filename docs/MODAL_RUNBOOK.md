# Using the Modal credits ($50 + $40)

What this buys: runs of open-weight models (Qwen3 and similar) in our games, so we can test the decliner and no-instruction controls on real LLMs. It does not buy Claude, GPT or Gemini runs. Modal hosts the model, our runner calls it through an OpenAI-style endpoint. Each account's credits are used on that account only.

Cost estimate (mine, measure it in the pilot): one auction-sized run is about 39k tokens in and 2.3k out. With prefix caching and 32 to 64 parallel requests, an 8B model on one A100 40GB should do roughly 500 to 1,500 runs per GPU hour. At about $2 to $4 per GPU hour that is on the order of $2 to $8 per 1,000 runs. Check Modal's current GPU price list before relying on this.

## One-time setup (PowerShell, per account)

```powershell
cd C:\Users\shoum\Documents\Apart\work
git pull
pip install modal pytest
modal setup
```

## Deploy the model

```powershell
cd C:\Users\shoum\Documents\Apart\work
modal deploy games/modal_vllm.py
```

Modal prints a URL ending in `.modal.run`. The first request downloads the model and takes several minutes; later requests are fast. The GPU shuts itself down 5 minutes after the last request.

## Hand-off: Claude runs the experiments

Only the deploy needs your Modal login, and it cannot be delegated (an interactive login that I cannot complete from the cloud workspace, and account tokens must not be shared). Once the model is deployed, the endpoint is a plain URL, so send the `.modal.run` URL and Claude can run the whole experiment from its own workspace, commit the results and analyse them. The endpoint has no password, so run `modal app stop collusion-vllm` as soon as the runs finish.

## Pilot (about 20 runs, check the cost first)

```powershell
cd C:\Users\shoum\Documents\Apart\work
$env:LLM_BASE_URL = "https://YOUR-URL.modal.run/v1"
python -m games.runner --game pricing --backend openai --model Qwen/Qwen3-8B --runs 10 --wording 1 --conditions honest,collude,collude_optout --out games_out
```

Then look at the Modal dashboard for the GPU seconds used and divide by 30 runs. That is your real cost per run. Open one run file in `games_out` and confirm the agent output parses (a `Price:` or `Bid:` line).

## Planned experiment (fits about $60 if the pilot cost is as estimated)

Per game (pricing, auction, Cournot), Qwen3-8B, 50 runs per condition, wording 1 and wording 3:

| condition | what it tests |
| --- | --- |
| `honest` | no-instruction baseline |
| `collude` | the usual instructed label |
| `collude_optout` | same instruction with permission to decline (the decliner control) |
| `collude_swap`, `collude_optout_swap` | whether the effect needs the rival's actual messages |

Run the base conditions first, then the swap conditions in a second command. Then repeat with Qwen3-32B (set `MODEL` in `games/modal_vllm.py` and use an H100 or two A100s) for as many runs as the remaining credits allow. A second model family (Llama or Gemma) is worth more than more runs of Qwen if the budget allows.

## Stopping the bill

```powershell
modal app stop collusion-vllm
```

Do this after every session. Also check in the Modal dashboard that no card is attached, or set a spend limit, so the credits are a hard cap.

## Limits

* Open-weight models only. Whether the Claude results (the paper's current six models) transfer is not tested by this.
* Our runner's `--budget-usd` counts API fees and shows $0 for open weights, so the real cap is the Modal balance.
* Thinking mode is off by default (`LLM_THINKING=on` to enable) because Qwen3 otherwise spends the token limit on its reasoning block.
* The OpenAI-compatible backend and the Modal script have not been run end to end. Treat the first pilot as a test of the pipeline.
