# -*- coding: utf-8 -*-
"""
审哥看图王 —— 免费、开源、无广告的 Windows 本地看图工具
项目地址：https://github.com/liangzaimo/ShenGeKanTu
许可证：AGPL-3.0
运行：pythonw kantu.py [图片路径]；打包：双击 build.bat
"""
import io
import math
import os
import sys
import re
import json
import time
import random
import shutil
import ctypes
import tempfile
import subprocess
from collections import OrderedDict
from datetime import datetime

from PySide6.QtCore import (Qt, QObject, Signal, QRunnable, QThreadPool, QTimer, QPointF, QPoint,
                            QRect, QRectF, QSize, QSizeF, QVariantAnimation, QMimeData, QUrl,
                            QByteArray, QThread, QMarginsF, QBuffer, QIODevice)
from PySide6.QtGui import (QImage, QPixmap, QPainter, QColor, QPen, QBrush, QTransform, QImageReader,
                           QMovie, QIcon, QCursor, QPainterPath, QFont, QGuiApplication, QKeySequence,
                           QPageSize, QPageLayout, QPolygonF, QAction, QFontMetrics, QPainterPathStroker)
from PySide6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QGridLayout,
                               QToolButton, QListWidget, QListWidgetItem, QLabel, QMenu, QDialog,
                               QPushButton, QCheckBox, QRadioButton, QButtonGroup, QSpinBox, QComboBox,
                               QStackedWidget, QFrame, QFileDialog, QMessageBox, QInputDialog,
                               QTableWidget, QTableWidgetItem, QHeaderView, QAbstractItemView,
                               QLineEdit, QProgressDialog, QFormLayout, QSizePolicy, QScrollArea,
                               QSlider, QTextBrowser, QPlainTextEdit, QColorDialog)
from PySide6.QtPrintSupport import QPrinter, QPrintDialog, QPrintPreviewDialog, QPrinterInfo
from PySide6.QtNetwork import QLocalServer, QLocalSocket

try:
    from PIL import Image, ImageOps
    Image.MAX_IMAGE_PIXELS = None
except Exception:  # pragma: no cover
    Image = None
    ImageOps = None

try:
    import pillow_heif
    pillow_heif.register_heif_opener()
    try:
        pillow_heif.register_avif_opener()
    except Exception:
        pass
except Exception:
    pillow_heif = None

IS_WIN = sys.platform == "win32"
if IS_WIN:
    import ctypes.wintypes

APP_NAME = "审哥看图王"
APP_ID = "KanTu"
PROGID = "KanTu.Image"
HOTKEY_ID = 0x4B54
PREV_KEYS = (Qt.Key_A, Qt.Key_W, Qt.Key_Up, Qt.Key_Left, Qt.Key_PageUp, Qt.Key_Backspace)
NEXT_KEYS = (Qt.Key_D, Qt.Key_S, Qt.Key_Down, Qt.Key_Right, Qt.Key_Space, Qt.Key_PageDown)

# ---------------------------------------------------------------- 格式
QT_EXTS = {"jpg", "jpeg", "jpe", "jfif", "png", "apng", "bmp", "dib", "gif", "webp", "ico", "cur",
           "tif", "tiff", "tga", "svg", "svgz", "wbmp", "pbm", "pgm", "ppm", "xbm", "xpm", "icns", "jp2"}
PIL_EXTS = {"heic", "heif", "avif", "pcx", "psd", "dds", "sgi", "rgb", "bw", "msp", "pcd", "ras", "sun", "pfm",
            "pnm", "j2k", "j2c", "jpc", "jpf", "jpx", "wmf", "emf"}
# FreeImage 能读的格式（2345看图王用的也是 FreeImage）
FI_EXTS = {"jng", "koa", "iff", "lbm", "mng", "pcd", "pcx", "ras", "wap", "wbmp", "wbm", "cut", "dds", "ddx",
           "hdr", "g3", "sgi", "exr", "j2k", "j2c", "jp2", "jpc", "pfm", "pct", "pict", "pic", "wdp", "jxr", "hdp",
           "pgx", "ska", "tbi", "psd", "tga", "targa", "xbm", "xpm", "pbm", "pgm", "ppm", "pnm", "tif", "tiff",
           "gif", "bmp", "ico", "png", "jpg", "jpeg", "webp"}
DOC_EXTS = {"ai", "ofd"}
RAW_EXTS = {"cr2", "cr3", "crw", "nef", "nrw", "arw", "srf", "sr2", "dng", "orf", "rw2", "raf", "srw",
            "pef", "raw", "rwl", "3fr", "erf", "kdc", "mrw", "x3f", "iiq", "mos"}
IMAGE_EXTS = QT_EXTS | PIL_EXTS | FI_EXTS | DOC_EXTS | RAW_EXTS
ANIM_EXTS = {"gif", "webp", "png", "apng"}
# 按 2345看图王的关联列表（去掉 PDF），再补上常见别名
ASSOC_ALL = ["bmp", "ico", "jpg", "jpeg", "jpe", "jfif", "jng", "koa", "iff", "mng", "pcd", "pcx", "png", "ras",
             "tga", "tif", "tiff", "wap", "wbmp", "psd", "cut", "xbm", "xpm", "dds", "ddx", "gif", "hdr", "g3", "sgi",
             "exr", "j2k", "jp2", "pfm", "pct", "pict", "raw", "wmf", "jpc", "pgx", "pnm", "ska", "webp", "wdp",
             "jxr", "tbi", "heic", "heif", "ai", "ofd", "avif", "svg", "cr2", "nef", "arw", "dng"]
ASSOC_DEFAULT = list(ASSOC_ALL)

SAVE_FMT = {"jpg": "JPEG", "jpeg": "JPEG", "jpe": "JPEG", "jfif": "JPEG", "png": "PNG", "webp": "WEBP",
            "bmp": "BMP", "gif": "GIF", "tif": "TIFF", "tiff": "TIFF", "ico": "ICO", "tga": "TGA",
            "heic": "HEIF", "heif": "HEIF", "avif": "AVIF"}

DEFAULTS = {
    # 常规
    "thumbs": False, "multiframe": True, "pointer_flip": False, "raw_full": False,
    "auto_orient": True, "fs_transparent": False, "edit_downscale": True,
    "folder_end_remember": False, "folder_end_action": "loop",
    # 习惯
    "on_top": False, "multi_window": True, "rotate_original": True, "loading_tip": True,
    "saveas_autorename": True, "wheel_enabled": True, "wheel_action": "zoom",
    "shot_hotkey_enabled": False, "shot_key": "A", "delete_confirm": True,
    # 文件关联
    "assoc_exts": ASSOC_DEFAULT,
    # 幻灯片
    "ss_order": "seq", "ss_loop": True, "ss_reverse": False, "ss_interval": 3,
    "ss_effect": "random", "ss_bg": "none",
    # 面板开关
    "lock_zoom": False, "navigator": False, "wheel_mode_tip": True,
    "geom": "", "conv_dir": "",
    "shot_color": "#ff3b30", "shot_size": 1,
    "tr_sl": "auto", "tr_tl": "zh-CN", "proxy": "",
    "wm_text": "仅供××使用", "wm_color": "#ff3b30", "wm_opacity": 35, "wm_size": 28, "wm_angle": 45,
}

CFG_DIR = os.path.join(os.environ.get("APPDATA") or os.path.expanduser("~"), APP_ID)
CFG_PATH = os.path.join(CFG_DIR, "settings.json")


def load_cfg():
    d = dict(DEFAULTS)
    try:
        with open(CFG_PATH, "r", encoding="utf-8") as f:
            d.update(json.load(f))
    except Exception:
        pass
    if d.get("assoc_ver", 0) < 2:
        d["assoc_exts"] = list(ASSOC_DEFAULT)
        d["assoc_ver"] = 2
    return d


def save_cfg(cfg):
    try:
        os.makedirs(CFG_DIR, exist_ok=True)
        tmp = CFG_PATH + ".tmp"
        with open(tmp, "w", encoding="utf-8") as f:
            json.dump(cfg, f, ensure_ascii=False, indent=1)
        os.replace(tmp, CFG_PATH)
    except Exception:
        pass


# ---------------------------------------------------------------- 工具函数
def ext_of(p):
    return os.path.splitext(p)[1][1:].lower()


def natkey(s):
    return [int(t) if t.isdigit() else t.lower() for t in re.split(r"(\d+)", s)]


def list_images(folder):
    try:
        names = [e.name for e in os.scandir(folder) if e.is_file() and ext_of(e.name) in IMAGE_EXTS]
    except Exception:
        return []
    names.sort(key=natkey)
    return [os.path.join(folder, n) for n in names]


def same_path(a, b):
    return os.path.normcase(os.path.abspath(a)) == os.path.normcase(os.path.abspath(b))


def unique_path(p):
    if not os.path.exists(p):
        return p
    base, ext = os.path.splitext(p)
    i = 1
    while os.path.exists(f"{base}({i}){ext}"):
        i += 1
    return f"{base}({i}){ext}"


def human_size(n):
    for u in ("B", "KB", "MB", "GB"):
        if n < 1024 or u == "GB":
            return f"{n:.0f} {u}" if u == "B" else f"{n:.2f} {u}"
        n /= 1024.0


def neighbor_folder(cur_dir, direction):
    parent = os.path.dirname(cur_dir.rstrip("\\/"))
    if not parent or same_path(parent, cur_dir):
        return None
    try:
        sibs = sorted([e.path for e in os.scandir(parent) if e.is_dir()], key=lambda p: natkey(os.path.basename(p)))
    except Exception:
        return None
    idx = next((i for i, p in enumerate(sibs) if same_path(p, cur_dir)), None)
    if idx is None:
        return None
    rng = range(idx + 1, len(sibs)) if direction > 0 else range(idx - 1, -1, -1)
    for i in rng:
        if list_images(sibs[i]):
            return sibs[i]
    return None


def np_to_qimage(arr):
    import numpy as np
    arr = np.ascontiguousarray(arr)
    h, w = arr.shape[:2]
    if arr.ndim == 2:
        return QImage(arr.tobytes(), w, h, w, QImage.Format_Grayscale8).copy()
    return QImage(arr.tobytes(), w, h, 3 * w, QImage.Format_RGB888).copy()


def pil_to_qimage(im):
    if im.mode not in ("RGB", "RGBA"):
        has_alpha = "A" in im.getbands() or (im.mode == "P" and "transparency" in im.info)
        im = im.convert("RGBA" if has_alpha else "RGB")
    w, h = im.size
    if im.mode == "RGB":
        return QImage(im.tobytes("raw", "RGB"), w, h, 3 * w, QImage.Format_RGB888).copy()
    return QImage(im.tobytes("raw", "RGBA"), w, h, 4 * w, QImage.Format_RGBA8888).copy()


def load_raw_qimage(path, full):
    import rawpy
    with rawpy.imread(path) as r:
        if not full:
            try:
                th = r.extract_thumb()
                if th.format == rawpy.ThumbFormat.JPEG:
                    img = QImage.fromData(QByteArray(th.data))
                    if not img.isNull():
                        return img
                elif th.format == rawpy.ThumbFormat.BITMAP:
                    return np_to_qimage(th.data)
            except Exception:
                pass
        rgb = r.postprocess(use_camera_wb=True, half_size=not full)
        return np_to_qimage(rgb)


_FI = None


def app_dir():
    if getattr(sys, "frozen", False):
        return os.path.dirname(sys.executable)
    return os.path.dirname(os.path.abspath(__file__))


def freeimage():
    """按需加载 FreeImage.dll（放在程序目录）"""
    global _FI
    if _FI is not None:
        return _FI or None
    lib = None
    cands = [os.path.join(app_dir(), "FreeImage.dll"), os.path.join(app_dir(), "_internal", "FreeImage.dll")] \
        if IS_WIN else ["libfreeimage.so.3", "libfreeimage.so"]
    for c in cands:
        try:
            lib = ctypes.WinDLL(c) if IS_WIN else ctypes.CDLL(c)
            break
        except OSError:
            continue
    if lib is None:
        _FI = False
        return None
    vp, c_int, c_uint = ctypes.c_void_p, ctypes.c_int, ctypes.c_uint
    spec = {"FreeImage_GetWidth": (c_uint, [vp]), "FreeImage_GetHeight": (c_uint, [vp]),
            "FreeImage_GetPitch": (c_uint, [vp]), "FreeImage_GetBits": (vp, [vp]),
            "FreeImage_GetImageType": (c_int, [vp]), "FreeImage_ConvertTo32Bits": (vp, [vp]),
            "FreeImage_ToneMapping": (vp, [vp, c_int, ctypes.c_double, ctypes.c_double]),
            "FreeImage_ConvertToStandardType": (vp, [vp, c_int]), "FreeImage_Unload": (None, [vp])}
    if IS_WIN:
        spec.update({"FreeImage_GetFileTypeU": (c_int, [ctypes.c_wchar_p, c_int]),
                     "FreeImage_GetFIFFromFilenameU": (c_int, [ctypes.c_wchar_p]),
                     "FreeImage_LoadU": (vp, [c_int, ctypes.c_wchar_p, c_int])})
    else:
        spec.update({"FreeImage_GetFileType": (c_int, [ctypes.c_char_p, c_int]),
                     "FreeImage_GetFIFFromFilename": (c_int, [ctypes.c_char_p]),
                     "FreeImage_Load": (vp, [c_int, ctypes.c_char_p, c_int])})
    for name, (res, args) in spec.items():
        fn = getattr(lib, name)
        fn.restype = res
        fn.argtypes = args
    _FI = lib
    return lib


def load_freeimage(path):
    fi = freeimage()
    if fi is None:
        raise RuntimeError("缺少 FreeImage.dll，打不开这个格式")
    if IS_WIN:
        fif = fi.FreeImage_GetFileTypeU(path, 0)
        if fif < 0:
            fif = fi.FreeImage_GetFIFFromFilenameU(path)
        load = lambda f: fi.FreeImage_LoadU(f, path, 0)
    else:
        bp = os.fsencode(path)
        fif = fi.FreeImage_GetFileType(bp, 0)
        if fif < 0:
            fif = fi.FreeImage_GetFIFFromFilename(bp)
        load = lambda f: fi.FreeImage_Load(f, bp, 0)
    if fif < 0:
        raise RuntimeError("无法识别的图片格式")
    dib = load(fif)
    if not dib:
        raise RuntimeError("FreeImage 读取失败")
    tmps = [dib]
    try:
        t = fi.FreeImage_GetImageType(dib)
        if t != 1:  # 非普通位图：HDR/EXR/16 位等
            conv = fi.FreeImage_ToneMapping(dib, 0, 0.0, 0.0) if t in (6, 11, 12) else None
            if not conv:
                conv = fi.FreeImage_ConvertToStandardType(dib, 1)
            if not conv:
                raise RuntimeError("无法转换这个图片")
            tmps.append(conv)
            dib = conv
        d32 = fi.FreeImage_ConvertTo32Bits(dib)
        if not d32:
            raise RuntimeError("无法转换这个图片")
        tmps.append(d32)
        w, h, pitch = fi.FreeImage_GetWidth(d32), fi.FreeImage_GetHeight(d32), fi.FreeImage_GetPitch(d32)
        buf = ctypes.string_at(fi.FreeImage_GetBits(d32), pitch * h)
        img = QImage(buf, w, h, pitch, QImage.Format_ARGB32).copy()
        return img.mirrored(False, True)
    finally:
        for d in tmps:
            fi.FreeImage_Unload(d)


def load_ai(path):
    try:
        import pymupdf as fitz
    except ImportError:
        import fitz
    doc = fitz.open(path, filetype="pdf")
    try:
        page = doc[0]
        zoom = min(4.0, max(1.0, 2400 / max(page.rect.width, page.rect.height, 1)))
        pix = page.get_pixmap(matrix=fitz.Matrix(zoom, zoom), alpha=False)
        return QImage(pix.samples, pix.width, pix.height, pix.stride, QImage.Format_RGB888).copy()
    finally:
        doc.close()


def load_ofd(path):
    import logging
    try:
        from loguru import logger
        logger.remove()
    except Exception:
        pass
    from easyofd import OFD
    o = OFD()
    o.read(path, fmt="path")
    pages = o.to_jpg()
    if not pages:
        raise RuntimeError("OFD 没有页面")
    return pil_to_qimage(pages[0])


def load_cv2(path):
    os.environ.setdefault("OPENCV_IO_ENABLE_OPENEXR", "1")
    import cv2
    import numpy as np
    data = np.fromfile(path, dtype=np.uint8)
    arr = cv2.imdecode(data, cv2.IMREAD_UNCHANGED | cv2.IMREAD_ANYDEPTH | cv2.IMREAD_ANYCOLOR)
    if arr is None:
        raise RuntimeError("OpenCV 读取失败")
    if arr.dtype != np.uint8:
        f = arr.astype(np.float32)
        if arr.dtype in (np.float32, np.float64):
            f = f / (1.0 + f)  # 简单色调映射
            f = np.clip(f ** (1 / 2.2), 0, 1) * 255
        else:
            f = f / max(1.0, float(f.max())) * 255
        arr = f.astype(np.uint8)
    if arr.ndim == 2:
        arr = cv2.cvtColor(arr, cv2.COLOR_GRAY2RGB)
    elif arr.shape[2] == 4:
        arr = cv2.cvtColor(arr, cv2.COLOR_BGRA2RGB)
    else:
        arr = cv2.cvtColor(arr, cv2.COLOR_BGR2RGB)
    return np_to_qimage(arr)


def _load_qt(path, cfg):
    r = QImageReader(path)
    r.setAutoTransform(cfg.get("auto_orient", True))
    img = r.read()
    if img.isNull():
        raise RuntimeError(r.errorString())
    return img


def _load_pil(path, cfg):
    if Image is None:
        raise RuntimeError("缺少 Pillow")
    with Image.open(path) as im:
        if ext_of(path) in ("wmf", "emf"):
            im.load(dpi=144)
        if cfg.get("auto_orient", True):
            im = ImageOps.exif_transpose(im)
        return pil_to_qimage(im)


def load_image(path, cfg):
    """返回 QImage（已按设置处理拍摄方向），依次尝试多个解码器，失败抛异常"""
    ext = ext_of(path)
    if ext == "ai":
        chain = [load_ai]
    elif ext == "ofd":
        chain = [load_ofd]
    elif ext in RAW_EXTS:
        def raw(p, c=cfg):
            try:
                return load_raw_qimage(p, c.get("raw_full", False))
            except ImportError:
                raise RuntimeError("打开 RAW 需要 rawpy")
        chain = [raw, lambda p: load_freeimage(p)]
    elif ext in ("exr", "hdr"):
        chain = [lambda p: load_freeimage(p), load_cv2]
    else:
        chain = []
        if ext in QT_EXTS:
            chain.append(lambda p: _load_qt(p, cfg))
        chain.append(lambda p: _load_pil(p, cfg))
        chain.append(lambda p: load_freeimage(p))
        if ext not in QT_EXTS:
            chain.append(lambda p: _load_qt(p, cfg))
        chain.append(load_cv2)
    errors = []
    for fn in chain:
        try:
            img = fn(path)
            if img is not None and not img.isNull():
                return img
        except Exception as e:
            errors.append(str(e))
    raise RuntimeError("不支持或已损坏的图片" + (("（" + errors[-1][:80] + "）") if errors else ""))


def make_thumb(path, cfg):
    ext = ext_of(path)
    if ext in QT_EXTS:
        r = QImageReader(path)
        r.setAutoTransform(True)
        sz = r.size()
        if sz.isValid() and sz.width() > 320:
            r.setScaledSize(sz.scaled(320, 240, Qt.KeepAspectRatio))
        img = r.read()
        if not img.isNull():
            return img.scaled(160, 120, Qt.KeepAspectRatio, Qt.SmoothTransformation)
    c = dict(cfg)
    c["raw_full"] = False
    img = load_image(path, c)
    return img.scaled(160, 120, Qt.KeepAspectRatio, Qt.SmoothTransformation)


def open_pil(path):
    """编辑用：打开并按拍摄方向摆正，返回 (img, format, info, exif)"""
    ext = ext_of(path)
    if ext in RAW_EXTS:
        import rawpy
        with rawpy.imread(path) as r:
            rgb = r.postprocess(use_camera_wb=True)
        return Image.fromarray(rgb), "JPEG", {}, None
    try:
        if ext in DOC_EXTS or ext in ("exr", "hdr"):
            raise OSError
        im = Image.open(path)
        im.load()
    except Exception:
        q = load_image(path, {"auto_orient": True, "raw_full": True})
        return qimage_to_pil(q), None, {}, None
    fmt = im.format
    info = dict(im.info)
    exif = None
    try:
        exif = im.getexif()
    except Exception:
        pass
    im2 = ImageOps.exif_transpose(im)
    if im2 is im:
        im2 = im.copy()
    im.close()
    if exif is not None:
        try:
            exif[0x0112] = 1
        except Exception:
            pass
    return im2, fmt, info, exif


def _prep_save(im, fmt, quality=95, info=None, exif=None):
    info = info or {}
    params = {}
    icc = info.get("icc_profile")
    if fmt in ("JPEG", "BMP"):
        if im.mode in ("RGBA", "LA", "P"):
            im = im.convert("RGBA")
            bg = Image.new("RGB", im.size, (255, 255, 255))
            bg.paste(im, mask=im.split()[-1])
            im = bg
        elif im.mode != "RGB":
            im = im.convert("RGB")
    if fmt == "JPEG":
        params.update(quality=quality, optimize=True)
    elif fmt in ("WEBP", "HEIF", "AVIF"):
        params.update(quality=quality)
    elif fmt == "TIFF":
        params.update(compression="tiff_lzw")
    elif fmt == "ICO":
        s = max(im.size)
        sizes = [x for x in (16, 24, 32, 48, 64, 128, 256) if x <= s] or [16]
        params.update(sizes=[(x, x) for x in sizes])
    elif fmt == "GIF" and im.mode not in ("P", "L"):
        im = im.convert("RGBA").convert("P", palette=Image.ADAPTIVE)
    if icc and fmt in ("JPEG", "PNG", "WEBP", "TIFF"):
        params["icc_profile"] = icc
    if exif is not None and fmt in ("JPEG", "WEBP", "TIFF", "PNG"):
        try:
            params["exif"] = exif.tobytes()
        except Exception:
            pass
    return im, params


def encode_size(im, fmt, quality=95, info=None, exif=None):
    im, params = _prep_save(im, fmt, quality, info, exif)
    buf = io.BytesIO()
    try:
        im.save(buf, fmt, **params)
    except Exception:
        params.pop("exif", None)
        buf = io.BytesIO()
        im.save(buf, fmt, **params)
    return buf.tell()


def save_pil(im, dst, fmt, quality=95, info=None, exif=None):
    im, params = _prep_save(im, fmt, quality, info, exif)
    d = os.path.dirname(dst) or "."
    fd, tmp = tempfile.mkstemp(suffix="." + (ext_of(dst) or "tmp"), dir=d)
    os.close(fd)
    try:
        try:
            im.save(tmp, fmt, **params)
        except Exception:
            params.pop("exif", None)
            im.save(tmp, fmt, **params)
        os.replace(tmp, dst)
    finally:
        if os.path.exists(tmp):
            os.remove(tmp)


def can_rotate_original(path):
    ext = ext_of(path)
    if ext not in SAVE_FMT or ext in ("gif", "ico"):
        return False
    if ext in ("heic", "heif", "avif") and pillow_heif is None:
        return False
    return Image is not None


def rotate_file(path, deg):
    im, fmt, info, exif = open_pil(path)
    im = im.rotate(-deg, expand=True)
    save_pil(im, path, fmt or SAVE_FMT[ext_of(path)], 95, info, exif)


def recycle(path):
    if IS_WIN:
        class SHFILEOPSTRUCTW(ctypes.Structure):
            _fields_ = [("hwnd", ctypes.wintypes.HWND), ("wFunc", ctypes.wintypes.UINT),
                        ("pFrom", ctypes.wintypes.LPCWSTR), ("pTo", ctypes.wintypes.LPCWSTR),
                        ("fFlags", ctypes.c_ushort), ("fAnyOperationsAborted", ctypes.wintypes.BOOL),
                        ("hNameMappings", ctypes.c_void_p), ("lpszProgressTitle", ctypes.wintypes.LPCWSTR)]
        op = SHFILEOPSTRUCTW()
        op.wFunc = 3  # FO_DELETE
        op.pFrom = os.path.abspath(path) + "\0"
        op.fFlags = 0x40 | 0x10 | 0x4 | 0x400  # ALLOWUNDO|NOCONFIRMATION|SILENT|NOERRORUI
        return ctypes.windll.shell32.SHFileOperationW(ctypes.byref(op)) == 0 and not os.path.exists(path)
    try:
        from send2trash import send2trash
        send2trash(path)
        return True
    except Exception:
        return False


