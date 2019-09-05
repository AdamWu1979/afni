#!/usr/bin/env python

# python3 status: compatible

ver='1.0' ; date='Aug 28, 2019'
# + [PT] start date for this program.  Thanks, RWC for the math behind
#        it!
#
ver='1.1' ; date='Aug 29, 2019'
# + [PT] change way we read from file;  use pre-existing AFNI functions
#
######################################################################

import sys, copy
import afni_util  as UTIL
import lib_afni1D as LAD

# -----------------------------------------------------------------------
# -----------------------------------------------------------------------

def gershgoriny_dist_aff12_from_I_file( fname ):
    '''Input a file of an aff12 matrix (either MATRIX or ONELINE format).
    Must have exactly 12 numbers.

    See help of 'gershorginy_dist_aff12_from_I()' for what happens
    next.

    Output is one scalar number.

    '''

    # read in, and get into proper shape with a transposition
    x = LAD.Afni1D( fname )
    x.transpose()

    if len(x.mat) == 3 and len(x.mat[0]) == 4 : 
        # then we have a MATRIX-format aff12.1D param already, and we
        # are all set to go
        out = gershgoriny_dist_aff12_from_I( x.mat )

    elif len(x.mat) == 1 and len(x.mat[0]) == 12 : 
        # then we have a ONELINE-format aff12.1D param, and we have to
        # reshape it
        M = [[0.0] * 4 for row in range(3)] 
        for i in range(3):
            M[i][:] = x.mat[0][4*i:4*(i+1)]
        out = gershgoriny_dist_aff12_from_I( M )
    else:
        print("** ERROR: Input matrix in {} has some problems! Doesn't look\n"
              "   like an aff12.1D format (ONELINE, 1x12; MATRIX, 3x4)\n"
              "".format(fname))
        sys.exit(3)
        
    return out

# -----------------------------------------------------------------------

def gershgoriny_dist_aff12_from_I( Minp ):
    '''Input a matrix Minp (=3x4 list) of aff12 values.  

To address the question, "Is the input matrix far from the identity
matrix + no translation?" we make it into a 4x4 matrix M, and
calculate D=M-I.  Then, we estimate the size of D, using the max
eigenvalue of D'D... and THAT is estimated (or bounded) by using
everyone's favorite Gershgorin theorem.

Therefore, this program outputs a single (scalar) value, computed as
follows: compute the 4 absolute row sums of D'D and take their
maximum, and take the square root of THAT value.  This final number is
our measure of the size of the difference matrix D, which can be
compared with a tolerance/epsilon value.

Thanks go to RWC for constructing+explaining this approach!

'''

    Nrow = len(Minp)
    if Nrow != 3 :
        print("** ERROR: Nrow in input matrix is {}, not 3!"
        "".format(Nrow))
        sys.exit(6)
    Ncol = len(Minp[0])
    if Ncol != 4 :
        print("** ERROR: Ncol in input matrix is {}, not 4!"
        "".format(Ncol))
        sys.exit(6)

    # Go through these steps to get D: 
    #    Minp -> square form M -> D = M-I
    D    = copy.deepcopy( Minp )
    ZZ   = UTIL.calc_zero_dtype( D[0][0] ) # all zeros bc we subtract I below
    D.append( [ZZ]*4 )
    for i in range(3):
        D[i][i]-= 1

    Dtr  = UTIL.transpose(D)                  # Make Dtranspose
    DtrD = UTIL.matrix_multiply_2D( Dtr, D )  # Calculated D'D

    # Calc sum of abs vals of ele in rows (SAVER); then get the max of
    # those, and sqrt it
    SAVER          = UTIL.matrix_sum_abs_val_ele_row( DtrD ) 
    max_SAVER      = max( SAVER )    
    max_SAVER_sqrt = max_SAVER**0.5  

    return max_SAVER_sqrt