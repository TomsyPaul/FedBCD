import numpy as np

from encryption.paillier import PaillierPublicKey, PaillierPrivateKey


def encrypt_array(public_key: PaillierPublicKey, A):
    encrypt_A = []
    for i in range(len(A)):
        encrypt_A.append(public_key.encrypt(float(A[i])))
    return np.array(encrypt_A)


def encrypt_matrix(public_key: PaillierPublicKey, A):
    if len(A.shape) == 1:
        A = np.expand_dims(A, axis=0)

    encrypt_A = []
    for i in range(len(A)):
        row = []
        for j in range(len(A[i])):
            if len(A.shape) == 3:
                row.append([public_key.encrypt(float(A[i, j, k])) for k in range(len(A[i][j]))])
            else:
                row.append(public_key.encrypt(float(A[i, j])))

        encrypt_A.append(row)
    return np.array(encrypt_A)


def encrypt_matmul(public_key: PaillierPublicKey, A, encrypted_B):
    """
     matrix multiplication between a plain matrix and an encrypted matrix

    :param public_key:
    :param A:
    :param encrypted_B:
    :return:
    """
    if A.shape[-1] != encrypted_B.shape[0]:
        print("A and encrypted_B shape are not consistent")
        exit(1)
    # TODO: need a efficient way to do this?
    res = [[public_key.encrypt(0) for _ in range(encrypted_B.shape[1])] for _ in range(len(A))]
    for i in range(len(A)):
        for j in range(encrypted_B.shape[1]):
            for m in range(len(A[i])):
                res[i][j] += A[i][m] * encrypted_B[m][j]
    return np.array(res)


def encrypt_matmul_3(public_key: PaillierPublicKey, A, encrypted_B):
    if A.shape[0] != encrypted_B.shape[0]:
        print("A and encrypted_B shape are not consistent")
        print(A.shape)
        print(encrypted_B.shape)
        exit(1)
    res = []
    for i in range(len(A)):
        res.append(encrypt_matmul(public_key, A[i], encrypted_B[i]))
    return np.array(res)


def decrypt(private_key: PaillierPrivateKey, x):
    return private_key.decrypt(x)


def decrypt_scalar(private_key: PaillierPrivateKey, x):
    return private_key.decrypt(x)


def decrypt_array(private_key: PaillierPrivateKey, X):
    decrypt_x = []
    for i in range(X.shape[0]):
        elem = private_key.decrypt(X[i])
        decrypt_x.append(elem)
    return decrypt_x


def decrypt_matrix(private_key: PaillierPrivateKey, A):
    if len(A.shape) == 1:
        A = np.expand_dims(A, axis=0)

    decrypt_A = []
    for i in range(len(A)):
        row = []
        for j in range(len(A[i])):
            if len(A.shape) == 3:
                row.append([private_key.decrypt(A[i, j, k]) for k in range(len(A[i][j]))])
            else:
                row.append(private_key.decrypt(A[i, j]))

        decrypt_A.append(row)
    return np.array(decrypt_A, dtype=np.float64)

# def decrypt_matrix(private_key: PaillierPrivateKey, X):
#     decrypt_x = []
#     for i in range(X.shape[0]):
#         row = [private_key.decrypt(a) for a in X[i]]
#         decrypt_x.append(row)
#     return np.array(decrypt_x)


# def decrypt_matrixes(private_key: PaillierPrivateKey, X):
#     decrypt_xs = []
#     for x in X:
#         decrypt_x = []
#         if len(x.shape) > 1:
#             for i in range(x.shape[0]):
#                 row = [private_key.decrypt(a) for a in x[i]]
#                 decrypt_x.append(row)
#         else:
#             decrypt_x = [private_key.decrypt(a) for a in x]
#         # decrypt_x = np.array(decrypt_x)
#         decrypt_xs.append(decrypt_x)
#     return np.array(decrypt_xs)
