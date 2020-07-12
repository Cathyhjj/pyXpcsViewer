import h5py
import os
import numpy as np
from multiprocessing import Pool
import time

hdf_dict = {
    'Iq': '/exchange/partition-mean-total',
    'Iqp': '/exchange/partition-mean-partial',
    'ql_sta': '/xpcs/sqlist',
    'ql_dyn': '/xpcs/dqlist',
    't0': '/measurement/instrument/detector/exposure_period',
    'tau': '/exchange/tau',
    'g2': '/exchange/norm-0-g2',
    'g2_err': '/exchange/norm-0-stderr',
    'Int_2D': '/exchange/pixelSum',
    'Int_t': '/exchange/frameSum',
    'ccd_x0': '/measurement/instrument/acquisition/beam_center_x',
    'ccd_y0': '/measurement/instrument/acquisition/beam_center_y',
    'det_dist': '/measurement/instrument/detector/distance',
    'pix_dim': '/measurement/instrument/detector/x_pixel_size',
    'X_energy': '/measurement/instrument/source_begin/energy',
    'xdim': '/measurement/instrument/detector/x_dimension',
    'ydim': '/measurement/instrument/detector/y_dimension'
}

avg_hdf_dict = {
    'Iq': '/Iq_ave',
    'g2': '/g2_ave',
    'g2_nb': '/g2_ave_nb',
    'g2_err': '/g2_ave_err',
    'fn_count': '/fn_count',
    't_el': '/t_el',
    'ql_sta': '/ql_sta',
    'ql_dyn': '/ql_dyn',
    'Int_2D': '/Int_2D_ave',
}


def read_file(fields, fn, prefix='./data'):
    res = []
    with h5py.File(os.path.join(prefix, fn), 'r') as HDF_Result:
        for field in fields:
            if field == 't_el':
                val1 = np.squeeze(HDF_Result.get(hdf_dict['t0']))
                val2 = np.squeeze(HDF_Result.get(hdf_dict['tau']))
                val = val1 * val2
            else:
                if field in hdf_dict.keys():
                    link = hdf_dict[field]
                    if link in HDF_Result.keys():
                        val = np.squeeze(HDF_Result.get(link))
                    else:
                        link = avg_hdf_dict[field]
                        val = np.squeeze(HDF_Result.get(link))
            res.append(val)
    return res


def read_file_wrap(args):
    return read_file(*args)

def read_multiple_files(fields, fn_list, prefix='./data', p_size=4):
    arg_list = []
    for fn in fn_list:
        arg_list.append((fields, fn, prefix))
    with Pool(p_size) as p:
        res = p.map(read_file_wrap, arg_list)
    return res


if __name__ == '__main__':
    fn_list = [
        'N077_D100_att02_0001_0001-100000.hdf',
        'N077_D100_att02_0002_0001-100000.hdf',
        'N077_D100_att02_0003_0001-100000.hdf',
        'N077_D100_att02_0004_0001-100000.hdf',
        'N077_D100_att02_0005_0001-100000.hdf',
        'N077_D100_att02_0006_0001-100000.hdf',
        'N077_D100_att02_0007_0001-100000.hdf',
        'N077_D100_att02_0008_0001-100000.hdf',
        'N077_D100_att02_0009_0001-100000.hdf'] * 50
    fields = ['Iq', 'ql_dyn', 'Int_2D']

    s1 = time.perf_counter()
    x = read_multiple_files(fields, fn_list)
    s2 = time.perf_counter()
    print(s2 - s1)

    s1 = time.perf_counter()
    for i in fn_list:
        read_file(fields, i)
    s2 = time.perf_counter()
    print(s2 - s1)