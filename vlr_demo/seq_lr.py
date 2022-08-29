import os
import numpy as np
import sys
import time
import matplotlib.pyplot as plt

from sklearn import metrics

home_dir = os.path.split(os.path.realpath(__file__))[0]
sys.path.append(os.path.join(home_dir))


class Arguments():
    def __init__(self):
        self.seed = 3
        self.n_local = 5
        self.batch_size = 256
        self.lr = 1e-3
        self.lbda = 0.001
        self.epochs = 50
        self.epsilon = 1e-7
        self.features_a = 8 * 7 * 6
        self.n_samples = 17903
        self.scale = 10


args = Arguments()


def load_data(path):
    x_train = np.load(path + 'x_train.npy')
    x_test = np.load(path + 'x_test.npy')
    y_train = np.load(path + 'y_train.npy')
    y_test = np.load(path + 'y_test.npy')
    x_val = np.load(path + 'x_val.npy')
    y_val = np.load(path + 'y_val.npy')

    x_train = np.concatenate((x_train, x_val), axis=0)
    y_train = np.concatenate((y_train, y_val), axis=0)

    y_train = np.expand_dims(y_train, 1)
    # y_test = np.expand_dims(y_test, 1)

    return x_train, x_test, y_train, y_test


def split_data(x_train, x_test, y_train, y_test, n_features=args.features_a):
    x_train_a = x_train[:, :n_features]
    x_train_b = x_train[:, n_features:]
    x_test_a = x_test[:, :n_features]
    x_test_b = x_test[:, n_features:]

    return x_train_a, x_train_b, x_test_a, x_test_b, y_train, y_test


def calculate_grad_with_label(w_a, x_a, w_b, x_b, y, lbda):
    # x_a : shape(N, feature)
    # w_a : shape(feature, 1)
    # y   : shape(N, 1)

    w_x_mul = np.dot(x_a, w_a) + np.dot(x_b, w_b)  # party B
    h_w = sigmoid(w_x_mul)  # party B  （aaaa~~, put an extra minus sign!! I'm so stupid!!）
    d = y - h_w  # party B
    grad_b = np.dot(x_b.T, d) / x_a.shape[0] + lbda * w_b

    return grad_b, d


def calculate_grad_with_d(w_a, x_a, d, lbda):
    # x_a : shape(N, feature_a)
    # w_a : shape(feature_a, 1)
    # y   : shape(N, 1)
    grad_a = np.dot(x_a.T, d) / x_a.shape[0] + lbda * w_a
    return grad_a


def cal_loss(w_a, x_a, w_b, x_b, y, lbda):
    # x_a : shape(N, feature)
    # w_a : shape(feature, 1)
    # y   : shape(N, 1)

    w_x_mul = np.dot(x_a, w_a) + np.dot(x_b, w_b)  # party B
    h_w = sigmoid(w_x_mul)  # party B  （aaaa~~, put an extra minus sign!! I'm so stupid!!）
    d = y - h_w  # party B
    grad_a = np.dot(x_a.T, d) / x_a.shape[0] + lbda * w_a
    grad_b = np.dot(x_b.T, d) / x_a.shape[0] + lbda * w_b
    loss1 = -sum(y * np.log(h_w + args.epsilon) + (1 - y) * np.log(1 - h_w + args.epsilon)) / x_a.shape[0]
    loss2 = lbda * (sum(w_a ** 2) + sum(w_b ** 2)) / 2.0
    loss = loss1 + loss2
    # loss = -sum(y * np.log(h_w + args.epsilon) + (1 - y) * np.log(1 - h_w + args.epsilon)) / x_a.shape[0] + lbda * (
    #             sum(w_a ** 2) + sum(w_b ** 2)) / 2.0
    print("loss1: {0}, loss2: {1}, loss_all: {2}".format(loss1, loss2, loss))

    return loss, grad_a, grad_b


