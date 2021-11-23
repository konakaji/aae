# 1. 概要
AAEでDataの学習を行うためのライブラリです。

# 2. 環境
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

# 3. 導入方法
## ライブラリのインストール
Projectのルートに移動して、下記を実行します。

```
pip install -r requirements.txt
```

# 4. 実行方法
## 学習
まずは、demo/learnpyを見てください。こちらは、
3-qubit x 4層のParameterized Quantum Circuitを使って、[0,0,1,0]というデータを、状態の係数に埋め込むデモです。
要素が2^2なのに、3-qubit用いるのは、AAE論文のCase2にあるように、ancilla qubitが必要なためです。
learnメソッドを実行することによって、filename=xxxで指定したファイル名で、"output/data_model/"以下のフォルダに、
学習済みモデルを保存します。関数が返すのは、result[0]が結果の状態ベクトル、result[1]が最終的なコストの値です。

```
def learn():
    data_learning = DataLearning(n_qubit=3, layer=4)
    result = data_learning.learn([0, 0, 1, 0], n_shot=N_SHOT, filename=DEMO_FILENAME, iteration=1)
    print(result[0], result[1])
    print(data_learning.get_state_vector())
```

### DataLearning.learnで指定可能な項目
- coefficinents: 埋め込みたい係数の列(必須)
- device: simulator, もしくはIBMQのデバイス
- filename: 保存したいデータ名
- reservation: IBMQのreservationシステムを使うか否か
- n_shot: 一つの勾配を計算するのに行う測定数
- variance: Gaussian Kernelの幅
- iteration: 学習を何ステップまで行うか
- lr_scheduler: 学習率の変化スケジュールの指定
- allocator: 論理qubitと物理qubitのマッピング方法指定
- dry: Trueにすると、fileが生成されない

```
def learn(self, coefficients: [float], device=None, filename="default-" + str(int(time.time())),
              reservation=False, n_shot=400, variance=0.25, iteration=200, lr_scheduler=UnitLRScheduler(0.1),
              allocator=None,
              dry=False)
```


## アルゴリズム実行
以下は、learnメソッドで構築したモデルを使って、量子アルゴリズムを実行する例です。
learnの際に指定したものと同じファイル名を指定して、data_learning.load(filename)でモデルを読み込みます。
data_learning.add_data_gates()で量子サーキットにデータロードサーキットを追加します。
なお、Case2の場合、ancillaの値が1である必要がありますが、
data_learning.execute_with_post_selection()を使って実行することで、ancillaの値が1になった場合に限定した結果が得られます。

```
def load():
    data_learning = DataLearning(n_qubit=3, layer=4)
    data_learning.load(DEMO_FILENAME)
    qr = qiskit.QuantumRegister(3)
    cr = qiskit.ClassicalRegister(3)
    qc = qiskit.QuantumCircuit(qr, cr)
    data_learning.add_data_gates(qc, qr)
    # add gates for quantum algorithm-------
    # qc.xxx()
    # ---------------------------------------
    qc.measure(1, 1)
    qc.measure(2, 2)
    simulator = qiskit.Aer.get_backend("qasm_simulator")
    future = data_learning.execute_with_post_selection(qc, simulator, shots=N_SHOT)
    samples = future.get()
    for sample in samples:
        print(sample)
```