# ---------------------------------------------------------------- 后台任务
class _Bus(QObject):
    done = Signal(object, object, object)


BUS = None


class _Job(QRunnable):
    def __init__(self, fn, cb):
        super().__init__()
        self.fn, self.cb = fn, cb
        self.setAutoDelete(True)

    def run(self):
        try:
            res, ok = self.fn(), True
        except Exception as e:
            res, ok = e, False
        try:
            BUS.done.emit(self.cb, ok, res)
        except RuntimeError:
            pass


def run_bg(pool, fn, cb):
    pool.start(_Job(fn, cb))


# ---------------------------------------------------------------- EXIF
EXIF_FIELDS = [("拍摄时间", 36867), ("相机厂商", 271), ("设备型号", 272), ("镜头型号", 42036),
               ("光圈值", 33437), ("最大光圈", 37381), ("曝光时间", 33434), ("曝光补偿", 37380),
               ("ISO感光度", 34855), ("焦距", 37386), ("测光模式", 37383), ("闪光灯", 37385),
               ("白平衡", 41987), ("亮度", 37379), ("曝光程序", 34850)]
METERING = {0: "未知", 1: "平均", 2: "中央重点", 3: "点测光", 4: "多点", 5: "矩阵", 6: "局部"}
PROGRAM = {0: "未定义", 1: "手动", 2: "程序自动", 3: "光圈优先", 4: "快门优先", 5: "创意", 6: "运动",
           7: "人像", 8: "风景"}


def _f(v):
    try:
        return float(v)
    except Exception:
        try:
            return v[0] / v[1]
        except Exception:
            return None


def read_exif(path):
    out = {}
    if Image is None or ext_of(path) in RAW_EXTS:
        return out
    try:
        with Image.open(path) as im:
            ex = im.getexif()
            d = dict(ex)
            try:
                d.update(ex.get_ifd(0x8769))
            except Exception:
                pass
    except Exception:
        return out
    for name, tag in EXIF_FIELDS:
        v = d.get(tag)
        if v is None or v == "":
            continue
        try:
            if tag == 33437:
                v = f"f/{_f(v):.1f}"
            elif tag == 37381:
                v = f"f/{2 ** (_f(v) / 2):.1f}"
            elif tag == 33434:
                t = _f(v)
                v = f"1/{round(1 / t)} 秒" if t and t < 1 else f"{t:g} 秒"
            elif tag == 37380:
                v = f"{_f(v):+.1f} EV"
            elif tag == 37386:
                v = f"{_f(v):g} mm"
            elif tag == 34855:
                v = str(v[0] if isinstance(v, (tuple, list)) else v)
            elif tag == 37383:
                v = METERING.get(int(v), str(v))
            elif tag == 37385:
                v = "闪光" if int(v) & 1 else "未闪光"
            elif tag == 41987:
                v = "手动" if int(v) == 1 else "自动"
            elif tag == 34850:
                v = PROGRAM.get(int(v), str(v))
            elif tag == 37379:
                v = f"{_f(v):.2f}"
            else:
                v = str(v).strip("\x00 ")
        except Exception:
            v = str(v)
        out[name] = v
    return out


# ---------------------------------------------------------------- 文件关联（只在用户点按钮时写入）
def app_command():
    if getattr(sys, "frozen", False):
        return f'"{sys.executable}" "%1"', sys.executable
    pyw = os.path.join(os.path.dirname(sys.executable), "pythonw.exe")
    if not os.path.exists(pyw):
        pyw = sys.executable
    return f'"{pyw}" "{os.path.abspath(__file__)}" "%1"', sys.executable


def _reg_set(sub, name, val):
    import winreg
    k = winreg.CreateKeyEx(winreg.HKEY_CURRENT_USER, sub, 0, winreg.KEY_WRITE)
    winreg.SetValueEx(k, name, 0, winreg.REG_SZ, val)
    winreg.CloseKey(k)


def _reg_del_tree(sub):
    import winreg
    try:
        k = winreg.OpenKey(winreg.HKEY_CURRENT_USER, sub, 0, winreg.KEY_ALL_ACCESS)
    except OSError:
        return
    while True:
        try:
            child = winreg.EnumKey(k, 0)
        except OSError:
            break
        _reg_del_tree(sub + "\\" + child)
    winreg.CloseKey(k)
    try:
        winreg.DeleteKey(winreg.HKEY_CURRENT_USER, sub)
    except OSError:
        pass


def _notify_assoc():
    try:
        ctypes.windll.shell32.SHChangeNotify(0x08000000, 0, None, None)
    except Exception:
        pass


def register_assoc(exts):
    cmd, exe = app_command()
    base = r"Software\Classes"
    _reg_set(base + "\\" + PROGID, "", "图片")
    _reg_set(base + "\\" + PROGID + r"\DefaultIcon", "", f"{exe},0")
    _reg_set(base + "\\" + PROGID + r"\shell\open\command", "", cmd)
    cap = r"Software\KanTu\Capabilities"
    _reg_set(cap, "ApplicationName", APP_NAME)
    _reg_set(cap, "ApplicationDescription", "免费开源、无广告的本地看图工具")
    import winreg
    for e in exts:
        _reg_set(base + "\\." + e + r"\OpenWithProgids", PROGID, "")
        _reg_set(cap + r"\FileAssociations", "." + e, PROGID)
        # 没有任何程序打开的格式（如 KOA、CUT），直接设为本软件
        owner = ""
        try:
            owner = winreg.QueryValue(winreg.HKEY_CLASSES_ROOT, "." + e) or ""
        except OSError:
            pass
        if not owner:
            _reg_set(base + "\\." + e, "", PROGID)
    _reg_set(r"Software\RegisteredApplications", "KanTu", cap)
    _notify_assoc()


def unregister_assoc():
    import winreg
    _reg_del_tree(r"Software\Classes\\" + PROGID)
    _reg_del_tree(r"Software\KanTu")
    for sub, name in [(r"Software\RegisteredApplications", "KanTu")] + \
            [(r"Software\Classes\." + e + r"\OpenWithProgids", PROGID) for e in ASSOC_ALL]:
        try:
            k = winreg.OpenKey(winreg.HKEY_CURRENT_USER, sub, 0, winreg.KEY_WRITE)
            winreg.DeleteValue(k, name)
            winreg.CloseKey(k)
        except OSError:
            pass
    for e in ASSOC_ALL:
        try:
            k = winreg.OpenKey(winreg.HKEY_CURRENT_USER, r"Software\Classes\." + e, 0,
                               winreg.KEY_READ | winreg.KEY_WRITE)
            if winreg.QueryValueEx(k, "")[0] == PROGID:
                winreg.DeleteValue(k, "")
            winreg.CloseKey(k)
        except OSError:
            pass
    _notify_assoc()


def current_default(ext):
    if not IS_WIN:
        return "-"
    import winreg
    try:
        k = winreg.OpenKey(winreg.HKEY_CURRENT_USER,
                           rf"Software\Microsoft\Windows\CurrentVersion\Explorer\FileExts\.{ext}\UserChoice")
        pid = winreg.QueryValueEx(k, "ProgId")[0]
        winreg.CloseKey(k)
    except OSError:
        pid = ""
    if not pid:
        try:
            pid = winreg.QueryValue(winreg.HKEY_CLASSES_ROOT, "." + ext) or ""
        except OSError:
            pid = ""
    if not pid:
        return "未设置"
    if pid == PROGID:
        return APP_NAME
    if "2345" in pid:
        return "2345看图王"
    if pid.startswith("AppX"):
        return "Windows 照片"
    if "PhotoViewer" in pid:
        return "Windows 照片查看器"
    return pid


# ---------------------------------------------------------------- 样式
QSS = """
QWidget{background:#ffffff;color:#1f2328;font-family:"Microsoft YaHei UI","Microsoft YaHei","PingFang SC";font-size:13px}
QToolTip{background:#ffffff;color:#1f2328;border:1px solid #dfe2e6;padding:4px}
QMenu{background:#ffffff;border:1px solid #dfe2e6;padding:6px 0}
QMenu::item{padding:7px 36px 7px 18px;background:transparent}
QMenu::item:selected{background:#e8f0fd;color:#1557bd}
QMenu::item:disabled{color:#a0a6ae}
QMenu::separator{height:1px;background:#e6e8eb;margin:4px 0}
QFrame#floatbar{background:#ffffff;border:1px solid #dfe2e6;border-radius:12px}
QFrame#floatbar QToolButton{background:transparent;border:none;border-radius:6px;padding:0 10px;min-height:40px;min-width:36px;font-size:13px;color:#1f2328}
QFrame#floatbar QToolButton:hover{background:#f0f2f5}
QFrame#floatbar QToolButton:checked{background:#e8f0fd;color:#1557bd}
QFrame#floatbar QToolButton#primarybtn{background:#1e6fe8;color:#ffffff}
QFrame#floatbar QToolButton#primarybtn:hover{background:#1b63d0}
QFrame#sep{background:#dfe2e6;border:none}
QToolButton#grid{background:transparent;border:none;border-radius:6px;padding:8px 4px;font-size:12px;color:#1f2328}
QToolButton#grid:hover{background:#f0f2f5}
QPushButton{background:#ffffff;border:1px solid #c9ced5;border-radius:6px;padding:6px 16px;color:#1f2328}
QPushButton:hover{background:#f0f2f5}
QPushButton:checked{background:#e8f0fd;border-color:#1e6fe8;color:#1557bd}
QPushButton:disabled{color:#a0a6ae}
QPushButton#primary{background:#1e6fe8;border:none;color:white}
QPushButton#primary:hover{background:#1b63d0}
QListWidget{background:#ffffff;border:none;outline:none}
QListWidget#thumbs{background:#f5f6f8;border-top:1px solid #dfe2e6}
QListWidget#thumbs::item{border-radius:4px;padding:2px;border:2px solid transparent}
QListWidget#thumbs::item:selected{background:#e8f0fd;border:2px solid #1e6fe8}
QListWidget#nav{background:#f5f6f8;border-right:1px solid #dfe2e6}
QListWidget#nav::item{height:44px;padding-left:16px;color:#1f2328}
QListWidget#nav::item:selected{background:#e8f0fd;color:#1557bd}
QLineEdit,QSpinBox,QComboBox,QPlainTextEdit,QTextBrowser{background:#ffffff;border:1px solid #c9ced5;border-radius:4px;padding:4px 6px;min-height:22px;selection-background-color:#cfe0fb;selection-color:#1f2328}
QComboBox QAbstractItemView{background:#ffffff;selection-background-color:#e8f0fd;selection-color:#1557bd}
QTableWidget{background:#ffffff;gridline-color:#e6e8eb;border:1px solid #dfe2e6}
QHeaderView::section{background:#f5f6f8;border:none;padding:6px;color:#5b636e}
QCheckBox,QRadioButton{spacing:8px;background:transparent}
QCheckBox:disabled,QRadioButton:disabled{color:#a0a6ae}
QCheckBox::indicator,QTableWidget::indicator{width:16px;height:16px;border:1px solid #9aa1ab;border-radius:3px;background:#ffffff}
QCheckBox::indicator:checked,QTableWidget::indicator:checked{background:qlineargradient(x1:0,y1:0,x2:0,y2:1,stop:0 #1e6fe8,stop:1 #1e6fe8);border:1px solid #1e6fe8}
QRadioButton::indicator{width:16px;height:16px;border:1px solid #9aa1ab;border-radius:9px;background:#ffffff}
QRadioButton::indicator:checked{background:qradialgradient(cx:0.5,cy:0.5,radius:0.5,fx:0.5,fy:0.5,stop:0 #ffffff,stop:0.3 #ffffff,stop:0.36 #1e6fe8,stop:1 #1e6fe8);border-color:#1e6fe8}
QSlider::groove:horizontal{height:4px;background:#dfe2e6;border-radius:2px}
QSlider::sub-page:horizontal{background:#1e6fe8;border-radius:2px}
QSlider::handle:horizontal{background:#ffffff;border:1px solid #9aa1ab;width:14px;height:14px;margin:-6px 0;border-radius:8px}
QLabel{background:transparent}
QLabel#hint{color:#5b636e;font-size:12px}
QLabel#sec{font-weight:bold;color:#1f2328;padding-top:6px}
QFrame#more{background:#ffffff;border:1px solid #dfe2e6;border-radius:10px}
QFrame#more QWidget{background:transparent}
QFrame#line{background:#e6e8eb;max-height:1px;min-height:1px}
QCheckBox#switch::indicator{width:36px;height:20px;border-radius:10px;background:#d5d9de;border:none}
QCheckBox#switch::indicator:checked{background:#1e6fe8}
QScrollArea{border:none}
QScrollBar:horizontal{height:8px;background:transparent}
QScrollBar::handle:horizontal{background:#c9ced5;border-radius:4px;min-width:30px}
QScrollBar:vertical{width:8px;background:transparent}
QScrollBar::handle:vertical{background:#c9ced5;border-radius:4px;min-height:30px}
QScrollBar::add-line,QScrollBar::sub-line{width:0;height:0}
QScrollBar::add-page,QScrollBar::sub-page{background:transparent}
QProgressBar{border:1px solid #c9ced5;border-radius:4px;text-align:center;background:#ffffff}
QProgressBar::chunk{background:#1e6fe8}
"""


def make_app_icon(size=256):
    pm = QPixmap(size, size)
    pm.fill(Qt.transparent)
    p = QPainter(pm)
    p.setRenderHint(QPainter.Antialiasing)
    r = size * 0.18
    p.setBrush(QColor("#2f6fe0"))
    p.setPen(Qt.NoPen)
    p.drawRoundedRect(QRectF(size * 0.06, size * 0.06, size * 0.88, size * 0.88), r, r)
    p.setBrush(QColor("#ffd45c"))
    p.drawEllipse(QPointF(size * 0.36, size * 0.36), size * 0.09, size * 0.09)
    p.setBrush(QColor("#ffffff"))
    poly = QPolygonF([QPointF(size * 0.16, size * 0.80), QPointF(size * 0.42, size * 0.48),
                      QPointF(size * 0.58, size * 0.66), QPointF(size * 0.68, size * 0.56),
                      QPointF(size * 0.86, size * 0.80)])
    p.drawPolygon(poly)
    p.end()
    return pm


def arrow_cursor(left):
    pm = QPixmap(40, 40)
    pm.fill(Qt.transparent)
    p = QPainter(pm)
    p.setRenderHint(QPainter.Antialiasing)
    p.setBrush(QColor(0, 0, 0, 150))
    p.setPen(Qt.NoPen)
    p.drawEllipse(2, 2, 36, 36)
    p.setPen(QPen(QColor("white"), 3, Qt.SolidLine, Qt.RoundCap, Qt.RoundJoin))
    if left:
        p.drawPolyline(QPolygonF([QPointF(23, 11), QPointF(14, 20), QPointF(23, 29)]))
    else:
        p.drawPolyline(QPolygonF([QPointF(17, 11), QPointF(26, 20), QPointF(17, 29)]))
    p.end()
    return QCursor(pm, 20, 20)


def dark_titlebar(w):
    """浅色主题：保持系统默认标题栏"""
    return
    if not IS_WIN:
        return
    try:
        hwnd = int(w.winId())
        v = ctypes.c_int(1)
        for attr in (20, 19):
            ctypes.windll.dwmapi.DwmSetWindowAttribute(hwnd, attr, ctypes.byref(v), 4)
    except Exception:
        pass


# ---------------------------------------------------------------- 看图画布
class Canvas(QWidget):
    def __init__(self, win):
        super().__init__(win)
        self.win = win
        self.setMouseTracking(True)
        self.setFocusPolicy(Qt.StrongFocus)
        self.setAttribute(Qt.WA_OpaquePaintEvent)
        self.base = None
        self.pix = None
        self.rot = 0
        self.scale = 1.0
        self.off = QPointF(0, 0)
        self.fit_mode = True
        self.loading_text = ""
        self.message = "拖入图片，或按 Ctrl+O 打开"
        self.bg = QColor("#eef0f3")
        self.bg_pix = None
        self.nav_pix = None
        self.crop_mode = False
        self.crop_start = None
        self.crop_rect = QRectF()
        self._drag = None
        self._drag_off = QPointF()
        self._moved = False
        self._nav_drag = False
        self._cache = None
        self._cache_timer = QTimer(self)
        self._cache_timer.setSingleShot(True)
        self._cache_timer.timeout.connect(self._build_cache)
        self.toast_text = ""
        self._toast_timer = QTimer(self)
        self._toast_timer.setSingleShot(True)
        self._toast_timer.timeout.connect(self._clear_toast)
        self._cur_l = arrow_cursor(True)
        self._cur_r = arrow_cursor(False)

    # ---- 尺寸换算（scale = 图片像素 : 屏幕物理像素）
    def k(self):
        return self.scale / self.devicePixelRatioF()

    def disp_size(self):
        if not self.pix:
            return 0.0, 0.0
        k = self.k()
        return self.pix.width() * k, self.pix.height() * k

    def image_rect(self):
        w, h = self.disp_size()
        return QRectF(self.off, QSizeF(w, h))

    # ---- 设置图片
    def clear(self, message=""):
        self.base = self.pix = None
        self.nav_pix = None
        self._cache = None
        self.message = message
        self.loading_text = ""
        self.update()

    def set_image(self, pix, view="auto"):
        old_scale, had = self.scale, self.pix is not None
        old_center = self._view_center_ratio() if had else None
        self.base = pix
        self.rot = 0
        self.message = ""
        self.loading_text = ""
        self.crop_mode = False
        self._apply_rot()
        if view == "lock" and had:
            self.scale = old_scale
            self.fit_mode = False
            self._restore_center(old_center)
        elif view in ("top", "bottom"):
            self._fit_width(view)
        else:
            self.reset_view()

    def set_frame(self, pix):
        """动图换帧：不改变视图"""
        self.base = pix
        self._apply_rot(keep_view=True)

    def rotate_view(self, deg):
        if not self.base:
            return
        self.rot = (self.rot + deg) % 360
        self._apply_rot()
        self.reset_view()

    def _apply_rot(self, keep_view=False):
        if self.base is None:
            self.pix = None
            return
        if self.rot:
            self.pix = self.base.transformed(QTransform().rotate(self.rot), Qt.SmoothTransformation)
        else:
            self.pix = self.base
        self.nav_pix = None
        self._cache = None
        if keep_view:
            self._clamp()
        self.update()

    def _view_center_ratio(self):
        w, h = self.disp_size()
        if not w or not h:
            return (0.5, 0.5)
        return ((self.width() / 2 - self.off.x()) / w, (self.height() / 2 - self.off.y()) / h)

    def _restore_center(self, c):
        w, h = self.disp_size()
        self.off = QPointF(self.width() / 2 - c[0] * w, self.height() / 2 - c[1] * h)
        self._clamp()
        self._changed()

    def fit_scale(self):
        if not self.pix or not self.pix.width() or not self.pix.height():
            return 1.0
        dpr = self.devicePixelRatioF()
        W, H = max(1, self.width()) * dpr, max(1, self.height()) * dpr
        return min(W / self.pix.width(), H / self.pix.height())

    def reset_view(self):
        if not self.pix:
            return
        self.scale = min(1.0, self.fit_scale())
        self.fit_mode = True
        self.off = QPointF(0, 0)
        self._clamp()
        self._changed()

    def fit_window(self):
        if not self.pix:
            return
        self.scale = self.fit_scale()
        self.fit_mode = False
        self._clamp()
        self._changed()

    def _fit_width(self, where):
        if not self.pix:
            return
        dpr = self.devicePixelRatioF()
        self.scale = min(1.0, self.width() * dpr / max(1, self.pix.width()))
        self.fit_mode = False
        w, h = self.disp_size()
        self.off = QPointF(0, 0 if where == "top" else self.height() - h)
        self._clamp()
        self._changed()

    def actual_size(self, anchor=None):
        self.zoom_to(1.0, anchor)

    def zoom_to(self, new_scale, anchor=None):
        if not self.pix:
            return
        if anchor is None:
            anchor = QPointF(self.width() / 2, self.height() / 2)
        k0 = self.k()
        img_pt = (anchor - self.off) / k0
        self.scale = max(0.01, min(32.0, new_scale))
        self.fit_mode = False
        self.off = anchor - img_pt * self.k()
        self._clamp()
        self._changed()
        self.toast(f"{self.scale * 100:.0f}%", 700)

    def _clamp(self):
        if not self.pix:
            return
        W, H = self.width(), self.height()
        w, h = self.disp_size()
        x, y = self.off.x(), self.off.y()
        x = (W - w) / 2 if w <= W else min(0.0, max(W - w, x))
        y = (H - h) / 2 if h <= H else min(0.0, max(H - h, y))
        self.off = QPointF(x, y)

    def _changed(self):
        self._cache = None
        if self.win.cfg.get("edit_downscale", True) and self.scale < 0.999:
            self._cache_timer.start(120)
        self.update()
        self.win.update_title()

    def _build_cache(self):
        if not self.pix or self.scale >= 0.999:
            return
        w = max(1, round(self.pix.width() * self.scale))
        h = max(1, round(self.pix.height() * self.scale))
        if w * h > 80_000_000:
            return
        sp = self.pix.scaled(w, h, Qt.IgnoreAspectRatio, Qt.SmoothTransformation)
        sp.setDevicePixelRatio(self.devicePixelRatioF())
        self._cache = (self.scale, self.pix.cacheKey(), sp)
        self.update()

    def pannable(self):
        w, h = self.disp_size()
        return w > self.width() + 1 or h > self.height() + 1

    # ---- 提示
    def toast(self, text, ms=2000):
        self.toast_text = text
        self._toast_timer.start(ms)
        self.update()

    def _clear_toast(self):
        self.toast_text = ""
        self.update()

    # ---- 鸟瞰图
    def _nav_rect(self):
        if not self.win.cfg.get("navigator") or not self.pix or not self.pannable():
            return None
        if self.nav_pix is None:
            self.nav_pix = self.pix.scaled(150, 110, Qt.KeepAspectRatio, Qt.SmoothTransformation)
        nw, nh = self.nav_pix.width(), self.nav_pix.height()
        return QRectF(16, self.height() - 90 - nh - 28, nw + 12, nh + 28)

    def _nav_goto(self, pos):
        box = self._nav_rect()
        if not box:
            return
        img = QRectF(box.x() + 6, box.y() + 22, self.nav_pix.width(), self.nav_pix.height())
        rx = min(1, max(0, (pos.x() - img.x()) / img.width()))
        ry = min(1, max(0, (pos.y() - img.y()) / img.height()))
        self._restore_center((rx, ry))

    # ---- 绘制
    def paintEvent(self, e):
        p = QPainter(self)
        r = QRectF(self.rect())
        if self.bg_pix is not None:
            p.drawPixmap(self.rect(), self.bg_pix)
            p.fillRect(r, QColor(0, 0, 0, 120))
        else:
            p.fillRect(r, self.bg)
        if self.pix:
            target = self.image_rect()
            cache = self._cache
            if cache and cache[0] == self.scale and cache[1] == self.pix.cacheKey():
                p.drawPixmap(target.topLeft(), cache[2])
            else:
                p.setRenderHint(QPainter.SmoothPixmapTransform, self.scale < 3)
                vis = target.intersected(r)
                if not vis.isEmpty():
                    k = self.k()
                    src = QRectF((vis.x() - target.x()) / k, (vis.y() - target.y()) / k,
                                 vis.width() / k, vis.height() / k)
                    p.drawPixmap(vis, self.pix, src)
            if self.crop_mode:
                self._paint_crop(p, target)
            box = self._nav_rect()
            if box:
                self._paint_nav(p, box)
        elif self.message:
            p.setPen(QColor("#6b7280"))
            p.setFont(QFont(self.font().family(), 13))
            p.drawText(r, Qt.AlignCenter, self.message)
        for text, y in ((self.loading_text, self.height() / 2), (self.toast_text, self.height() - 120)):
            if not text:
                continue
            f = QFont(self.font().family(), 12)
            p.setFont(f)
            fm = QFontMetrics(f)
            w = fm.horizontalAdvance(text) + 32
            h = fm.height() + 16
            rr = QRectF((self.width() - w) / 2, y - h / 2, w, h)
            p.setRenderHint(QPainter.Antialiasing)
            p.setPen(Qt.NoPen)
            p.setBrush(QColor(0, 0, 0, 170))
            p.drawRoundedRect(rr, 8, 8)
            p.setPen(QColor("white"))
            p.drawText(rr, Qt.AlignCenter, text)
        p.end()

    def _paint_crop(self, p, target):
        cr = self.crop_rect
        path = QPainterPath()
        path.addRect(QRectF(self.rect()))
        if not cr.isEmpty():
            inner = QPainterPath()
            inner.addRect(cr)
            path = path.subtracted(inner)
        p.fillPath(path, QColor(0, 0, 0, 140))
        if not cr.isEmpty():
            p.setPen(QPen(QColor("#1e6fe8"), 2))
            p.setBrush(Qt.NoBrush)
            p.drawRect(cr)
            k = self.k()
            label = f"{cr.width() / k:.0f} × {cr.height() / k:.0f}"
            p.setPen(QColor("white"))
            p.drawText(QPointF(cr.x() + 4, max(14.0, cr.y() - 6)), label)

    def _paint_nav(self, p, box):
        p.setRenderHint(QPainter.Antialiasing)
        p.setPen(QPen(QColor("#dfe2e6"), 1))
        p.setBrush(QColor(255, 255, 255, 240))
        p.drawRoundedRect(box, 6, 6)
        p.setPen(QColor("#5b636e"))
        p.drawText(QRectF(box.x() + 8, box.y() + 2, box.width(), 20), Qt.AlignVCenter, "鸟瞰图")
        img = QRectF(box.x() + 6, box.y() + 22, self.nav_pix.width(), self.nav_pix.height())
        p.drawPixmap(img.topLeft(), self.nav_pix)
        w, h = self.disp_size()
        vx = max(0, -self.off.x()) / w
        vy = max(0, -self.off.y()) / h
        vw = min(1, self.width() / w)
        vh = min(1, self.height() / h)
        p.setBrush(Qt.NoBrush)
        p.setPen(QPen(QColor("#1e6fe8"), 2))
        p.drawRect(QRectF(img.x() + vx * img.width(), img.y() + vy * img.height(),
                          vw * img.width(), vh * img.height()))

    # ---- 裁剪
    def crop_image_rect(self):
        """把屏幕选区换算成图片像素坐标（基于当前显示方向）"""
        if self.crop_rect.isEmpty() or not self.pix:
            return QRect()
        k = self.k()
        r = QRectF((self.crop_rect.x() - self.off.x()) / k, (self.crop_rect.y() - self.off.y()) / k,
                   self.crop_rect.width() / k, self.crop_rect.height() / k)
        return r.toAlignedRect().intersected(QRect(0, 0, self.pix.width(), self.pix.height()))

    # ---- 鼠标
    def _flip_zone(self, pos):
        if not self.win.cfg.get("pointer_flip") or self.crop_mode or not self.win.files:
            return 0
        if pos.x() < self.width() * 0.2:
            return -1
        if pos.x() > self.width() * 0.8:
            return 1
        return 0

    def _update_cursor(self, pos):
        if self.crop_mode:
            self.setCursor(Qt.CrossCursor)
            return
        z = self._flip_zone(pos)
        if z < 0:
            self.setCursor(self._cur_l)
        elif z > 0:
            self.setCursor(self._cur_r)
        elif self._drag is not None and self._moved:
            self.setCursor(Qt.ClosedHandCursor)
        elif self.pannable():
            self.setCursor(Qt.OpenHandCursor)
        else:
            self.setCursor(Qt.ArrowCursor)

    def mousePressEvent(self, e):
        if e.button() != Qt.LeftButton:
            return
        pos = e.position()
        if self.crop_mode:
            self.crop_start = pos
            self.crop_rect = QRectF()
            self.update()
            return
        box = self._nav_rect()
        if box and box.contains(pos):
            self._nav_drag = True
            self._nav_goto(pos)
            return
        self._drag = pos
        self._drag_off = QPointF(self.off)
        self._moved = False

    def leaveEvent(self, e):
        self.win.bar_leave()
        super().leaveEvent(e)

    def mouseMoveEvent(self, e):
        pos = e.position()
        self.win.bar_track(pos)
        if self.crop_mode and self.crop_start is not None:
            self.crop_rect = QRectF(self.crop_start, pos).normalized().intersected(self.image_rect())
            self.update()
        elif self._nav_drag:
            self._nav_goto(pos)
        elif self._drag is not None and (e.buttons() & Qt.LeftButton):
            d = pos - self._drag
            if abs(d.x()) + abs(d.y()) > 3:
                self._moved = True
            if self._moved and self.pix:
                self.off = self._drag_off + d
                self._clamp()
                self.update()
        self._update_cursor(pos)

    def mouseReleaseEvent(self, e):
        if e.button() != Qt.LeftButton:
            return
        if self.crop_mode:
            self.crop_start = None
            return
        if self._nav_drag:
            self._nav_drag = False
            return
        if self._drag is not None and not self._moved:
            z = self._flip_zone(e.position())
            if z:
                self.win.flip(z)
        self._drag = None
        self._update_cursor(e.position())

    def mouseDoubleClickEvent(self, e):
        if e.button() != Qt.LeftButton:
            return
        if self.crop_mode:
            self.win.finish_crop()
            return
        if self._flip_zone(e.position()):
            return
        self.win.toggle_fullscreen()

    def wheelEvent(self, e):
        self.win.on_wheel(e)

    def contextMenuEvent(self, e):
        if self.crop_mode:
            self.win.cancel_crop()
            return
        self.win.show_context_menu(e.globalPos())

    def resizeEvent(self, e):
        self.win.place_bar()
        if self.fit_mode:
            self.reset_view()
        else:
            self._clamp()
            self._changed()


