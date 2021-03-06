#! /usr/bin/env python

import os
import logging
import shutil
import subprocess

import numpy as np

from subprocess import call

from gc3libs.optimizer.dif_evolution import DifferentialEvolutionParallel

PENALTY_VALUE=10000


class nlcOne4eachPair():
  def __init__(self, lower_bds, upper_bds):

    self.lower_bds = lower_bds
    self.upper_bds = upper_bds
    self.ctryPair = ['JP', 'US']
 
    self.EY = [ 1.005416, 1.007292 ]
    self.sigmaY = [ 0.010643, 0.00862 ]
      
  def __call__(self, x):
    '''
    Evaluates constraints. 
    Inputs: 
      x -- Habit parametrization, EH, sigmaH
    Outputs: 
      c -- Vector of constraints values, where c_i >= 0 indicates that constraint is satisified.
           Constraints 1-4 are bound constraints for EH and sigmaH
           Constraints 5 and 6 are economic constraints, one for Japan, one for US. 
    '''
    c = np.array([])
    # bound constraints
    # EH box
    c = np.append(c, x[0] - self.lower_bds[0])
    c = np.append(c, -(x[0] - self.upper_bds[0]))
    # sigmaH box
    c = np.append(c, x[1] - self.lower_bds[1])
    c = np.append(c, -(x[1] - self.upper_bds[1]))
    # both countries have the same E
    EH     = np.array([x[0], x[0]])
    sigmaH = np.array([x[1], x[1]])

    for ixCtry in range(2):
      c = np.append(c, ( EH[ixCtry] / sigmaH[ixCtry] ) * ( self.sigmaY[ixCtry] / self.EY[ixCtry] ) - 1 )

    return c

def forwardPremium(vectors):
    """
    For each element of the input vectors, `forwardPremiumOut`
    execution needs to be launched and supervised.
    Parameter file `parameters.in` needs to be customised for each
    member of the given population and passed as part of the
    `forwardPremiumOut` execution either to the cloud or to the grid
    infrastructure.
    Once the execution of `forwardPremiumOut` has terminated, the
    value of `FamaFrenchbeta` should be extracted from the output file
    `simulation.out` located in the output folder.
    If a simulation does not produce a valid output, a penalty value
    should be used instead (use PENALTY_VALUE).
    The forwardPremium function terminates when *all* members of the
    given population have been evaluated and a result vector
    containing the scaled `FamaFrenchbeta` values should then be returned

    Arguments:
    `vectors`: list of population members to be exaluated
    example of vectors [ EX, sigmaX ] of size 10:
    
    [ 0.82679479,  0.00203506]
    [ 0.97514143,  0.00533972]
    [ 0.93623727,  0.00291099]
    [ 0.68093853,  0.00131595]
    [ 0.92752913,  0.00691528]
    [ 0.8828415,  0.00598679]
    [ 0.69607706,  0.00264031]
    [ 0.87176971,  0.00162624]
    [ 0.50521085,  0.00167101]
    [ 0.96557172,  0.00473888]

    Starting from `parameters.in` template file
    http://ocikbapps.uzh.ch/gc3wiki/teaching/lsci2012/project/parameters.in
    substitute EA/EB and sigmaA/sigmaB from each
    member of the given population.

    Output:
    `results`: list of corresponding `FamaFrenchbeta` values scaled in respect
    of the empirical value ( -0.63 )
    Note: the FamaFrenchbeta value extracted from the simulation output file,
    needs to be compared with the empirical value and scaled in respect of the
    standard deviation:
            abs(`FamaFrenchbeta` - (-0.63))/0.25
    This is the value that should be returned as part of `results` for each element
    of the given population (i.e. vectors)

    """
    # replace this with a real implementation
    results = []
    for ex, sigmax in vectors:
      FAKE_FF_BETA = runApp(ex, sigmax)
      results.append(abs(FAKE_FF_BETA - (-0.63))/0.25)
    return results


def runApp(ex, sigmax):
      print "forwardPremiumOut running with EX=%g, sigmaX=%g ..." % (ex, sigmax)
      # the actual vale should be extracted from the forwardPremium output file 'simulation.out'
      call(["rm", "-rf", "output*", "parameters.in"])
      #call(["mkdir", "output"])
      rf = open('parameters.in.orig', 'r')
      with open('parameters.in', 'w') as wf:
        while 1:
          line = rf.readline()
          if not line:
              break
          line = line.replace('EX', str(ex))
          line = line.replace("sigmaX", str(sigmax))
          wf.write(line)
      call(["./forwardPremiumOut"])
      try:
        with open('output/simulation.out') as of:
          print "simulation.out", of.readline() #TODO: read result
          FAKE_FF_BETA = 2
          return FAKE_FF_BETA
      except IOError as e:
        print 'Job Failed!'
        
      return PENALTY_VALUE


def calibrate_forwardPremium():
  """
  Drver script to calibrate forwardPremium EX and sigmaX parameters.
  It uses DifferentialEvolutionParallel as an implementation of
  Ken Price's differential evolution
  algorithm: [[http://www1.icsi.berkeley.edu/~storn/code.html]].
  """

  dim = 2 # the population will be composed of 2 parameters to  optimze: [ EX, sigmaX ]
  lower_bounds = [0.5,0.001] # Respectivaly for [ EX, sigmaX ]
  upper_bounds = [1,0.01]  # Respectivaly for [ EX, sigmaX ]
  y_conv_crit = 0.98 # convergence treshold; stop when the evaluated output function y_conv_crit

  # define constraints
  ev_constr = nlcOne4eachPair(lower_bounds, upper_bounds)

  opt = DifferentialEvolutionParallel(
    dim = dim,          # number of parameters of the objective function
    lower_bds = lower_bounds,
    upper_bds = upper_bounds,
    pop_size = 5,     # number of population members ### orig:100 #TODO
    de_step_size = 0.85,# DE-stepsize ex [0, 2]
    prob_crossover = 1, # crossover probabililty constant ex [0, 1]
    itermax = 20,      # maximum number of iterations (generations)
    x_conv_crit = None, # stop when variation among x's is < this
    y_conv_crit = y_conv_crit, # stop when ofunc < y_conv_crit
    de_strategy = 'DE_local_to_best',
    nlc = ev_constr # pass constraints object 
    )

  # Initialise population using the arguments passed to the
  # DifferentialEvolutionParallel iniitalization
  opt.new_pop = opt.draw_initial_sample()

  # This is where the population gets evaluated
  # it is part of the initialization step
  newVals = forwardPremium(opt.new_pop)

  # Update iteration count
  opt.cur_iter += 1

  # Update population and evaluate convergence
  opt.update_population(opt.new_pop, newVals)
  
  while not opt.has_converged():

    # Generate new population and enforce constrains
    opt.new_pop = opt.enforce_constr_re_evolve(opt.modify(opt.pop))

    # Update iteration count
    opt.cur_iter += 1

    # This is where the population gets evaluated
    # this step gets iterated until a population converges
    newVals = forwardPremium(opt.new_pop)
    print 'newVals', newVals

    # Update population and evaluate convergence
    opt.update_population(opt.new_pop, newVals)

  # Once iteration has terminated, extract `bestval` which should represent
  # the element in *all* populations that lead to the closest match to the
  # empirical value
  EX_best, sigmaX_best = opt.best

  print "Calibration converged after [%d] steps. EX_best: %f, sigmaX_best: %f" % (opt.cur_iter, EX_best, sigmaX_best)
  
if __name__ == '__main__':
  calibrate_forwardPremium()
