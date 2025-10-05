#!/bin/bash
set -euxo pipefail
source /opt/miniconda3/bin/activate
cat <<'EOF_59812759871' > /root/environment.yml
name: testbed
channels:
  - defaults
  - conda-forge
dependencies:
  - _libgcc_mutex=0.1=main
  - _openmp_mutex=5.1=1_gnu
  - ca-certificates=2024.9.24=h06a4308_0
  - ld_impl_linux-64=2.40=h12ee557_0
  - libffi=3.4.4=h6a678d5_1
  - libgcc-ng=11.2.0=h1234567_1
  - libgomp=11.2.0=h1234567_1
  - libstdcxx-ng=11.2.0=h1234567_1
  - ncurses=6.4=h6a678d5_0
  - openssl=3.0.15=h5eee18b_0
  - pip=24.2=py39h06a4308_0
  - python=3.9.20=he870216_1
  - readline=8.2=h5eee18b_0
  - setuptools=75.1.0=py39h06a4308_0
  - sqlite=3.45.3=h5eee18b_0
  - tk=8.6.14=h39e8969_0
  - tzdata=2024b=h04d1e81_0
  - wheel=0.44.0=py39h06a4308_0
  - xz=5.4.6=h5eee18b_1
  - zlib=1.2.13=h5eee18b_1
  - pip:
      - alabaster==0.7.16
      - babel==2.16.0
      - cachetools==5.5.0
      - certifi==2024.8.30
      - chardet==5.2.0
      - charset-normalizer==3.4.0
      - colorama==0.4.6
      - cython==3.0.11
      - distlib==0.3.9
      - docutils==0.20.1
      - exceptiongroup==1.2.2
      - filelock==3.16.1
      - html5lib==1.1
      - idna==3.10
      - imagesize==1.4.1
      - importlib-metadata==8.5.0
      - iniconfig==2.0.0
      - jinja2==3.1.4
      - markupsafe==3.0.2
      - packaging==24.1
      - platformdirs==4.3.6
      - pluggy==1.5.0
      - pygments==2.18.0
      - pyproject-api==1.8.0
      - pytest==8.3.3
      - requests==2.32.3
      - six==1.16.0
      - snowballstemmer==2.2.0
      - tomli==2.0.2
      - tox==4.16.0
      - tox-current-env==0.0.11
      - urllib3==2.2.3
      - virtualenv==20.26.6
      - webencodings==0.5.1
      - zipp==3.20.2
prefix: /opt/miniconda3/envs/testbed

EOF_59812759871
conda env create -f /root/environment.yml
conda activate testbed
