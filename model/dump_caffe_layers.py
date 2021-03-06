# -*- coding: utf-8 -*-
""" Dump Caffe layers

This module dumped information from Caffe model. 

################################################################################
# Author: Weikun Han <weikunhan@gmail.com>
# Crate Date: 04/13/2018
# Update:
# Reference: 
################################################################################
"""

import caffe
import numpy as np
import os

# Please modify input path to locate you file
CAFFE_DIR = 'caffe/'
LAYERS_OUTPUT = 'caffe/layers'

# Check location to save datasets
if not os.path.exists(LAYERS_OUTPUT):
    os.makedirs(LAYERS_OUTPUT)
    
# Setup input and output name
caffe_proto_filename = 'pose_deploy.prototxt'
caffe_model_filename = 'pose_iter_440000.caffemodel'

# Initial Caffe network
caffe_model = os.path.join(CAFFE_DIR, caffe_model_filename)
caffe_proto = os.path.join(CAFFE_DIR, caffe_proto_filename)
caffe.set_mode_cpu()
net = caffe.Net(caffe_proto, caffe_model, caffe.TEST)

# Check for each layer name and each input data shapes 
for name, blob in net.blobs.items():
    
    print('{:<5}:  {}'.format(name, blob.data.shape))

print('------------------------Beginning dumping------------------------------')
    
# Write out weight matrices and bias vectors
for name, param in net.params.items():
    np.save(os.path.join(LAYERS_OUTPUT, 'w_{:s}.npy'.format(name)), 
            param[0].data)
    np.save(os.path.join(LAYERS_OUTPUT, 'b_{:s}.npy'.format(name)), 
            param[1].data)
    
    print('{:<5}:  weight-{} bias-{}'.format(name, 
                                             param[0].data.shape, 
                                             param[1].data.shape))

print('-------------------------Finished dumping------------------------------')
