import numpy as np
import matplotlib.pyplot as plt
from matplotlib.patches import Circle


def correct_diagonal_c2(c2):
    size = c2.shape[0]
    side_band = c2[(np.arange(size - 1), np.arange(1, size))]
    diag_val = np.zeros(size)
    diag_val[:-1] += side_band
    diag_val[1:] += side_band
    norm = np.ones(size)
    norm[1:-1] = 2
    c2_copy = np.copy(c2)
    c2_copy[np.diag_indices(c2.shape[0])] = diag_val / norm
    return c2_copy


def get_twotime_qindex(meta, ix, iy, hdl):
    shape = meta['twotime_dqmap'].shape
    if len(hdl.axes[0].patches) >= 2:
        hdl.axes[0].patches.pop(0)
    if len(hdl.axes[1].patches) >= 2:
        hdl.axes[1].patches.pop(0)

    h = np.argmin(np.abs(np.arange(shape[1]) - ix))
    v = np.argmin(np.abs(np.arange(shape[0]) - iy))

    meta['twotime_pos'] = (v, h)
    plot_id = meta['twotime_dqmap'][v, h]

    color = np.random.rand(3, )
    mark0 = Circle((ix, iy), radius=5, edgecolor='white', facecolor=color)
    hdl.axes[0].add_patch(mark0)
    if meta['twotime_text'] is None:
        text_a = hdl.axes[0].text(ix, iy, 'A')
        text_b = hdl.axes[0].text(ix, iy, 'A')
        meta['twotime_text'] = [text_a, text_b]
    else:
        text_b = meta['twotime_text'][1]
        pos = text_b.get_position()
        text_a = meta['twotime_text'][0]
        text_a.set_position(pos)

        text_b.set_position((ix, iy))
        text_b.set_text('B')

    mark1 = Circle((ix, iy), radius=5, edgecolor='white', facecolor=color)
    hdl.axes[1].add_patch(mark1)
    hdl.draw()

    return plot_id


def plot_twotime_map(xfile,
                     hdl,
                     meta=None,
                     group='xpcs',
                     saxs_cmap='jet',
                     qmap_cmap='hot',
                     scale='log',
                     auto_crop=True,
                     auto_rotate=True):

    # if xfile.full_path == meta['twotime_fname'] and \
    #         group == meta['twotime_group']:
    #     return

    dqmap, saxs, rpath, idlist = xfile.get_twotime_maps(group)
    time_scale = xfile.get_time_scale(group)

    meta['twotime_key'] = rpath
    meta['twotime_group'] = group
    meta['twotime_scale'] = time_scale
    meta['twotime_idlist'] = idlist

    if auto_crop:
        idx = np.nonzero(dqmap >= 1)
        sl_v = slice(np.min(idx[0]), np.max(idx[0]))
        sl_h = slice(np.min(idx[1]), np.max(idx[1]))
        dqmap = dqmap[sl_v, sl_h]
        saxs = saxs[sl_v, sl_h]

    if auto_rotate:
        if dqmap.shape[0] > dqmap.shape[1]:
            dqmap = np.swapaxes(dqmap, 0, 1)
            saxs = np.swapaxes(saxs, 0, 1)

    # emphasize the beamstop region which has qindex = 0;
    qindex_max = np.max(dqmap)
    dqmap[dqmap == 0] = qindex_max + 1

    meta['twotime_dqmap'] = dqmap
    meta['twotime_fname'] = xfile.full_path
    meta['twotime_saxs'] = saxs
    meta['twotime_ready'] = True

    if scale == 'log':
        min_val = np.min(saxs[saxs > 0])
        saxs[saxs <= 0] = min_val
        saxs = np.log10(saxs).astype(np.float32)

    hdl.clear()
    ax = hdl.subplots(1, 3, sharex=True, sharey=True)
    im0 = ax[0].imshow(saxs, cmap=plt.get_cmap(saxs_cmap))
    im1 = ax[1].imshow(dqmap, cmap=plt.get_cmap(qmap_cmap))
    im2 = ax[2].imshow(np.zeros_like(dqmap), vmin=0, vmax=2)

    ax[0].set_title('SAXS-2D')
    ax[1].set_title('dqmap')
    ax[2].set_title('selection')
    plt.colorbar(im0, ax=ax[0])
    plt.colorbar(im1, ax=ax[1])
    plt.colorbar(im2, ax=ax[2])
    hdl.draw()