def cal_auc_acc(w_a, x_a, w_b, x_b, y, lbda):
    w_x_mul = np.dot(x_a, w_a) + np.dot(x_b, w_b)
    probaOfPositive = sigmoid(w_x_mul)
    probaOfNegative = 1 - probaOfPositive
    proba = np.hstack((probaOfNegative, probaOfPositive))
    y_pred = np.argmax(proba, axis=1)
    acc = sum(y_pred == y) / float(y.shape[0])
    auc = metrics.roc_auc_score(y, probaOfPositive)
    confusionMatrix = metrics.confusion_matrix(y_test, y_pred)
    return acc, auc, confusionMatrix


def sigmoid(x):
    return np.exp(np.fmin(x, 0)) / (1.0 + np.exp(-np.abs(x)))


def plot_curve(path):
    # path = "./result/LR/cyclic/n_local_1"
    acc_li = np.load(path + "acc.npy")
    auc_li = np.load(path + "auc.npy")
    loss_li = np.load(path + "loss.npy")
    grad_norm = np.load(path + "grad_norm.npy")

    n_batchs = int(args.n_samples / args.batch_size) + 1
    plt.figure()
    plt.plot(np.arange(len(acc_li)) * args.scale, acc_li)
    plt.xlabel("communication rounds")
    plt.ylabel("Accuracy")
    plt.savefig(path + "acc.png")
    plt.show()

    plt.plot(np.arange(len(auc_li)) * args.scale, auc_li)
    plt.xlabel("communication rounds")
    plt.ylabel("Auc")
    plt.savefig(path + "auc.png")
    plt.show()

    plt.plot(np.arange(len(loss_li)) * args.scale, loss_li)
    plt.xlabel("communication rounds")
    plt.ylabel("loss")
    plt.savefig(path + "loss.png")
    plt.show()

    plt.semilogy(np.arange(len(grad_norm)) * args.scale, grad_norm)
    plt.xlabel("communication rounds")
    plt.ylabel("grad_norm")
    plt.savefig(path + "grad.png")
    plt.show()