# ---------------------------------------------------------------- 更多面板
class ToggleRow(QWidget):
    def __init__(self, title, sub, checked, cb):
        super().__init__()
        lay = QHBoxLayout(self)
        lay.setContentsMargins(10, 6, 10, 6)
        col = QVBoxLayout()
        col.setSpacing(2)
        t = QLabel(title)
        s = QLabel(sub)
        s.setObjectName("hint")
        col.addWidget(t)
        col.addWidget(s)
        lay.addLayout(col, 1)
        self.box = QCheckBox()
        self.box.setObjectName("switch")
        self.box.setChecked(checked)
        self.box.toggled.connect(cb)
        lay.addWidget(self.box)

    def mousePressEvent(self, e):
        self.box.toggle()


class MorePanel(QFrame):
    def __init__(self, win):
        super().__init__(win, Qt.Popup | Qt.FramelessWindowHint)
        self.setObjectName("more")
        self.setAttribute(Qt.WA_StyledBackground)
        self.win = win
        lay = QVBoxLayout(self)
        lay.setContentsMargins(8, 8, 8, 8)
        lay.setSpacing(2)
        cfg = win.cfg
        lay.addWidget(ToggleRow("锁定缩放比", "翻页时保持当前比例", cfg["lock_zoom"],
                                lambda v: win.set_opt("lock_zoom", v)))
        lay.addWidget(ToggleRow("缩略图", "底部显示当前文件夹的图片", cfg["thumbs"],
                                lambda v: win.set_opt("thumbs", v)))
        lay.addWidget(ToggleRow("鸟瞰图", "看大图时快速定位查看区域", cfg["navigator"],
                                lambda v: win.set_opt("navigator", v)))
        line = QFrame()
        line.setObjectName("line")
        lay.addWidget(line)
        grid = QHBoxLayout()
        for text, fn in (("修改尺寸", win.resize_dialog), ("幻灯片", win.start_slideshow),
                         ("设置", win.open_settings)):
            b = QToolButton()
            b.setObjectName("grid")
            b.setText(text)
            b.setMinimumSize(60, 44)
            b.clicked.connect(lambda _=False, f=fn: (self.close(), QTimer.singleShot(0, f)))
            grid.addWidget(b)
        lay.addLayout(grid)
        self.setFixedWidth(300)


# ---------------------------------------------------------------- 小对话框
def ask_with_checkbox(parent, title, text, buttons, check_text="不再提示"):
    """buttons: [(key, text)]；返回 (key 或 None, 勾选状态)"""
    box = QMessageBox(parent)
    box.setWindowTitle(title)
    box.setText(text)
    mapping = {}
    for i, (key, t) in enumerate(buttons):
        b = box.addButton(t, QMessageBox.AcceptRole if i == 0 else QMessageBox.ActionRole)
        mapping[b] = key
    cancel = box.addButton("取消", QMessageBox.RejectRole)
    cb = QCheckBox(check_text)
    box.setCheckBox(cb)
    box.exec()
    clicked = box.clickedButton()
    if clicked is cancel or clicked not in mapping:
        return None, cb.isChecked()
    return mapping[clicked], cb.isChecked()


class InfoDialog(QDialog):
    def __init__(self, win, path, img):
        super().__init__(win, Qt.Tool)
        self.setWindowTitle("图片信息")
        self.setAttribute(Qt.WA_DeleteOnClose)
        lay = QVBoxLayout(self)
        form = QFormLayout()
        form.setLabelAlignment(Qt.AlignRight)
        form.setHorizontalSpacing(14)
        st = os.stat(path)
        name = QLabel(os.path.basename(path))
        name.setTextInteractionFlags(Qt.TextSelectableByMouse)
        name.setWordWrap(True)
        form.addRow("图片名称：", name)
        form.addRow("图片类型：", QLabel(ext_of(path).upper()))
        form.addRow("图片大小：", QLabel(human_size(st.st_size)))
        w, h = (img.width(), img.height()) if img is not None else (0, 0)
        form.addRow("图片尺寸：", QLabel(f"{w} * {h}"))
        form.addRow("修改时间：", QLabel(datetime.fromtimestamp(st.st_mtime).strftime("%Y-%m-%d %H:%M:%S")))
        lay.addLayout(form)
        line = QFrame()
        line.setObjectName("line")
        lay.addWidget(line)
        ex = read_exif(path)
        form2 = QFormLayout()
        form2.setLabelAlignment(Qt.AlignRight)
        form2.setHorizontalSpacing(14)
        for label, _ in EXIF_FIELDS:
            v = QLabel(ex.get(label, ""))
            v.setTextInteractionFlags(Qt.TextSelectableByMouse)
            form2.addRow(label + "：", v)
        lay.addLayout(form2)
        self.setMinimumWidth(300)


class WheelTipDialog(QDialog):
    def __init__(self, parent):
        super().__init__(parent)
        self.setWindowTitle("滚轮看图模式")
        lay = QVBoxLayout(self)
        lay.setContentsMargins(28, 24, 28, 20)
        lay.setSpacing(16)
        t = QLabel("已进入滚轮看图模式，再次点击工具栏按钮可退出")
        t.setAlignment(Qt.AlignCenter)
        t.setStyleSheet("font-size:15px")
        lay.addWidget(t)
        s = QLabel("滚轮：上下移动图片，到头自动翻页\nCtrl + 滚轮：缩放图片")
        s.setAlignment(Qt.AlignCenter)
        s.setObjectName("hint")
        lay.addWidget(s)
        row = QHBoxLayout()
        self.cb = QCheckBox("不再提示")
        row.addWidget(self.cb)
        row.addStretch(1)
        ok = QPushButton("确定")
        ok.setObjectName("primary")
        ok.clicked.connect(self.accept)
        row.addWidget(ok)
        lay.addLayout(row)


class ConvertDialog(QDialog):
    FORMATS = [("JPG", "jpg"), ("PNG", "png"), ("WEBP", "webp"), ("BMP", "bmp"), ("TIFF", "tif"),
               ("ICO", "ico"), ("GIF", "gif")]
    QUALITY_FMTS = ("jpg", "webp")

    def __init__(self, win, path):
        super().__init__(win)
        self.setWindowTitle("格式转换")
        self.path = path
        self._alive = True
        self._im = None
        self._token = 0
        self.pool = QThreadPool(self)
        self.pool.setMaxThreadCount(1)
        lay = QFormLayout(self)
        lay.setContentsMargins(28, 24, 28, 20)
        lay.setHorizontalSpacing(16)
        lay.setVerticalSpacing(16)
        lay.setLabelAlignment(Qt.AlignRight | Qt.AlignVCenter)
        self.fmt = QComboBox()
        for t, e in self.FORMATS:
            self.fmt.addItem(t, e)
        self.fmt.setMinimumWidth(260)
        lay.addRow("转换类型：", self.fmt)
        qr = QHBoxLayout()
        self.quality = QSlider(Qt.Horizontal)
        self.quality.setRange(1, 100)
        self.quality.setValue(80)
        self.q_label = QLabel()
        self.q_label.setMinimumWidth(120)
        qr.addWidget(self.quality, 1)
        qr.addWidget(self.q_label)
        lay.addRow("图片质量：", qr)
        self.size_label = QLabel("计算中…")
        lay.addRow("预估大小：", self.size_label)
        pr = QHBoxLayout()
        self.out = QLineEdit(win.cfg.get("conv_dir") or os.path.dirname(path))
        ch = QPushButton("更改…")
        ch.clicked.connect(self._browse)
        pr.addWidget(self.out, 1)
        pr.addWidget(ch)
        lay.addRow("保存路径：", pr)
        self.name = QLineEdit(os.path.splitext(os.path.basename(path))[0])
        lay.addRow("图片名称：", self.name)
        bt = QHBoxLayout()
        bt.addStretch(1)
        ok = QPushButton("转换")
        ok.setObjectName("primary")
        ok.setMinimumWidth(110)
        ok.clicked.connect(self._ok)
        ca = QPushButton("取消")
        ca.setMinimumWidth(110)
        ca.clicked.connect(self.reject)
        bt.addWidget(ok)
        bt.addSpacing(12)
        bt.addWidget(ca)
        lay.addRow(bt)
        self.timer = QTimer(self)
        self.timer.setSingleShot(True)
        self.timer.timeout.connect(self._estimate)
        self.fmt.currentIndexChanged.connect(lambda _: self._changed())
        self.quality.valueChanged.connect(lambda _: self._changed())
        self.setMinimumWidth(560)
        self._changed()
        self.name.setFocus()
        self.name.selectAll()

    def ext(self):
        return self.fmt.currentData()

    def _changed(self):
        q = self.quality.value()
        has_q = self.ext() in self.QUALITY_FMTS
        self.quality.setEnabled(has_q)
        if has_q:
            level = "高质量" if q >= 80 else "中等质量" if q >= 50 else "低质量"
            self.q_label.setText(f"{q}%（{level}）")
        else:
            self.q_label.setText("无损格式")
        self.size_label.setText("计算中…")
        self.timer.start(250)

    def _estimate(self):
        self._token += 1
        tk = self._token
        ext, q, path = self.ext(), self.quality.value(), self.path

        def job():
            if self._im is None:
                self._im = open_pil(path)
            im, _, info, exif = self._im
            return encode_size(im, SAVE_FMT[ext], q, info, exif)

        def done(ok, res):
            if not self._alive or tk != self._token:
                return
            try:
                self.size_label.setText(human_size(res) if ok else "无法估算")
            except RuntimeError:
                pass

        run_bg(self.pool, job, done)

    def _browse(self):
        d = QFileDialog.getExistingDirectory(self, "选择保存路径", self.out.text())
        if d:
            self.out.setText(d)

    def _ok(self):
        name = self.name.text().strip()
        if not name or any(ch in name for ch in '\\/:*?"<>|'):
            QMessageBox.warning(self, "格式转换", "图片名称不能为空，也不能包含 \\ / : * ? \" < > |")
            return
        d = self.out.text().strip()
        if not d:
            QMessageBox.warning(self, "格式转换", "请选择保存路径")
            return
        self.dst = os.path.join(d, name + "." + self.ext())
        if os.path.exists(self.dst):
            if same_path(self.dst, self.path):
                QMessageBox.warning(self, "格式转换", "不能覆盖原图，请换个名称")
                return
            if QMessageBox.question(self, "格式转换", "已有同名文件，覆盖吗？") != QMessageBox.Yes:
                return
        self.accept()

    def done(self, r):
        self._alive = False
        super().done(r)


class ResizeDialog(QDialog):
    def __init__(self, win, w, h, count):
        super().__init__(win)
        self.setWindowTitle("修改图片尺寸")
        self.w0, self.h0 = max(1, w), max(1, h)
        lay = QFormLayout(self)
        lay.setHorizontalSpacing(16)
        lay.setVerticalSpacing(12)
        lay.addRow("当前尺寸：", QLabel(f"{w} × {h}"))
        self.by_pct = QRadioButton("按百分比")
        self.by_px = QRadioButton("按像素")
        self.by_pct.setChecked(True)
        self.pct = QSpinBox()
        self.pct.setRange(1, 1000)
        self.pct.setValue(50)
        self.pct.setSuffix(" %")
        r1 = QHBoxLayout()
        r1.addWidget(self.by_pct)
        r1.addWidget(self.pct)
        r1.addStretch(1)
        lay.addRow("方式：", r1)
        self.sw = QSpinBox()
        self.sh = QSpinBox()
        for s in (self.sw, self.sh):
            s.setRange(1, 100000)
        self.sw.setValue(w)
        self.sh.setValue(h)
        self.keep = QCheckBox("保持比例")
        self.keep.setChecked(True)
        r2 = QHBoxLayout()
        r2.addWidget(self.by_px)
        r2.addWidget(QLabel("宽"))
        r2.addWidget(self.sw)
        r2.addWidget(QLabel("高"))
        r2.addWidget(self.sh)
        r2.addWidget(self.keep)
        lay.addRow("", r2)
        self._lock = False
        self.sw.valueChanged.connect(lambda v: self._sync(True))
        self.sh.valueChanged.connect(lambda v: self._sync(False))
        self.sw.valueChanged.connect(lambda v: self.by_px.setChecked(True))
        self.cur = QRadioButton("当前图片")
        self.all = QRadioButton(f"当前文件夹全部（{count} 张，保持比例时缩放到宽高范围内）")
        self.cur.setChecked(True)
        g = QVBoxLayout()
        g.addWidget(self.cur)
        g.addWidget(self.all)
        lay.addRow("范围：", g)
        self.newfile = QRadioButton("另存为新文件（文件名_修改尺寸）")
        self.overwrite = QRadioButton("覆盖原图")
        self.newfile.setChecked(True)
        g2 = QVBoxLayout()
        g2.addWidget(self.newfile)
        g2.addWidget(self.overwrite)
        lay.addRow("保存：", g2)
        self.quality = QSpinBox()
        self.quality.setRange(1, 100)
        self.quality.setValue(92)
        lay.addRow("质量（JPG/WEBP）：", self.quality)
        bt = QHBoxLayout()
        bt.addStretch(1)
        ok = QPushButton("确定")
        ok.setObjectName("primary")
        ok.clicked.connect(self.accept)
        ca = QPushButton("取消")
        ca.clicked.connect(self.reject)
        bt.addWidget(ok)
        bt.addWidget(ca)
        lay.addRow(bt)

    def _sync(self, from_w):
        if self._lock or not self.keep.isChecked():
            return
        self._lock = True
        if from_w:
            self.sh.setValue(max(1, round(self.sw.value() * self.h0 / self.w0)))
        else:
            self.sw.setValue(max(1, round(self.sh.value() * self.w0 / self.h0)))
        self._lock = False

    def target_size(self, w, h):
        if self.by_pct.isChecked():
            f = self.pct.value() / 100
            return max(1, round(w * f)), max(1, round(h * f))
        tw, th = self.sw.value(), self.sh.value()
        if self.all.isChecked() and self.keep.isChecked():
            f = min(tw / w, th / h)
            return max(1, round(w * f)), max(1, round(h * f))
        return tw, th


# ---------------------------------------------------------------- 打印
PAPERS = [("A4", QPageSize.PageSizeId.A4, None), ("A5", QPageSize.PageSizeId.A5, None),
          ("A6", QPageSize.PageSizeId.A6, None), ("Letter", QPageSize.PageSizeId.Letter, None),
          ("6寸照片（4×6 英寸）", None, (4, 6)), ("5寸照片（3.5×5 英寸）", None, (3.5, 5)),
          ("7寸照片（5×7 英寸）", None, (5, 7))]


def paint_print(printer, img, per_page=1, fit="fit", margin_mm=5.0):
    if img is None or img.isNull():
        return
    painter = QPainter(printer)
    painter.setRenderHint(QPainter.SmoothPixmapTransform)
    res = printer.resolution()
    page = printer.pageLayout().paintRectPixels(res)
    m = margin_mm / 25.4 * res
    area = QRectF(m, m, page.width() - 2 * m, page.height() - 2 * m)
    cols, rows = {1: (1, 1), 2: (1, 2), 4: (2, 2), 6: (2, 3), 9: (3, 3)}.get(per_page, (1, 1))
    if area.width() > area.height():
        cols, rows = rows, cols
    gap = 2 / 25.4 * res if per_page > 1 else 0
    cw = (area.width() - gap * (cols - 1)) / cols
    ch = (area.height() - gap * (rows - 1)) / rows
    iw, ih = img.width(), img.height()
    for i in range(cols * rows):
        c, r = i % cols, i // cols
        cell = QRectF(area.x() + c * (cw + gap), area.y() + r * (ch + gap), cw, ch)
        if fit == "actual":
            dpm = img.dotsPerMeterX() or 3780
            f = res / (dpm * 0.0254)
            w, h = iw * f, ih * f
        elif fit == "fill":
            f = max(cw / iw, ch / ih)
            w, h = iw * f, ih * f
        else:
            f = min(cw / iw, ch / ih)
            w, h = iw * f, ih * f
        target = QRectF(cell.x() + (cw - w) / 2, cell.y() + (ch - h) / 2, w, h)
        painter.save()
        painter.setClipRect(cell)
        painter.drawImage(target, img)
        painter.restore()
    painter.end()


class PrintDialog(QDialog):
    def __init__(self, win, img):
        super().__init__(win)
        self.setWindowTitle("高级打印")
        self.img = img
        lay = QFormLayout(self)
        lay.setHorizontalSpacing(16)
        lay.setVerticalSpacing(10)
        self.printer_box = QComboBox()
        names = QPrinterInfo.availablePrinterNames()
        default = QPrinterInfo.defaultPrinterName()
        self.printer_box.addItems(names)
        if default in names:
            self.printer_box.setCurrentText(default)
        lay.addRow("打印机：", self.printer_box)
        self.paper = QComboBox()
        for t, _, _ in PAPERS:
            self.paper.addItem(t)
        lay.addRow("纸张：", self.paper)
        self.orient = QComboBox()
        self.orient.addItems(["纵向", "横向"])
        if img is not None and img.width() > img.height():
            self.orient.setCurrentIndex(1)
        lay.addRow("方向：", self.orient)
        self.per = QComboBox()
        for n in (1, 2, 4, 6, 9):
            self.per.addItem(f"每页 {n} 张", n)
        lay.addRow("排版：", self.per)
        self.fit = QComboBox()
        self.fit.addItem("适应纸张（完整显示）", "fit")
        self.fit.addItem("铺满纸张（裁掉多余）", "fill")
        self.fit.addItem("原始尺寸", "actual")
        lay.addRow("缩放：", self.fit)
        self.margin = QSpinBox()
        self.margin.setRange(0, 50)
        self.margin.setValue(5)
        self.margin.setSuffix(" mm")
        lay.addRow("页边距：", self.margin)
        self.copies = QSpinBox()
        self.copies.setRange(1, 99)
        lay.addRow("份数：", self.copies)
        bt = QHBoxLayout()
        pv = QPushButton("预览")
        pv.clicked.connect(self.preview)
        ok = QPushButton("打印")
        ok.setObjectName("primary")
        ok.clicked.connect(self.do_print)
        ca = QPushButton("取消")
        ca.clicked.connect(self.reject)
        bt.addWidget(pv)
        bt.addStretch(1)
        bt.addWidget(ok)
        bt.addWidget(ca)
        lay.addRow(bt)
        if not names:
            ok.setEnabled(False)
            lay.addRow("", QLabel("没有找到打印机"))

    def make_printer(self):
        pr = QPrinter(QPrinter.HighResolution)
        if self.printer_box.currentText():
            pr.setPrinterName(self.printer_box.currentText())
        _, pid, inch = PAPERS[self.paper.currentIndex()]
        if pid is not None:
            pr.setPageSize(QPageSize(pid))
        else:
            pr.setPageSize(QPageSize(QSizeF(*inch), QPageSize.Unit.Inch, self.paper.currentText(),
                                     QPageSize.SizeMatchPolicy.ExactMatch))
        pr.setPageOrientation(QPageLayout.Orientation.Landscape if self.orient.currentIndex() == 1
                              else QPageLayout.Orientation.Portrait)
        pr.setCopyCount(self.copies.value())
        return pr

    def _paint(self, pr):
        paint_print(pr, self.img, self.per.currentData(), self.fit.currentData(), self.margin.value())

    def preview(self):
        pr = self.make_printer()
        dlg = QPrintPreviewDialog(pr, self)
        dlg.setWindowTitle("打印预览")
        dlg.paintRequested.connect(self._paint)
        dlg.resize(900, 700)
        dlg.exec()

    def do_print(self):
        self._paint(self.make_printer())
        self.accept()


