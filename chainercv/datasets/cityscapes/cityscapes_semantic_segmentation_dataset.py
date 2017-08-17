import glob
import os

import numpy as np

from chainer import dataset
from chainer.dataset import download
from chainercv.datasets.cityscapes.cityscapes_utils import cityscapes_labels
from chainercv.utils import read_image


class CityscapesSemanticSegmentationDataset(dataset.DatasetMixin):

    """Dataset class for a semantic segmentation task on `Cityscapes dataset`_.

    .. _`Cityscapes dataset`: https://www.cityscapes-dataset.com

    .. note::

        Please manually downalod the data because it is not allowed to
        re-distribute Cityscapes dataset.

    Args:
        data_dir (string): Path to the dataset directory. The directory should
            contain at least two directories, :obj:`leftImg8bit` and either
            :obj:`gtFine` or :obj:`gtCoarse`. If :obj:`None` is given, it uses
            :obj:`$CHAINER_DATSET_ROOT/pfnet/chainercv/cityscapes` as default.
        label_mode (string): The resolution of the labels. It should be either
            :obj:`fine` or :obj:`coarse`.
        split ({'train', 'val'}): Select from dataset splits used in
            Cityscapes dataset.
        ignore_labels (bool): If True, the labels marked :obj:`ignoreInEval`
            defined in the original
            `cityscapesScripts<https://github.com/mcordts/cityscapesScripts>_`
            will be replaced with :obj:`-1` in the :meth:`get_example` method.
            The default value is :obj:`True`

    """

    def __init__(self, data_dir=None, label_mode=None, split='train',
                 ignore_labels=True):
        if data_dir is None:
            data_dir = download.get_dataset_directory(
                'pfnet/chainercv/cityscapes')
        if label_mode is None:
            raise ValueError('You need to give some value to \'label_mode\' '
                             'argment.')
        elif label_mode != 'fine' and label_mode != 'coarse':
            raise ValueError('\'label_name\' argment should be eighter '
                             '\'fine\' or \'coarse\'. But {} was '
                             'given.'.format(label_mode))

        img_dir = os.path.join(data_dir, os.path.join('leftImg8bit', split))
        resol = 'gtFine' if label_mode == 'fine' else 'gtCoarse'
        label_dir = os.path.join(data_dir, resol)
        self.ignore_labels = ignore_labels

        self.label_fnames = list()
        self.img_fnames = list()
        city_dnames = list()
        for dname in glob.glob(os.path.join(label_dir, '*')):
            if split in dname:
                for city_dname in glob.glob(os.path.join(dname, '*')):
                    for label_fname in glob.glob(
                            os.path.join(city_dname, '*_labelIds.png')):
                        self.label_fnames.append(label_fname)
                        city_dnames.append(os.path.basename(city_dname))
        for city_dname, label_fname in zip(city_dnames, self.label_fnames):
            label_fname = os.path.basename(label_fname)
            img_fname = label_fname.replace(
                '{}_labelIds'.format(resol), 'leftImg8bit')
            img_fname = os.path.join(img_dir, city_dname, img_fname)
            self.img_fnames.append(img_fname)

    def __len__(self):
        return len(self.img_fnames)

    def get_example(self, i):
        """Returns the i-th example.

        Returns a color image and a label image. The color image is in CHW
        format and the label image is in HW format.

        Args:
            i (int): The index of the example.

        Returns:
            tuple of a color image and a label whose shapes are (3, H, W) and
            (H, W) respectively. H and W are height and width of the image.
            The dtype of the color image is :obj:`numpy.float32` and
            the dtype of the label image is :obj:`numpy.int32`.

        """
        img = read_image(self.img_fnames[i])
        label_orig = read_image(
            self.label_fnames[i], dtype=np.int32, color=False)[0]
        H, W = label_orig.shape
        if self.ignore_labels:
            label_out = np.ones((H, W), dtype=np.int32) * -1
            for label in cityscapes_labels:
                if not label.ignoreInEval:
                    label_out[np.where(label_orig == label.id)] = label.trainId
        else:
            label_out = label_orig
        return img, label_out
