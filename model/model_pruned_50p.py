# -*- coding: utf-8 -*-
""" Model pruned %50

The model is based on the pruned Keras model (From dump_pruned_keras_model.ipynb)
The difference for the orignal Keras model just pruned some fiters from orignal.

------------------------Beginning dumping------------------------------

################################################################################
# Author: Weikun Han <weikunhan@gmail.com>
# Crate Date: 04/015/2018        
# Update:
# Reference: 
#    https://github.com/michalfaber/keras_Realtime_Multi-Person_Pose_Estimation
################################################################################
"""

from keras.models import Model
from keras.layers.merge import Concatenate
from keras.layers import Activation, Input, Lambda
from keras.layers.convolutional import Conv2D
from keras.layers.pooling import MaxPooling2D
from keras.layers.merge import Multiply
from keras.regularizers import l2
from keras.initializers import random_normal,constant

def relu(x): return Activation('relu')(x)

def conv(x, nf, ks, name, weight_decay):
    kernel_reg = l2(weight_decay[0]) if weight_decay else None
    bias_reg = l2(weight_decay[1]) if weight_decay else None

    x = Conv2D(nf, (ks, ks), padding='same', name=name,
               kernel_regularizer=kernel_reg,
               bias_regularizer=bias_reg,
               kernel_initializer=random_normal(stddev=0.01),
               bias_initializer=constant(0.0))(x)
    return x

def pooling(x, ks, st, name):
    x = MaxPooling2D((ks, ks), strides=(st, st), name=name)(x)
    return x

def vgg_block(x, weight_decay):
    # Block 1
    x = conv(x, 32, 3, "conv1_1", (weight_decay, 0))
    x = relu(x)
    x = conv(x, 32, 3, "conv1_2", (weight_decay, 0))
    x = relu(x)
    x = pooling(x, 2, 2, "pool1_1")

    # Block 2
    x = conv(x, 64, 3, "conv2_1", (weight_decay, 0))
    x = relu(x)
    x = conv(x, 64, 3, "conv2_2", (weight_decay, 0))
    x = relu(x)
    x = pooling(x, 2, 2, "pool2_1")

    # Block 3
    x = conv(x, 64, 3, "conv3_1", (weight_decay, 0))
    x = relu(x)
    x = conv(x, 128, 3, "conv3_2", (weight_decay, 0))
    x = relu(x)
    x = conv(x, 128, 3, "conv3_3", (weight_decay, 0))
    x = relu(x)
    x = conv(x, 128, 3, "conv3_4", (weight_decay, 0))
    x = relu(x)
    x = pooling(x, 2, 2, "pool3_1")

    # Block 4
    x = conv(x, 256, 3, "conv4_1", (weight_decay, 0))
    x = relu(x)
    x = conv(x, 256, 3, "conv4_2", (weight_decay, 0))
    x = relu(x)

    # Additional non vgg layers
    x = conv(x, 128, 3, "conv4_3_CPM", (weight_decay, 0))
    x = relu(x)
    x = conv(x, 128, 3, "conv4_4_CPM", (weight_decay, 0))
    x = relu(x)

    return x


def stage1_block(x, num_p, branch, weight_decay):
    
    # Block 1
    x = conv(x, 64, 3, 'conv5_1_CPM_L{}'.format(branch), (weight_decay, 0))
    x = relu(x)
    x = conv(x, 64, 3, 'conv5_2_CPM_L{}'.format(branch), (weight_decay, 0))
    x = relu(x)
    x = conv(x, 64, 3, 'conv5_3_CPM_L{}'.format(branch), (weight_decay, 0))
    x = relu(x)
    x = conv(x, 256, 1, 'conv5_4_CPM_L{}'.format(branch), (weight_decay, 0))
    x = relu(x)
    x = conv(x, num_p, 1, 'conv5_5_CPM_L{}'.format(branch), (weight_decay, 0))
    x = relu(x)
    
    return x


def stageT_block(x, num_p, stage, branch, weight_decay):
    
    # Block 1
    x = conv(x, 64, 7, "Mconv1_stage%d_L%d" % (stage, branch), (weight_decay, 0))
    x = relu(x)
    x = conv(x, 64, 7, "Mconv2_stage%d_L%d" % (stage, branch), (weight_decay, 0))
    x = relu(x)
    x = conv(x, 64, 7, "Mconv3_stage%d_L%d" % (stage, branch), (weight_decay, 0))
    x = relu(x)
    x = conv(x, 64, 7, "Mconv4_stage%d_L%d" % (stage, branch), (weight_decay, 0))
    x = relu(x)
    x = conv(x, 64, 7, "Mconv5_stage%d_L%d" % (stage, branch), (weight_decay, 0))
    x = relu(x)
    x = conv(x, 64, 1, "Mconv6_stage%d_L%d" % (stage, branch), (weight_decay, 0))
    x = relu(x)
    x = conv(x, num_p, 1, "Mconv7_stage%d_L%d" % (stage, branch), (weight_decay, 0))
    x = relu(x)

    return x


def apply_mask(x, mask1, mask2, num_p, stage, branch):
    w_name = "weight_stage%d_L%d" % (stage, branch)
    if num_p == 38:
        w = Multiply(name=w_name)([x, mask1]) # vec_weight

    else:
        w = Multiply(name=w_name)([x, mask2])  # vec_heat
    return w

def openpose_model():
    stages = 6
    np_branch1 = 38
    np_branch2 = 19

    img_input_shape = (None, None, 3)

    img_input = Input(shape=img_input_shape)

    img_normalized = Lambda(lambda x: x / 256 - 0.5)(img_input) # [-0.5, 0.5]

    # VGG
    stage0_out = vgg_block(img_normalized, None)

    # stage 1 - branch 1 (PAF)
    stage1_branch1_out = stage1_block(stage0_out, np_branch1, 1, None)

    # stage 1 - branch 2 (confidence maps)
    stage1_branch2_out = stage1_block(stage0_out, np_branch2, 2, None)

    x = Concatenate()([stage1_branch1_out, stage1_branch2_out, stage0_out])

    # stage t >= 2
    stageT_branch1_out = None
    stageT_branch2_out = None
    for sn in range(2, stages + 1):
        stageT_branch1_out = stageT_block(x, np_branch1, sn, 1, None)
        stageT_branch2_out = stageT_block(x, np_branch2, sn, 2, None)

        if (sn < stages):
            x = Concatenate()([stageT_branch1_out, stageT_branch2_out, stage0_out])

    model = Model(inputs=[img_input], outputs=[stageT_branch1_out, stageT_branch2_out])

    return model
