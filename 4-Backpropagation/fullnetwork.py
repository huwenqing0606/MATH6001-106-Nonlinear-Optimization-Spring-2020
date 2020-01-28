# -*- coding: utf-8 -*- #
"""
Created on Wed Jan 22 08:23:40 2020
@author: Wenqing Hu (Missouri S&T)
"""

"""
Construct the output function of a fully connnected neural network 
with L layers and network size n_1, ..., n_L
parameters L, n_1, ..., n_L are given
"""

import numpy as np
from activations import Sigmoid, ReLU, Tanh, Exponential

"""
one layer of the neural network, input vector x^{in}, output \sigma(W x^{in} + b)
W is weight vector, b is the bias
"""
class onelayer(object):
    
    def __init__(self,
                 inputvector=[],    #input vector， has to be array type#
                 activation=Sigmoid(),        #activation function, will be applied termwise#
                 weight=[],         #weights from input to output layer, should be an array of size outputsize x inputsize#
                 bias=[],           #bias vectors in the particular layer, a vector array of length = outputsize#
                 ):
        self.inputvector=inputvector
        self.activation=activation
        self.weight=weight
        self.bias=bias
        
    def output(self):
        print("weight*input=", self.weight*self.inputvector)
        preoutput=self.weight*self.inputvector+self.bias
        length=preoutput.size
        print("preoutput=", preoutput)
        print("length=", length)
        output=[]
        for i in range(length):
            print("i=", i)
            output.append(self.activation.fn(preoutput[i]))
        print("output=", np.array(output))
        return np.array(output)
    



"""
a fully connected neural network with L hidden layers, input is a number x, output is a number y
L hidden layers with layer sizes n_1, ..., n_L
activation are given the same for all layers
all weights and biases are initialized under the LeCun initilization: W_{ij} as N(0,1/n_l) where l is the label of hidden layer and b_k as N(0,1)
"""    
class fullnetwork(object):
    
    def __init__(self,
                 L=1, #number of hidden layers#
                 n=np.random.randint(1, 6, size=1), #network size for each hidden layer n[0]=n_1, ..., m[L-1]=n_L#
                 activation=Sigmoid()):
        self.L=L
        self.n=n
        self.activation=activation
    
    def output(self, x):
        layervector=np.array(x) #layervector corresponds to the outputs of all neurons at the current layer#
        print("layervector=", layervector)
        for l in range(self.L):
            if l==self.L-1:
                weight=[[np.random.normal(loc=0.0, scale=1/np.sqrt(self.n[l])) for i in range(self.n[l])] for j in range(1)]
                print("weight=", np.array(weight))
                bias=[[np.random.normal(loc=0.0, scale=1.0) for i in range(1)] for k in range(1)]                        
                print("bias=", np.array(bias))
                addlayer=onelayer(inputvector=layervector, activation=self.activation, weight=np.array(weight), bias=np.array(bias))
                layervector=addlayer.output()
            elif l==0:
                weight=[[np.random.normal(loc=0.0, scale=1.0) for i in range(1)] for j in range(self.n[l])]
                print("weight=", np.array(weight))
                bias=[[np.random.normal(loc=0.0, scale=1.0) for i in range(1)] for j in range(self.n[l])]                        
                print("bias=", np.array(bias))
                addlayer=onelayer(inputvector=layervector, activation=self.activation, weight=np.array(weight), bias=np.array(bias))
                layervector=addlayer.output()
            else:
                weight=[[np.random.normal(loc=0.0, scale=1/np.sqrt(self.n[l-1])) for i in range(self.n[l-1])] for j in range(self.n[l])]
                print("weight=", np.array(weight))
                bias=[[np.random.normal(loc=0.0, scale=1.0) for i in range(1)] for k in range(self.n[l])]                        
                print("bias=", np.array(bias))
                addlayer=onelayer(inputvector=layervector, activation=self.activation, weight=np.array(weight), bias=np.array(bias))
                layervector=addlayer.output()
        return layervector
    
    

"""
test the output
"""
if __name__ == "__main__":
    L=5 #number of hidden layers#
    n=np.random.randint(1, 6, size=L) #network size for each hidden layer n[0]=n_1, ..., m[L-1]=n_L#
    print(n)
    network=fullnetwork(L=L, n=n, activation=Sigmoid())
    network.output(1)
    weight=[[1 for i in range(2)] for j in range(3)]
    print("weight=", np.array(weight))
    bias=[1 for k in range(3)]                        
    print("bias=", np.array(bias))
    addlayer=onelayer(inputvector=np.array([1,2]), activation=Sigmoid(), weight=np.array(weight), bias=np.array(bias))
    layervector=addlayer.output()

    
