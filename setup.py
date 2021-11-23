import setuptools

with open("README.md", "r") as fh:
    long_description = fh.read()

setuptools.setup(
    name="aae",
    version="0.0.2",
    author="kouhei nakaji",
    author_email="kohei.nakaji@keio.jp",
    description="Tool for approximately loading coefficients",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/konakaji/aae",
    packages=setuptools.find_packages(),
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    install_requires=[
        "attrs==20.3.0",
        "bs4==0.0.1",
        "certifi==2020.12.5",
        "cffi==1.14.4",
        "chardet==4.0.0",
        "cryptography==3.3.1",
        "cycler==0.10.0",
        "Cython==0.29.21",
        "decorator==4.4.2",
        "dill==0.3.3",
        "dlx==1.0.4",
        "docplex==2.20.204",
        "fastdtw==0.3.4",
        "fastjsonschema==2.15.0",
        "h5py==3.1.0",
        "idna==2.10",
        "inflection==0.5.1",
        "joblib==1.0.0",
        "jsonschema==3.2.0",
        "kiwisolver==1.3.1",
        "lxml==4.6.2",
        "matplotlib==3.3.4",
        "more-itertools==8.6.0",
        "mpmath==1.1.0",
        "multitasking==0.0.9",
        "nest-asyncio==1.5.1",
        "networkx==2.5",
        "ntlm-auth==1.5.0",
        "numpy==1.19.1",
        "pandas==1.2.1",
        "Pillow==8.1.0",
        "ply==3.11",
        "psutil==5.8.0",
        "pybind11==2.6.2",
        "pycparser==2.20",
        "pyparsing==2.4.7",
        "pyrsistent==0.17.3",
        "python-constraint==1.4.0",
        "python-dateutil==2.8.1",
        "pytz==2021.1",
        "qiskit==0.23.4",
        "qiskit-aer==0.7.3",
        "qiskit-aqua==0.8.1",
        "qiskit-ibmq-provider==0.11.1",
        "qiskit-ignis==0.5.1",
        "qiskit-terra==0.16.3",
        "Quandl==3.6.0",
        "requests==2.25.1",
        "requests-ntlm==1.1.0",
        "retworkx==0.7.2",
        "scikit-learn==0.24.1",
        "scipy==1.6.0",
        "six==1.15.0",
        "soupsieve==2.1",
        "sympy==1.7.1",
        "threadpoolctl==2.1.0",
        "urllib3==1.26.3",
        "websockets==8.1"
    ],
    python_requires='>=3.7',
)
