import numpy as np
import math
from scipy.optimize import minimize

'''
Lagrange multiplier augmented function:

A(x,y; lambda) =   f(x,y) + lambda * g(x,y)

f(x, y) = summation( T/p_i * v(p))
g(x, y) = -(alpha + beta * sum(s_i/p_i) - rate * T)^2
'''

class LagrangeCalculator(object):
    def __init__(self, sensors, rate, alpha, beta, lmbda):
        '''
        :param sensors: list of Sensor objects
        :param rate: rate calculated by simulator (i.e. 100.0)  upload rate, bytes/sec
        '''
        self.sensors = sensors
        self.num_of_sensor = len(sensors)
        self.ALPHA = alpha
        self.BETA = beta
        self.RATE = rate
        self.LAMBDA = lmbda
        self.ROS = []                           # ro_i,     depends on sensor
        self.GAMMAS = []                        # gamma_i,  depends on process/environment
        self.S = []                             # s_i,      depends on bytes produced by a sensor
        for i in range(0, self.num_of_sensor):
            self.ROS.append(sensors[i].period)
            self.GAMMAS.append(sensors[i].gamma)
            self.S.append(sensors[i].size)

    def infoValue(self, p, ro_i, gamma_i):
        '''
        :param p: Period (in second)
        :param ro_i: Minimum Period (in second)
        :param gamma_i: Scaling factor
        :return: Information value of this sensor reading
        '''
        return math.exp( -(p-ro_i) / gamma_i )

    def func(self, X):
        T = X[self.num_of_sensor]
        # p0 = X[0]
        # p1 = X[1]
        # p2 = X[2]
        # p3 = X[3]
        # T = X[4]
        # L = X[5] # this is the multiplier. lambda is a reserved keyword in python
        # return -((T/p0)*self.infoValue(p0, self.ROS[0], self.GAMMAS[0]) \
        #        + (T/p1)*self.infoValue(p1, self.ROS[1], self.GAMMAS[1]) \
        #        + (T/p2)*self.infoValue(p0, self.ROS[2], self.GAMMAS[2]) \
        #        + (T/p3)*self.infoValue(p0, self.ROS[3], self.GAMMAS[3]) \
        #        - L* self.LAMBDA * math.pow((self.ALPHA + self.BETA * (  self.S[0]/p0 + self.S[1]/p1 + self.S[2]/p2 + self.S[3]/p3 ) - self.RATE * T), 2))

        # value_term, bytes_term is a generator
        value_term = (((T / X[i]) * self.infoValue(X[i], self.ROS[i], self.GAMMAS[i])) for i in range(0, self.num_of_sensor))
        bytes_term = ((self.S[i]/X[i]) for i in range(0, self.num_of_sensor))

        # add the terms
        sum_value_terms = 0.0
        sum_bytes_terms = 0.0
        for i in value_term:
            sum_value_terms += i
        for i in bytes_term:
            sum_bytes_terms += i

        return -( sum_value_terms - self.LAMBDA * math.pow(self.ALPHA + self.BETA * (sum_bytes_terms - self.RATE * T), 2) )


    def tester(self):

        ########################################
        ## add the boundaries, example below ###
        # bnds = ((self.ROS[0], 36000.0), (self.ROS[1], 36000.0), (self.ROS[2], 36000.0), (self.ROS[3], 36000.0), (0.01, None))
        '''
                p0 >= 0.6
                p1 >= 0.2
                p2 >= 0.2
                p3 >= 0.2
                1 <= T <= 60
        '''
        bnds = ()                                   # boundary for T (time period to upload)
        for i in range(0, self.num_of_sensor):
            bnds = bnds + ((self.ROS[i], 36000),)
        bnds = bnds + ((0.01, None),)
        ########################################


        ########################################################
        ## add the parameters initial guesses, example below ###
        # example: [2.0, 2.0, 2.0, 2.0, 2.0, 0]
        ########################################################
        solver_input_list = []
        for i in range(0, self.num_of_sensor):
            solver_input_list.append(self.sensors[i].period)
        INITIAL_T_GUESS = 10
        solver_input_list.append(INITIAL_T_GUESS)
        ########################################################

        ########################################################
        ## SOLVE
        ########################################################
        X2 = minimize(self.func, solver_input_list,  bounds=bnds)
        print "maximized value of the objective function", -self.func(list(X2.x))

        for i in range(0,self.num_of_sensor):
            print "Period", i, ": ", X2.x[i], " sec"
        print "T (Time Interval to Upload)", X2.x[self.num_of_sensor], "sec"
        return X2.x
