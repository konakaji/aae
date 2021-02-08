# 概要
dow jonesの株価をロードする量子サーキットを学習し、そのサーキットを使ってSVDを実行、SVD entropyを計算するスクリプト群です。

# 環境
- python3.8.5, pip20.1.1で動作確認済み
- その他ライブラリのバージョンは、requirements.txtに記載
  - 特にqiskitのバージョンは下記
```
qiskit==0.23.4
qiskit-aer==0.7.3
qiskit-aqua==0.8.1
qiskit-ibmq-provider==0.11.1
qiskit-ignis==0.5.1
qiskit-terra==0.16.3
```

# 導入方法
## ライブラリのインストール
Projectのルートに移動して、下記を実行。

```
pip install -r requirements.txt
```
## IBMQ用のセットアップ
プロジェクトルート/ibmq/.ibmq_key を作成し、ファイルにはapiキー記述する。その際スペースや改行が入らないようにする。

```例)プロジェクトルート/ibmq/.ibmq_key
ceaf7e4xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
```

# 実行方法
## データロードサーキットの学習
プロジェクトのルート/svd/に移動し、下記で実行可能。
```
python learn_sampler.py (オプション)
```
オプションの一覧は下記で見ることができる。
```
python learn_sampler.py -h

optional arguments:
  -h, --help            show this help message and exit
  -d DEVICE, --device DEVICE
                        name of the ibmq device ex: ibmq_tronto
  -i ITER, --iter ITER  # of iterations in a trial
  -r RESERVATION, --reservation RESERVATION
                        if you made reservation, set true
  -t TRIAL, --trial TRIAL
                        # of trials
  -l LAYER, --layer LAYER
                        # of layers
  -n NSHOT, --nshot NSHOT
                        # of Nshot
  -v VARIANCE, --variance VARIANCE
                        variance of Gaussian Kernel
  -ds DS                start date index
  -de DE                end of date index
  -c CUTOFF, --cutoff CUTOFF
                        cut off of the kernel
  --prefix PREFIX       prefix of the model and the energy files
  -lr LR                learning rate

```

基本的には、-d, -r, --prefixのみを利用する。例えばibmq_trontoをreservationで実行したければ
```
python learn_sampler.py -d ibmq_tronto -r True --prefix tronto
```
とする。prefixのオプションは、実験セッティングのラベルに
  -lr LR                learning rate
  -lr LR                learning ra
