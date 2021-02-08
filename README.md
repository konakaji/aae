# 概要
dow jonesの株価をロードする量子サーキットを学習し、そのサーキットを使ってSVDを実行、SVD entropyを計算するスクリプト群です。

# 環境
- python3.8.5, pip20.1.1で動作確認済みです。
- その他ライブラリのバージョンは、requirements.txtに記載しています
  - 特にqiskitのバージョンは下記です。
```
qiskit==0.23.4
qiskit-aer==0.7.3
qiskit-aqua==0.8.1
qiskit-ibmq-provider==0.11.1
qiskit-ignis==0.5.1
qiskit-terra==0.16.3
```
# Code Readingについて
- 多数のクラスで構成されるパッケージのため、Pycharm等の統合開発環境を使うのが良いかもしれません。
- 実機まわりのコードは、下記が主な部分です。
  - Projectのルート/ibmq/base.py
  - Projectのルート/svd/core/sampler.py 中のQiskitSamplerのdo_sample
  - Projectのルート/svd/learn_sampler.py 中のdo_learn

# 導入方法
## ライブラリのインストール
Projectのルートに移動して、下記を実行します。

```
pip install -r requirements.txt
```
## IBMQ用のセットアップ
プロジェクトルート/ibmq/.ibmq_key を作成し、ファイルにはapiキー記述します。その際スペースや改行が入らないようにします。

```例)プロジェクトルート/ibmq/.ibmq_key
ceaf7e4xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
```

# 実行方法
## データ
Dow Jones Industrial Averageに含まれる銘柄の中で、2008年末の時価総額トップ４(https://toyokeizai.net/articles/-/2713)を利用します。
- XOM (Exxonmobil)
- WMT (Walmart)
- PG (P&G)
- MSFT (Microsoft)

データとしては、2008年4月から2009年3月の月初のopening priceの値を用います。データはこのパッケージにすでに含まれています。

## データロードサーキットの学習
### 実行方法
プロジェクトのルート/svd/に移動し、下記で実行可能です。
```
python learn_sampler.py (オプション)
```
オプションの一覧は下記で見ることができます。
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

基本的には、-d, -r, -l, --prefixを利用する。例えば5層のAnsatzを使って、ibmq_trontoをreservationで実行したければ
```
python learn_sampler.py -l 5 -d ibmq_tronto -r True --prefix tronto
```
とします。--prefixは、実験セッティングを区別するラベルに対応するので、わかりやすい名前をつけるのが推奨されます(何も指定しなければ、"default"になる)。--prefixをnaive以外に設定すれば、2つのサーキットを使って最適化されます。naiveに設定すると、一つのサーキットを使って最適化します。
なお、-d, -rを指定しなければ、単にqasm_simulatorで実行されます。-ds, -deは、SVD entropyを計算する期間に対応しています。例えば、

```
python learn_sampler.py -ds 1 -de 3
```
とすれば、3つの期間:(1〜5), (2〜6), (3〜7)のSVD entropyを計算するための、3つのデータロードサーキットを学習することに相当します。なお、dateの0, 1, 2...は下記のように対応します。

``` input/date.txt
0	Apr 01, 2008
1	May 01, 2008
2	Jun 02, 2008
3	Jul 01, 2008
4	Aug 01, 2008
5	Sep 02, 2008
6	Oct 01, 2008
7	Nov 03, 2008
8	Dec 01, 2008
9	Jan 02, 2009
10	Feb 02, 2009
11	Mar 02, 2009
12	Apr 01, 2009
```
例えば、(1〜5)はMay 01 2008からSep 02, 2008ということです。

### 結果
結果は下記のように保存されます。
- 各エネルギーの値の推移が、output/energy/(prefix)-(期間のindex)-(実行時のタイムスタンプ).txt、
- Data Samplerのモデルが、output/model/(prefix)-(期間のindex)-(実行時のタイムスタンプ).txt

## SVD の実行
プロジェクトのルート/svd/に移動し、下記で実行可能です。
```
python learn_svd.py (オプション)
```
先ほどと同様、下記にてオプションを確認できます。

```
python learn_svd.py -h

optional arguments:
  -h, --help            show this help message and exit
  -i ITER, --iter ITER  # of iterations in a trial
  -t TRIAL, --trial TRIAL
                        # of trials
  -l LAYER, --layer LAYER
                        # of layers
  -ds DS                start date index
  -de DE                end of date index
  --prefix PREFIX       prefix of the model and the energy files
  -lr LR                learning rate
```
--prefixに指定したものと同じprefixを持つData Samplerの中で最もコストの値を下げられたものを使います。その他、-lはSVDを行うサーキットの深さを指定します。svdに関しては無限回サンプルできたと仮定する(=state_vectorを使って最適化する)ので、現状実機を指定するオプションを用意していません。
### 結果
結果は下記のように保存されます。
- SVD 実行後のモデルが、output/svd_model/(prefix)-(期間のindex)-(実行時のタイムスタンプ).txt

## Entropyの計算
プロジェクトのルート/svd/に移動し、下記で実行可能です。
```
python compute_entropy.py (オプション)
```
先ほどと同様、下記にてオプションを確認できます。

```
python compute_entropy.py -h

optional arguments:
  -h, --help            show this help message and exit
  -ds DS                start date index
  -de DE                end of date index
  --prefixes [PREFIXES [PREFIXES ...]]
                        list of prefixes of the model and the energy files
```
--prefixesにはエントロピーを計算させたい、実験セッティングのprefixを一つずつ、記述します。

```
python compute_entropy.py --prefixes default tronto classical
```
ここで、classicalを指定すると、古典計算も実行します。

## 結果
- output/entropy/(prefix).txt の形で保存します。
