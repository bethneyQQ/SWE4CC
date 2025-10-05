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
  - pip=24.2=py38h06a4308_0
  - python=3.8.20=he870216_0
  - readline=8.2=h5eee18b_0
  - setuptools=75.1.0=py38h06a4308_0
  - sqlite=3.45.3=h5eee18b_0
  - tk=8.6.14=h39e8969_0
  - wheel=0.44.0=py38h06a4308_0
  - xz=5.4.6=h5eee18b_1
  - zlib=1.2.13=h5eee18b_1
  - pip:
      - aiohappyeyeballs==2.4.3
      - aiohttp==3.10.9
      - aiosignal==1.3.1
      - argon2-cffi==23.1.0
      - argon2-cffi-bindings==21.2.0
      - asgiref==3.8.1
      - async-timeout==4.0.3
      - attrs==24.2.0
      - backports-zoneinfo==0.2.1
      - bcrypt==4.2.0
      - certifi==2024.8.30
      - cffi==1.17.1
      - charset-normalizer==3.4.0
      - docutils==0.20.1
      - exceptiongroup==1.2.2
      - frozenlist==1.4.1
      - geoip2==4.8.0
      - h11==0.14.0
      - idna==3.10
      - jinja2==3.1.4
      - markupsafe==2.1.5
      - maxminddb==2.6.2
      - multidict==6.1.0
      - numpy==1.24.4
      - outcome==1.3.0.post0
      - pillow==10.4.0
      - propcache==0.2.0
      - pycparser==2.22
      - pylibmc==1.6.3
      - pymemcache==4.0.0
      - pysocks==1.7.1
      - python-memcached==1.62
      - pytz==2024.2
      - pywatchman==2.0.0
      - pyyaml==6.0.2
      - redis==5.1.1
      - requests==2.32.3
      - selenium==4.25.0
      - sniffio==1.3.1
      - sortedcontainers==2.4.0
      - sqlparse==0.5.1
      - tblib==3.0.0
      - trio==0.26.2
      - trio-websocket==0.11.1
      - typing-extensions==4.12.2
      - tzdata==2024.2
      - urllib3==2.2.3
      - websocket-client==1.8.0
      - wsproto==1.2.0
      - yarl==1.14.0
prefix: /opt/miniconda3/envs/testbed

EOF_59812759871
conda env create -f /root/environment.yml
conda activate testbed
