<p align="center">
  <a href="http://swe-bench.github.io">
    <img src="docs/assets/figures/swellama_banner.svg" style="height: 10em" alt="Kawi the SWE-Llama" />
  </a>
</p>

<p align="center"><strong>[&nbsp;<a href="https://swebench.com/SWE-bench/">Read the Docs</a>&nbsp;]</strong></p>

<p align="center">
  <a href="docs/other_languages/README_JP.md">日本語</a> |
  <a href="docs/other_languages/README_CN.md">中文简体</a> |
  <a href="docs/other_languages/README_TW.md">中文繁體</a>
</p>

<p align="center">
    <a href="https://www.python.org/">
        <img alt="Build" src="https://img.shields.io/badge/Python-3.8+-1f425f.svg?color=purple">
    </a>
    <a href="https://copyright.princeton.edu/policy">
        <img alt="License" src="https://img.shields.io/badge/License-MIT-blue">
    </a>
    <a href="https://badge.fury.io/py/swebench">
        <img src="https://badge.fury.io/py/swebench.svg">
    </a>
</p>

---

Code and data for the following works:
* [ICLR 2025] <a href="https://arxiv.org/abs/2410.03859">SWE-bench Multimodal: Do AI Systems Generalize to Visual Software Domains?</a>
* [ICLR 2024 Oral] <a href="https://arxiv.org/abs/2310.06770">SWE-bench: Can Language Models Resolve Real-World GitHub Issues?</a>

