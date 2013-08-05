"""
==================================================================
Comparing PyStruct and SVM-Struct for multi-class classification
==================================================================
This example compares the performance of pystruct and SVM^struct on a
multi-class problem.
For the example to work, you need to install SVM^multiclass and
set the path in this file.
We are not using SVM^python, as that would be much slower, and we would
need to implement our own model in a SVM^python compatible way.
Instead, we just call the SVM^multiclass binary.

This comparison is only meaningful in the sense that both libraries
use general structured prediction solvers to solve the task.
The specialized implementation of the Crammer-Singer SVM in LibLinear
is much faster than either one.

For SVM^struct, the plot show CPU time as reportet by SVM^struct.
For pystruct, the plot shows the time spent in the fit function
according to time.clock.

Both models have disabled constraint caching. With constraint caching,
SVM^struct is somewhat faster, but PyStruct doesn't gain anything.
"""

import tempfile
import os
from time import clock

import numpy as np
from sklearn.datasets import dump_svmlight_file
from sklearn.datasets import fetch_mldata, load_iris, load_digits
from sklearn.metrics import accuracy_score
import matplotlib.pyplot as plt

from pystruct.models import CrammerSingerSVMModel
from pystruct.learners import OneSlackSSVM

# please set the path to the svm-struct multiclass binaries here
svmstruct_path = "/home/user/amueller/tools/svm_multiclass/"


class MultiSVM():
    """scikit-learn compatible interface for SVM^multi.

    Dumps the data to a file and calls the binary.
    """
    def __init__(self, C=1.):
        self.C = C

    def fit(self, X, y):
        self.model_file = tempfile.mktemp(suffix='.svm')
        train_data_file = tempfile.mktemp(suffix='.svm_dat')
        dump_svmlight_file(X, y + 1, train_data_file, zero_based=False)
        C = self.C * 100. * len(X)
        svmstruct_process = os.popen(svmstruct_path
                                     + "svm_multiclass_learn -w 3 -c %f %s %s"
                                     % (C, train_data_file, self.model_file))
        self.output_ = svmstruct_process.read().split("\n")
        self.runtime_ = float(self.output_[-4].split(":")[1])

    def _predict(self, X, y=None):
        if y is None:
            y = np.ones(len(X))
        train_data_file = tempfile.mktemp(suffix='.svm_dat')

        dump_svmlight_file(X, y, train_data_file, zero_based=False)

        prediction_file = tempfile.mktemp(suffix='.out')
        os.system(svmstruct_path + "svm_multiclass_classify %s %s %s"
                  % (train_data_file, self.model_file, prediction_file))
        return np.loadtxt(prediction_file)

    def predict(self, X):
        return self._predict(X)[:, 0] - 1

    def score(self, X, y):
        y_pred = self.predict(X)
        return accuracy_score(y, y_pred)

    def decision_function(self, X):
        return self._predict(X)[:, 1:]


def eval_on_data(X, y, svm, Cs):
    accuracies, times = [], []
    for C in Cs:
        svm.C = C
        start = clock()
        svm.fit(X, y)
        if hasattr(svm, "runtime_"):
            times.append(svm.runtime_)
        else:
            times.append(clock() - start)
        accuracies.append(accuracy_score(y, svm.predict(X)))
    return accuracies, times


def plot_curves(curve_svmstruct, curve_pystruct, Cs, title="", filename=""):
    plt.figure(figsize=(5, 4))
    plt.plot(curve_svmstruct, "--", label="SVM^struct", c='red', linewidth=3)
    plt.plot(curve_pystruct, "-.", label="PyStruct", c='blue', linewidth=3)
    plt.xlabel("C")
    plt.xticks(np.arange(len(Cs)), Cs)
    plt.legend(loc='best')
    plt.title(title)
    if filename:
        plt.savefig("%s.pdf" % filename, bbox_inches='tight')


def main():
    Cs = 10. ** np.arange(-4, 1)
    multisvm = MultiSVM()
    svm = OneSlackSSVM(CrammerSingerSVMModel(), tol=0.001)

    iris = load_iris()
    X, y = iris.data, iris.target

    accs_pystruct, times_pystruct = eval_on_data(X, y, svm, Cs=Cs)
    accs_svmstruct, times_svmstruct = eval_on_data(X, y, multisvm, Cs=Cs)

    plot_curves(times_svmstruct, times_pystruct, Cs=Cs, title="times iris")
    plot_curves(accs_svmstruct, accs_pystruct, Cs=Cs, title="accuracy iris")

    digits = load_digits()
    X, y = digits.data / 16., digits.target

    svm = OneSlackSSVM(CrammerSingerSVMModel(), tol=0.001)
    accs_pystruct, times_pystruct = eval_on_data(X, y, svm, Cs=Cs)
    accs_svmstruct, times_svmstruct = eval_on_data(X, y, multisvm, Cs=Cs)

    plot_curves(times_svmstruct, times_pystruct, Cs=Cs, title="times digits")
    plot_curves(accs_svmstruct, accs_pystruct, Cs=Cs, title="accuracy digits")

    #digits = fetch_mldata("USPS")
    #X, y = digits.data, digits.target.astype(np.int)
    #svm = OneSlackSSVM(CrammerSingerSVMModel(), tol=0.001)

    #accs_pystruct, times_pystruct = eval_on_data(X, y - 1, svm, Cs=Cs)
    #accs_svmstruct, times_svmstruct = eval_on_data(X, y, multisvm, Cs=Cs)

    #plot_timings(np.array(times_svmstruct), times_pystruct,
                 #dataset="usps")
    plt.show()


if __name__ == "__main__":
    main()
