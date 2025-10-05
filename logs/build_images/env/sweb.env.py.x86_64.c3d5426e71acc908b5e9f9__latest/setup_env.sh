#!/bin/bash
set -euxo pipefail
source /opt/miniconda3/bin/activate
conda create -n testbed python=3.9 -y
cat <<'EOF_59812759871' > $HOME/requirements.txt
black==22.3.0
flake8==4.0.1
flake8-typing-imports==1.12.0
isort==5.10.1
mypy==0.941

astroid==2.11.3  # Pinned to a specific version for tests
typing-extensions~=4.1
pytest~=7.0
pytest-benchmark~=3.4
pytest-timeout~=2.1

coveralls~=3.3
coverage~=6.2
pre-commit~=2.17;python_full_version>="3.6.2"
tbump~=6.6.0
contributors-txt>=0.7.3
pyenchant~=3.2
pytest-cov~=3.0
pytest-profiling~=1.7
pytest-xdist~=2.5
types-setuptools

EOF_59812759871
conda activate testbed && python -m pip install -r $HOME/requirements.txt
rm $HOME/requirements.txt
conda activate testbed
