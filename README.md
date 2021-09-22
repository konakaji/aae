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

# 3. 導入方法
## ライブラリのインストール
Projectのルートに移動して、下記を実行します。

```
pip install -r requirements.txt
```
## IBMQ用のセットアップ
プロジェクトルート/ibmq/.ibmq_key を作成し、ファイルにはapiキー記述します。その際スペースや改行が入らないようにします。
(なおqasm_simulatorを用いる場合は、こちらのステップは飛ばして頂いて構いません。)

```例)プロジェクトルート/ibmq/.ibmq_key
ceaf7e4xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
```

# 4. 実行方法
## 学習
まずは、svd/data_learning_demo.pyを見てください。こちらは、
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
### DataLearning.loadで指定可能な項目
- filename: learnで作成した学習済みモデルの名前
- device: simulator, もしくはIBMQのデバイス
- reservation: IBMQのreservationシステムを使うか否か 
- allocator: 論理qubitと物理qubitのマッピング方法指定

# 5.更なるカスタマイズの方法
## 読むべきコード
上記で解説したDataLearningクラスは下記です。こちらのファイルに含まれるコードを読み進めてください。
```
svd/svd/extention/data_learning.py
```

DataLearningクラスはDataLearningBaseを継承しており、主な関数はDataLearningBaseの方に記述しています。
- クラスを継承すると、関数を引き継ぐことができます。(例:DataLearningBaseで実装している関数は、DataLearningクラスでも使える)
- なお、positiveデータの学習を扱うPositiveDataLearningクラスもDataLearningBaseを継承しています

## コスト関数を変更したい場合
DataLearningBaseの中の下記が重要。
```
  def _build_task(self, probability, another_probability, additional_circuit, encoder,
                  converter, data_sampler, factory, optimizer, variance, nshot):
      mmd_gradient_cost = self._build_gradient_cost(probability, another_probability, additional_circuit,
                                                    encoder)
      # costs used just for displaying (computed by using state_vector)
      kl_cost = KLCost(probability, encoder)
      another_kl_cost = KLCost(another_probability, encoder, converter)
      mmd_cost = MMDCost(probability, encoder)
      mmd_cost.custom_kernel = gaussian_kernel(variance)
      another_mmd_cost = MMDCost(another_probability, encoder, CircuitAppender(additional_circuit))
      task_watcher = TaskWatcher([ImageGenrator(OPTIMIZATION_FIGURE_PATH, probability),
                                  ImageGenrator(SECOND_OPTIMIZATION_FIGURE_PATH, another_probability,
                                                converter=converter)],
                                 [kl_cost, another_kl_cost, mmd_cost, another_mmd_cost])

      def total_cost(sampler):
          return mmd_cost.value(sampler) + another_mmd_cost.value(sampler)

      return AdamGradientOptimizationTask(data_sampler, factory, mmd_gradient_cost,
                                          task_watcher, nshot, optimizer), total_cost
```
- mmd_gradient_costが、パラメータの更新用に使われるコスト関数
  - kl_cost, another_kl_cost, mmd_cost, another_mmd_costは状況確認用であり、パラメータ更新には使われていない
- このmmd_gradient_costを置き換えれば、別のコスト関数での学習が可能
- probabilityは係数の2乗に対応、another_probabilityは、Hadamard後の係数の2乗に対応

- mmd_gradient_costは下記のクラス
```
class MultipleMMDGradientCost(MMDGradientCost):
    def __init__(self, probability: Probability,
                 another_probability: Probability, another_circuit: QiskitCircuit, encoder: Encoder, lambda_1=0.5,
                 lambda_2=0.5):
        self.probability = probability
        self.another_probability = another_probability
        self.another_circuit = another_circuit
        self.lambda_1 = lambda_1
        self.lambda_2 = lambda_2
        super().__init__(probability, encoder)

    def sample_gradient(self, sampler: ParametrizedQiskitSampler,
                        factory: ParametrizedQiskitSamplerFactory, n_shot):
        sampler.circuit.additional_circuit = None
        base_gradient = super().do_sample_gradient(sampler, factory, n_shot, self.probability)
        sampler.circuit.additional_circuit = self.another_circuit
        another_gradient = super().do_sample_gradient(sampler, factory, n_shot, self.another_probability)
        sampler.circuit.additional_circuit = None
        return self.lambda_1 * base_gradient + self.lambda_2 * another_gradient
```
- sample_gradientの返り値は、gradient vector
- do_sample_gradientがParameter shift ruleを使ってMMDのgradientを計算する関数。
- 別のgradientを返すような、以下の関数を実装して代入しさえすれば良い

```
class NewGradientCost(GradientCost):
  def __init__(xxx):
    self.xxx = xxxx

  def sample_gradient(self, sampler: ParametrizedQiskitSampler,
                        factory: ParametrizedQiskitSamplerFactory, n_shot):
      originalのgradientを実装したもの...
      
```
- DataLearning classを書き換えるのはやや煩雑かと思いますので、costをDataLearning.learnに代入できるように変更する予定です
- 学習実行中のエネルギーの値を正しくモニターしたければ、TaskWatcherも書き換える必要があります
  - これもDataLearning.learnに代入できるように変更する予定です
```
task_watcher = TaskWatcher([ImageGenrator(OPTIMIZATION_FIGURE_PATH, probability),
                                  ImageGenrator(SECOND_OPTIMIZATION_FIGURE_PATH, another_probability,
                                                converter=converter)],
                                 [kl_cost, another_kl_cost, mmd_cost, another_mmd_cost])
```



