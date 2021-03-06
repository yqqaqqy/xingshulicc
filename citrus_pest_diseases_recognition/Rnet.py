# -*- coding: utf-8 -*-
from __future__ import print_function
"""
Created on Wed Feb 13 16:16:50 2019

@author: xingshuli
"""
from keras.layers import Conv2D
from keras.layers import Dense
from keras.layers import MaxPooling2D
from keras.layers import Activation
from keras.layers import GlobalAveragePooling2D

from keras.layers import Dropout
from keras.layers import BatchNormalization
from keras.layers import Concatenate
from keras.layers import Input

from keras import backend as K
from keras.models import Model

from keras import regularizers

weight_decay = 0.001

def _initial_conv_block(input):
    channel_axis = 1 if K.image_data_format() == 'channels_first' else -1
    x = Conv2D(filters = 32, kernel_size = (7, 7), strides = (2, 2), padding = 'same', 
               kernel_regularizer = regularizers.l2(weight_decay), name = 'init_conv')(input)
    x = BatchNormalization(axis = channel_axis, name = 'init_conv_bn')(x)
    x = Activation('relu', name = 'init_conv_relu')(x)
    x = MaxPooling2D(pool_size = (3, 3), strides = (2, 2), padding = 'same', 
                     name = 'init_MaxPool')(x)
    
    return x


def _MLP_block(inputs, filters, block):
    if K.image_data_format() == 'channels_first':
        bn_axis = 1
    else:
        bn_axis = -1
    
    base_name = 'block' + '_' + str(block)
    
    x = Conv2D(filters = filters, kernel_size = (3, 3), strides = (1, 1), padding = 'same', 
               kernel_regularizer = regularizers.l2(weight_decay), name = base_name + '_conv_1')(inputs)
    x = BatchNormalization(axis = bn_axis, name = base_name + '_bn_1')(x)
    x = Activation('relu', name = base_name + '_relu_1')(x)
    
    x = Conv2D(filters = filters, kernel_size = (1, 1), strides = (1, 1), padding = 'same', 
               use_bias = False, kernel_regularizer = regularizers.l2(weight_decay), name = base_name + '_conv_2')(x)
    x = BatchNormalization(axis = bn_axis, name = base_name + '_bn_2')(x)
    x = Activation('relu', name = base_name + '_relu_2')(x)
    
    x = Conv2D(filters = filters, kernel_size = (1, 1), strides = (1, 1), padding = 'same', 
               use_bias = False, kernel_regularizer = regularizers.l2(weight_decay), name = base_name + '_conv_3')(x)
    x = BatchNormalization(axis = bn_axis, name = base_name + '_bn_3')(x)
    x = Activation('relu', name = base_name + '_relu_3')(x)
    
    return x


def _end_block(inputs, filters):
    channel_axis = 1 if K.image_data_format() == 'channels_first' else -1
    base_name = 'end_block'
    
    x = Conv2D(filters = filters, kernel_size = (1, 1), strides = (1, 1), padding = 'same', 
               use_bias = False, kernel_regularizer = regularizers.l2(weight_decay), name = base_name + '_conv_1')(inputs)
    x = BatchNormalization(axis = channel_axis, name = base_name + '_bn_1')(x)
    x = Activation('relu', name = base_name + '_relu_1')(x)
    
    x = Conv2D(filters = filters, kernel_size = (1, 1), strides = (1, 1), padding = 'same', 
               use_bias = False, kernel_regularizer = regularizers.l2(weight_decay), name = base_name + '_conv_2')(x)
    x = BatchNormalization(axis = channel_axis, name = base_name + '_bn_2')(x)
    x = Activation('relu', name = base_name + '_relu_2')(x)
    
    return x

def New_net(input_shape, classes):
    inputs = Input(shape = input_shape)
    
    x_1 = _initial_conv_block(inputs)
#    The shape of x_1: 56 x 56 x 32
    
    x_2 = _MLP_block(x_1, 64, 1)
#    The shape of x_2: 56 x 56 x 64
    
    Pool_1 = MaxPooling2D(pool_size = (2, 2), strides = (2, 2), padding = 'same', 
                          name = 'MaxPool_1')(x_2)
#    The shape of Pool_1: 28 x 28 x 64
    
    x_3 = Concatenate(axis = -1)([x_1, x_2])
#    The shape of x_3: 56 x 56 x 96
    
    x_4 = _MLP_block(x_3, 128, 2)
#    The shape of x_4: 56 x 56 x 128
    
    Pool_2 = MaxPooling2D(pool_size = (2, 2), strides = (2, 2), padding = 'same', 
                          name = 'MaxPool_2')(x_4)
#    The shape of Pool_2: 28 x 28 x 128
    
    x_5 = Concatenate(axis = -1)([Pool_1, Pool_2])
#    The shape of x_5: 28 x 28 x 192
    
    x_6 = _MLP_block(x_5, 256, 3)
#    The shape of x_6: 28 x 28 x 256
    
    Pool_3 = MaxPooling2D(pool_size = (2, 2), strides = (2, 2), padding = 'same', 
                          name = 'MaxPool_3')(x_6)
#    The shape of Pool_3: 14 x 14 x 256
    
    x_7 = Concatenate(axis = -1)([Pool_2, x_6])
#    The shape of x_7: 28 x 28 x 384
    
    x_8 = _MLP_block(x_7, 512, 4)
#    The shape of x_8: 28 x 28 x 512
    
    Pool_4 = MaxPooling2D(pool_size = (2, 2), strides = (2, 2), padding = 'same', 
                          name = 'MaxPool_4')(x_8)
#    The shape of Pool_4: 14 x 14 x 512
    
    x = Concatenate(axis = -1)([Pool_3, Pool_4])
#    The shape of x: 14 x 14 x 768
    x = _end_block(x, 512)
    x = MaxPooling2D(pool_size = (2, 2), strides = (2, 2), padding = 'same', 
                     name = 'MaxPool_5')(x)
#    The shape of x: 7 x 7 x 512
    
    output = GlobalAveragePooling2D()(x)
    
    output = Dense(512, activation = 'relu', name = 'fc_1')(output)
    output = Dropout(0.5)(output)
    output = Dense(classes, activation = 'softmax', name = 'fc_2')(output)
    
    model = Model(inputs = inputs, outputs = output, name = 'R_net')
    
    return model







