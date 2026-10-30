"""Real-ESRGAN x4 anime (RRDBNet, 6 blocks) inference in pure numpy, no PyTorch needed.

This made source/parrot_x4.png from source/parrot.jpg (188 x 425 -> 752 x 1700, about 40 s on
4 CPU cores). The weights are not in this repository; get RealESRGAN_x4plus_anime_6B.pth from
https://github.com/xinntao/Real-ESRGAN/releases/tag/v0.2.2.4 (BSD-3-Clause).

The .pth checkpoint is read with a restricted unpickler: only OrderedDict, the tensor rebuild
function and storage type names are resolved (to local stand-ins), so the file cannot run code.

usage: python3 -I tools/upscale_esrgan.py RealESRGAN_x4plus_anime_6B.pth source/parrot.jpg source/parrot_x4.png
"""
import collections
import pickle
import sys
import time
import zipfile

import numpy as np
from PIL import Image

DTYPES = {
    'FloatStorage': np.float32, 'HalfStorage': np.float16, 'DoubleStorage': np.float64,
    'LongStorage': np.int64, 'IntStorage': np.int32, 'ByteStorage': np.uint8,
}


class StorageType:
    def __init__(self, name):
        self.name = name


def rebuild_tensor_v2(storage, offset, size, stride, requires_grad=False, hooks=None, metadata=None):
    item = storage.itemsize
    view = np.lib.stride_tricks.as_strided(
        storage[offset:], shape=tuple(size), strides=tuple(s * item for s in stride))
    return np.array(view, dtype=np.float32)


class SafeUnpickler(pickle.Unpickler):
    def __init__(self, f, zf, prefix):
        super().__init__(f)
        self.zf = zf
        self.prefix = prefix

    def find_class(self, module, name):
        if module == 'collections' and name == 'OrderedDict':
            return collections.OrderedDict
        if module == 'torch._utils' and name == '_rebuild_tensor_v2':
            return rebuild_tensor_v2
        if module == 'torch' and name in DTYPES:
            return StorageType(name)
        raise pickle.UnpicklingError(f'blocked global {module}.{name}')

    def persistent_load(self, pid):
        typename, storage_type, key, _location, _numel = pid
        if typename != 'storage' or not isinstance(storage_type, StorageType):
            raise pickle.UnpicklingError(f'unexpected persistent id {pid!r}')
        data = self.zf.read(f'{self.prefix}/data/{key}')
        return np.frombuffer(data, dtype=DTYPES[storage_type.name])


def load_state(path):
    zf = zipfile.ZipFile(path)
    pkl = [n for n in zf.namelist() if n.endswith('data.pkl')][0]
    prefix = pkl[: -len('/data.pkl')]
    with zf.open(pkl) as f:
        obj = SafeUnpickler(f, zf, prefix).load()
    for key in ('params_ema', 'params'):
        if isinstance(obj, dict) and key in obj:
            return obj[key]
    return obj


def conv3x3(x, w, b, max_cols_bytes=400 << 20):
    """x (C, H, W) float32, w (O, C, 3, 3), b (O,) -> (O, H, W); im2col in row chunks."""
    c, h, wd = x.shape
    o = w.shape[0]
    w2 = w.reshape(o, c * 9)
    xp = np.pad(x, ((0, 0), (1, 1), (1, 1)))
    out = np.empty((o, h, wd), dtype=np.float32)
    rows = max(1, min(h, max_cols_bytes // (c * 9 * wd * 4)))
    for r0 in range(0, h, rows):
        r1 = min(h, r0 + rows)
        n = r1 - r0
        cols = np.empty((c, 9, n, wd), dtype=np.float32)
        for ky in range(3):
            for kx in range(3):
                cols[:, ky * 3 + kx] = xp[:, r0 + ky:r0 + ky + n, kx:kx + wd]
        res = w2 @ cols.reshape(c * 9, n * wd)
        res += b[:, None]
        out[:, r0:r1] = res.reshape(o, n, wd)
    return out


def lrelu(x):
    return np.where(x > 0, x, x * np.float32(0.2))


def rdb(x, p, pre):
    def cv(i, inp):
        return conv3x3(inp, p[f'{pre}.conv{i}.weight'], p[f'{pre}.conv{i}.bias'])
    x1 = lrelu(cv(1, x))
    x2 = lrelu(cv(2, np.concatenate((x, x1))))
    x3 = lrelu(cv(3, np.concatenate((x, x1, x2))))
    x4 = lrelu(cv(4, np.concatenate((x, x1, x2, x3))))
    x5 = cv(5, np.concatenate((x, x1, x2, x3, x4)))
    return x5 * np.float32(0.2) + x


def up2(x):
    return np.repeat(np.repeat(x, 2, axis=1), 2, axis=2)


def rrdbnet(x, p):
    nblocks = 1 + max(int(k.split('.')[1]) for k in p if k.startswith('body.'))
    feat = conv3x3(x, p['conv_first.weight'], p['conv_first.bias'])
    body = feat
    for i in range(nblocks):
        inp = body
        for j in (1, 2, 3):
            body = rdb(body, p, f'body.{i}.rdb{j}')
        body = body * np.float32(0.2) + inp
    feat = feat + conv3x3(body, p['conv_body.weight'], p['conv_body.bias'])
    feat = lrelu(conv3x3(up2(feat), p['conv_up1.weight'], p['conv_up1.bias']))
    feat = lrelu(conv3x3(up2(feat), p['conv_up2.weight'], p['conv_up2.bias']))
    feat = lrelu(conv3x3(feat, p['conv_hr.weight'], p['conv_hr.bias']))
    return conv3x3(feat, p['conv_last.weight'], p['conv_last.bias'])


def main(weights, src, dst):
    t0 = time.time()
    p = load_state(weights)
    img = np.asarray(Image.open(src).convert('RGB'), dtype=np.float32) / 255.0
    x = np.ascontiguousarray(img.transpose(2, 0, 1))
    y = rrdbnet(x, p)
    y = np.clip(y.transpose(1, 2, 0), 0, 1)
    Image.fromarray((y * 255.0 + 0.5).astype(np.uint8)).save(dst)
    print(f'{src} {img.shape[1]}x{img.shape[0]} -> {dst} {y.shape[1]}x{y.shape[0]} in {time.time() - t0:.1f}s')


if __name__ == '__main__':
    main(*sys.argv[1:4])