def gradient_generator(x_train, x_test, y_train, y_test, path):
    print("------ Sequential ------")

    output_file = path + "results_" + str(args.n_local) + "_r.csv"
    x_train_a, x_train_b, x_test_a, x_test_b, y_train_b, y_test = split_data(x_train, x_test, y_train, y_test)

    n_samples = x_train_a.shape[0]
    feature_a = x_train_a.shape[1]
    feature_b = x_train_b.shape[1]

    w_a = np.zeros((feature_a, 1))
    w_b = np.zeros((feature_b, 1))

    np.random.seed(args.seed)
    indexes = np.arange(n_samples)
    np.random.shuffle(indexes)
    n_batch = int(n_samples / args.batch_size)

    acc_li = []
    auc_li = []
    grad_norm = []
    loss_li = []

    init_loss, init_grad_a, init_grad_b = cal_loss(w_a, x_train_a, w_b, x_train_b, y_train_b, args.lbda)
    init_acc, init_auc, init_cf = cal_auc_acc(w_a, x_test_a, w_b, x_test_b, y_test, args.lbda)
    acc_li.append(init_acc)
    auc_li.append(init_auc)
    grad_norm.append(sum(init_grad_a ** 2) + sum(init_grad_b ** 2))
    loss_li.append(init_loss)

    print("initial loss: {}, init grad norm: {}".format(init_loss, grad_norm[-1]))
    print("init acc: {}, init_auc: {}, init confusion matrix: {}".format(init_acc, init_auc, init_cf))

    args.epochs = 1
    args.n_local = 20
    args.batch_size = 128
    print("learning rate {0}".format(args.lr))
    print("n local {0}".format(args.n_local))
    print("epoch {0}".format(args.epochs))
    print("n_batch {0}".format(n_batch))

    with open(output_file, 'w', encoding='UTF8') as file:
        file.write("epoch" + "," + "loss" + "," + "acc" + "," + "auc" + "\n")
        file.flush()
        comm = 0  # communication counts
        for e in range(args.epochs):
            lssum = 0
            # if (e + 1) % 5 == 0:
            # 	args.lr = args.lr / (e + 1)
            for i_batch in range(n_batch):
                # args.lr = base / np.sqrt(e*n_batch + i_batch + 1)
                cur_indexes = indexes[i_batch * args.batch_size:min((i_batch + 1) * args.batch_size, n_samples)]
                x_a_batch = x_train_a[cur_indexes]
                x_b_batch = x_train_b[cur_indexes]
                y_batch = y_train[cur_indexes]

                # grad_b, d = calculate_grad_with_label(w_a, x_a_batch, w_b, x_b_batch, y_batch, args.lbda)
                # grad_a = calculate_grad_with_d(w_a, x_a_batch, d, args.lbda)
                for j in range(args.n_local):
                    # print("B epoch: {0}, local: {1}".format(e, j))
                    grad_b, d = calculate_grad_with_label(w_a, x_a_batch, w_b, x_b_batch, y_batch, args.lbda)
                    w_b = w_b + args.lr * grad_b
                for j in range(args.n_local):
                    # print("A epoch: {0}, local: {1}".format(e, j))
                    grad_a = calculate_grad_with_d(w_a, x_a_batch, d, args.lbda)
                    w_a = w_a + args.lr * grad_a

                # print("epoch: {0}; batch {1}".format(e, i_batch))
                # print("w_a {0}".format(w_a))
                # print("w_b {0}".format(w_b))
                comm += 1
                if comm % 5 == 0:
                    print("epoch: {0}; batch {1}".format(e, i_batch))
                    print("w_a {0}".format(w_a))
                    print("w_b {0}".format(w_b))
                    acc, auc, cf = cal_auc_acc(w_a, x_test_a, w_b, x_test_b, y_test, args.lbda)
                    total_loss, total_grad_a, total_grad_b = cal_loss(w_a, x_train_a, w_b, x_train_b, y_train,
                                                                      args.lbda)
                    print("acc {0}; auc {1}".format(acc, auc))
                    # print("epoch: {}. loss: {}, grad_norm: {}, acc: {}, auc: {}".format(e, lssum, sum(grad_a**2)+sum(grad_b**2), acc, auc))
                    acc_li.append(acc)
                    auc_li.append(auc)
                    grad_norm.append(sum(total_grad_a ** 2) + sum(total_grad_b ** 2))
                    loss_li.append(total_loss)
                    print(
                        "epoch: {}. iter: {}. loss: {}, grad_norm: {}, acc: {}, auc: {}".format(e, i_batch, total_loss,
                                                                                                sum(
                                                                                                    total_grad_a ** 2) + sum(
                                                                                                    total_grad_b ** 2),
                                                                                                acc, auc))
                    file.write(str(e) + "," + str(total_loss) + "," + str(acc) + "," + str(auc) + "\n")
                    file.flush()
    print("confusion matrix:")
    print(cf)
    # path = "./result/LR/"
    np.save(path + "acc.npy", acc_li)
    np.save(path + "auc.npy", auc_li)
    np.save(path + "grad_norm.npy", grad_norm)
    np.save(path + "loss.npy", loss_li)


if __name__ == "__main__":
    t = time.time()
    # path1 = "../data/in-hospital-mortality/ihm_data/"
    path1 = "../../data/ihm_data/"
    x_train, x_test, y_train, y_test = load_data(path1)
    print("x_train: {}, x_test: {}, y_train: {}, y_test: {}".format(x_train.shape, x_test.shape, y_train.shape,
                                                                    y_test.shape))
    x_train_a, x_train_b, x_test_a, x_test_b, y_train, y_test = split_data(x_train, x_test, y_train, y_test)
    print("x_train_a: {}, x_train_b: {}, x_test_a: {}, x_test_b: {}, y_train: {}, y_test: {}".format(x_train_a.shape,
                                                                                                     x_train_b.shape,
                                                                                                     x_test_a.shape,
                                                                                                     x_test_b.shape,
                                                                                                     y_train.shape,
                                                                                                     y_test.shape))
    # print(y_train.shape)

    path = "./result/LR/seq-cyclic/"
    gradient_generator(x_train, x_test, y_train, y_test, path)
    print("total time:", (time.time() - t), "s")
    plot_curve(path)