## 📰 News
* **[Jan. 13, 2025]**: We've integrated [SWE-bench Multimodal](https://swebench.github.io/multimodal) ([paper](https://arxiv.org/abs/2410.03859), [dataset](https://huggingface.co/datasets/SWE-bench/SWE-bench_Multimodal)) into this repository! Unlike SWE-bench, we've kept evaluation for the test split *private*. Submit to the leaderboard using [sb-cli](https://github.com/swe-bench/sb-cli/tree/main), our new cloud-based evaluation tool.
* **[Jan. 11, 2025]**: Thanks to [Modal](https://modal.com/), you can now run evaluations entirely on the cloud! See [here](https://github.com/swe-bench/SWE-bench/blob/main/docs/assets/evaluation.md#%EF%B8%8F-evaluation-with-modal) for more details.
* **[Aug. 13, 2024]**: Introducing *SWE-bench Verified*! Part 2 of our collaboration with [OpenAI Preparedness](https://openai.com/preparedness/). A subset of 500 problems that real software engineers have confirmed are solvable. Check out more in the [report](https://openai.com/index/introducing-swe-bench-verified/)!
* **[Jun. 27, 2024]**: We have an exciting update for SWE-bench - with support from [OpenAI's Preparedness](https://openai.com/preparedness/) team: We're moving to a fully containerized evaluation harness using Docker for more reproducible evaluations! Read more in our [report](https://github.com/swe-bench/SWE-bench/blob/main/docs/20240627_docker/README.md).
* **[Apr. 2, 2024]**: We have released [SWE-agent](https://github.com/SWE-agent/SWE-agent), which sets the state-of-the-art on the full SWE-bench test set! ([Tweet 🔗](https://twitter.com/jyangballin/status/1775114444370051582))
* **[Jan. 16, 2024]**: SWE-bench has been accepted to ICLR 2024 as an oral presentation! ([OpenReview 🔗](https://openreview.net/forum?id=VTF8yNQM66))

## 👋 Overview
SWE-bench is a benchmark for evaluating large language models on real world software issues collected from GitHub.
Given a *codebase* and an *issue*, a language model is tasked with generating a *patch* that resolves the described problem.

<img src="docs/assets/figures/teaser.png">

To access SWE-bench, copy and run the following code:
```python
from datasets import load_dataset
swebench = load_dataset('princeton-nlp/SWE-bench', split='test')
```

## 🚀 Set Up
SWE-bench uses Docker for reproducible evaluations.
Follow the instructions in the [Docker setup guide](https://docs.docker.com/engine/install/) to install Docker on your machine.
If you're setting up on Linux, we recommend seeing the [post-installation steps](https://docs.docker.com/engine/install/linux-postinstall/) as well.

Finally, to build SWE-bench from source, follow these steps:
```bash
git clone git@github.com:princeton-nlp/SWE-bench.git
cd SWE-bench
pip install -e .
```

Test your installation by running:
```bash
python -m swebench.harness.run_evaluation \
    --predictions_path gold \
    --max_workers 1 \
    --instance_ids sympy__sympy-20590 \
    --run_id validate-gold
```
> [!NOTE]
> If using a MacOS M-series or other ARM-based systems, add `--namespace ''` to the above script.
> By default, the evaluation script pulls images (built for Linux) from [DockerHub](https://hub.docker.com/u/swebench).
> Adding `--namespace ''` will cause evaluation images to be built locally instead.

## 💽 Usage
Evaluate patch predictions on SWE-bench Lite with the following command:
```bash
python -m swebench.harness.run_evaluation \
    --dataset_name princeton-nlp/SWE-bench_Lite \
    --predictions_path <path_to_predictions> \
    --max_workers <num_workers> \
    --run_id <run_id>
    # use --predictions_path 'gold' to verify the gold patches
    # use --run_id to name the evaluation run
    # use --modal true to run on Modal
```

This command will generate docker build logs (`logs/build_images`) and evaluation logs (`logs/run_evaluation`) in the current directory.

The final evaluation results will be stored in the `evaluation_results` directory.

> [!WARNING]
> SWE-bench evaluation can be resource intensive
> We recommend running on an `x86_64` machine with at least 120GB of free storage, 16GB of RAM, and 8 CPU cores.
> We recommend using fewer than `min(0.75 * os.cpu_count(), 24)` for `--max_workers`.
>
> If running with Docker desktop, make sure to increase your virtual disk space to ~120 free GB. Set max_workers to be consistent with the above for the CPUs available to Docker.
>
> Support for `arm64` machines is experimental.

To see the full list of arguments for the evaluation harness, run:
```bash
python -m swebench.harness.run_evaluation --help
```

See the [evaluation tutorial](docs/guides/evaluation.md) for the full rundown on datasets you can evaluate.
If you're looking for non-local, cloud based evaluations, check out...
* [sb-cli](https://github.com/swe-bench/sb-cli), our tool for running evaluations automatically on AWS, or...
* Running SWE-bench evaluation on [Modal](https://modal.com/). Details [here](docs/guides/evaluation.md#Cloud-Based-Evaluation)

Additionally, you can also:
* [Train](https://github.com/swe-bench/SWE-bench/tree/main/swebench/inference/make_datasets) your own models on our pre-processed datasets. (🆕 Check out [SWE-smith](https://swesmith.com/), a dedicated toolkit for creating SWE training data.)
* Run [inference](docs/reference/inference.md) on existing models (both local and API models). The inference step is where you give the model a repo + issue and have it generate a fix.
* 🆕 **Use [Claude Code](docs/guides/claude_code_integration.md)** for enhanced AI-powered software engineering with Anthropic's specialized coding assistant
*  Run SWE-bench's [data collection procedure](https://github.com/swe-bench/SWE-bench/blob/main/swebench/collect/) ([tutorial](docs/guides/collection.md)) on your own repositories, to make new SWE-Bench tasks.
    * ⚠️ We are temporarily pausing support for queries around creating SWE-bench instances. Please see the note in the tutorial.

### 🤖 Supported Model Integrations

SWE-bench supports multiple AI model providers:

#### Claude Code Integration
[Claude Code](https://claude.com/claude-code) - Anthropic's specialized CLI for software engineering:

```bash
# Install Claude Code CLI
npm install -g @anthropic-ai/claude-code

# Set your API key and run
export ANTHROPIC_API_KEY="your-key-here"
python -m swebench.inference.run_api \
    --dataset_name_or_path princeton-nlp/SWE-bench_Lite_oracle \
    --model_name_or_path claude-3.5-sonnet \
    --output_dir ./results \
    --model_args "max_instances=10"
```

**Supported models:** `claude-4`, `claude-code`, `claude-3.5-sonnet`, `claude-3-opus`, `claude-3-sonnet`, `claude-3-haiku`

📖 [Claude Code Integration Guide](docs/guides/claude_code_integration.md)

#### Qwen Integration
Qwen models via DashScope OpenAI-compatible API:

```bash
export DASHSCOPE_API_KEY="your-key-here"
python -m swebench.inference.run_api \
    --dataset_name_or_path princeton-nlp/SWE-bench_Lite_oracle \
    --model_name_or_path qwen-coder-plus \
    --output_dir ./results \
    --model_args "max_instances=10"
```

**Supported models:** `qwen-max`, `qwen-plus`, `qwen-turbo`, `qwen-coder-plus`, `qwen-coder-turbo`, `qwen2.5-*`

#### DeepSeek Integration
DeepSeek models via OpenAI-compatible API:

```bash
export DEEPSEEK_API_KEY="your-key-here"
python -m swebench.inference.run_api \
    --dataset_name_or_path princeton-nlp/SWE-bench_Lite_oracle \
    --model_name_or_path deepseek-coder \
    --output_dir ./results \
    --model_args "max_instances=10"
```

**Supported models:** `deepseek-chat`, `deepseek-coder`, `deepseek-reasoner`, `deepseek-v3`, `deepseek-coder-v2-instruct`

📖 [Qwen & DeepSeek Integration Guide](docs/guides/qwen_deepseek_integration.md)

### 📊 Results Analysis

After running inference, analyze predictions with comprehensive metrics:

```bash
# Analyze predictions (auto-generates JSON report)
python analyze_predictions.py results/your-model__SWE-bench_Lite_oracle__test.jsonl

# With evaluation results
python analyze_predictions.py results/predictions.jsonl \
    --evaluation results/evaluation.json
```

**Analysis Features:**
- ✅ **95%+ Metadata Coverage** - Captures all API-provided fields
- 📈 Statistical analysis (mean, median, percentiles, stdev)
- 💰 Cost tracking per instance and aggregated
- ⏱️ Latency analysis with P95/P99 metrics
- 🎯 Token usage with cache effectiveness
- 📝 Patch statistics and file modification patterns
- 🔍 Instance-level details with timestamps and response IDs
- 🌐 Multi-provider support (Claude Code, Qwen, DeepSeek)

**New in v2.0:**
- Request timestamps and time ranges
- API response IDs for traceability
- Provider and API version tracking
- System fingerprints for reproducibility
- Fixed DeepSeek cache token extraction

**Sample Output:**
```
📊 BASIC STATISTICS
Total Samples: 2
Request Time Range: 2025-09-29T22:48:23 to 2025-09-29T22:48:34

⚡ PERFORMANCE METRICS
Latency: Mean 11002ms | P95 11394ms
Cost: Total $0.0019 | Mean $0.0010
Tokens: Input 3,426 | Output 926

🤖 MODEL INFORMATION
Providers: {'DeepSeek': 2}
API Versions: {'OpenAI-compatible': 2}
```

See [Claude Code Integration Guide](docs/guides/claude_code_integration.md#results-analysis) for full analysis documentation.

## ⬇️ Downloads
| Datasets | Models | RAG |
| - | - | - |
| [💿 SWE-bench](https://huggingface.co/datasets/SWE-bench/SWE-bench) | [🦙 SWE-Llama 13b](https://huggingface.co/princeton-nlp/SWE-Llama-13b) | [🤗 "Oracle" Retrieval](https://huggingface.co/datasets/SWE-bench/SWE-bench_oracle) |
| [💿 SWE-bench Lite](https://huggingface.co/datasets/SWE-bench/SWE-bench_Lite) | [🦙 SWE-Llama 13b (PEFT)](https://huggingface.co/princeton-nlp/SWE-Llama-13b-peft) | [🤗 BM25 Retrieval 13K](https://huggingface.co/datasets/SWE-bench/SWE-bench_bm25_13K) |
| [💿 SWE-bench Verified](https://huggingface.co/datasets/SWE-bench/SWE-bench_Verified) | [🦙 SWE-Llama 7b](https://huggingface.co/princeton-nlp/SWE-Llama-7b) | [🤗 BM25 Retrieval 27K](https://huggingface.co/datasets/SWE-bench/SWE-bench_bm25_27K) |
| [💿 SWE-bench Multimodal](https://huggingface.co/datasets/SWE-bench/SWE-bench_Multimodal) | [🦙 SWE-Llama 7b (PEFT)](https://huggingface.co/princeton-nlp/SWE-Llama-7b-peft) | [🤗 BM25 Retrieval 40K](https://huggingface.co/datasets/SWE-bench/SWE-bench_bm25_40K) |
| | | [🤗 BM25 Retrieval 50K (Llama tokens)](https://huggingface.co/datasets/SWE-bench/SWE-bench_bm25_50k_llama) |

## 💫 Contributions
We would love to hear from the broader NLP, Machine Learning, and Software Engineering research communities, and we welcome any contributions, pull requests, or issues!
To do so, please either file a new pull request or issue and fill in the corresponding templates accordingly. We'll be sure to follow up shortly!

Contact person: [Carlos E. Jimenez](http://www.carlosejimenez.com/) and [John Yang](https://john-b-yang.github.io/) (Email: carlosej@princeton.edu, johnby@stanford.edu).

## ✍️ Citation & license
MIT license. Check `LICENSE.md`.

If you find our work helpful, please use the following citations.

For SWE-bench (Verified):
```bibtex
@inproceedings{
    jimenez2024swebench,
    title={{SWE}-bench: Can Language Models Resolve Real-world Github Issues?},
    author={Carlos E Jimenez and John Yang and Alexander Wettig and Shunyu Yao and Kexin Pei and Ofir Press and Karthik R Narasimhan},
    booktitle={The Twelfth International Conference on Learning Representations},
    year={2024},
    url={https://openreview.net/forum?id=VTF8yNQM66}
}
```

For SWE-bench Multimodal
```bibtex
@inproceedings{
    yang2024swebenchmultimodal,
    title={{SWE}-bench Multimodal: Do AI Systems Generalize to Visual Software Domains?},
    author={John Yang and Carlos E. Jimenez and Alex L. Zhang and Kilian Lieret and Joyce Yang and Xindi Wu and Ori Press and Niklas Muennighoff and Gabriel Synnaeve and Karthik R. Narasimhan and Diyi Yang and Sida I. Wang and Ofir Press},
    booktitle={The Thirteenth International Conference on Learning Representations},
    year={2025},
    url={https://openreview.net/forum?id=riTiq3i21b}
}
```

For SWE-bench Multilingual
```bibtex
@misc{yang2025swesmith,
    title={SWE-smith: Scaling Data for Software Engineering Agents},
    author={John Yang and Kilian Lieret and Carlos E. Jimenez and Alexander Wettig and Kabir Khandpur and Yanzhe Zhang and Binyuan Hui and Ofir Press and Ludwig Schmidt and Diyi Yang},
    year={2025},
    eprint={2504.21798},
    archivePrefix={arXiv},
    primaryClass={cs.SE},
    url={https://arxiv.org/abs/2504.21798},
}
```

## Our Other Projects

<div align="center">
  <a href="https://github.com/SWE-bench/sb-cli"><img src="docs/assets/sbcli_logo_text_below.svg" alt="sb-cli" height="120px"></a>
   &nbsp;&nbsp;
  <a href="https://github.com/SWE-bench/SWE-smith"><img src="docs/assets/swesmith_logo_text_below.svg" alt="SWE-smith" height="120px"></a>
   &nbsp;&nbsp;
  <a href="https://github.com/SWE-agent/SWE-agent"><img src="docs/assets/sweagent_logo_text_below.svg" alt="SWE-agent" height="120px"></a>
   &nbsp;&nbsp;
  <a href="https://github.com/SWE-agent/Mini-SWE-Agent"><img src="docs/assets/mini_logo_text_below.svg" alt="Mini-SWE-Agent" height="120px"></a>
  &nbsp;&nbsp;
  <a href="https://github.com/SWE-agent/SWE-ReX"><img src="docs/assets/swerex_logo_text_below.svg" alt="SWE-ReX" height="120px"></a>
   &nbsp;&nbsp;
  <!-- <a href="https://github.com/SWE-bench/SWE-bench"><img src="docs/assets/swebench_logo_text_below.svg" alt="SWE-bench" height="120px"></a> -->
</div>
