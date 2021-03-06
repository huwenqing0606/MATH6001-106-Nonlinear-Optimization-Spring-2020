#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Sun Mar 29 16:44:22 2020

@author: Wenqing Hu (Missouri S&T)
"""

#SGD, SVRG and SARAH for quadratic loss and Gaussian input data
#tensorflow version=1.14.0

import numpy as np
import matplotlib.pyplot as plt
import matplotlib as mpl
from mpl_toolkits.mplot3d import Axes3D
from matplotlib import animation
from random import sample, choice

import datetime
starttime = datetime.datetime.now()

import tensorflow as tf
tf.enable_eager_execution()

#set the parameters A, B for the loss function
A=1
B=1
#set the training sample size and the batchsize
training_sample_size=100
batchsize=1
#for SGD, set the number of iteration steps
num_steps=1000
#for SVRG, set the number of epochs and epochlength (m)
num_epochs=100
epochlength=10
#set the learning rate
lr=0.01

#a small tool function, calculate the length of sample_x and sample_y, they should be equal
def size(sample_x, sample_y):
    if len(sample_x)==len(sample_y):
        length=len(sample_y)
    else:
        print("Number of samples x and y do not match!")
        return None
    return length

"""
Loss Function L(w_1, w_2; (x_1, x_2, y)) = 0.5(Aw_1x_1+Bw_2x_2-y)^2 for A, B>0
and its gradients with respect to the weight parameters w_1 and w_2
the gradients are calculated via the tf.GradientTape() mode
"""
class LossFunction(object):
    def __init__(self,
                 axA,
                 axB):
        self.axA=axA
        self.axB=axB
    
    #value of the loss function    
    def value(self, w, x, y):
        return 0.5*(self.axA*w[0]*x[0]+self.axB*w[1]*x[1]-y)**2
    
    #gradient of the loss function with respect to the weights (w_1, w_2)
    def grad(self, w, x, y):
        tfw_1=tf.Variable(initial_value=w[0], dtype='float')
        tfw_2=tf.Variable(initial_value=w[1], dtype='float')
        with tf.GradientTape() as tape:
            loss=0.5*tf.math.square(tf.subtract(tf.add(tf.multiply(tf.multiply(self.axA, tfw_1), x[0]), tf.multiply(tf.multiply(self.axB, tfw_2), x[1])), y))
        grad_w_1, grad_w_2=tape.gradient(loss, [tfw_1, tfw_2])
        return np.array([grad_w_1.numpy(), grad_w_2.numpy()])
    
    #average of a sequence of function=loss functions/loss gradients for a given list of samples (x_i, y_i)
    def average(self, w, sample_x, sample_y, function):
        average=function(w, sample_x[0], sample_y[0])
        sample_size=size(sample_x, sample_y)
        for i in range(sample_size-1):
            average+=function(w, sample_x[i+1], sample_y[i+1])
        average=average/sample_size
        return average
   
    
"""
The stochastic optimizer for: SGD, SVRG, SARAH
first create the updates for each iteration, then optimizes via different schemes of iteration loop
"""
class stochastic_optimizer(object):
    def __init__(self, 
                 function,              #the loss function class (contains grad info)
                 training_sample_x,     #training and test samples
                 training_sample_y,     
                 test_sample_x, 
                 test_sample_y):
        self.function=function
        self.training_sample_x=training_sample_x
        self.training_sample_y=training_sample_y
        self.test_sample_x=test_sample_x
        self.test_sample_y=test_sample_y
    
    #the SGD estimator update = the change of parameter via stochastic gradients    
    def SGD_update(self, w, lr, batchsize):
        #detect the size of the training set
        trainingsize=size(self.training_sample_x, self.training_sample_y)
        #randomly choose the index set that forms the mini-batch
        batch_index=sample(list(range(0,trainingsize)), batchsize)
        #from the mini-batch index set select the corresponding training samples (x, y)
        batch_x=[]
        batch_y=[]
        for i in range(batchsize):
            batch_x.append(self.training_sample_x[batch_index[i]])
            batch_y.append(self.training_sample_y[batch_index[i]])
        batch_x=np.array(batch_x)
        batch_y=np.array(batch_y)
        #calculate the stochastic gradient updates 
        grad=self.function.average(w, batch_x, batch_y, self.function.grad)
        update=-lr*grad
        return update
    
    #the SGD optimizer, iterates a certain number of steps to update the weights
    def SGD_optimizer(self, w_init, steps, lr, batchsize):
        w_current=w_init
        trajectory_w=[]
        loss_list=[]
        test_error_list=[]
        for i in range(steps):
            #record the current model weights w 
            trajectory_w.append(w_current) 
            #calculate the test error for the current model weights w
            test_error=self.function.value(w_current, self.test_sample_x, self.test_sample_y)
            test_error_list.append(test_error)
            #calculate the training error (loss) for the current model weights w
            loss_list.append(self.function.average(w_current, self.training_sample_x, self.training_sample_y, self.function.value))
            #update w via stochastic optimization
            w=w_current+self.SGD_update(w_current, lr, batchsize)
            w_current=w
        return trajectory_w, loss_list, test_error_list

    #the SVRG estimator update = the inner loop update via variance-reduced stochastic gradients
    # w_checkpoint is the checkpoint w value recorded, i.e., the w-tilde in the Algorithm in the SVRG paper (Johnson-Zhang, NIPS 2013)
    def SVRG_update(self, w, lr, w_checkpoint):
        #grad_checkpoint is the gradient value of the empirical loss at the checkpoint, i.e., the mu-tilde
        grad_checkpoint=self.function.average(w_checkpoint, self.training_sample_x, self.training_sample_y, self.function.grad)
        #sample one random index from the set [0,...,training_size-1]
        trainingsize=size(self.training_sample_x, self.training_sample_y)
        index=choice(list(range(0,trainingsize)))
        #return the variance-reduced stochastic gradient
        grad_1 = self.function.grad(w, self.training_sample_x[index], self.training_sample_y[index])
        grad_2 = self.function.grad(w_checkpoint, self.training_sample_x[index], self.training_sample_y[index])
        grad = grad_1 - grad_2 + grad_checkpoint
        update = -lr*grad
        return update
    
    #the SVRG optimizer, iterates a certain number of epochs, with each epoch under a cetain length (epochlength=m), to get the updated weights
    def SVRG_optimizer(self, w_init, epochs, epochlength, lr):
        w_checkpoint=w_init
        trajectory_w=[]
        loss_list=[]
        test_error_list=[]
        for s in range(epochs):
            #record the current model weights w 
            trajectory_w.append(w_checkpoint) 
            #calculate the test error for the current model weights w
            test_error=self.function.value(w_checkpoint, self.test_sample_x, self.test_sample_y)
            test_error_list.append(test_error)
            #calculate the training error (loss) for the current model weights w
            loss_list.append(self.function.average(w_checkpoint, self.training_sample_x, self.training_sample_y, self.function.value))
            #the inner loop list of w is initialized, will fill in w_1,...,w_m (m=epochlength)
            w_innerloop_list=[]
            #start the inner loop at w_checkpoint
            w_current=w_checkpoint
            for i in range(epochlength):
                w_next = w_current + self.SVRG_update(w_current, lr, w_checkpoint)
                w_innerloop_list.append(w_next)
                w_current=w_next
            #update the checkpoint by randomly select from the list in the inner loop w_1,...,w_m (m=epochlength)
            w_checkpoint=choice(list(w_innerloop_list))
        return trajectory_w, loss_list, test_error_list
    
    #the SARAH estimator update = the inner loop update via variance-reduced stochastic gradients
    def SARAH_update(self, w_current, w_previous, lr, update_previous):
        #sample one random index from the set [0,...,training_size-1]
        trainingsize=size(self.training_sample_x, self.training_sample_y)
        index=choice(list(range(0,trainingsize)))
        #return the SARAH version of the variance-reduced stochastic gradient
        grad_1 = self.function.grad(w_current, self.training_sample_x[index], self.training_sample_y[index])
        grad_2 = self.function.grad(w_previous, self.training_sample_x[index], self.training_sample_y[index])
        grad = grad_1 - grad_2 
        update = - lr*grad + update_previous
        return update
    
    #the SARAH optimizer, iterates a certain number of epochs, with each epoch under a cetain length (epochlength=m), to get the updated weights
    def SARAH_optimizer(self, w_init, epochs, epochlength, lr):
        w_checkpoint=w_init
        trajectory_w=[]
        loss_list=[]
        test_error_list=[]
        for s in range(epochs):
            #record the current model weights w 
            trajectory_w.append(w_checkpoint) 
            #calculate the test error for the current model weights w
            test_error=self.function.value(w_checkpoint, self.test_sample_x, self.test_sample_y)
            test_error_list.append(test_error)
            #calculate the training error (loss) for the current model weights w
            loss_list.append(self.function.average(w_checkpoint, self.training_sample_x, self.training_sample_y, self.function.value))
            #the inner loop list of w is initialized, will fill in w_1,...,w_m (m=epochlength)
            w_innerloop_list=[]
            #start the inner loop at w_checkpoint
            w_previous=w_checkpoint
            w_innerloop_list.append(w_previous)
            update_previous=-lr*self.function.average(w_checkpoint, self.training_sample_x, self.training_sample_y, self.function.grad)
            w_current=w_previous-lr*update_previous
            for i in range(epochlength):
                w_innerloop_list.append(w_current)
                update_current = self.SARAH_update(w_current, w_previous, lr, update_previous)
                w_next = w_current + update_current 
                update_previous = update_current
                w_previous = w_current
                w_current = w_next
            #update the checkpoint by randomly select from the list in the inner loop w_1,...,w_m (m=epochlength)
            w_checkpoint=choice(list(w_innerloop_list))
        return trajectory_w, loss_list, test_error_list
    

        
        
"""
running the code, plot 
(1) the trajectory animation; 
(2) the evolution of the training error; 
(3) the evolution of test error.
"""
if __name__ == "__main__":
    #generate the training samples (x_i, y_i)
    training_sample_x=np.random.normal(0,1,size=(training_sample_size, 2))
    training_sample_y=np.random.normal(0,1,size=training_sample_size)
    #initialize the initial weights
    w_init=[1, 1]
    #pick a particular pair of test sample (x, y) from the given distribution
    test_sample_x=np.random.normal(0,1,size=2)
    test_sample_y=np.random.normal(0,1,size=1)
    #optimization step obtain a sequence of losses and weights trajectory
    for optname in {"SVRG"}:
        #set the loss function and the stochastic optimizer with given training and test samples
        function=LossFunction(axA=A, axB=B)
        optimizer=stochastic_optimizer(function=function, 
                                       training_sample_x=training_sample_x,
                                       training_sample_y=training_sample_y,
                                       test_sample_x=test_sample_x,
                                       test_sample_y=test_sample_y)
        #optimize, SGD, SVRG and SARAH
        if optname=="SGD":
            trajectory_w, loss_list, test_error_list=optimizer.SGD_optimizer(w_init, num_steps, lr, batchsize)
        elif optname=="SVRG":
            trajectory_w, loss_list, test_error_list=optimizer.SVRG_optimizer(w_init, num_epochs, epochlength, lr)
        elif optname=="SARAH":
            trajectory_w, loss_list, test_error_list=optimizer.SARAH_optimizer(w_init, num_epochs, epochlength, lr)        
        else:
            print(0)

        #print the weight, loss and test error sequence
        print("weight trajectory=", trajectory_w)
        print("loss=", loss_list)
        print("test error=", test_error_list)
        
        #plot the trajctory as an animation
        trajectory_w_1=[]
        trajectory_w_2=[]
        for index in range(len(trajectory_w)):
            trajectory_w_1.append(trajectory_w[index][0])
            trajectory_w_2.append(trajectory_w[index][1])
        fig = plt.figure()
        ax=Axes3D(fig)
        line=ax.plot([],[],'b:')
        point=ax.plot([],[],'bo',markersize=10)
        images=[]
        def init():
            line=ax.plot([],[],'b:',markersize=8)
            point=ax.plot([],[],'bo',markersize=10)
            return line,point
        def anmi(i):
            ax.clear()
            line =ax.plot(trajectory_w_1[0:i],trajectory_w_2[0:i],loss_list[0:i],'b:', markersize=8)
            point = ax.plot(trajectory_w_1[i-1:i],trajectory_w_2[i-1:i],loss_list[i-1:i],'bo', markersize=10)
            return line,point
        if optname=="SGD":
            anim = animation.FuncAnimation(fig, anmi, init_func=init,
                                           frames=num_steps, interval=10, blit=False,repeat=False)
            anim.save(optname+'_A='+str(A)+'_B='+str(B)+'_trainingsize='+str(training_sample_size)+'_batchsize='+str(batchsize)+'_learningrate='+str(lr)+'_steps='+str(num_steps)+'.gif', writer='imagemagick')
        elif optname=="SVRG":
            anim = animation.FuncAnimation(fig, anmi, init_func=init,
                                           frames=num_epochs, interval=10, blit=False,repeat=False)
            anim.save(optname+'_A='+str(A)+'_B='+str(B)+'_trainingsize='+str(training_sample_size)+'_learningrate='+str(lr)+'_epochs='+str(num_epochs)+'_epochlength='+str(epochlength)+'.gif', writer='imagemagick')
        elif optname=="SARAH":
            anim = animation.FuncAnimation(fig, anmi, init_func=init,
                                           frames=num_epochs, interval=10, blit=False,repeat=False)
            anim.save(optname+'_A='+str(A)+'_B='+str(B)+'_trainingsize='+str(training_sample_size)+'_learningrate='+str(lr)+'_epochs='+str(num_epochs)+'_epochlength='+str(epochlength)+'.gif', writer='imagemagick')
        else:
            print(0)


        #plot the training error (loss) and the test error
        fig = plt.figure()
        mpl.rcParams['legend.fontsize'] = 10
        plt.plot(loss_list)
        plt.xlabel('iteration')
        plt.ylabel('loss')
        plt.title(optname)
        if optname=="SGD":
            plt.savefig('Loss_'+optname+'_A='+str(A)+'_B='+str(B)+'_trainingsize='+str(training_sample_size)+'_batchsize='+str(batchsize)+'_learningrate='+str(lr)+'_steps='+str(num_steps)+'.jpg')
        elif optname=="SVRG":
            plt.savefig('Loss_'+optname+'_A='+str(A)+'_B='+str(B)+'_trainingsize='+str(training_sample_size)+'_learningrate='+str(lr)+'_epochs='+str(num_epochs)+'_epochlength='+str(epochlength)+'.jpg')
        elif optname=="SARAH":
            plt.savefig('Loss_'+optname+'_A='+str(A)+'_B='+str(B)+'_trainingsize='+str(training_sample_size)+'_learningrate='+str(lr)+'_epochs='+str(num_epochs)+'_epochlength='+str(epochlength)+'.jpg')
        else:
            print(0)     
        plt.show()

        plt.plot(test_error_list)
        plt.xlabel('iteration')
        plt.ylabel('test error')
        plt.title(optname)
        if optname=="SGD":
            plt.savefig('TestError_'+optname+'_A='+str(A)+'_B='+str(B)+'_trainingsize='+str(training_sample_size)+'_batchsize='+str(batchsize)+'_learningrate='+str(lr)+'_steps='+str(num_steps)+'.jpg')
        elif optname=="SVRG":
            plt.savefig('TestError_'+optname+'_A='+str(A)+'_B='+str(B)+'_trainingsize='+str(training_sample_size)+'_learningrate='+str(lr)+'_epochs='+str(num_epochs)+'_epochlength='+str(epochlength)+'.jpg')
        elif optname=="SARAH":
            plt.savefig('TestError_'+optname+'_A='+str(A)+'_B='+str(B)+'_trainingsize='+str(training_sample_size)+'_learningrate='+str(lr)+'_epochs='+str(num_epochs)+'_epochlength='+str(epochlength)+'.jpg')
        else:
            print(0)
        plt.show()

endtime = datetime.datetime.now()
print("running time:", (endtime-starttime).seconds, "seconds.")