def update_twotime_map(meta, hdl):
    dqmap = meta['twotime_dqmap']

    selection = np.zeros_like(dqmap, dtype=np.uint8)
    for n, x in enumerate(meta['twotime_plot_list']):
        if x > 0:
            selection += (dqmap == x).astype(np.uint8) * (n + 1)
    hdl.axes[2].imshow(selection, vmin=0, vmax=2)
    hdl.draw()


def plot_twotime(xfile, hdl, hdl_map, meta, plot_index=1, cmap='jet', 
                vmin=None, vmax=None, show_box=False, correct_diag=False):

    if xfile.type != 'Twotime':
        return None

    if plot_index not in meta['twotime_idlist']:
        msg = 'plot_index is not found.'
        return msg

    # check if a twotime selected point is already there;
    if 'twotime_pos' not in meta or meta['twotime_dqmap'][
            meta['twotime_pos']] != plot_index:
        v, h = np.where(meta['twotime_dqmap'] == plot_index)
        ret = (np.mean(v), np.mean(h))
    else:
        ret = None

    if 'twotime_plot_list' not in meta:
        meta['twotime_plot_list'] = [-1, -1] 
        meta['twotime_ims'] = []
    
    if plot_index != meta['twotime_plot_list'][-1]:
        meta['twotime_plot_list'].append(plot_index)
        c2 = xfile.get_twotime_c2(plot_index=plot_index,
                                  twotime_key=meta['twotime_key'])
        meta['twotime_ims'].append(np.copy(c2))
        if len(meta['twotime_plot_list']) > 2:
            meta['twotime_plot_list'].pop(0)
        if len(meta['twotime_ims']) > 2:
            meta['twotime_ims'].pop(0)

    plot_list = meta['twotime_plot_list']

    t = meta['twotime_scale'] * np.arange(len(meta['twotime_ims'][-1]))
    t_min = np.min(t)
    t_max = np.max(t)

    num_c2 = len(meta['twotime_ims'])
    # num_c2 = 1 -> 2 column;
    # num_c2 = 2 -> 3 column;

    hdl.clear()
    ax = hdl.subplots(1, num_c2 + 1)

    title = ['A: %d' % plot_list[0], 'B: %d' % plot_list[1]]

    for n in range(num_c2):
        c2 = meta['twotime_ims'][n]
        if correct_diag:
            c2 = correct_diagonal_c2(meta['twotime_ims'][n])

        im = ax[n].imshow(c2,
                          interpolation='none',
                          origin='lower',
                          extent=([t_min, t_max, t_min, t_max]),
                          cmap=plt.get_cmap(cmap),
                          vmin=vmin,
                          vmax=vmax)
        plt.colorbar(im, ax=ax[n])
        ax[n].set_ylabel('t1 (s)')
        ax[n].set_xlabel('t2 (s)')
        ax[n].set_title(title[n])

    # the first element in the list seems to deviate from the rest a lot
    g2f = xfile.g2_full[:, plot_index - 1][1:]
    g2p = xfile.g2_partials[:, :, plot_index - 1].T
    g2p = g2p[:, 1:]

    t = meta['twotime_scale'] * np.arange(g2f.size)
    ax[-1].plot(t, g2f, lw=3, color='blue', alpha=0.5, label='full')

    delta_t = (t_max - t_min) / (g2p.shape[0])
    for n in range(g2p.shape[0]):
        t = meta['twotime_scale'] * np.arange(g2p[n].size)
        ax[-1].plot(t, g2p[n], label=f'{n}', alpha=0.5)

        if show_box:
            xy = (delta_t * n, delta_t * n)
            rect = plt.Rectangle(xy, delta_t, delta_t, 
                             facecolor='none', edgecolor='k', alpha=0.5)
            ax[-2].add_patch(rect)
            ax[-2].text(*xy, f'{n}')

    ax[-1].set_xscale('log')
    ax[-1].set_ylabel('g2')
    ax[-1].set_xlabel('t (s)')
    ax[-1].set_title('Full/Partial g2')
    ax[-1].legend()
    hdl.fig.tight_layout()

    hdl.draw()

    update_twotime_map(meta, hdl_map)
    return ret
