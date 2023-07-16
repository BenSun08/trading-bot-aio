import os
import math
import logging

import numpy as np


def sigmoid(x):
    """Performs sigmoid operation
    """
    try:
        if x < 0:
            return 1 - 1 / (1 + math.exp(x))
        return 1 / (1 + math.exp(-x))
    except Exception as err:
        print("Error in sigmoid: " + err)



def downsample(data, wd, sample_rate=0.3):
    wd += 1
    data = np.array(data).reshape(1,-1)
    if data.shape[-1] % wd !=0:
        arr = data.squeeze()
        pad = wd - data.shape[-1] % wd
        data = np.pad(arr, (0, pad), 'edge')
        data.reshape(1,-1)
    splt = np.array_split(data, data.shape[-1]//wd, axis=(len(data.shape)-1))
    splt = np.array(splt).squeeze()
    # print("splt", splt.shape)

    # calculate variance and index after sort
    sig = np.var(splt,axis=1) 
    sort_idx = np.argsort(sig)


    # down-sample for 1 / sample_rate
    return splt[sort_idx[::int(1/sample_rate)]]


def get_state_train(data, t, n_days, sample_rate):
    """Returns an n-day state representation ending at time t
    """
    # d = t - n_days + 1
    # block = data[d: t + 1] if d >= 0 else -d * [data[0]] + data[0: t + 1]  # pad with t0
    # res = []
    # for i in range(n_days - 1):
    #     res.append(sigmoid(block[i + 1] - block[i]))
    # return np.array([res])
    
    # Modified:
    # Each data segments is in length of (window + 1)
    # In training process, each data seg can be separated into [:wind] and [1:wind+1]
    # print(np.array(data).shape)
    results = downsample(data, n_days, sample_rate).squeeze()
    final_res = []
    # print(results.shape)
    for arr in results:
        arr = arr.squeeze()
        res = []
        for i in range(len(arr)-1):
            res.append(sigmoid(arr[i + 1] - arr[i]))
        final_res.append(np.array([res]))
    return np.array([final_res]).squeeze()
        

def get_state(data, t, n_days):
    """Returns an n-day state representation ending at time t
    """
    d = t - n_days + 1
    block = data[d: t + 1] if d >= 0 else -d * [data[0]] + data[0: t + 1]  # pad with t0
    res = []
    for i in range(n_days - 1):
        res.append(sigmoid(block[i + 1] - block[i]))
    return np.array([res])
    
    # Modified:
    # Each data segments is in length of (window + 1)
    # In training process, each data seg can be separated into [:wind] and [1:wind+1]
    # print(np.array(data).shape)
