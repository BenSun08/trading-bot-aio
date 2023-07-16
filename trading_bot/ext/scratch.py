import numpy as np

# a = np.array(np.arange(1,12)).reshape(1,-1)
# print(a.shape)
# state, next_state = a[:,:-1], a[:,1:]
# print(state)
# print(next_state)


# wd = 11
# a = np.array(np.arange(1,50)).reshape(1,-1)
# if a.shape[-1] % wd !=0:
#     arr = a.squeeze()
#     pad = wd - a.shape[-1] % wd
#     print(pad)
#     a = np.pad(arr, (0, pad), 'edge')
#     a.reshape(1,-1)
# splt = np.array_split(a, a.shape[-1]//wd, axis=(len(a.shape)-1))
# splt = np.array(splt)
# print(splt)
# print(splt[0])
# sig = np.var(splt,axis=1)
# print(sig)
# print()
# sort_idx = np.argsort(sig)
# print(splt[sort_idx])
# print(splt[sort_idx[::2]])


def downsample(data, wd, sample_rate=0.3):
    wd = 11
    # a = np.array(np.arange(1,50)).reshape(1,-1)
    print(data.shape)
    if data.shape[-1] % wd !=0:
        arr = data.squeeze()
        pad = wd - data.shape[-1] % wd
        data = np.pad(arr, (0, pad), 'edge')
        data.reshape(1,-1)
    splt = np.array_split(data, data.shape[-1]//wd, axis=(len(data.shape)-1))
    splt = np.array(splt)

    # calculate variance and index after sort
    sig = np.var(splt,axis=1)
    print(splt.shape, sig.shape)
    sort_idx = np.argsort(sig)


    # down-sample for 1 / sample_rate
    return splt[sort_idx[::int(sample_rate*10)]]

a = np.array(np.arange(1,95)).reshape(1,-1)
results = downsample(a, 10, 0.3)
print(results)
# b = a[1][1]
# print(id(b))
# c = a[1,1]
# print(id(c))