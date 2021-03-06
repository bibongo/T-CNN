#!/usr/bin/env python

import numpy as np
import sys
import os
import os.path as osp
from argparse import ArgumentParser
from glob import glob
sys.path.insert(1, '.')
from vdetlib.utils.protocol import proto_load, proto_dump, track_proto_from_annot_proto, load_frame_to_det
from vdetlib.vdet.dataset import imagenet_vdet_class_idx, imagenet_det_200_class_idx
from vdetlib.vdet.tubelet_cls import scoring_tracks, raw_dets_spatial_max_pooling, score_proto_temporal_maxpool, score_proto_interpolation

import time

def main(args):
    vid_proto = proto_load(args.vid_file)
    frame_to_det = load_frame_to_det(vid_proto, args.det_dir)

    if not os.path.isdir(args.save_dir):
        try:
            os.makedirs(args.save_dir)
        except:
            pass

    track_files = glob(osp.join(args.track_dir, '*.track*'))
    if len(track_files) == 0:
        print "Warning: {} has no tracks".format(args.track_dir)
        return

    for track_file in track_files:
        track_proto = proto_load(track_file)

        vid_name = vid_proto['video']
        assert vid_name == track_proto['video']
        cls_name = osp.basename(track_file).split('.')[1]
        cls_index = imagenet_vdet_class_idx[cls_name]

        # spatial max pooling
        score_proto = raw_dets_spatial_max_pooling(vid_proto, track_proto,
            frame_to_det, cls_index, overlap_thres=args.overlap_thres)

        # temporal max pooling
        temporal_max_score_proto = score_proto_temporal_maxpool(score_proto, args.window)

        # interpolation
        interpolated_score_proto = score_proto_interpolation(temporal_max_score_proto, vid_proto)

        # save score proto
        save_file = osp.join(args.save_dir,
                             '{}.{}.score'.format(vid_name, cls_name))
        if osp.isfile(save_file):
            print "{} already exists.".format(save_file)
            continue
        proto_dump(interpolated_score_proto, save_file)
        print "{} created.".format(save_file)


if __name__ == '__main__':
    parser = ArgumentParser()
    parser.add_argument('vid_file')
    parser.add_argument('track_dir')
    parser.add_argument('det_dir')
    parser.add_argument('save_dir')
    parser.add_argument('--overlap_thres', type=float, required=True)
    parser.add_argument('--window', type=int, required=False, default=1,
        help='Temporal max-pooling window size. Must be odd number. [1]')
    args = parser.parse_args()
    main(args)
