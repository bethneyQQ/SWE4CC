#!/bin/bash
set -euxo pipefail
source /opt/miniconda3/bin/activate
conda create -n testbed python=3.9 -y
cat <<'EOF_59812759871' > $HOME/requirements.txt
black==22.6.0
flake8==5.0.4
flake8-typing-imports==1.13.0
isort==5.10.1
mypy==0.971

astroid==2.12.13  # Pinned to a specific version for tests
typing-extensions~=4.4
py~=1.11.0
pytest~=7.2
pytest-benchmark~=4.0
pytest-timeout~=2.1
towncrier~=22.8
requests

coveralls~=3.3
coverage~=6.4
pre-commit~=2.20
tbump~=6.9.0
contributors-txt>=0.9.0
pytest-cov~=3.0
pytest-profiling~=1.7
pytest-xdist~=2.5
types-setuptools
tox>=3

EOF_59812759871
conda activate testbed && python -m pip install -r $HOME/requirements.txt
rm $HOME/requirements.txt
conda activate testbed