# ---------------------------------------------------------------- 编辑
SHOT_COLORS = ["#ff3b30", "#ff9500", "#ffcc00", "#34c759", "#1e90ff", "#af52de", "#ffffff", "#000000"]
SHOT_SIZES = [(2, 16, "细"), (4, 22, "中"), (7, 30, "粗")]  # (线宽, 文字像素, 名称)
_OCR = None


def tool_icon(name, color="#3a3f47"):
    s = 24
    pm = QPixmap(s * 2, s * 2)
    pm.setDevicePixelRatio(2)
    pm.fill(Qt.transparent)
    p = QPainter(pm)
    p.setRenderHint(QPainter.Antialiasing)
    p.setPen(QPen(QColor(color), 1.8, Qt.SolidLine, Qt.RoundCap, Qt.RoundJoin))
    p.setBrush(Qt.NoBrush)
    P = QPointF
    if name == "rect":
        p.drawRoundedRect(QRectF(5, 6, 14, 12), 1.5, 1.5)
    elif name == "ellipse":
        p.drawEllipse(QRectF(4, 5, 16, 14))
    elif name == "arrow":
        p.drawLine(P(6, 18), P(18, 6))
        p.drawPolyline(QPolygonF([P(11, 6), P(18, 6), P(18, 13)]))
    elif name == "pen":
        p.drawPolygon(QPolygonF([P(6, 17), P(7, 13.5), P(15.5, 5), P(19, 8.5), P(10.5, 17)]))
        p.drawLine(P(5, 20.5), P(19, 20.5))
    elif name == "mosaic":
        p.drawRect(QRectF(5, 5, 14, 14))
        p.setBrush(QColor(color))
        p.drawRect(QRectF(7, 7, 4.5, 4.5))
        p.drawRect(QRectF(12.5, 12.5, 4.5, 4.5))
    elif name == "text":
        f = QFont()
        f.setPixelSize(18)
        p.setFont(f)
        p.drawText(QRectF(0, 0, s, s), Qt.AlignCenter, "T")
    elif name == "watermark":
        for i in range(4):
            x = 3 + i * 4.5
            p.drawLine(P(x, 19), P(x + 6, 6))
    elif name == "pin":
        p.drawLine(P(12, 14), P(12, 21))
        p.drawPolygon(QPolygonF([P(8, 4), P(16, 4), P(15, 6), P(15, 10), P(18, 14), P(6, 14), P(9, 10), P(9, 6)]))
    elif name == "ocr":
        for x, y, dx, dy in ((4, 4, 1, 1), (20, 4, -1, 1), (4, 20, 1, -1), (20, 20, -1, -1)):
            p.drawPolyline(QPolygonF([P(x, y + 4 * dy), P(x, y), P(x + 4 * dx, y)]))
        p.drawLine(P(8.5, 8.5), P(15.5, 8.5))
        p.drawLine(P(12, 8.5), P(12, 16))
    elif name == "undo":
        path = QPainterPath(P(7, 9))
        path.lineTo(14, 9)
        path.cubicTo(P(20.5, 9), P(20.5, 19), P(14, 19))
        path.lineTo(8, 19)
        p.drawPath(path)
        p.drawPolyline(QPolygonF([P(10.5, 5.5), P(7, 9), P(10.5, 12.5)]))
    elif name == "save":
        p.drawLine(P(12, 4), P(12, 15))
        p.drawPolyline(QPolygonF([P(7.5, 10.5), P(12, 15), P(16.5, 10.5)]))
        p.drawPolyline(QPolygonF([P(5, 15), P(5, 20), P(19, 20), P(19, 15)]))
    elif name == "close":
        p.drawLine(P(6, 6), P(18, 18))
        p.drawLine(P(18, 6), P(6, 18))
    elif name == "ok":
        p.drawPolyline(QPolygonF([P(5, 12.5), P(10, 17.5), P(19, 7)]))
    elif name == "grip":
        p.setPen(Qt.NoPen)
        p.setBrush(QColor(color))
        for x in (9, 15):
            for y in (6, 10, 14, 18):
                p.drawEllipse(P(x, y), 1.3, 1.3)
    p.end()
    return QIcon(pm)


def color_icon(color, size_idx):
    s = 24
    pm = QPixmap(s * 2, s * 2)
    pm.setDevicePixelRatio(2)
    pm.fill(Qt.transparent)
    p = QPainter(pm)
    p.setRenderHint(QPainter.Antialiasing)
    p.setPen(QPen(QColor("#8b929c"), 1.5))
    p.setBrush(Qt.NoBrush)
    p.drawEllipse(QRectF(3, 3, 18, 18))
    r = (3, 5, 7)[size_idx]
    p.setPen(Qt.NoPen)
    p.setBrush(QColor(color))
    p.drawEllipse(QPointF(12, 12), r, r)
    p.end()
    return QIcon(pm)


def paint_arrow(p, a, b, color, w):
    dx, dy = b.x() - a.x(), b.y() - a.y()
    length = math.hypot(dx, dy)
    if length < 2:
        return
    ux, uy = dx / length, dy / length
    head = max(12.0, w * 4.0)
    base = QPointF(b.x() - ux * head, b.y() - uy * head)
    px, py = -uy * head * 0.45, ux * head * 0.45
    p.setPen(QPen(QColor(color), w, Qt.SolidLine, Qt.RoundCap, Qt.RoundJoin))
    p.drawLine(a, QPointF(base.x() + ux, base.y() + uy))
    p.setPen(Qt.NoPen)
    p.setBrush(QColor(color))
    p.drawPolygon(QPolygonF([b, QPointF(base.x() + px, base.y() + py), QPointF(base.x() - px, base.y() - py)]))
    p.setBrush(Qt.NoBrush)


def paint_watermark(p, rect, wm, family, unit=1.0):
    text = wm.get("text") or ""
    if not text:
        return
    p.save()
    p.setClipRect(rect)
    p.setOpacity(max(0.05, min(1.0, wm["opacity"] / 100)))
    f = QFont(family)
    px = max(1, round(wm["size"] * unit))
    f.setPixelSize(px)
    p.setFont(f)
    p.setPen(QColor(wm["color"]))
    fm = QFontMetrics(f)
    tw = fm.horizontalAdvance(text) + px * 3
    th = px * 4
    c = rect.center()
    p.translate(c)
    p.rotate(-float(wm["angle"]))
    diag = math.hypot(rect.width(), rect.height()) / 2 + tw
    y, row = -diag, 0
    while y < diag:
        x = -diag + (tw / 2 if row % 2 else 0)
        while x < diag:
            p.drawText(QPointF(x, y), text)
            x += tw
        y += th
        row += 1
    p.restore()


def run_ocr(img):
    global _OCR
    try:
        from rapidocr_onnxruntime import RapidOCR
    except ImportError:
        raise RuntimeError("文字识别需要安装：pip install rapidocr_onnxruntime")
    if _OCR is None:
        _OCR = RapidOCR()
    ba = QByteArray()
    buf = QBuffer(ba)
    buf.open(QIODevice.WriteOnly)
    img.save(buf, "PNG")
    buf.close()
    result, _ = _OCR(bytes(ba))
    if not result:
        return ""
    items = []
    for box, text, _score in result:
        ys = [pt[1] for pt in box]
        xs = [pt[0] for pt in box]
        items.append((min(ys), max(ys), min(xs), text))
    items.sort(key=lambda t: (t[0], t[2]))
    lines = []
    for it in items:
        if lines and abs(it[0] - lines[-1][0]) < (it[1] - it[0]) * 0.5:
            lines[-1][1].append(it)
        else:
            lines.append([it[0], [it]])
    return "\n".join(" ".join(t[3] for t in sorted(l[1], key=lambda t: t[2])) for l in lines)


def qimage_to_pil(img):
    has_alpha = img.hasAlphaChannel()
    q = img.convertToFormat(QImage.Format_RGBA8888)
    data = bytes(q.constBits())
    im = Image.frombuffer("RGBA", (q.width(), q.height()), data, "raw", "RGBA", q.bytesPerLine(), 1).copy()
    return im if has_alpha else im.convert("RGB")


def file_meta(path, reset_orient):
    try:
        with Image.open(path) as im:
            info = dict(im.info)
            exif = im.getexif()
        if reset_orient:
            exif[0x0112] = 1
        return info, exif
    except Exception:
        return {}, None


def add_shadow(w):
    from PySide6.QtWidgets import QGraphicsDropShadowEffect
    eff = QGraphicsDropShadowEffect(w)
    eff.setBlurRadius(24)
    eff.setOffset(0, 4)
    eff.setColor(QColor(0, 0, 0, 45))
    w.setGraphicsEffect(eff)


class FloatBar(QFrame):
    """白色悬浮工具栏"""

    def __init__(self, parent):
        super().__init__(parent)
        self.setObjectName("floatbar")
        self.setAttribute(Qt.WA_StyledBackground)
        self.lay = QHBoxLayout(self)
        self.lay.setContentsMargins(10, 6, 10, 6)
        self.lay.setSpacing(2)
        add_shadow(self)

    def btn(self, text, tip, fn, icon=None, checkable=False, primary=False):
        b = QToolButton()
        b.setText(text)
        b.setToolTip(tip)
        b.setFocusPolicy(Qt.NoFocus)
        b.setCheckable(checkable)
        if icon is not None:
            b.setIcon(icon)
            b.setIconSize(QSize(22, 22))
            b.setToolButtonStyle(Qt.ToolButtonIconOnly if not text else Qt.ToolButtonTextBesideIcon)
        if primary:
            b.setObjectName("primarybtn")
        b.clicked.connect(lambda _=False: fn())
        self.lay.addWidget(b)
        return b

    def sep(self):
        s = QFrame()
        s.setObjectName("sep")
        s.setFixedSize(1, 24)
        self.lay.addSpacing(4)
        self.lay.addWidget(s)
        self.lay.addSpacing(4)


class EditToolbar(FloatBar):
    def __init__(self, ev):
        super().__init__(ev)
        self.ev = ev
        self.color_btn = self.btn("", "颜色和粗细", ev.show_style_popup, icon=QIcon())
        self.sep()
        self.tool_btns = {}
        for key, name in (("rect", "矩形"), ("ellipse", "椭圆"), ("arrow", "箭头"), ("pen", "画笔"),
                          ("mosaic", "马赛克"), ("text", "文字")):
            self.tool_btns[key] = self.btn(name, name, lambda k=key: ev.set_tool(k), checkable=True)
        self.wm_btn = self.btn("水印", "水印：文字、颜色、透明度、角度", ev.edit_watermark, checkable=True)
        self.sep()
        self.btn("钉在桌面", "把图片钉在桌面最前面", ev.pin)
        self.btn("文字识别", "离线识别图片里的文字", ev.ocr)
        self.sep()
        self.btn("撤销", "撤销（Ctrl+Z）", ev.undo)
        self.btn("另存为", "另存为（Ctrl+Shift+S）", ev.save_as)
        self.btn("保存", "保存并覆盖原图（Ctrl+S）", ev.save, primary=True)
        self.btn("退出编辑", "退出编辑（Esc）", ev.exit)
        self.refresh()

    def refresh(self):
        self.color_btn.setIcon(color_icon(self.ev.color, self.ev.size_idx))
        for k, b in self.tool_btns.items():
            b.setChecked(k == self.ev.tool)
        self.wm_btn.setChecked(bool(self.ev.watermark))


