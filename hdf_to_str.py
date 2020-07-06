import h5py
import numpy as np
from scipy.stats import describe
import os
np.set_printoptions(precision=3, suppress=True)


def describe_numpy(arr):
    repr = str(arr.shape) + ', ' + str(arr.dtype) + ':'
    if arr.size > 1:
        res = describe(arr.ravel())
        repr += 'minmax=%s, mean=%s' % (np.round(res.minmax, 2),
                                        np.round(res.mean, 2))
    else:
        repr += 'val = %s' % str(arr[0])
    return repr


def read_h5py(hdl, path, level, guide_str0):
    if path not in hdl:
        return
    result = []

    guide_mid = guide_str0 + '├──'
    guide_lst = guide_str0 + '└──'
    guide_nxt_mid = guide_str0 + '│  '
    guide_nxt_lst = guide_str0 + '   '

    if isinstance(hdl[path], h5py._hl.dataset.Dataset):

        if hdl[path].shape == ():
            return [guide_lst + 'empty']
        info = describe_numpy(np.array(hdl[path]))
        result.append(guide_lst + info)
        return result

    for n, key in enumerate(hdl[path].keys()):
        if n == len(hdl[path].keys()) - 1:
            guide = guide_lst
            guide_nxt = guide_nxt_lst
        else:
            guide = guide_mid
            guide_nxt = guide_nxt_mid

        new_path = os.path.join(path, key)
        # print(new_path)
        if isinstance(key, str):
            result.append(guide + key)
            info = read_h5py(hdl, new_path, level + 1, guide_nxt)
            result = result + info
        elif isinstance(key, np.ndarray):
            info = describe_numpy(hdl[new_path])
            result.append(guide + info)
        else:
            return
    return result


def get_hdf_info(path, fname):
    hdl = h5py.File(os.path.join(path, fname), 'r')
    res = read_h5py(hdl, '.', 0, '')
    return res


if __name__ == '__main__':
    pass

