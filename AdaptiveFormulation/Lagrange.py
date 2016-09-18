import numpy as np
import math

'''
Lagrange multiplier augmented function:

A(x,y; lambda) =   f(x,y) + lambda * g(x,y)

f(x, y) = summation( T/p_i * v(p))
g(x, y) = -(alpha + beta * sum(s_i/p_i) - rate * T)^2
'''

NUM_SENSOR = 4.0
ROS = [1.0, 1.0,1.0, 1.0]               # ro_i,     depends on sensor
GAMMAS = [0.08, 0.8, 2, 1]              # gamma_i,  depends on process/environment
SENSOR_BYTES = [2.0, 5.0, 5.0, 4.0]     # s_i,      depends on bytes produced by a sensor
S = SENSOR_BYTES
ALPHA = 1000
BETA = 3
RATE = 10                           # rate,     upload rate, bytes/sec

def infoValue(p, ro_i, gamma_i):
    return math.exp( -(p-ro_i) / gamma_i )

def func(X):
    p0 = X[0]
    p1 = X[1]
    p2 = X[2]
    p3 = X[3]
    T = X[4]
    L = X[5] # this is the multiplier. lambda is a reserved keyword in python

    return -((T/p0)*infoValue(p0, ROS[0], GAMMAS[0]) \
           + (T/p1)*infoValue(p1, ROS[1], GAMMAS[1]) \
           + (T/p2)*infoValue(p0, ROS[2], GAMMAS[2]) \
           + (T/p3)*infoValue(p0, ROS[3], GAMMAS[3]) \
           - L * math.pow((ALPHA + BETA * (  S[0]/p0 + S[1]/p1 + S[2]/p2 + S[3]/p3 ) - RATE * T), 2))


from scipy.optimize import minimize

bnds = ((0.6, 3600), (0.2, 3600), (0.2, 3600), (0.2, 3600), (1, 60), (None, None))
'''
p0 >= 0.6
p1 >= 0.2
p2 >= 0.2
p3 >= 0.2
1 <= T <= 60
'''
X2 = minimize(func, [0, 0, 0, 0, 0, 9],  bounds=bnds)         #these are the initial guesses for p[i] and T
#print "Max value: ", X2.x
print "maximized value of the objective function", -func(list(X2.x))

for i in range(0,4):
    print "Period", i, ": ", X2.x[i], " sec"
print "T (Time Interval to Upload)", X2.x[4], "sec"