class StylePopup(QFrame):
    def __init__(self, ev):
        super().__init__(ev, Qt.Popup | Qt.FramelessWindowHint)
        self.ev = ev
        self.setObjectName("more")
        self.setAttribute(Qt.WA_StyledBackground)
        lay = QVBoxLayout(self)
        lay.setContentsMargins(10, 10, 10, 10)
        row = QHBoxLayout()
        row.setSpacing(4)
        for i, (_, _, name) in enumerate(SHOT_SIZES):
            b = QPushButton(name)
            b.setCheckable(True)
            b.setChecked(i == ev.size_idx)
            b.clicked.connect(lambda _=False, i=i: self._pick(size=i))
            row.addWidget(b)
        lay.addLayout(row)
        grid = QGridLayout()
        grid.setSpacing(6)
        for i, c in enumerate(SHOT_COLORS):
            b = QToolButton()
            b.setFixedSize(28, 28)
            border = "#1f2328" if c == ev.color else "#c9ced5"
            b.setStyleSheet(f"QToolButton{{background:{c};border:2px solid {border};border-radius:4px}}")
            b.clicked.connect(lambda _=False, c=c: self._pick(color=c))
            grid.addWidget(b, i // 4, i % 4)
        more = QPushButton("自定义颜色…")
        more.clicked.connect(self._custom)
        lay.addLayout(grid)
        lay.addWidget(more)

    def _custom(self):
        c = QColorDialog.getColor(QColor(self.ev.color), self.ev, "选择颜色")
        if c.isValid():
            self._pick(color=c.name())

    def _pick(self, color=None, size=None):
        if color:
            self.ev.color = color
        if size is not None:
            self.ev.size_idx = size
        self.ev.style_changed()
        self.close()


class WatermarkDialog(QDialog):
    def __init__(self, ev, wm):
        super().__init__(ev)
        self.setWindowTitle("水印")
        self.ev = None
        self.wm = dict(wm)
        lay = QFormLayout(self)
        lay.setHorizontalSpacing(14)
        lay.setVerticalSpacing(10)
        self.text = QLineEdit(self.wm["text"])
        lay.addRow("文字：", self.text)
        self.color_btn = QPushButton()
        self.color_btn.setFixedSize(60, 26)
        self.color_btn.clicked.connect(self._color)
        self._paint_color()
        lay.addRow("颜色：", self.color_btn)
        r = QHBoxLayout()
        self.op = QSlider(Qt.Horizontal)
        self.op.setRange(5, 100)
        self.op.setValue(int(self.wm["opacity"]))
        self.op_label = QLabel(f"{self.op.value()}%")
        self.op.valueChanged.connect(lambda v: (self.op_label.setText(f"{v}%"), self._live()))
        r.addWidget(self.op, 1)
        r.addWidget(self.op_label)
        lay.addRow("不透明度：", r)
        self.size = QSpinBox()
        self.size.setRange(8, 300)
        self.size.setValue(int(self.wm["size"]))
        lay.addRow("字号：", self.size)
        self.angle = QSpinBox()
        self.angle.setRange(-90, 90)
        self.angle.setValue(int(self.wm["angle"]))
        self.angle.setSuffix(" °")
        lay.addRow("角度：", self.angle)
        for w in (self.size, self.angle):
            w.valueChanged.connect(lambda _: self._live())
        self.text.textChanged.connect(lambda _: self._live())
        bt = QHBoxLayout()
        clear = QPushButton("去掉水印")
        clear.clicked.connect(lambda: self.done(2))
        ok = QPushButton("确定")
        ok.setObjectName("primary")
        ok.clicked.connect(self.accept)
        ca = QPushButton("取消")
        ca.clicked.connect(self.reject)
        bt.addWidget(clear)
        bt.addStretch(1)
        bt.addWidget(ok)
        bt.addWidget(ca)
        lay.addRow(bt)
        self.ev = ev

    def _paint_color(self):
        self.color_btn.setStyleSheet(f"background:{self.wm['color']};border:1px solid #c9ced5;border-radius:4px")

    def _color(self):
        c = QColorDialog.getColor(QColor(self.wm["color"]), self, "水印颜色")
        if c.isValid():
            self.wm["color"] = c.name()
            self._paint_color()
            self._live()

    def result_wm(self):
        self.wm.update(text=self.text.text(), opacity=self.op.value(), size=self.size.value(),
                       angle=self.angle.value())
        return self.wm

    def _live(self):
        if self.ev is not None:
            self.ev.watermark = dict(self.result_wm())
            self.ev.update()


class EditView(QWidget):
    """在当前图片上标注：所有标注都以图片像素坐标保存，保存时按原图分辨率输出"""

    def __init__(self, win, img, path):
        super().__init__()
        self.win = win
        self.path = path
        self.img = img
        self.pix = QPixmap.fromImage(img)
        w, h = img.width(), img.height()
        block = max(6, round(max(w, h) / 110))
        small = self.pix.scaled(max(1, w // block), max(1, h // block), Qt.IgnoreAspectRatio, Qt.FastTransformation)
        self.mosaic = small.scaled(w, h, Qt.IgnoreAspectRatio, Qt.FastTransformation)
        self.img_rect = QRectF(0, 0, w, h)
        self.items = []
        self.cur = None
        self.tool = None
        self.color = win.cfg.get("shot_color", "#ff3b30")
        self.size_idx = int(win.cfg.get("shot_size", 1)) % 3
        self.watermark = None
        self.text_edit = None
        self.dirty = False
        self.k = 1.0
        self.off = QPointF()
        self.setMouseTracking(True)
        self.setFocusPolicy(Qt.StrongFocus)
        self.bar = EditToolbar(self)

    # ---- 布局
    def resizeEvent(self, e):
        self.commit_text()
        W, H = self.width(), self.height()
        aw, ah = max(1, W - 48), max(1, H - 24 - 96)
        dpr = self.devicePixelRatioF()
        self.k = min(1.0 / dpr, aw / self.img_rect.width(), ah / self.img_rect.height())
        dw, dh = self.img_rect.width() * self.k, self.img_rect.height() * self.k
        self.off = QPointF((W - dw) / 2, 24 + (ah - dh) / 2)
        self.bar.adjustSize()
        self.bar.move(max(0, (W - self.bar.width()) // 2), H - self.bar.height() - 16)
        self.bar.raise_()

    def to_img(self, pos):
        return QPointF((pos.x() - self.off.x()) / self.k, (pos.y() - self.off.y()) / self.k)

    def to_view(self, pt):
        return QPointF(pt.x() * self.k + self.off.x(), pt.y() * self.k + self.off.y())

    def clamp(self, pt):
        r = self.img_rect
        return QPointF(min(max(pt.x(), 0.0), r.width()), min(max(pt.y(), 0.0), r.height()))

    # ---- 工具
    def set_tool(self, k):
        self.commit_text()
        self.tool = None if self.tool == k else k
        self.bar.refresh()
        self.setCursor(Qt.IBeamCursor if self.tool == "text" else Qt.CrossCursor if self.tool else Qt.ArrowCursor)

    def show_style_popup(self):
        pop = StylePopup(self)
        pop.adjustSize()
        g = self.bar.mapToGlobal(QPoint(0, 0))
        pop.move(g.x(), g.y() - pop.height() - 6)
        pop.show()

    def style_changed(self):
        self.win.cfg["shot_color"] = self.color
        self.win.cfg["shot_size"] = self.size_idx
        save_cfg(self.win.cfg)
        if self.text_edit is not None:
            self._style_text_edit()
        self.bar.refresh()

    def edit_watermark(self):
        self.commit_text()
        cfg = self.win.cfg
        old = self.watermark
        base = dict(old) if old else {"text": cfg["wm_text"], "color": cfg["wm_color"], "opacity": cfg["wm_opacity"],
                                      "size": cfg["wm_size"], "angle": cfg["wm_angle"], "unit": 1.0 / self.k}
        self.watermark = dict(base)
        self.update()
        dlg = WatermarkDialog(self, base)
        r = dlg.exec()
        if r == QDialog.Accepted:
            wm = dlg.result_wm()
            self.watermark = wm if wm["text"] else None
            cfg.update(wm_text=wm["text"], wm_color=wm["color"], wm_opacity=wm["opacity"], wm_size=wm["size"],
                       wm_angle=wm["angle"])
            save_cfg(cfg)
            self.dirty = True
        elif r == 2:
            self.watermark = None
            self.dirty = True
        else:
            self.watermark = old
        self.bar.refresh()
        self.update()
        self.setFocus()

    def undo(self):
        if self.text_edit is not None:
            self._drop_text_edit()
        elif self.items:
            self.items.pop()
        elif self.watermark:
            self.watermark = None
            self.bar.refresh()
        self.update()

    # ---- 文字
    def _style_text_edit(self):
        px = SHOT_SIZES[self.size_idx][1]
        f = QFont(self.font().family())
        f.setPixelSize(px)
        self.text_edit.setFont(f)
        self.text_edit.setStyleSheet(f"QLineEdit{{background:rgba(255,255,255,90);color:{self.color};"
                                     f"border:1px dashed {self.color};padding:0px;margin:0px}}")
        self.text_edit.setFixedHeight(QFontMetrics(f).height() + 6)
        self._fit_text_edit()

    def _fit_text_edit(self):
        if self.text_edit is None:
            return
        fm = QFontMetrics(self.text_edit.font())
        self.text_edit.setFixedWidth(max(60, fm.horizontalAdvance(self.text_edit.text() + "  ") + 12))

    def start_text(self, pos):
        self.commit_text()
        e = QLineEdit(self)
        e.setFrame(False)
        self.text_edit = e
        self._style_text_edit()
        e.move(int(pos.x()), int(pos.y()))
        e.textChanged.connect(lambda _: self._fit_text_edit())
        e.returnPressed.connect(self.commit_text)
        e.show()
        e.setFocus()

    def _drop_text_edit(self):
        if self.text_edit is not None:
            self.text_edit.hide()
            self.text_edit.deleteLater()
            self.text_edit = None
            self.setFocus()

    def commit_text(self):
        e = self.text_edit
        if e is None:
            return
        text = e.text()
        if text.strip():
            self.items.append({"t": "text", "pos": self.to_img(QPointF(e.pos()) + QPointF(4, 3)), "text": text,
                               "c": self.color, "px": SHOT_SIZES[self.size_idx][1] / self.k})
            self.dirty = True
        self._drop_text_edit()
        self.update()

    # ---- 绘制（图片坐标）
    def paint_items(self, p):
        p.save()
        p.setClipRect(self.img_rect)
        p.setRenderHint(QPainter.Antialiasing)
        for it in self.items + ([self.cur] if self.cur else []):
            t = it["t"]
            if t == "mosaic":
                st = QPainterPathStroker()
                st.setWidth(it["w"])
                st.setCapStyle(Qt.RoundCap)
                st.setJoinStyle(Qt.RoundJoin)
                p.save()
                p.setClipPath(st.createStroke(it["path"]), Qt.IntersectClip)
                p.drawPixmap(self.img_rect, self.mosaic, QRectF(self.mosaic.rect()))
                p.restore()
            elif t == "text":
                f = QFont(self.font().family())
                f.setPixelSize(max(1, round(it["px"])))
                p.setFont(f)
                p.setPen(QColor(it["c"]))
                p.drawText(QRectF(it["pos"], QSizeF(100000, it["px"] * 2)), Qt.AlignLeft | Qt.AlignTop, it["text"])
            else:
                p.setPen(QPen(QColor(it["c"]), it["w"], Qt.SolidLine, Qt.RoundCap, Qt.RoundJoin))
                p.setBrush(Qt.NoBrush)
                if t == "rect":
                    p.drawRect(it["r"].normalized())
                elif t == "ellipse":
                    p.drawEllipse(it["r"].normalized())
                elif t == "pen":
                    p.drawPath(it["path"])
                elif t == "arrow":
                    paint_arrow(p, it["a"], it["b"], it["c"], it["w"])
        if self.watermark:
            paint_watermark(p, self.img_rect, self.watermark, self.font().family(), self.watermark.get("unit", 1.0))
        p.restore()

    def paintEvent(self, e):
        p = QPainter(self)
        p.fillRect(self.rect(), QColor("#eef0f3"))
        p.save()
        p.translate(self.off)
        p.scale(self.k, self.k)
        p.setRenderHint(QPainter.SmoothPixmapTransform)
        p.drawPixmap(self.img_rect, self.pix, QRectF(self.pix.rect()))
        self.paint_items(p)
        p.restore()
        p.setPen(QPen(QColor("#1e6fe8"), 1.5))
        p.drawRect(QRectF(self.off, QSizeF(self.img_rect.width() * self.k, self.img_rect.height() * self.k)))
        if not self.tool and not self.items and not self.watermark:
            p.setPen(QColor("#5b636e"))
            p.drawText(QRectF(0, 0, self.width(), 22), Qt.AlignCenter, "先在下方选一个工具，再在图片上拖动")
        p.end()

    # ---- 鼠标
    def mousePressEvent(self, e):
        pos = e.position()
        if e.button() == Qt.RightButton:
            if self.tool:
                self.set_tool(self.tool)
            return
        if e.button() != Qt.LeftButton or not self.tool:
            return
        ip = self.to_img(pos)
        if not self.img_rect.contains(ip):
            return
        if self.tool == "text":
            self.start_text(pos)
            return
        self.commit_text()
        c, w = self.color, SHOT_SIZES[self.size_idx][0] / self.k
        if self.tool in ("rect", "ellipse"):
            self.cur = {"t": self.tool, "r": QRectF(ip, ip), "c": c, "w": w}
        elif self.tool == "arrow":
            self.cur = {"t": "arrow", "a": ip, "b": ip, "c": c, "w": w}
        else:
            path = QPainterPath(ip)
            path.lineTo(ip + QPointF(0.1, 0.1))
            self.cur = {"t": self.tool, "path": path, "c": c, "w": w if self.tool == "pen" else w * 6}
        self.update()

    def mouseMoveEvent(self, e):
        if not self.cur:
            return
        q = self.clamp(self.to_img(e.position()))
        if self.cur["t"] in ("rect", "ellipse"):
            self.cur["r"] = QRectF(self.cur["r"].topLeft(), q)
        elif self.cur["t"] == "arrow":
            self.cur["b"] = q
        else:
            self.cur["path"].lineTo(q)
        self.update()

    def mouseReleaseEvent(self, e):
        if e.button() != Qt.LeftButton or not self.cur:
            return
        it, self.cur = self.cur, None
        ok = True
        if it["t"] in ("rect", "ellipse"):
            r = it["r"].normalized()
            ok = r.width() * self.k > 2 and r.height() * self.k > 2
        elif it["t"] == "arrow":
            ok = math.hypot(it["b"].x() - it["a"].x(), it["b"].y() - it["a"].y()) * self.k > 3
        if ok:
            self.items.append(it)
            self.dirty = True
        self.update()

    def keyPressEvent(self, e):
        k = e.key()
        mod = e.modifiers()
        ctrl = bool(mod & Qt.ControlModifier)
        if k == Qt.Key_Escape:
            if self.text_edit is not None:
                self._drop_text_edit()
            elif self.tool:
                self.set_tool(self.tool)
            else:
                self.exit()
        elif ctrl and k == Qt.Key_Z:
            self.undo()
        elif ctrl and k == Qt.Key_S:
            self.save_as() if mod & Qt.ShiftModifier else self.save()
        e.accept()

    # ---- 输出
    def render(self):
        self.commit_text()
        out = QImage(self.img.width(), self.img.height(), QImage.Format_ARGB32_Premultiplied)
        out.fill(Qt.transparent)
        p = QPainter(out)
        p.drawPixmap(0, 0, self.pix)
        self.paint_items(p)
        p.end()
        return out

    def _write(self, dst):
        ext = ext_of(dst)
        fmt = SAVE_FMT.get(ext)
        if not fmt:
            raise RuntimeError("不支持保存为 ." + ext)
        im = qimage_to_pil(self.render())
        info, exif = file_meta(self.path, self.win.cfg.get("auto_orient", True)) if Image is not None else ({}, None)
        save_pil(im, dst, fmt, 95, info, exif)

    def save(self):
        self.commit_text()
        if not self.dirty:
            self.win.end_edit()
            return
        ext = ext_of(self.path)
        if ext not in SAVE_FMT or ext in ("gif", "ico") or ext in RAW_EXTS:
            QMessageBox.information(self, "保存", "这个格式不能直接覆盖保存，请另存为。")
            self.save_as()
            return
        try:
            self._write(self.path)
        except Exception as ex:
            QMessageBox.warning(self, "保存失败", str(ex))
            return
        self.dirty = False
        self.win.after_edit_saved(self.path)

    def save_as(self):
        self.commit_text()
        stem, ext = os.path.splitext(self.path)
        if ext_of(self.path) not in SAVE_FMT or ext_of(self.path) in ("gif", "ico"):
            ext = ".png"
        default = unique_path(stem + "_编辑" + ext)
        dst, _ = QFileDialog.getSaveFileName(self, "另存为", default,
                                             "JPG (*.jpg);;PNG (*.png);;WEBP (*.webp);;BMP (*.bmp);;所有文件 (*)")
        if not dst:
            return
        if not ext_of(dst):
            dst += ".png"
        try:
            self._write(dst)
        except Exception as ex:
            QMessageBox.warning(self, "保存失败", str(ex))
            return
        self.dirty = False
        self.win.after_edit_saved(dst, new_file=True)

    def exit(self):
        self.commit_text()
        if self.dirty:
            box = QMessageBox(self)
            box.setWindowTitle("退出编辑")
            box.setText("图片已修改，要保存吗？")
            sv = box.addButton("保存", QMessageBox.AcceptRole)
            ds = box.addButton("不保存", QMessageBox.DestructiveRole)
            box.addButton("取消", QMessageBox.RejectRole)
            box.exec()
            if box.clickedButton() is sv:
                self.save()
                return
            if box.clickedButton() is not ds:
                return
        self.win.end_edit()

    def pin(self):
        img = self.render()
        scr = self.screen() or QGuiApplication.primaryScreen()
        g = scr.availableGeometry()
        scale = min(1.0 / scr.devicePixelRatio(), g.width() * 0.6 / img.width(), g.height() * 0.6 / img.height())
        disp = QSize(round(img.width() * scale), round(img.height() * scale))
        pos = QPoint(g.center().x() - disp.width() // 2, g.center().y() - disp.height() // 2)
        self.win.add_pin(img, pos, 1.0 / scale)

    def ocr(self):
        self.win.show_ocr(self.render())


# ---------------------------------------------------------------- 图片翻译
TR_LANGS = [("auto", "自动检测"), ("zh-CN", "中文（简体）"), ("zh-TW", "中文（繁体）"), ("en", "英语"),
            ("id", "印尼语"), ("ms", "马来语"), ("ja", "日语"), ("ko", "韩语"), ("th", "泰语"), ("vi", "越南语"),
            ("ru", "俄语"), ("fr", "法语"), ("de", "德语"), ("es", "西班牙语"), ("pt", "葡萄牙语"), ("ar", "阿拉伯语"),
            ("hi", "印地语"), ("bn", "孟加拉语")]


def _http_opener(cfg):
    import urllib.request
    p = (cfg.get("proxy") or "").strip()
    if p:
        if "://" not in p:
            p = "http://" + p
        handler = urllib.request.ProxyHandler({"http": p, "https": p})
    else:
        handler = urllib.request.ProxyHandler()  # 跟随系统代理（v2rayN 的“系统代理”）
    return urllib.request.build_opener(handler)


def _gtx(opener, text, sl, tl):
    import urllib.parse
    import urllib.request
    q = urllib.parse.urlencode({"client": "gtx", "sl": sl, "tl": tl, "dt": "t", "q": text})
    req = urllib.request.Request("https://translate.googleapis.com/translate_a/single?" + q,
                                 headers={"User-Agent": "Mozilla/5.0"})
    try:
        with opener.open(req, timeout=20) as r:
            data = json.loads(r.read().decode("utf-8"))
    except Exception as e:
        raise RuntimeError(f"连不上谷歌翻译，请确认代理已开启（{e}）")
    return "".join(seg[0] for seg in (data[0] or []) if seg and seg[0])


def google_translate(lines, sl, tl, cfg):
    """逐行翻译：多行合并成一次请求，按换行拆回；行数对不上时逐行请求"""
    import urllib.parse
    opener = _http_opener(cfg)
    chunks, cur, size = [], [], 0
    for line in lines:
        n = len(urllib.parse.quote(line)) + 3
        if cur and size + n > 5000:
            chunks.append(cur)
            cur, size = [], 0
        cur.append(line)
        size += n
    if cur:
        chunks.append(cur)
    out = []
    for ch in chunks:
        res = _gtx(opener, "\n".join(ch), sl, tl).split("\n")
        if len(res) != len(ch):
            res = [_gtx(opener, l, sl, tl) for l in ch]
        out.extend(r.strip() for r in res)
    return out


def qimage_to_bgr(img):
    import numpy as np
    q = img.convertToFormat(QImage.Format_RGB888)
    w, h, bpl = q.width(), q.height(), q.bytesPerLine()
    arr = np.frombuffer(bytes(q.constBits()), np.uint8).reshape(h, bpl)[:, :w * 3].reshape(h, w, 3)
    return arr[:, :, ::-1].copy()


def ocr_engine():
    global _OCR
    try:
        from rapidocr_onnxruntime import RapidOCR
    except ImportError:
        raise RuntimeError("文字识别需要安装：pip install rapidocr_onnxruntime")
    if _OCR is None:
        _OCR = RapidOCR()
    return _OCR


def ocr_lines(bgr):
    """返回 [(四点坐标, 文字)]，按从上到下、从左到右排序"""
    result, _ = ocr_engine()(bgr)
    out = []
    for box, text, score in (result or []):
        try:
            sc = float(score)
        except Exception:
            sc = 1.0
        if text and text.strip() and sc >= 0.5:
            out.append(([(float(x), float(y)) for x, y in box], text.strip()))
    out.sort(key=lambda t: (min(p[1] for p in t[0]), min(p[0] for p in t[0])))
    return out


def _norm(s):
    return re.sub(r"\s+", "", s).lower()


def erase_text(bgr, boxes):
    """在每个文字框里找出文字像素并用周围背景补上；返回 (补好的图, 每个框的文字颜色 BGR)"""
    import cv2
    import numpy as np
    h, w = bgr.shape[:2]
    gray = cv2.cvtColor(bgr, cv2.COLOR_BGR2GRAY)
    mask = np.zeros((h, w), np.uint8)
    out = bgr.copy()
    colors = []
    for box in boxes:
        pts = np.array(box, np.float32)
        bh = max(4.0, min(np.linalg.norm(pts[0] - pts[3]), np.linalg.norm(pts[1] - pts[2])))
        pad = max(2, int(bh * 0.12))
        m = pad * 2 + 6
        x0, y0 = max(0, int(pts[:, 0].min()) - m), max(0, int(pts[:, 1].min()) - m)
        x1, y1 = min(w, int(pts[:, 0].max()) + m + 1), min(h, int(pts[:, 1].max()) + m + 1)
        if x1 - x0 < 2 or y1 - y0 < 2:
            colors.append((0, 0, 0))
            continue
        poly = np.zeros((y1 - y0, x1 - x0), np.uint8)
        cv2.fillPoly(poly, [np.round(pts - [x0, y0]).astype(np.int32)], 255)
        poly = cv2.dilate(poly, np.ones((pad * 2 + 1, pad * 2 + 1), np.uint8))
        ring = cv2.dilate(poly, np.ones((5, 5), np.uint8)) & ~poly
        g = gray[y0:y1, x0:x1]
        rg = g[ring > 0] if ring.any() else g[poly == 0]
        bg = float(np.median(rg)) if rg.size else float(np.median(g))
        ring_c = bgr[y0:y1, x0:x1][ring > 0] if ring.any() else None
        diff = np.abs(g.astype(np.int16) - bg)
        txt = ((diff > 22) & (poly > 0)).astype(np.uint8) * 255
        if txt.sum() < 255 * 4:
            txt = poly.copy()
        it = 2 if bh < 30 else 3
        txt = cv2.dilate(txt, np.ones((3, 3), np.uint8), iterations=it) & poly
        sel = bgr[y0:y1, x0:x1][(diff > 60) & (poly > 0)]
        if sel.size:
            colors.append(tuple(int(v) for v in np.median(sel, axis=0)))
        else:
            colors.append((0, 0, 0) if bg > 128 else (255, 255, 255))
        if ring_c is not None and ring_c.size and float(ring_c.std(axis=0).max()) < 10:
            # 纯色背景：整块直接填背景色，最干净
            region = out[y0:y1, x0:x1]
            region[poly > 0] = np.median(ring_c, axis=0).astype(np.uint8)
        else:
            mask[y0:y1, x0:x1] |= txt
    if not mask.any():
        return out, colors
    radius = 3 if max(h, w) < 2500 else 5
    return cv2.inpaint(out, mask, radius, cv2.INPAINT_TELEA), colors


def draw_translations(base, items, family):
    """items: [(四点坐标, 译文, (b,g,r))]；在补好的图上原位置画译文"""
    out = base.convertToFormat(QImage.Format_RGB32)
    p = QPainter(out)
    p.setRenderHint(QPainter.Antialiasing)
    p.setRenderHint(QPainter.TextAntialiasing)
    for box, text, (b, g, r) in items:
        (x0, y0), (x1, y1), (x2, y2), (x3, y3) = box
        width = math.hypot(x1 - x0, y1 - y0)
        height = math.hypot(x3 - x0, y3 - y0)
        if width < 2 or height < 2:
            continue
        angle = math.degrees(math.atan2(y1 - y0, x1 - x0))
        f = QFont(family)
        size = max(6, int(height * 0.82))
        f.setPixelSize(size)
        fm = QFontMetrics(f)
        while size > 6 and fm.horizontalAdvance(text) > width * 1.02:
            size = max(6, int(size * 0.92))
            f.setPixelSize(size)
            fm = QFontMetrics(f)
        lines = [text]
        if fm.horizontalAdvance(text) > width * 1.02:  # 太长就分两行
            mid = len(text) // 2
            lines = [text[:mid], text[mid:]]
            size = max(6, int(height * 0.45))
            f.setPixelSize(size)
            fm = QFontMetrics(f)
        p.save()
        p.translate(x0, y0)
        p.rotate(angle)
        p.setFont(f)
        p.setPen(QColor(r, g, b))
        rect = QRectF(0, 0, max(width, fm.horizontalAdvance(max(lines, key=len)) + 2), height)
        p.drawText(rect, Qt.AlignLeft | Qt.AlignVCenter, "\n".join(lines))
        p.restore()
    p.end()
    return out


class TranslateView(QWidget):
    def __init__(self, win, img, path):
        super().__init__()
        self.win = win
        self.path = path
        self.img = img.convertToFormat(QImage.Format_RGB32)
        self.result = None
        self.lines = None  # [(box, text)]
        self.pairs = []
        self.show_result = True
        self.busy = ""
        self.dirty = False
        self._token = 0
        self._bgr = None
        self.k = 1.0
        self.off = QPointF()
        self.setFocusPolicy(Qt.StrongFocus)
        self.pool = QThreadPool(self)
        self.pool.setMaxThreadCount(1)

        self.toggle = FloatBar(self)
        self.btn_src = self.toggle.btn("原图", "看原图（按住空格也可以）", lambda: self.set_view(False), checkable=True)
        self.btn_dst = self.toggle.btn("译文", "看翻译后的图", lambda: self.set_view(True), checkable=True)
        self.btn_dst.setChecked(True)

        self.bar = FloatBar(self)
        self.bar.lay.addWidget(QLabel("从"))
        self.sl = QComboBox()
        for code, name in TR_LANGS:
            self.sl.addItem(name, code)
        self.bar.lay.addWidget(self.sl)
        self.bar.lay.addSpacing(6)
        self.bar.lay.addWidget(QLabel("翻译成"))
        self.tl = QComboBox()
        for code, name in TR_LANGS[1:]:
            self.tl.addItem(name, code)
        self.bar.lay.addWidget(self.tl)
        self.sl.setCurrentIndex(max(0, self.sl.findData(win.cfg.get("tr_sl", "auto"))))
        self.tl.setCurrentIndex(max(0, self.tl.findData(win.cfg.get("tr_tl", "zh-CN"))))
        self.sl.currentIndexChanged.connect(lambda _: self.translate())
        self.tl.currentIndexChanged.connect(lambda _: self.translate())
        self.bar.sep()
        self.bar.btn("复制译文", "复制全部译文文字", self.copy_text)
        self.bar.btn("复制图片", "复制翻译后的图片", self.copy_image)
        self.bar.btn("另存为", "保存翻译后的图片（Ctrl+S）", self.save_as, primary=True)
        self.bar.btn("退出翻译", "退出（Esc）", self.exit)
        self.start()

    # ---- 流程
    def start(self):
        self.busy = "正在识别文字…"
        self.update()
        img = self.img
        tk = self._next()

        def job():
            bgr = qimage_to_bgr(img)
            return bgr, ocr_lines(bgr)

        run_bg(self.pool, job, lambda ok, res, tk=tk: self._ocr_done(tk, ok, res))

    def _next(self):
        self._token += 1
        return self._token

    def _alive(self, tk):
        try:
            return tk == self._token and self.win.editor is self
        except RuntimeError:
            return False

    def _ocr_done(self, tk, ok, res):
        if not self._alive(tk):
            return
        if not ok:
            self._fail(res)
            return
        self._bgr, self.lines = res
        if not self.lines:
            self.busy = ""
            self.win.canvas.toast("没有识别到文字", 2500)
            self.result = None
            self.update()
            return
        self.translate()

    def translate(self):
        if self.lines is None:
            return
        sl, tl = self.sl.currentData(), self.tl.currentData()
        self.win.cfg["tr_sl"], self.win.cfg["tr_tl"] = sl, tl
        save_cfg(self.win.cfg)
        self.busy = "正在翻译…"
        self.update()
        tk = self._next()
        lines, bgr, cfg = list(self.lines), self._bgr, dict(self.win.cfg)

        def job():
            texts = google_translate([t for _, t in lines], sl, tl, cfg)
            pairs = [(box, src, dst) for (box, src), dst in zip(lines, texts)]
            todo = [(box, dst) for box, src, dst in pairs if dst and _norm(dst) != _norm(src)]
            clean, colors = erase_text(bgr, [b for b, _ in todo])
            return pairs, todo, clean, colors

        run_bg(self.pool, job, lambda ok, res, tk=tk: self._tr_done(tk, ok, res))

    def _tr_done(self, tk, ok, res):
        if not self._alive(tk):
            return
        if not ok:
            self._fail(res)
            return
        pairs, todo, clean, colors = res
        self.pairs = pairs
        base = np_to_qimage(clean[:, :, ::-1])
        self.result = draw_translations(base, [(b, t, c) for (b, t), c in zip(todo, colors)], self.font().family())
        self.busy = ""
        self.set_view(True)

    def _fail(self, err):
        self.busy = ""
        self.update()
        QMessageBox.warning(self, "图片翻译", str(err))

    # ---- 显示
    def set_view(self, translated):
        self.show_result = bool(translated) and self.result is not None
        self.btn_dst.setChecked(self.show_result)
        self.btn_src.setChecked(not self.show_result)
        self.update()

    def resizeEvent(self, e):
        W, H = self.width(), self.height()
        aw, ah = max(1, W - 48), max(1, H - 64 - 96)
        dpr = self.devicePixelRatioF()
        self.k = min(1.0 / dpr, aw / self.img.width(), ah / self.img.height())
        dw, dh = self.img.width() * self.k, self.img.height() * self.k
        self.off = QPointF((W - dw) / 2, 64 + (ah - dh) / 2)
        for b, y in ((self.toggle, 12), (self.bar, None)):
            b.adjustSize()
            b.move(max(0, (W - b.width()) // 2), y if y is not None else H - b.height() - 16)
            b.raise_()

    def paintEvent(self, e):
        p = QPainter(self)
        p.fillRect(self.rect(), QColor("#eef0f3"))
        img = self.result if (self.show_result and self.result is not None) else self.img
        p.setRenderHint(QPainter.SmoothPixmapTransform)
        target = QRectF(self.off, QSizeF(self.img.width() * self.k, self.img.height() * self.k))
        p.drawImage(target, img)
        if self.busy:
            f = QFont(self.font().family(), 12)
            p.setFont(f)
            fm = QFontMetrics(f)
            w = fm.horizontalAdvance(self.busy) + 40
            rr = QRectF((self.width() - w) / 2, self.height() / 2 - 22, w, 44)
            p.setRenderHint(QPainter.Antialiasing)
            p.setPen(Qt.NoPen)
            p.setBrush(QColor(0, 0, 0, 170))
            p.drawRoundedRect(rr, 8, 8)
            p.setPen(QColor("white"))
            p.drawText(rr, Qt.AlignCenter, self.busy)
        p.end()

    def keyPressEvent(self, e):
        k = e.key()
        if k == Qt.Key_Escape:
            self.exit()
        elif k == Qt.Key_Space and not e.isAutoRepeat():
            self.set_view(False)
        elif k == Qt.Key_S and e.modifiers() & Qt.ControlModifier:
            self.save_as()
        elif k == Qt.Key_C and e.modifiers() & Qt.ControlModifier:
            self.copy_image()
        e.accept()

    def keyReleaseEvent(self, e):
        if e.key() == Qt.Key_Space and not e.isAutoRepeat():
            self.set_view(True)
        e.accept()

    # ---- 输出
    def copy_text(self):
        if not self.pairs:
            return
        QApplication.clipboard().setText("\n".join(d for _, _, d in self.pairs))
        self.win.canvas.toast("已复制译文", 1500)

    def copy_image(self):
        if self.result is not None:
            QApplication.clipboard().setImage(self.result)
            self.win.canvas.toast("已复制翻译后的图片", 1500)

    def save_as(self):
        if self.result is None:
            return
        stem, ext = os.path.splitext(self.path)
        if ext_of(self.path) not in SAVE_FMT or ext_of(self.path) in ("gif", "ico"):
            ext = ".png"
        tag = "_" + (self.tl.currentText().split("（")[0] or "译文")
        default = unique_path(stem + tag + ext)
        dst, _ = QFileDialog.getSaveFileName(self, "保存翻译后的图片", default,
                                             "JPG (*.jpg);;PNG (*.png);;WEBP (*.webp);;BMP (*.bmp);;所有文件 (*)")
        if not dst:
            return
        if not ext_of(dst):
            dst += ".png"
        try:
            fmt = SAVE_FMT.get(ext_of(dst))
            if not fmt:
                raise RuntimeError("不支持保存为 ." + ext_of(dst))
            info, exif = file_meta(self.path, True) if Image is not None else ({}, None)
            save_pil(qimage_to_pil(self.result), dst, fmt, 95, info, exif)
        except Exception as ex:
            QMessageBox.warning(self, "保存失败", str(ex))
            return
        self.win.after_edit_saved(dst, new_file=True)

    def exit(self):
        self._token += 1
        self.win.end_edit()


class PinWindow(QWidget):
    def __init__(self, win, img, pos, dpr):
        super().__init__(None, Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint | Qt.Tool)
        self.setAttribute(Qt.WA_DeleteOnClose)
        self.win = win
        self.img = img
        self.dpr = dpr or 1.0
        self.zoom = 1.0
        self._drag = None
        self.setWindowTitle("钉图")
        self.setToolTip("拖动移动 · 滚轮缩放 · 双击或 Esc 关闭 · 右键更多")
        self._apply_size()
        self.move(pos)

    def _apply_size(self):
        self.resize(max(20, round(self.img.width() / self.dpr * self.zoom)),
                    max(20, round(self.img.height() / self.dpr * self.zoom)))

    def paintEvent(self, e):
        p = QPainter(self)
        p.setRenderHint(QPainter.SmoothPixmapTransform)
        p.drawImage(QRectF(self.rect()), self.img)
        p.setPen(QPen(QColor("#1e90ff"), 1))
        p.drawRect(QRectF(self.rect()).adjusted(0.5, 0.5, -0.5, -0.5))
        p.end()

    def mousePressEvent(self, e):
        if e.button() == Qt.LeftButton:
            self._drag = e.globalPosition().toPoint() - self.pos()

    def mouseMoveEvent(self, e):
        if self._drag is not None:
            self.move(e.globalPosition().toPoint() - self._drag)

    def mouseReleaseEvent(self, e):
        self._drag = None

    def mouseDoubleClickEvent(self, e):
        self.close()

    def wheelEvent(self, e):
        d = e.angleDelta().y()
        if d:
            self.zoom = max(0.1, min(5.0, self.zoom * (1.1 ** (d / 120))))
            self._apply_size()
            self.update()

    def keyPressEvent(self, e):
        if e.key() == Qt.Key_Escape:
            self.close()
        elif e.key() == Qt.Key_C and e.modifiers() & Qt.ControlModifier:
            QApplication.clipboard().setImage(self.img)

    def contextMenuEvent(self, e):
        m = QMenu(self)
        m.addAction("复制", lambda: QApplication.clipboard().setImage(self.img))
        m.addAction("保存…", self._save)
        m.addAction("原始大小", lambda: (setattr(self, "zoom", 1.0), self._apply_size(), self.update()))
        m.addSeparator()
        m.addAction("关闭", self.close)
        m.exec(e.globalPos())

    def _save(self):
        folder = os.path.join(os.path.expanduser("~"), "Pictures")
        default = unique_path(os.path.join(folder, datetime.now().strftime("钉图_%Y%m%d_%H%M%S.png")))
        dst, _ = QFileDialog.getSaveFileName(self, "保存", default, "PNG (*.png);;JPG (*.jpg)")
        if dst:
            self.img.save(dst if ext_of(dst) else dst + ".png", None, 95)


class OcrDialog(QDialog):
    def __init__(self, win):
        super().__init__(win, Qt.Window)
        self.setWindowTitle("文字识别")
        self.setAttribute(Qt.WA_DeleteOnClose)
        self._alive = True
        lay = QVBoxLayout(self)
        self.edit = QPlainTextEdit()
        self.edit.setPlainText("正在识别…（第一次使用需要几秒加载）")
        self.edit.setStyleSheet("QPlainTextEdit{font-size:14px}")
        lay.addWidget(self.edit, 1)
        bt = QHBoxLayout()
        bt.addStretch(1)
        cp = QPushButton("复制全部")
        cp.setObjectName("primary")
        cp.clicked.connect(lambda: (QApplication.clipboard().setText(self.edit.toPlainText()), cp.setText("已复制")))
        cl = QPushButton("关闭")
        cl.clicked.connect(self.close)
        bt.addWidget(cp)
        bt.addWidget(cl)
        lay.addLayout(bt)
        self.resize(520, 420)

    def set_result(self, ok, res):
        if not self._alive:
            return
        if ok:
            self.edit.setPlainText(res or "（没有识别到文字）")
        else:
            self.edit.setPlainText("识别失败：" + str(res))

    def closeEvent(self, e):
        self._alive = False
        super().closeEvent(e)


# ---------------------------------------------------------------- 幻灯片
class SlideShow(QWidget):
    EFFECTS = ["fade", "slide", "up", "zoom"]

    def __init__(self, win, files, start):
        super().__init__(None, Qt.Window | Qt.FramelessWindowHint)
        self.setWindowTitle("幻灯片")
        self.win = win
        cfg = win.cfg
        self.cfg = cfg
        n = len(files)
        if cfg["ss_order"] == "random":
            rest = [i for i in range(n) if i != start]
            random.shuffle(rest)
            order = [start] + rest
        elif cfg["ss_reverse"]:
            order = [(start - i) % n for i in range(n)]
        else:
            order = [(start + i) % n for i in range(n)]
        self.files, self.order, self.pos = files, order, 0
        self.cur = self.old = None
        self.cur_bg = self.old_bg = None
        self.t = 1.0
        self.effect = "none"
        self.paused = False
        self.anim = QVariantAnimation(self)
        self.anim.setStartValue(0.0)
        self.anim.setEndValue(1.0)
        self.anim.setDuration(700)
        self.anim.valueChanged.connect(self._tick)
        self.timer = QTimer(self)
        self.timer.setInterval(max(1, int(cfg["ss_interval"])) * 1000)
        self.timer.timeout.connect(lambda: self.advance(1))
        self.hint = ""
        self.hint_timer = QTimer(self)
        self.hint_timer.setSingleShot(True)
        self.hint_timer.timeout.connect(self._hide_hint)
        self.setCursor(Qt.BlankCursor)
        self.setMouseTracking(True)
        self._show(first=True)
        self.timer.start()

    def current_path(self):
        return self.files[self.order[self.pos]]

    def _pix(self, path):
        img = self.win.cache_get(path)
        if img is None:
            try:
                img = load_image(path, self.cfg)
                self.win.cache_put(path, img)
            except Exception:
                return None
        return QPixmap.fromImage(img)

    def _bg(self, pix):
        if self.cfg["ss_bg"] != "blur" or pix is None:
            return None
        small = pix.scaled(48, 27, Qt.KeepAspectRatioByExpanding, Qt.SmoothTransformation)
        return small.scaled(self.width() or 1920, self.height() or 1080, Qt.IgnoreAspectRatio,
                            Qt.SmoothTransformation)

    def _show(self, first=False):
        tries = 0
        pix = self._pix(self.current_path())
        while pix is None and tries < len(self.order):
            self.pos = (self.pos + 1) % len(self.order)
            pix = self._pix(self.current_path())
            tries += 1
        self.old, self.old_bg = self.cur, self.cur_bg
        self.cur = pix
        self.cur_bg = self._bg(pix)
        eff = self.cfg["ss_effect"]
        if eff == "random":
            eff = random.choice(self.EFFECTS)
        self.effect = eff
        if first or self.old is None or eff == "none":
            self.t = 1.0
            self.update()
        else:
            self.anim.stop()
            self.anim.start()
        nxt = self.files[self.order[(self.pos + 1) % len(self.order)]]
        self.win.preload(nxt)

    def advance(self, d):
        np_ = self.pos + d
        if np_ >= len(self.order) or np_ < 0:
            if not self.cfg["ss_loop"]:
                self.close()
                return
            np_ %= len(self.order)
        self.pos = np_
        self._show()
        if not self.paused:
            self.timer.start()

    def _tick(self, v):
        self.t = float(v)
        self.update()

    def _hide_hint(self):
        self.hint = ""
        self.setCursor(Qt.BlankCursor)
        self.update()

    def _fit_rect(self, pix):
        dpr = self.devicePixelRatioF()
        W, H = self.width(), self.height()
        w, h = pix.width() / dpr, pix.height() / dpr
        f = min(1.0, W / w, H / h)
        w, h = w * f, h * f
        return QRectF((W - w) / 2, (H - h) / 2, w, h)

    def paintEvent(self, e):
        p = QPainter(self)
        p.setRenderHint(QPainter.SmoothPixmapTransform)
        W = self.width()
        H = self.height()
        bgc = QColor("white") if self.cfg["ss_bg"] == "white" else QColor("black")
        p.fillRect(self.rect(), bgc)
        t = self.t
        if self.cur_bg is not None:
            p.setOpacity(t if self.old_bg is not None else 1)
            p.drawPixmap(self.rect(), self.cur_bg)
            if self.old_bg is not None and t < 1:
                p.setOpacity(1 - t)
                p.drawPixmap(self.rect(), self.old_bg)
            p.setOpacity(1)
            p.fillRect(self.rect(), QColor(0, 0, 0, 90))
        if self.old is not None and t < 1:
            r = self._fit_rect(self.old)
            if self.effect == "fade" or self.effect == "zoom":
                p.setOpacity(1 - t)
                p.drawPixmap(r, self.old, QRectF(self.old.rect()))
            elif self.effect == "slide":
                p.drawPixmap(r.translated(-t * W, 0), self.old, QRectF(self.old.rect()))
            elif self.effect == "up":
                p.drawPixmap(r.translated(0, -t * H), self.old, QRectF(self.old.rect()))
            p.setOpacity(1)
        if self.cur is not None:
            r = self._fit_rect(self.cur)
            if t < 1:
                if self.effect == "fade":
                    p.setOpacity(t)
                elif self.effect == "slide":
                    r = r.translated((1 - t) * W, 0)
                elif self.effect == "up":
                    r = r.translated(0, (1 - t) * H)
                elif self.effect == "zoom":
                    s = 0.85 + 0.15 * t
                    c = r.center()
                    r = QRectF(c.x() - r.width() * s / 2, c.y() - r.height() * s / 2, r.width() * s,
                               r.height() * s)
                    p.setOpacity(t)
            p.drawPixmap(r, self.cur, QRectF(self.cur.rect()))
            p.setOpacity(1)
        if self.hint:
            p.setPen(QColor("white") if bgc == QColor("black") else QColor("black"))
            p.drawText(QRectF(0, H - 50, W, 40), Qt.AlignCenter, self.hint)
        p.end()

    def _show_hint(self, text):
        self.hint = text
        self.setCursor(Qt.ArrowCursor)
        self.hint_timer.start(2000)
        self.update()

    def mouseMoveEvent(self, e):
        self._show_hint(f"{self.pos + 1}/{len(self.order)}   P 暂停 · ←→ / AD 切换 · Esc 退出")

    def mousePressEvent(self, e):
        if e.button() == Qt.RightButton:
            self.close()
        elif e.button() == Qt.LeftButton:
            self.advance(1)

    def keyPressEvent(self, e):
        k = e.key()
        if k in (Qt.Key_Escape, Qt.Key_F5):
            self.close()
        elif k in (Qt.Key_P, Qt.Key_Pause):
            self.paused = not self.paused
            if self.paused:
                self.timer.stop()
                self._show_hint("已暂停")
            else:
                self.timer.start()
                self._show_hint("继续播放")
        elif k in NEXT_KEYS:
            self.advance(1)
        elif k in PREV_KEYS:
            self.advance(-1)

    def closeEvent(self, e):
        self.timer.stop()
        self.anim.stop()
        self.win.on_slideshow_closed(self.current_path())
        super().closeEvent(e)


# ---------------------------------------------------------------- 设置
class Page(QWidget):
    def __init__(self, cfg):
        super().__init__()
        self.cfg = cfg
        self.bindings = []
        self.lay = QVBoxLayout(self)
        self.lay.setContentsMargins(24, 12, 24, 12)
        self.lay.setSpacing(8)

    def section(self, text):
        l = QLabel(text)
        l.setObjectName("sec")
        self.lay.addWidget(l)

    def hint(self, text):
        l = QLabel(text)
        l.setObjectName("hint")
        l.setWordWrap(True)
        l.setContentsMargins(26, 0, 0, 0)
        self.lay.addWidget(l)

    def check(self, key, text, row=None):
        cb = QCheckBox(text)
        cb.setChecked(bool(self.cfg[key]))
        self.bindings.append((key, cb.isChecked, cb.setChecked))
        (row if row is not None else self.lay).addWidget(cb)
        return cb

    def radios(self, key, options, vertical=False):
        box = QVBoxLayout() if vertical else QHBoxLayout()
        box.setSpacing(24 if not vertical else 6)
        grp = QButtonGroup(self)
        btns = {}
        for v, t in options:
            rb = QRadioButton(t)
            grp.addButton(rb)
            btns[v] = rb
            box.addWidget(rb)
        if not vertical:
            box.addStretch(1)

        def get():
            return next((v for v, b in btns.items() if b.isChecked()), options[0][0])

        def put(v):
            (btns.get(v) or btns[options[0][0]]).setChecked(True)

        put(self.cfg[key])
        self.bindings.append((key, get, put))
        self.lay.addLayout(box)
        return btns

    def row(self):
        r = QHBoxLayout()
        r.setSpacing(24)
        self.lay.addLayout(r)
        return r

    def combo(self, key, options, label=None):
        r = QHBoxLayout()
        if label:
            r.addWidget(QLabel(label))
        cb = QComboBox()
        for v, t in options:
            cb.addItem(t, v)

        def get():
            return cb.currentData()

        def put(v):
            i = cb.findData(v)
            cb.setCurrentIndex(max(0, i))

        put(self.cfg[key])
        self.bindings.append((key, get, put))
        r.addWidget(cb)
        r.addStretch(1)
        self.lay.addLayout(r)
        return cb

    def save(self, cfg):
        for key, get, _ in self.bindings:
            cfg[key] = get()

    def restore_defaults(self):
        for key, _, put in self.bindings:
            put(DEFAULTS[key])


class AssocPage(Page):
    def __init__(self, cfg):
        super().__init__(cfg)
        self.section("文件关联（只在你点下面按钮时才修改，不会自动抢默认）")
        self.table = QTableWidget(len(ASSOC_ALL), 3)
        self.table.setHorizontalHeaderLabels(["关联", "文件类型", "当前默认程序"])
        self.table.verticalHeader().setVisible(False)
        self.table.setSelectionMode(QAbstractItemView.NoSelection)
        self.table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        hh = self.table.horizontalHeader()
        hh.setSectionResizeMode(0, QHeaderView.ResizeToContents)
        hh.setSectionResizeMode(1, QHeaderView.ResizeToContents)
        hh.setSectionResizeMode(2, QHeaderView.Stretch)
        for i, e in enumerate(ASSOC_ALL):
            it = QTableWidgetItem()
            it.setFlags(Qt.ItemIsUserCheckable | Qt.ItemIsEnabled)
            self.table.setItem(i, 0, it)
            self.table.setItem(i, 1, QTableWidgetItem(e.upper()))
            self.table.setItem(i, 2, QTableWidgetItem(""))
        self.lay.addWidget(self.table, 1)
        self._put(cfg["assoc_exts"])
        self.bindings.append(("assoc_exts", self._get, self._put))
        self.refresh()
        r = QHBoxLayout()
        a = QPushButton("全选")
        a.clicked.connect(lambda: self._put(ASSOC_ALL))
        n = QPushButton("全不选")
        n.clicked.connect(lambda: self._put([]))
        r.addWidget(a)
        r.addWidget(n)
        r.addStretch(1)
        self.lay.addLayout(r)
        r2 = QHBoxLayout()
        go = QPushButton("把勾选的格式设为用本软件打开…")
        go.setObjectName("primary")
        go.clicked.connect(self.apply_assoc)
        un = QPushButton("取消本软件的关联")
        un.clicked.connect(self.remove_assoc)
        r2.addWidget(go)
        r2.addWidget(un)
        r2.addStretch(1)
        self.lay.addLayout(r2)
        if not IS_WIN:
            go.setEnabled(False)
            un.setEnabled(False)

    def _get(self):
        return [e for i, e in enumerate(ASSOC_ALL) if self.table.item(i, 0).checkState() == Qt.Checked]

    def _put(self, exts):
        for i, e in enumerate(ASSOC_ALL):
            self.table.item(i, 0).setCheckState(Qt.Checked if e in exts else Qt.Unchecked)

    def refresh(self):
        for i, e in enumerate(ASSOC_ALL):
            self.table.item(i, 2).setText(current_default(e))

    def apply_assoc(self):
        exts = self._get()
        if not exts:
            return
        try:
            register_assoc(exts)
        except Exception as ex:
            QMessageBox.warning(self, "关联失败", str(ex))
            return
        QMessageBox.information(
            self, "设置默认程序",
            "已把本软件登记为这些格式的可选程序。\n\n"
            "Windows 不允许软件自己改默认程序，接下来会打开系统的“默认应用”：\n"
            "点“照片查看器”，选“审哥看图王”即可。\n"
            "想逐个格式设置：在同一页往下点“按文件类型指定默认应用”。\n\n"
            "如果还装着 2345看图王，先在它的设置里关掉“图片格式关联保护”，否则它会改回去。")
        try:
            os.startfile("ms-settings:defaultapps")
        except Exception:
            pass
        QTimer.singleShot(3000, self.refresh)

    def remove_assoc(self):
        try:
            unregister_assoc()
        except Exception as ex:
            QMessageBox.warning(self, "失败", str(ex))
            return
        self.refresh()
        QMessageBox.information(self, "完成", "已删除本软件的关联登记。")


SHORTCUTS = [("A / W / ↑ / ← / PageUp", "上一张"), ("D / S / ↓ / → / 空格 / PageDown", "下一张"),
             ("Home / End", "第一张 / 最后一张"), ("滚轮", "缩放（可在习惯设置里改）"),
             ("Ctrl + 滚轮", "缩放"), ("+ / -", "放大 / 缩小"), ("Ctrl+0", "适应窗口"),
             ("Ctrl+1 / 1:1 按钮", "原始大小"), ("拖动图片", "移动图片"), ("双击 / Enter / F11", "全屏切换"),
             ("Esc", "退出全屏 / 取消裁剪 / 关闭"), ("Ctrl+L / Ctrl+R", "左转 / 右转"), ("F5", "幻灯片"),
             ("Del", "删除到回收站"), ("F2", "重命名"), ("I", "图片信息"), ("Ctrl+C", "复制"),
             ("Ctrl+S", "另存为"), ("Ctrl+O", "打开图片"), ("Ctrl+P", "高级打印"), ("Ctrl+E", "修改尺寸"),
             ("Ctrl+Alt+P", "裁剪"), ("E", "编辑（标注 / 马赛克 / 水印 / 文字识别）"), ("T", "图片翻译"), ("Ctrl+T", "缩略图开关"), ("Ctrl+↑ / Ctrl+↓", "多页 TIF 翻页"),
             ("F1", "使用说明")]


class SettingsDialog(QDialog):
    def __init__(self, win):
        super().__init__(win)
        self.win = win
        self.setWindowTitle("设置")
        self.resize(780, 620)
        cfg = dict(win.cfg)
        self.cfg = cfg
        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.setSpacing(0)
        body = QHBoxLayout()
        body.setSpacing(0)
        self.nav = QListWidget()
        self.nav.setObjectName("nav")
        self.nav.setFixedWidth(132)
        self.stack = QStackedWidget()
        body.addWidget(self.nav)
        body.addWidget(self.stack, 1)
        outer.addLayout(body, 1)
        self.pages = []

        g = Page(cfg)
        g.section("辅助看图工具")
        r = g.row()
        g.check("thumbs", "默认显示缩略图", r)
        g.check("multiframe", "启用多帧图片查看（GIF/WEBP 动图、多页 TIF）", r)
        r.addStretch(1)
        r = g.row()
        g.check("pointer_flip", "启用鼠标指针翻页（点窗口左右两侧翻页）", r)
        r.addStretch(1)
        g.check("raw_full", "RAW 文件原图查看")
        g.hint("原图查看会影响 RAW 的显示速度；不勾选时显示相机内嵌预览图")
        g.section("智能旋转数码照片")
        g.check("auto_orient", "按照拍摄时的横竖方向显示照片")
        g.hint("竖着拍的照片会自动转正显示，但不会保存旋转后的照片")
        g.section("全屏背景")
        g.radios("fs_transparent", [(True, "透明（显示桌面）"), (False, "不透明")])
        g.section("图片美化尺寸优化")
        g.radios("edit_downscale", [(True, "缩小到最佳尺寸显示（推荐，更清晰更流畅）"), (False, "直接缩放原图")])
        g.section("文件夹穿透")
        g.check("folder_end_remember", "记住我的选择，当浏览完当前文件夹时")
        g.radios("folder_end_action", [("next", "总是自动前往下一个文件夹"), ("loop", "总是在本文件夹内循环浏览")])
        g.lay.addStretch(1)
        self._add("常规设置", g)

        h = Page(cfg)
        h.section("看图窗口使用习惯")
        r = h.row()
        h.check("on_top", "看图窗口总位于所有窗口最前面", r)
        h.check("multi_window", "允许打开多个看图窗口", r)
        r.addStretch(1)
        h.section("旋转图片")
        h.radios("rotate_original", [(True, "旋转原图（会改变原图）"), (False, "仅旋转视图（不改变原图）")])
        h.hint("部分格式（GIF、ICO、RAW 等）不支持原图旋转时，自动只旋转视图")
        h.section("翻页等待")
        h.check("loading_tip", "翻页时智能显示等待提示")
        h.hint("翻页响应慢时，在窗口中间显示“正在加载图像…”")
        h.section("编辑图片")
        h.check("saveas_autorename", "另存图片时自动重命名")
        h.check("delete_confirm", "删除图片前确认")
        h.section("在看图界面中双击图片")
        h.lay.addWidget(QLabel("在全屏和窗口模式间切换"))
        h.section("鼠标滚轮设置")
        h.check("wheel_enabled", "启用鼠标滚轮")
        h.radios("wheel_action", [("page", "滚轮为翻页"), ("zoom", "滚轮为缩放"),
                                  ("scroll", "上下移动图片（看长图方便，到头自动翻页）")], vertical=True)
        h.section("图片翻译（谷歌翻译）")
        r = h.row()
        r.addWidget(QLabel("代理地址"))
        px = QLineEdit(cfg.get("proxy", ""))
        px.setPlaceholderText("留空 = 跟随系统代理；例如 127.0.0.1:10808")
        px.setMinimumWidth(280)
        h.bindings.append(("proxy", lambda: px.text().strip(), px.setText))
        r.addWidget(px)
        r.addStretch(1)
        h.hint("v2rayN 开了“系统代理”就不用填")
        h.lay.addStretch(1)
        self._add("习惯设置", self._scroll(h), h)

        self.assoc = AssocPage(cfg)
        self._add("文件关联", self.assoc)

        s = Page(cfg)
        s.section("默认播放顺序")
        s.radios("ss_order", [("seq", "顺序播放"), ("random", "随机播放")])
        r2 = s.row()
        s.check("ss_loop", "循环播放", r2)
        s.check("ss_reverse", "倒序", r2)
        r2.addStretch(1)
        s.section("默认播放速度")
        rr = QHBoxLayout()
        rr.addWidget(QLabel("间隔"))
        sp = QSpinBox()
        sp.setRange(1, 120)
        sp.setValue(int(cfg["ss_interval"]))
        sp.setSuffix(" 秒")
        s.bindings.append(("ss_interval", sp.value, sp.setValue))
        rr.addWidget(sp)
        h_ = QLabel("（范围 1~120 秒）")
        h_.setObjectName("hint")
        rr.addWidget(h_)
        rr.addStretch(1)
        s.lay.addLayout(rr)
        s.section("默认过渡效果")
        s.combo("ss_effect", [("random", "随机效果"), ("none", "无效果"), ("fade", "淡入淡出"),
                              ("slide", "左右推移"), ("up", "上下推移"), ("zoom", "缩放渐显")])
        s.section("默认播放背景")
        s.combo("ss_bg", [("none", "黑色"), ("blur", "模糊背景"), ("white", "白色")])
        s.lay.addStretch(1)
        self._add("幻灯片", s)

        k = Page(cfg)
        k.section("快捷键一览")
        t = QTableWidget(len(SHORTCUTS), 2)
        t.setHorizontalHeaderLabels(["按键", "功能"])
        t.verticalHeader().setVisible(False)
        t.setEditTriggers(QAbstractItemView.NoEditTriggers)
        t.setSelectionMode(QAbstractItemView.NoSelection)
        t.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeToContents)
        t.horizontalHeader().setSectionResizeMode(1, QHeaderView.Stretch)
        for i, (a, b) in enumerate(SHORTCUTS):
            t.setItem(i, 0, QTableWidgetItem(a))
            t.setItem(i, 1, QTableWidgetItem(b))
        k.lay.addWidget(t, 1)
        self._add("快捷键", k)

        self.nav.currentRowChanged.connect(self.stack.setCurrentIndex)
        self.nav.setCurrentRow(0)

        bar = QHBoxLayout()
        bar.setContentsMargins(16, 12, 16, 12)
        b1 = QPushButton("恢复本页默认")
        b1.clicked.connect(lambda: self.pages[self.stack.currentIndex()].restore_defaults())
        b2 = QPushButton("恢复全部默认")
        b2.clicked.connect(lambda: [p.restore_defaults() for p in self.pages])
        ok = QPushButton("确定")
        ok.setObjectName("primary")
        ok.clicked.connect(lambda: (self.apply(), self.accept()))
        ca = QPushButton("取消")
        ca.clicked.connect(self.reject)
        ap = QPushButton("应用")
        ap.clicked.connect(self.apply)
        for b in (b1, b2):
            bar.addWidget(b)
        bar.addStretch(1)
        for b in (ok, ca, ap):
            bar.addWidget(b)
        line = QFrame()
        line.setObjectName("line")
        outer.addWidget(line)
        outer.addLayout(bar)

    def _scroll(self, page):
        sa = QScrollArea()
        sa.setWidgetResizable(True)
        sa.setFrameShape(QFrame.NoFrame)
        sa.setWidget(page)
        return sa

    def _add(self, title, widget, page=None):
        self.nav.addItem(title)
        self.stack.addWidget(widget)
        self.pages.append(page or widget)

    def apply(self):
        for p in self.pages:
            p.save(self.cfg)
        self.win.apply_cfg(self.cfg)


HELP_SECTIONS = [
    ("打开图片", [
        "设好默认程序后，双击图片直接打开",
        "也可以把图片或文件夹拖进窗口，或按 Ctrl+O",
        "打开一张图后，同一文件夹的图片都能翻看",
    ]),
    ("翻页", [
        "上一张：A、W、↑、←、PageUp",
        "下一张：D、S、↓、→、空格、PageDown",
        "第一张 / 最后一张：Home / End",
        "底部工具栏平时隐藏，鼠标移到窗口底部才出现",
        "工具栏的 ‹ › 按钮；开启“鼠标指针翻页”后，点窗口左右两侧也能翻页",
        "看完一个文件夹时，可以选择去下一个文件夹或在本文件夹循环（设置 → 常规 → 文件夹穿透）",
    ]),
    ("缩放和移动", [
        "滚轮：缩放（设置 → 习惯 → 鼠标滚轮可改成翻页）",
        "Ctrl + 滚轮：缩放",
        "+ / -：放大 / 缩小；Ctrl+0：适应窗口；Ctrl+1 或 1:1 按钮：原始大小",
        "图片比窗口大时，按住左键拖动",
        "更多 → 鸟瞰图：看大图时在左下角快速定位",
        "更多 → 锁定缩放比：翻页时保持当前比例",
    ]),
    ("滚轮模式（看长图）", [
        "点工具栏“滚轮模式”进入，再点一次退出",
        "滚轮上下移动图片，到头自动翻到下一张或上一张",
        "Ctrl + 滚轮：缩放",
    ]),
    ("全屏", [
        "双击图片、Enter 或 F11 进入 / 退出全屏，Esc 退出",
        "全屏背景可选透明或不透明（设置 → 常规）",
    ]),
    ("旋转、删除、打印", [
        "↺ ↻ 按钮或 Ctrl+L / Ctrl+R 旋转；默认直接旋转原图，可在设置里改成只旋转显示",
        "Del 或删除按钮：删除到回收站",
        "Ctrl+P 高级打印：选纸张、方向、每页几张、适应/铺满/原始尺寸、页边距、份数，可预览",
    ]),
    ("右键菜单", [
        "打印、复制、另存为、删除、裁剪、格式转换、修改尺寸、重命名",
        "设为桌面背景、用其他软件打开、打开新图片、打开所在位置",
        "图片信息（快捷键 I）：大小、尺寸、修改时间和相机拍摄参数",
        "裁剪：拖出选区后按 Enter 或双击保存，Esc 取消",
        "格式转换：选格式、质量，看预估大小，选保存路径和名称",
        "修改尺寸：按百分比或像素，可处理整个文件夹",
    ]),
    ("编辑图片", [
        "鼠标移到底部，点工具栏的“编辑”；或右键 → 编辑；或按 E",
        "先在下方选工具，再在图片上拖动：矩形、椭圆、箭头、画笔、马赛克",
        "文字：点一下图片输入，Enter 确定",
        "左边的圆点：选颜色和粗细（细 / 中 / 粗）",
        "水印：改文字、颜色、不透明度、字号、角度（默认 45°），整张图平铺，设置会记住",
        "钉在桌面：把图片变成置顶小窗，可拖动、滚轮缩放，双击或 Esc 关闭",
        "文字识别：离线识别图片里的文字，可复制",
        "Ctrl+Z 撤销；Ctrl+S 保存（覆盖原图）；Ctrl+Shift+S 另存为；Esc 退出编辑",
        "右键：取消当前工具",
    ]),
    ("图片翻译", [
        "鼠标移到底部点“翻译”，或右键 → 图片翻译，或按 T",
        "自动识别图片里的文字，用谷歌翻译后直接替换成中文，原来的外文会被抹掉",
        "上方可切换“原图 / 译文”，按住空格临时看原图",
        "底部可选源语言和目标语言（默认自动检测 → 中文简体），改了会重新翻译",
        "复制译文：复制全部翻译文字；复制图片；另存为：保存翻译后的图片（不改原图）",
        "需要能访问谷歌：v2rayN 打开“系统代理”即可，或在 设置 → 习惯设置 里填代理地址",
    ]),
    ("幻灯片", [
        "更多 → 幻灯片，或按 F5",
        "←→ / A D 切换，P 暂停，Esc 或右键退出",
        "播放顺序、间隔、过渡效果、背景在设置 → 幻灯片里改",
    ]),
    ("设为默认看图软件", [
        "右键 → 设置 → 文件关联，勾选格式，点“把勾选的格式设为用本软件打开…”",
        "支持的格式和 2345看图王一样（除 PDF）：JPG PNG GIF BMP TIF WEBP HEIC AVIF PSD TGA PCX ICO SVG RAW EXR HDR JP2 J2K WDP AI OFD 等",
        "KOA、CUT、G3 这类没有程序认领的冷门格式，点按钮后会直接用本软件打开",
        "在弹出的 Windows“默认应用”里点“照片查看器”，选“审哥看图王”",
        "本软件不会自己抢默认程序",
        "还装着 2345看图王的话，先关掉它的“图片格式关联保护”或卸载它",
    ]),
    ("其他", [
        "设置保存在 %APPDATA%\\KanTu\\settings.json",
        "F1 打开本说明",
    ]),
]


def help_text():
    out = [APP_NAME + " 使用说明", ""]
    for title, lines in HELP_SECTIONS:
        out.append("【" + title + "】")
        out.extend("  · " + l for l in lines)
        out.append("")
    return "\n".join(out)


def help_html():
    parts = [f"<h2 style='margin:0 0 8px 0'>{APP_NAME} 使用说明</h2>"]
    for title, lines in HELP_SECTIONS:
        parts.append(f"<h3 style='color:#1e6fe8;margin:14px 0 4px 0'>{title}</h3><ul style='margin:0'>")
        parts.extend(f"<li style='margin:3px 0'>{l}</li>" for l in lines)
        parts.append("</ul>")
    return "".join(parts)


class HelpDialog(QDialog):
    def __init__(self, win):
        super().__init__(win, Qt.Window)
        self.setWindowTitle("使用说明")
        self.setAttribute(Qt.WA_DeleteOnClose)
        lay = QVBoxLayout(self)
        tb = QTextBrowser()
        tb.setStyleSheet("QTextBrowser{border:none;padding:12px;font-size:14px}")
        tb.setHtml(help_html())
        lay.addWidget(tb)
        self.resize(640, 720)


# ---------------------------------------------------------------- 主窗口
class MainWindow(QMainWindow):
    def __init__(self, cfg):
        super().__init__()
        self.cfg = cfg
        self.setWindowTitle(APP_NAME)
        self.setWindowIcon(QIcon(make_app_icon()))
        self.setAcceptDrops(True)
        self.files = []
        self.index = -1
        self.cur_path = None
        self.cur_img = None
        self.movie = None
        self.page_count = 1
        self.page = 0
        self.wheel_mode = False
        self._wheel_acc = 0
        self._last_flip = 0.0
        self._pending_view = "auto"
        self._errors = {}
        self._loading = set()
        self._thumb_req = set()
        self._cache = OrderedDict()
        self._slideshow = None
        self.editor = None
        self._was_max = False
        self.load_pool = QThreadPool(self)
        self.load_pool.setMaxThreadCount(3)
        self.thumb_pool = QThreadPool(self)
        self.thumb_pool.setMaxThreadCount(2)
        self.file_pool = QThreadPool(self)
        self.file_pool.setMaxThreadCount(1)
        self.ocr_pool = QThreadPool(self)
        self.ocr_pool.setMaxThreadCount(1)
        self._pins = []

        central = QWidget()
        v = QVBoxLayout(central)
        v.setContentsMargins(0, 0, 0, 0)
        v.setSpacing(0)
        self.stack = QStackedWidget()
        self.canvas = Canvas(self)
        self.stack.addWidget(self.canvas)
        v.addWidget(self.stack, 1)
        self.thumbs = QListWidget()
        self.thumbs.setObjectName("thumbs")
        self.thumbs.setViewMode(QListWidget.IconMode)
        self.thumbs.setFlow(QListWidget.LeftToRight)
        self.thumbs.setWrapping(False)
        self.thumbs.setMovement(QListWidget.Static)
        self.thumbs.setIconSize(QSize(80, 60))
        self.thumbs.setFixedHeight(88)
        self.thumbs.setSpacing(2)
        self.thumbs.setUniformItemSizes(True)
        self.thumbs.setFocusPolicy(Qt.NoFocus)
        self.thumbs.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.thumbs.itemClicked.connect(lambda it: self.show_index(self.thumbs.row(it)))
        self.thumbs.horizontalScrollBar().valueChanged.connect(lambda _: self._request_visible_thumbs())
        self.thumbs.setVisible(cfg["thumbs"])
        v.addWidget(self.thumbs)
        self.setCentralWidget(central)
        self.toolbar = self._build_toolbar()
        self.toolbar.installEventFilter(self)
        self.toolbar.hide()
        self._bar_timer = QTimer(self)
        self._bar_timer.setSingleShot(True)
        self._bar_timer.timeout.connect(self._maybe_hide_bar)

        self.load_timer = QTimer(self)
        self.load_timer.setSingleShot(True)
        self.load_timer.timeout.connect(self._show_loading_tip)
        self._placeholder = self._make_placeholder()
        self._build_actions()
        self.more = None

        geom = cfg.get("geom")
        if geom:
            try:
                self.restoreGeometry(QByteArray.fromBase64(geom.encode()))
            except Exception:
                self.resize(1100, 760)
        else:
            self.resize(1100, 760)
        self.setWindowFlag(Qt.WindowStaysOnTopHint, bool(cfg["on_top"]))

    # ---- 界面
    def _build_toolbar(self):
        bar = FloatBar(self.canvas)
        self.btn_wheel = bar.btn("滚轮模式", "滚轮看图模式：滚轮上下移动并翻页，Ctrl+滚轮缩放", lambda: None, checkable=True)
        self.btn_wheel.toggled.connect(self.set_wheel_mode)
        bar.btn("1:1", "原始大小 / 适应窗口", self.toggle_actual)
        bar.btn("＋", "放大", lambda: self.canvas.zoom_to(self.canvas.scale * 1.25))
        bar.btn("－", "缩小", lambda: self.canvas.zoom_to(self.canvas.scale / 1.25))
        bar.sep()
        bar.btn("‹", "上一张", lambda: self.flip(-1))
        bar.btn("›", "下一张", lambda: self.flip(1))
        bar.sep()
        bar.btn("↺", "左转", lambda: self.rotate(-90))
        bar.btn("↻", "右转", lambda: self.rotate(90))
        bar.btn("编辑", "在图片上标注、打马赛克、加水印、文字识别（E）", self.start_edit)
        bar.btn("翻译", "把图片里的外文直接翻译成中文（T）", self.start_translate)
        bar.btn("删除", "删除到回收站（Del）", self.delete_current)
        bar.btn("打印", "高级打印（Ctrl+P）", self.advanced_print)
        self.btn_more = bar.btn("更多 ▴", "更多", self.show_more)
        bar.adjustSize()
        return bar

    # ---- 底部工具栏：鼠标移到底部才显示
    def place_bar(self):
        if not hasattr(self, "toolbar"):
            return
        c = self.canvas
        b = self.toolbar
        b.adjustSize()
        b.move(max(0, (c.width() - b.width()) // 2), c.height() - b.height() - 16)

    def bar_track(self, pos):
        if self.editor is not None:
            return
        if pos.y() >= self.canvas.height() - 100:
            if not self.toolbar.isVisible():
                self.place_bar()
                self.toolbar.show()
                self.toolbar.raise_()
            self._bar_timer.stop()
        elif self.toolbar.isVisible() and not self._bar_timer.isActive():
            self._bar_timer.start(500)

    def bar_leave(self):
        if self.toolbar.isVisible():
            self._bar_timer.start(500)

    def _maybe_hide_bar(self):
        if self.toolbar.underMouse() or (self.more is not None and self.more.isVisible()):
            self._bar_timer.start(500)
            return
        self.toolbar.hide()

    def eventFilter(self, obj, ev):
        if obj is self.toolbar:
            if ev.type() == ev.Type.Enter:
                self._bar_timer.stop()
            elif ev.type() == ev.Type.Leave:
                self._bar_timer.start(500)
        return super().eventFilter(obj, ev)

    # ---- 编辑
    def start_edit(self):
        if not self._need() or self.editor is not None:
            return
        self._stop_movie()
        self.cancel_crop()
        img = self.canvas.pix.toImage() if self.canvas.pix is not None else self.cur_img
        self.editor = EditView(self, img, self.cur_path)
        self.stack.addWidget(self.editor)
        self.stack.setCurrentWidget(self.editor)
        self.toolbar.hide()
        self.thumbs.hide()
        for a in self.A.values():
            a.setEnabled(False)
        self.editor.setFocus()
        self.update_title()

    def start_translate(self):
        if not self._need() or self.editor is not None:
            return
        self._stop_movie()
        self.cancel_crop()
        img = self.canvas.pix.toImage() if self.canvas.pix is not None else self.cur_img
        self.editor = TranslateView(self, img, self.cur_path)
        self.stack.addWidget(self.editor)
        self.stack.setCurrentWidget(self.editor)
        self.toolbar.hide()
        self.thumbs.hide()
        for a in self.A.values():
            a.setEnabled(False)
        self.editor.setFocus()

    def end_edit(self):
        ed = self.editor
        if ed is None:
            return
        self.editor = None
        self.stack.setCurrentWidget(self.canvas)
        self.stack.removeWidget(ed)
        ed.deleteLater()
        for a in self.A.values():
            a.setEnabled(True)
        self.thumbs.setVisible(bool(self.cfg["thumbs"]) and not self.isFullScreen())
        self.activateWindow()
        self.canvas.setFocus()
        self.update_title()

    def after_edit_saved(self, path, new_file=False):
        self.end_edit()
        self.invalidate(path)
        self._thumb_req.discard(path)
        if new_file:
            self._after_new_file(path)
            self.canvas.toast("已另存为：" + os.path.basename(path), 2500)
        else:
            self.show_index(self.index)
            if path in self.files:
                self._request_thumb(self.files.index(path))
            self.canvas.toast("已保存", 2000)

    def _make_placeholder(self):
        pm = QPixmap(80, 60)
        pm.fill(QColor("#dfe2e6"))
        return QIcon(pm)

    def _build_actions(self):
        A = {}

        def act(key, text, fn, shortcut=None):
            a = QAction(text, self)
            if shortcut:
                a.setShortcuts([QKeySequence(s) for s in (shortcut if isinstance(shortcut, list) else [shortcut])])
                a.setShortcutContext(Qt.WindowShortcut)
            a.triggered.connect(fn)
            self.addAction(a)
            A[key] = a
            return a

        act("adv_print", "高级打印", self.advanced_print, "Ctrl+P")
        act("sys_print", "系统打印", self.system_print)
        act("copy", "复制", self.copy_image, "Ctrl+C")
        act("save_as", "图片另存为…", self.save_as, "Ctrl+S")
        act("delete", "删除", self.delete_current, "Del")
        act("crop", "裁剪…", self.start_crop, "Ctrl+Alt+P")
        act("convert", "格式转换…", self.convert_dialog)
        act("resize", "修改图片尺寸…", self.resize_dialog, "Ctrl+E")
        act("rename", "重命名", self.rename_current, "F2")
        act("wallpaper", "设为桌面背景", self.set_wallpaper)
        act("open", "打开新的图片…", self.open_dialog, "Ctrl+O")
        act("locate", "打开图片所在位置", self.open_location)
        act("info", "图片信息", self.show_info, "I")
        act("settings", "设置…", self.open_settings)
        act("help", "使用说明", self.show_help, "F1")
        act("edit", "编辑（标注、马赛克、水印、文字识别）", self.start_edit, "E")
        act("translate", "图片翻译", self.start_translate, "T")
        act("slideshow", "幻灯片", self.start_slideshow, "F5")
        act("rot_l", "左转", lambda: self.rotate(-90), "Ctrl+L")
        act("rot_r", "右转", lambda: self.rotate(90), "Ctrl+R")
        act("fit", "适应窗口", lambda: self.canvas.fit_window(), "Ctrl+0")
        act("actual", "原始大小", lambda: self.canvas.actual_size(), "Ctrl+1")
        act("thumbs", "缩略图", lambda: self.set_opt("thumbs", not self.cfg["thumbs"]), "Ctrl+T")
        act("zoom_in", "放大", lambda: self.canvas.zoom_to(self.canvas.scale * 1.25), ["+", "=", "Ctrl++"])
        act("zoom_out", "缩小", lambda: self.canvas.zoom_to(self.canvas.scale / 1.25), ["-", "Ctrl+-"])
        act("page_prev", "上一页", lambda: self.show_page(self.page - 1), "Ctrl+Up")
        act("page_next", "下一页", lambda: self.show_page(self.page + 1), "Ctrl+Down")
        self.A = A

    def show_more(self):
        self.more = MorePanel(self)
        self.more.adjustSize()
        g = self.btn_more.mapToGlobal(QPoint(self.btn_more.width(), 0))
        self.more.move(g.x() - self.more.width(), g.y() - self.more.height() - 6)
        self.more.show()

    def update_title(self):
        if not self.cur_path:
            self.setWindowTitle(APP_NAME)
            return
        parts = [os.path.basename(self.cur_path)]
        if self.files:
            parts.append(f"{self.index + 1}/{len(self.files)}")
        if self.cur_img is not None:
            parts.append(f"{self.cur_img.width()}×{self.cur_img.height()}")
        try:
            parts.append(human_size(os.path.getsize(self.cur_path)))
        except OSError:
            pass
        if self.canvas.pix:
            parts.append(f"{self.canvas.scale * 100:.0f}%")
        if self.page_count > 1:
            parts.append(f"第 {self.page + 1}/{self.page_count} 页")
        self.setWindowTitle("  ·  ".join(parts) + f"  -  {APP_NAME}")

    # ---- 设置
    def set_opt(self, key, val):
        self.cfg[key] = val
        save_cfg(self.cfg)
        if key == "thumbs":
            self.thumbs.setVisible(bool(val) and not self.isFullScreen())
            if val:
                self._sync_thumbs()
        self.canvas.update()

    def apply_cfg(self, new):
        old = dict(self.cfg)
        self.cfg.update(new)
        save_cfg(self.cfg)
        if old["on_top"] != self.cfg["on_top"]:
            geo = self.geometry()
            self.setWindowFlag(Qt.WindowStaysOnTopHint, bool(self.cfg["on_top"]))
            self.show()
            self.setGeometry(geo)
            dark_titlebar(self)
        self.thumbs.setVisible(bool(self.cfg["thumbs"]) and not self.isFullScreen())
        if old["auto_orient"] != self.cfg["auto_orient"] or old["raw_full"] != self.cfg["raw_full"]:
            self._cache.clear()
            if self.files:
                self.show_index(self.index)
        if self._slideshow is None:
            self.canvas.update()

    def show_help(self):
        dlg = HelpDialog(self)
        dark_titlebar(dlg)
        dlg.show()

    def open_settings(self):
        dlg = SettingsDialog(self)
        dark_titlebar(dlg)
        dlg.exec()

    # ---- 缓存与加载
    def cache_get(self, path):
        img = self._cache.get(path)
        if img is not None:
            self._cache.move_to_end(path)
        return img

    def cache_put(self, path, img):
        self._cache[path] = img
        self._cache.move_to_end(path)
        while len(self._cache) > 8:
            self._cache.popitem(last=False)

    def invalidate(self, path):
        self._cache.pop(path, None)
        self._errors.pop(path, None)

    def preload(self, path):
        if path in self._cache or path in self._loading or path in self._errors:
            return
        self._loading.add(path)
        cfg = dict(self.cfg)
        run_bg(self.load_pool, lambda: load_image(path, cfg), lambda ok, res, p=path: self._on_loaded(p, ok, res))

    def _on_loaded(self, path, ok, res):
        self._loading.discard(path)
        if ok:
            self.cache_put(path, res)
        else:
            self._errors[path] = str(res)
        if self.cur_path and path == self.cur_path:
            self._display()

    def _show_loading_tip(self):
        if self.cfg["loading_tip"] and self.cur_path in self._loading:
            self.canvas.loading_text = "正在加载图像…"
            self.canvas.update()

    # ---- 打开
    def open_path(self, path):
        path = os.path.abspath(path)
        if os.path.isdir(path):
            files = list_images(path)
            if not files:
                self.canvas.toast("这个文件夹里没有图片")
                return
            self.set_files(files, 0)
            return
        if not os.path.exists(path):
            self.canvas.toast("文件不存在")
            return
        files = list_images(os.path.dirname(path))
        idx = next((i for i, p in enumerate(files) if same_path(p, path)), None)
        if idx is None:
            files.append(path)
            idx = len(files) - 1
        self.set_files(files, idx)

    def set_files(self, files, idx, view="auto"):
        self.files = files
        self._thumb_req.clear()
        self._errors.clear()
        self.thumbs.clear()
        for p in files:
            it = QListWidgetItem(self._placeholder, "")
            it.setToolTip(os.path.basename(p))
            it.setSizeHint(QSize(88, 70))
            self.thumbs.addItem(it)
        self.show_index(idx, view)

    def open_dialog(self):
        start = os.path.dirname(self.cur_path) if self.cur_path else ""
        flt = "图片 (" + " ".join("*." + e for e in sorted(IMAGE_EXTS)) + ");;所有文件 (*)"
        p, _ = QFileDialog.getOpenFileName(self, "打开图片", start, flt)
        if p:
            self.open_path(p)

    def show_index(self, i, view="auto"):
        if not self.files:
            self.cur_path = None
            self.cur_img = None
            self.index = -1
            self._stop_movie()
            self.canvas.clear("拖入图片，或按 Ctrl+O 打开")
            self.update_title()
            return
        i = max(0, min(i, len(self.files) - 1))
        self.index = i
        self.cur_path = self.files[i]
        self._stop_movie()
        self.page_count, self.page = 1, 0
        if view == "auto" and self.wheel_mode:
            view = "top"
        if view == "auto" and self.cfg["lock_zoom"]:
            view = "lock"
        self._pending_view = view
        if self.cur_path in self._cache or self.cur_path in self._errors:
            self._display()
        else:
            self.preload(self.cur_path)
            self.load_timer.start(300)
        for d in (1, -1, 2):
            j = i + d
            if 0 <= j < len(self.files):
                self.preload(self.files[j])
        self._sync_thumbs()
        self.update_title()

    def _display(self):
        path = self.cur_path
        self.load_timer.stop()
        self.canvas.loading_text = ""
        img = self.cache_get(path)
        if img is None:
            self.cur_img = None
            self.canvas.clear("无法打开这张图片\n" + self._errors.get(path, ""))
            self.update_title()
            return
        self.cur_img = img
        self.canvas.set_image(QPixmap.fromImage(img), self._pending_view)
        self._pending_view = "auto"
        ext = ext_of(path)
        if self.cfg["multiframe"]:
            try:
                if ext in ANIM_EXTS:
                    r = QImageReader(path)
                    if r.supportsAnimation() and r.imageCount() != 1:
                        m = QMovie(path)
                        if m.isValid():
                            self.movie = m
                            m.frameChanged.connect(self._on_frame)
                            m.start()
                elif ext in ("tif", "tiff"):
                    r = QImageReader(path)
                    self.page_count = max(1, r.imageCount())
            except Exception:
                pass
        self.update_title()

    def _on_frame(self, _):
        if self.movie is not None:
            self.canvas.set_frame(QPixmap.fromImage(self.movie.currentImage()))

    def _stop_movie(self):
        if self.movie is not None:
            self.movie.stop()
            try:
                self.movie.frameChanged.disconnect(self._on_frame)
            except Exception:
                pass
            self.movie.deleteLater()
            self.movie = None

    def show_page(self, n):
        if self.page_count <= 1 or not self.cur_path:
            return
        n = max(0, min(n, self.page_count - 1))
        r = QImageReader(self.cur_path)
        r.setAutoTransform(self.cfg["auto_orient"])
        if r.jumpToImage(n):
            img = r.read()
            if not img.isNull():
                self.page = n
                self.cur_img = img
                self.canvas.set_image(QPixmap.fromImage(img))
                self.update_title()

    # ---- 缩略图
    def _sync_thumbs(self):
        if not self.thumbs.isVisible() or self.index < 0:
            return
        self.thumbs.blockSignals(True)
        self.thumbs.setCurrentRow(self.index)
        self.thumbs.blockSignals(False)
        it = self.thumbs.item(self.index)
        if it:
            self.thumbs.scrollToItem(it, QAbstractItemView.PositionAtCenter)
        for j in range(self.index - 15, self.index + 16):
            self._request_thumb(j)
        self._request_visible_thumbs()

    def _request_visible_thumbs(self):
        if not self.thumbs.isVisible():
            return
        vw = self.thumbs.viewport().width()
        x = 0
        while x < vw:
            idx = self.thumbs.indexAt(QPoint(x + 10, 30))
            if idx.isValid():
                self._request_thumb(idx.row())
            x += 40

    def _request_thumb(self, j):
        if not (0 <= j < len(self.files)):
            return
        path = self.files[j]
        if path in self._thumb_req:
            return
        self._thumb_req.add(path)
        cfg = dict(self.cfg)
        files = self.files
        run_bg(self.thumb_pool, lambda: make_thumb(path, cfg),
               lambda ok, res, p=path, f=files: self._on_thumb(p, f, ok, res))

    def _on_thumb(self, path, files, ok, res):
        if files is not self.files or not ok:
            return
        try:
            j = self.files.index(path)
        except ValueError:
            return
        it = self.thumbs.item(j)
        if it:
            it.setIcon(QIcon(QPixmap.fromImage(res)))

    # ---- 翻页
    def flip(self, d, view="auto"):
        if not self.files:
            return
        j = self.index + d
        if 0 <= j < len(self.files):
            self.show_index(j, view)
            return
        if len(self.files) == 1 and not self.cfg["folder_end_remember"]:
            act = None
        elif self.cfg["folder_end_remember"]:
            act = self.cfg["folder_end_action"]
        else:
            act, remember = ask_with_checkbox(self, "已经是最后一张" if d > 0 else "已经是第一张",
                                              "当前文件夹已浏览完，接下来：",
                                              [("next", "前往下一个文件夹" if d > 0 else "前往上一个文件夹"),
                                               ("loop", "在本文件夹内循环浏览")], "记住我的选择")
            if act and remember:
                self.cfg["folder_end_remember"] = True
                self.cfg["folder_end_action"] = act
                save_cfg(self.cfg)
        if act is None:
            self.canvas.toast("已经是最后一张" if d > 0 else "已经是第一张")
            return
        if act == "loop":
            self.show_index(0 if d > 0 else len(self.files) - 1, view)
            return
        nf = neighbor_folder(os.path.dirname(self.cur_path), d)
        if not nf:
            self.canvas.toast("没有下一个文件夹了" if d > 0 else "没有上一个文件夹了")
            return
        files = list_images(nf)
        self.set_files(files, 0 if d > 0 else len(files) - 1, view)
        self.canvas.toast("已进入文件夹：" + os.path.basename(nf))

    # ---- 滚轮
    def set_wheel_mode(self, on):
        self.wheel_mode = bool(on)
        if on:
            if self.cfg["wheel_mode_tip"]:
                dlg = WheelTipDialog(self)
                dark_titlebar(dlg)
                dlg.exec()
                if dlg.cb.isChecked():
                    self.cfg["wheel_mode_tip"] = False
                    save_cfg(self.cfg)
            if self.canvas.pix:
                self.canvas._fit_width("top")
        else:
            self.canvas.reset_view()

    def on_wheel(self, e):
        dy = e.angleDelta().y() or e.angleDelta().x()
        if not dy:
            return
        ctrl = bool(e.modifiers() & Qt.ControlModifier)
        if self.wheel_mode:
            action = "zoom" if ctrl else "scroll"
        else:
            if not self.cfg["wheel_enabled"]:
                return
            action = "zoom" if ctrl else self.cfg["wheel_action"]
        if action == "zoom":
            self.canvas.zoom_to(self.canvas.scale * (1.15 ** (dy / 120)), e.position())
        elif action == "page":
            self._wheel_acc += dy
            if abs(self._wheel_acc) >= 120:
                d = -1 if self._wheel_acc > 0 else 1
                self._wheel_acc = 0
                self._throttled_flip(d)
        else:
            self._wheel_scroll(dy)

    def _throttled_flip(self, d, view="auto"):
        now = time.monotonic()
        if now - self._last_flip < 0.25:
            return
        self._last_flip = now
        self.flip(d, view)

    def _wheel_scroll(self, dy):
        c = self.canvas
        if not c.pix:
            self._throttled_flip(-1 if dy > 0 else 1)
            return
        w, h = c.disp_size()
        H = c.height()
        if h <= H + 1:
            self._throttled_flip(-1 if dy > 0 else 1, "top" if dy < 0 else "bottom")
            return
        y = c.off.y()
        at_top = y >= -0.5
        at_bottom = y <= H - h + 0.5
        if dy < 0 and at_bottom:
            self._throttled_flip(1, "top")
        elif dy > 0 and at_top:
            self._throttled_flip(-1, "bottom")
        else:
            c.off = QPointF(c.off.x(), y + dy)
            c._clamp()
            c.update()

    # ---- 键盘
    def keyPressEvent(self, e):
        k = e.key()
        mod = e.modifiers()
        c = self.canvas
        if k == Qt.Key_Escape:
            if c.crop_mode:
                self.cancel_crop()
            elif self.isFullScreen():
                self.toggle_fullscreen()
            else:
                self.close()
        elif k in NEXT_KEYS and not mod & (Qt.ControlModifier | Qt.AltModifier):
            self.flip(1)
        elif k in PREV_KEYS and not mod & (Qt.ControlModifier | Qt.AltModifier):
            self.flip(-1)
        elif k == Qt.Key_Home:
            self.show_index(0)
        elif k == Qt.Key_End:
            self.show_index(len(self.files) - 1)
        elif k in (Qt.Key_Return, Qt.Key_Enter):
            if c.crop_mode:
                self.finish_crop()
            else:
                self.toggle_fullscreen()
        elif k == Qt.Key_F11:
            self.toggle_fullscreen()
        else:
            super().keyPressEvent(e)

    def toggle_actual(self):
        c = self.canvas
        if not c.pix:
            return
        if abs(c.scale - 1.0) < 1e-3:
            c.fit_window() if c.fit_scale() < 1 else c.reset_view()
            c.toast(f"{c.scale * 100:.0f}%", 700)
        else:
            c.actual_size()

    # ---- 全屏
    def toggle_fullscreen(self):
        if self.isFullScreen():
            self.canvas.bg_pix = None
            self.thumbs.setVisible(bool(self.cfg["thumbs"]))
            if self._was_max:
                self.showMaximized()
            else:
                self.showNormal()
        else:
            self._was_max = self.isMaximized()
            self.canvas.bg_pix = None
            if self.cfg["fs_transparent"]:
                self.setWindowOpacity(0.0)
                QApplication.processEvents()
                QThread.msleep(80)
                scr = self.screen() or QGuiApplication.primaryScreen()
                g = scr.geometry()
                self.canvas.bg_pix = scr.grabWindow(0, 0, 0, g.width(), g.height())
                self.setWindowOpacity(1.0)
            self.thumbs.hide()
            self.showFullScreen()

    # ---- 右键菜单
    def show_context_menu(self, gpos):
        has = self.cur_img is not None
        A = self.A
        m = QMenu(self)
        A["edit"].setEnabled(has)
        m.addAction(A["edit"])
        A["translate"].setEnabled(has)
        m.addAction(A["translate"])
        m.addSeparator()
        for key in ("adv_print", "sys_print", "copy", "save_as", "delete", "crop", "convert", "resize", "rename"):
            A[key].setEnabled(has)
            m.addAction(A[key])
        m.addSeparator()
        A["wallpaper"].setEnabled(has and IS_WIN)
        m.addAction(A["wallpaper"])
        sub = m.addMenu("使用其他软件打开")
        sub.setEnabled(has)
        if IS_WIN:
            sub.addAction("画图", lambda: self._open_with("mspaint.exe"))
            sub.addAction("Windows 照片", lambda: self._open_with(None, photos=True))
        sub.addAction("选择其他程序…", lambda: self._open_with(None))
        m.addAction(A["open"])
        A["locate"].setEnabled(has)
        m.addAction(A["locate"])
        m.addSeparator()
        A["info"].setEnabled(has)
        m.addAction(A["info"])
        m.addAction(A["settings"])
        m.addAction(A["help"])
        m.exec(gpos)

    # ---- 文件操作
    def _need(self):
        if self.cur_path and self.cur_img is not None:
            return True
        return False

    def delete_current(self):
        if not self.cur_path:
            return
        path = self.cur_path
        if self.cfg["delete_confirm"]:
            act, dont = ask_with_checkbox(self, "删除", f"把这张图片删除到回收站？\n{os.path.basename(path)}",
                                          [("del", "删除")])
            if act is None:
                return
            if dont:
                self.cfg["delete_confirm"] = False
                save_cfg(self.cfg)
        self._stop_movie()
        if not recycle(path):
            self.canvas.toast("删除失败")
            return
        i = self.index
        self.files.pop(i)
        self.invalidate(path)
        self.thumbs.takeItem(i)
        self._thumb_req.discard(path)
        if not self.files:
            self.show_index(0)
        else:
            self.show_index(min(i, len(self.files) - 1))
        self.canvas.toast("已删除到回收站")

    def rename_current(self):
        if not self.cur_path:
            return
        path = self.cur_path
        stem, ext = os.path.splitext(os.path.basename(path))
        name, ok = QInputDialog.getText(self, "重命名", "新文件名：", QLineEdit.Normal, stem)
        if not ok or not name.strip() or name.strip() == stem:
            return
        new = os.path.join(os.path.dirname(path), name.strip() + ext)
        if os.path.exists(new):
            QMessageBox.warning(self, "重命名", "已有同名文件")
            return
        self._stop_movie()
        try:
            os.rename(path, new)
        except Exception as ex:
            QMessageBox.warning(self, "重命名失败", str(ex))
            return
        img = self._cache.pop(path, None)
        if img is not None:
            self.cache_put(new, img)
        self._thumb_req.discard(path)
        self.files[self.index] = new
        it = self.thumbs.item(self.index)
        if it:
            it.setToolTip(os.path.basename(new))
        self.show_index(self.index)

    def copy_image(self):
        if not self._need():
            return
        md = QMimeData()
        md.setImageData(self.cur_img)
        md.setUrls([QUrl.fromLocalFile(self.cur_path)])
        QApplication.clipboard().setMimeData(md)
        self.canvas.toast("已复制")

    def save_as(self):
        if not self._need():
            return
        path = self.cur_path
        default = os.path.join(os.path.dirname(path), os.path.basename(path))
        if self.cfg["saveas_autorename"]:
            default = unique_path(default)
        flt = "JPG (*.jpg);;PNG (*.png);;WEBP (*.webp);;BMP (*.bmp);;TIFF (*.tif);;所有文件 (*)"
        dst, _ = QFileDialog.getSaveFileName(self, "图片另存为", default, flt)
        if not dst:
            return
        if not ext_of(dst):
            dst += "." + ext_of(path)
        try:
            rot = self.canvas.rot
            if rot == 0 and ext_of(dst) == ext_of(path):
                if not same_path(dst, path):
                    shutil.copy2(path, dst)
            else:
                fmt = SAVE_FMT.get(ext_of(dst))
                if not fmt:
                    raise RuntimeError("不支持保存为这个格式")
                im, _, info, exif = open_pil(path)
                if rot:
                    im = im.rotate(-rot, expand=True)
                save_pil(im, dst, fmt, 95, info, exif)
            self._after_new_file(dst)
            self.canvas.toast("已保存：" + os.path.basename(dst))
        except Exception as ex:
            QMessageBox.warning(self, "保存失败", str(ex))

    def _after_new_file(self, dst):
        if os.path.dirname(os.path.abspath(dst)) == os.path.dirname(os.path.abspath(self.cur_path or dst)):
            cur = self.cur_path
            files = list_images(os.path.dirname(cur))
            idx = next((i for i, p in enumerate(files) if same_path(p, cur)), 0)
            self.files = files
            self.thumbs.clear()
            self._thumb_req.clear()
            for p in files:
                it = QListWidgetItem(self._placeholder, "")
                it.setToolTip(os.path.basename(p))
                it.setSizeHint(QSize(88, 70))
                self.thumbs.addItem(it)
            self.index = idx
            self._sync_thumbs()
            self.update_title()

    def rotate(self, deg):
        if not self._need():
            return
        c = self.canvas
        path = self.cur_path
        if self.cfg["rotate_original"] and can_rotate_original(path) and self.movie is None and self.page_count == 1 \
                and ext_of(path) not in RAW_EXTS:
            c.rotate_view(deg)
            self.invalidate(path)

            def done(ok, res, p=path):
                if not ok:
                    self.canvas.toast("原图旋转失败，只旋转了视图：" + str(res)[:40], 3000)
                    return
                self._thumb_req.discard(p)
                if p in self.files:
                    self._request_thumb(self.files.index(p))
                if p == self.cur_path and c.pix is not None:
                    c.base, c.rot = c.pix, 0
                    self.cache_put(p, c.pix.toImage())
                    self.cur_img = self.cache_get(p)
                    self.update_title()

            run_bg(self.file_pool, lambda: rotate_file(path, deg), done)
        else:
            c.rotate_view(deg)

    def start_crop(self):
        if not self._need():
            return
        self._stop_movie()
        c = self.canvas
        c.crop_mode = True
        c.crop_rect = QRectF()
        c.setCursor(Qt.CrossCursor)
        c.toast("拖动鼠标选择区域；Enter 或双击保存，Esc 或右键取消", 4000)
        c.update()

    def cancel_crop(self):
        c = self.canvas
        c.crop_mode = False
        c.crop_rect = QRectF()
        c.setCursor(Qt.ArrowCursor)
        c.update()

    def finish_crop(self):
        c = self.canvas
        r = c.crop_image_rect()
        if r.isEmpty() or r.width() < 2 or r.height() < 2:
            c.toast("请先拖动选择区域")
            return
        path = self.cur_path
        stem, ext = os.path.splitext(path)
        default = unique_path(stem + "_裁剪" + (ext if ext_of(path) in SAVE_FMT else ".png"))
        dst, _ = QFileDialog.getSaveFileName(self, "保存裁剪后的图片", default,
                                             "JPG (*.jpg);;PNG (*.png);;WEBP (*.webp);;BMP (*.bmp);;所有文件 (*)")
        if not dst:
            return
        if not ext_of(dst):
            dst += ".png"
        try:
            ok_pil = False
            if Image is not None and ext_of(path) not in RAW_EXTS and self.cfg["auto_orient"]:
                im, _, info, exif = open_pil(path)
                if c.rot:
                    im = im.rotate(-c.rot, expand=True)
                if im.size == (c.pix.width(), c.pix.height()):
                    im = im.crop((r.x(), r.y(), r.x() + r.width(), r.y() + r.height()))
                    save_pil(im, dst, SAVE_FMT.get(ext_of(dst), "PNG"), 95, info, exif)
                    ok_pil = True
            if not ok_pil:
                out = c.pix.copy(r).toImage()
                if not out.save(dst, None, 95):
                    raise RuntimeError("保存失败")
        except Exception as ex:
            QMessageBox.warning(self, "裁剪失败", str(ex))
            return
        self.cancel_crop()
        self._after_new_file(dst)
        c.toast("已保存：" + os.path.basename(dst))

    def _batch(self, title, items, fn):
        dlg = QProgressDialog(title, "取消", 0, len(items), self)
        dlg.setWindowTitle(title)
        dlg.setWindowModality(Qt.WindowModal)
        dlg.setMinimumDuration(300)
        errors = []
        outs = []
        for i, p in enumerate(items):
            if dlg.wasCanceled():
                break
            dlg.setValue(i)
            dlg.setLabelText(f"{title}：{os.path.basename(p)}")
            QApplication.processEvents()
            try:
                outs.append(fn(p))
            except Exception as ex:
                errors.append(f"{os.path.basename(p)}：{ex}")
        dlg.setValue(len(items))
        return outs, errors

    def convert_dialog(self):
        if not self._need():
            return
        dlg = ConvertDialog(self, self.cur_path)
        dark_titlebar(dlg)
        if dlg.exec() != QDialog.Accepted:
            return
        ext, q, dst = dlg.ext(), dlg.quality.value(), dlg.dst
        dlg.pool.waitForDone()
        try:
            os.makedirs(os.path.dirname(dst), exist_ok=True)
            im, _, info, exif = dlg._im or open_pil(self.cur_path)
            save_pil(im, dst, SAVE_FMT[ext], q, info, exif)
        except Exception as ex:
            QMessageBox.warning(self, "格式转换失败", str(ex))
            return
        self.cfg["conv_dir"] = os.path.dirname(dst)
        save_cfg(self.cfg)
        self._after_new_file(dst)
        self.canvas.toast("已转换：" + os.path.basename(dst), 2500)

    def resize_dialog(self):
        if not self._need():
            return
        dlg = ResizeDialog(self, self.cur_img.width(), self.cur_img.height(), len(self.files))
        dark_titlebar(dlg)
        if dlg.exec() != QDialog.Accepted:
            return
        items = list(self.files) if dlg.all.isChecked() else [self.cur_path]
        overwrite = dlg.overwrite.isChecked()
        q = dlg.quality.value()
        self._stop_movie()

        def one(p):
            im, fmt, info, exif = open_pil(p)
            nw, nh = dlg.target_size(*im.size)
            im = im.resize((nw, nh), Image.LANCZOS)
            e = ext_of(p)
            if e not in SAVE_FMT:
                e = "jpg"
            f = SAVE_FMT[e]
            if overwrite and ext_of(p) in SAVE_FMT:
                dst = p
            else:
                dst = unique_path(os.path.splitext(p)[0] + "_修改尺寸." + e)
            save_pil(im, dst, f, q, info, exif)
            self.invalidate(dst)
            self._thumb_req.discard(dst)
            return dst

        outs, errors = self._batch("修改尺寸", items, one)
        self._report("修改尺寸", outs, errors)
        if overwrite:
            self.show_index(self.index)
            self._sync_thumbs()
        elif outs:
            self._after_new_file(outs[-1])

    def _report(self, title, outs, errors):
        if errors:
            QMessageBox.warning(self, title, f"完成 {len(outs)} 张，失败 {len(errors)} 张：\n" + "\n".join(errors[:15]))
        else:
            self.canvas.toast(f"{title}完成：{len(outs)} 张")

    def set_wallpaper(self):
        if not IS_WIN or not self._need():
            return
        path = self.cur_path
        if ext_of(path) not in ("jpg", "jpeg", "bmp", "png"):
            os.makedirs(CFG_DIR, exist_ok=True)
            dst = os.path.join(CFG_DIR, "wallpaper.png")
            self.cur_img.save(dst)
            path = dst
        ok = ctypes.windll.user32.SystemParametersInfoW(20, 0, os.path.abspath(path), 3)
        self.canvas.toast("已设为桌面背景" if ok else "设置失败")

    def _open_with(self, exe, photos=False):
        if not self.cur_path:
            return
        p = os.path.abspath(self.cur_path)
        try:
            if exe:
                subprocess.Popen([exe, p])
            elif photos and IS_WIN:
                subprocess.Popen(["explorer.exe", "ms-photos:viewer?fileName=" + p])
            elif IS_WIN:
                subprocess.Popen(["rundll32.exe", "shell32.dll,OpenAs_RunDLL", p])
            else:
                subprocess.Popen(["xdg-open", p])
        except Exception as ex:
            self.canvas.toast("打开失败：" + str(ex))

    def open_location(self):
        if not self.cur_path:
            return
        p = os.path.abspath(self.cur_path)
        if IS_WIN:
            subprocess.Popen(f'explorer /select,"{p}"')
        else:
            subprocess.Popen(["xdg-open", os.path.dirname(p)])

    def show_info(self):
        if not self._need():
            return
        dlg = InfoDialog(self, self.cur_path, self.cur_img)
        dark_titlebar(dlg)
        dlg.adjustSize()
        g = self.geometry()
        dlg.move(g.right() - dlg.width() - 24, g.top() + 40)
        dlg.show()

    # ---- 打印
    def advanced_print(self):
        if not self._need():
            return
        dlg = PrintDialog(self, self._print_image())
        dark_titlebar(dlg)
        dlg.exec()

    def _print_image(self):
        if self.canvas.pix is not None and self.canvas.rot:
            return self.canvas.pix.toImage()
        return self.cur_img

    def system_print(self):
        if not self._need():
            return
        pr = QPrinter(QPrinter.HighResolution)
        dlg = QPrintDialog(pr, self)
        if dlg.exec() == QDialog.Accepted:
            paint_print(pr, self._print_image(), 1, "fit", 0)

    def add_pin(self, img, pos, dpr):
        w = PinWindow(self, img, pos, dpr)
        self._pins.append(w)
        w.destroyed.connect(lambda _=None, w=w: self._pins.remove(w) if w in self._pins else None)
        w.show()

    def show_ocr(self, img):
        dlg = OcrDialog(self)
        dark_titlebar(dlg)
        dlg.show()
        dlg.raise_()
        dlg.activateWindow()

        def done(ok, res, d=dlg):
            try:
                d.set_result(ok, res)
            except RuntimeError:
                pass

        run_bg(self.ocr_pool, lambda: run_ocr(img), done)

    # ---- 幻灯片
    def start_slideshow(self):
        if not self.files:
            return
        self._stop_movie()
        self._slideshow = SlideShow(self, list(self.files), max(0, self.index))
        self._slideshow.setAttribute(Qt.WA_DeleteOnClose)
        scr = self.screen() or QGuiApplication.primaryScreen()
        self._slideshow.setGeometry(scr.geometry())
        self._slideshow.showFullScreen()
        self._slideshow.activateWindow()

    def on_slideshow_closed(self, path):
        self._slideshow = None
        idx = next((i for i, p in enumerate(self.files) if p == path), self.index)
        self.show_index(idx)
        self.activateWindow()

    # ---- 拖放 / 关闭
    def dragEnterEvent(self, e):
        if e.mimeData().hasUrls():
            e.acceptProposedAction()

    def dropEvent(self, e):
        urls = [u.toLocalFile() for u in e.mimeData().urls() if u.isLocalFile()]
        if urls:
            self.open_path(urls[0])

    def showEvent(self, e):
        super().showEvent(e)
        if not getattr(self, "_shown_once", False):
            self._shown_once = True
            dark_titlebar(self)

    def closeEvent(self, e):
        if self.editor is not None and self.editor.dirty:
            self.editor.exit()
            if self.editor is not None:
                e.ignore()
                return
        if not self.isFullScreen():
            self.cfg["geom"] = bytes(self.saveGeometry().toBase64()).decode()
        save_cfg(self.cfg)
        for w in list(self._pins):
            w.close()
        super().closeEvent(e)


# ---------------------------------------------------------------- 单实例
def server_name():
    return "KanTuViewer-" + (os.environ.get("USERNAME") or os.environ.get("USER") or "u")


def forward_to_running(paths):
    sock = QLocalSocket()
    sock.connectToServer(server_name())
    if not sock.waitForConnected(300):
        return False
    sock.write(json.dumps(paths).encode("utf-8"))
    sock.flush()
    sock.waitForBytesWritten(1000)
    sock.disconnectFromServer()
    return True


def start_server(win):
    QLocalServer.removeServer(server_name())
    srv = QLocalServer(win)

    def on_conn():
        s = srv.nextPendingConnection()
        if s is None:
            return

        def read():
            try:
                paths = json.loads(bytes(s.readAll()).decode("utf-8"))
            except Exception:
                return
            if paths:
                win.open_path(paths[0])
            if win.isMinimized():
                win.showNormal()
            win.raise_()
            win.activateWindow()

        s.readyRead.connect(read)

    srv.newConnection.connect(on_conn)
    srv.listen(server_name())
    return srv


def main():
    if "--write-help" in sys.argv:
        i = sys.argv.index("--write-help")
        folder = sys.argv[i + 1] if len(sys.argv) > i + 1 else "."
        os.makedirs(folder, exist_ok=True)
        with open(os.path.join(folder, "使用说明.txt"), "w", encoding="utf-8-sig", newline="\r\n") as f:
            f.write(help_text())
        return
    if "--make-icon" in sys.argv:
        app = QApplication(sys.argv)
        pm = make_app_icon(256)
        out = os.path.join(os.path.dirname(os.path.abspath(__file__)), "kantu.ico")
        if Image is not None:
            tmp = out + ".png"
            pm.save(tmp, "PNG")
            with Image.open(tmp) as im:
                im.save(out, sizes=[(16, 16), (24, 24), (32, 32), (48, 48), (64, 64), (128, 128), (256, 256)])
            os.remove(tmp)
        else:
            pm.save(out, "ICO")
        print("已生成", out)
        return

    if IS_WIN:
        try:
            ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID("KanTu.Viewer")
        except Exception:
            pass
    QApplication.setHighDpiScaleFactorRoundingPolicy(Qt.HighDpiScaleFactorRoundingPolicy.PassThrough)
    app = QApplication(sys.argv)
    app.setApplicationName(APP_NAME)
    app.setStyle("Fusion")
    app.setStyleSheet(QSS)
    app.setWindowIcon(QIcon(make_app_icon()))
    QImageReader.setAllocationLimit(0)
    global BUS
    BUS = _Bus()
    BUS.done.connect(lambda cb, ok, res: cb(ok, res))

    cfg = load_cfg()
    args = [a for a in sys.argv[1:] if not a.startswith("-")]
    if not cfg["multi_window"] and forward_to_running(args):
        return

    win = MainWindow(cfg)
    srv = start_server(win) if not cfg["multi_window"] else None
    win.show()
    if args:
        QTimer.singleShot(0, lambda: win.open_path(args[0]))
    code = app.exec()
    del srv
    sys.exit(code)


if __name__ == "__main__":
    main()
