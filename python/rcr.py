"""
RCR.PY: Performs calculations for RCR model

Author:       Brian Krauth
              Department of Economics
              Simon Fraser University
Usage:

       rcr.py [infile outfile logfile]

       where

           infile      An optional argument giving the name
                       of the input file.  Default is IN.TXT.

           outfile     An optional argument giving the name of
                       the output file. Default is OUT.TXT.

           logfile     An optional argument giving the name of
                       the output file. Default is LOG.TXT.

       The RCR program will read in the INFILE, perform
       the calculations, and then write the results to OUTFILE.
       The program may also report information on its status to
       LOGFILE.

"""
# Standard library imports
import sys
import warnings
from datetime import datetime

# Third party imports
import numpy as np
from numpy.linalg import inv
import pandas as pd
import scipy.stats
import statsmodels.iolib as si
import statsmodels.iolib.summary as su
import matplotlib.pyplot as plt

# Local application imports
# (none)


# I/O and system functions


def get_command_arguments(args):
    """Retrieve command arguments, usually from sys.argv."""
    # ARGS should be a list of 1 to 5 strings like sys.argv
    if isinstance(args, list) and all([type(item) == str for item in args]):
        if (len(args) > 5):
            msg = "Unused program arguments {0}".format(args[5:])
            warnings.warn(msg)
            pass
    else:
        msg = "Invalid command arguments, using defaults: {0}".format(args)
        warnings.warn(msg)
        args = []
    infile = args[1].strip() if len(args) > 1 else "in.txt"
    outfile = args[2].strip() if len(args) > 2 else "pout.txt"
    logfile = args[3].strip() if len(args) > 3 else "plog.txt"
    detail_file = args[4].strip() if len(args) > 4 else ""
    return infile, outfile, logfile, detail_file


def set_logfile(fname):
    """Set name of log file"""
    global logfile
    if isinstance(fname, str) or fname is None:
        logfile = fname
    else:
        pass


def get_logfile():
    """Retrieve name of log file.  If undefined, return None"""
    global logfile
    if "logfile" not in globals():
        logfile = None
    return logfile


def write_to_logfile(str, mode="a"):
    """Write a note to the log file."""
    logfile = get_logfile()
    if logfile is None:
        return
    try:
        with open(logfile, mode) as lf:
            lf.write(str)
    except OSError:
        msg = "Cannot write to logfile {0}.".format(logfile)
        warnings.warn(msg)
    return None


def start_logfile(logfile):
    """Start the log file."""
    set_logfile(logfile)
    # TODO: Add any warnings that have already been thrown
    write_to_logfile("Log file {0} for RCR version 1.0\n".format(logfile),
                     mode="w")
    start_time = datetime.now().strftime("%H:%M on %m/%d/%y")
    write_to_logfile("Run at {0}.\n".format(start_time))


def read_data(infile):
    """Read RCR data from input file"""
    write_to_logfile("Reading data from input file {0}.\n".format(infile))
    # infile argument should be a single string
    if not isinstance(infile, str):
        msg = "Infile should be a single string"
        warn(msg)
    # Line 1 should be three whitespace delimited numbers
    try:
        line1 = pd.read_csv(infile,
                            delim_whitespace=True,
                            skiprows=[1, 2],
                            header=None).values[0, ]
        n_moments, n_lambda, external_big_number = tuple(line1)
    except FileNotFoundError:
        msg = "infile {0} not found.\n".format(infile)
        die(msg)
    except ValueError:
        msg = "Incorrect format in line 1 of infile {0}.\n".format(infile)
        die(msg)
    except Exception:
        msg = "Unknown problem with line 1 of infile {0}.\n".format(infile)
        die(msg)
    else:
        msg1 = "Line 1: n_moments = {0}, n_lambda = {1}".format(n_moments,
                                                                n_lambda)
        msg2 = "external_big_number = {0}.\n".format(external_big_number)
        write_to_logfile(msg1 + ", " + msg2)
    # Line 2 should be n_moments whitespace delimited numbers
    try:
        moment_vector = pd.read_csv(infile,
                                    delim_whitespace=True,
                                    skiprows=[0, 2],
                                    header=None).values[0, ].astype(np.float64)
    except ValueError:
        msg = "Incorrect format in line 2 of infile {0}.\n".format(infile)
        die(msg)
    except Exception:
        msg = "Unknown problem with line 2 of infile {0}.\n".format(infile)
        die(msg)
    else:
        msg = "Line 2: moment_vector = a vector of length {0}.\n"
        write_to_logfile(msg.format(len(moment_vector)))
    # Lines 3+ should be two whitespace delimited numbers each
    try:
        lambda_range = pd.read_csv(infile,
                                   delim_whitespace=True,
                                   skiprows=[0, 1],
                                   header=None).values[0, ].astype(np.float64)
    except ValueError:
        msg = "Incorrect format in line 3 of infile {0}.\n".format(infile)
        die(msg)
    except Exception:
        msg = "Unknown problem with line 3 of infile {0}.\n".format(infile)
        die(msg)
    else:
        write_to_logfile("Line 3: lambda_range = {0}.\n".format(lambda_range))
        write_to_logfile("For calculations, lambda_range,...\n")
    write_to_logfile("Data successfully loaded from file {0}\n".format(infile))
    # Check to make sure n_lambda is a valid (i.e., positive) value
    n_lambda = int(n_lambda)
    #   1. It should be twice as long as lambda_range. if not, just reset it
    if len(lambda_range) != 2*n_lambda:
        msg = "n_lambda reset from {0} to len(lambda_range)/2 = {1}."
        warn(msg.format(n_lambda, int(len(lambda_range)/2)))
        n_lambda = int(len(lambda_range) / 2)
    #   2. It should be positive.
    assert n_lambda > 0
    #   3. For now, it should be one.
    assert n_lambda == 1
    # Check to make sure n_moments is a valid value
    n_moments = int(n_moments)
    #   1. It should be the same as the length of moment_vector.  if not,
    #      just reset it.
    if n_moments != len(moment_vector):
        msg = "n_moments reset from {0} to len(moment_vector) = {1}."
        warn(msg.format(n_moments, len(moment_vector)))
        n_moments = len(moment_vector)
    #   2. It must be at least 9 (i.e., there must be at least one explanatory
    #      variable)
    assert n_moments >= 9
    #   3. The number of implied explanatory variables must be an integer
    k = int((np.sqrt(9 + 8 * n_moments) - 1) / 2)
    assert (2 * (n_moments + 1)) == int(k ** 2 + k)
    # Check to make sure external_big_number is a valid value
    assert external_big_number > 0.0
    # If external_big_number is bigger than sys.float_info.max, then issue a
    # warning but don't stop program.
    # TODO: I'm not satisfied with this.
    if (external_big_number > sys.float_info.max):
        msg = "Largest Python real ({0}) is less than largest in Stata {1}"
        warn(msg.format(sys.float_info.max, external_big_number))
    return n_moments, n_lambda, external_big_number, \
        moment_vector, lambda_range


def write_results(result_matrix, outfile):
    """Write the results_matrix array to outfile."""
    write_to_logfile("Writing results to output file {0}.\n".format(outfile))
    write_to_logfile("Actual results = ...\n")
    try:
        with np.printoptions(threshold=np.inf, linewidth=np.inf):
            np.savetxt(outfile, result_matrix, delimiter=" ")
    except OSError:
        msg = "Cannot write to output file {0}.".format(outfile)
        warn(msg)
    else:
        write_to_logfile("RCR successfully concluded.\n")


def write_details(thetavec, lambdavec, detail_file):
    # If a detail_file has been specified, output thetavec and lambdavec to
    # that file
    if (len(detail_file) > 0):
        try:
            with open(detail_file, mode="w") as df:
                df.write("theta, lambda \n")
                for i in range(0, len(thetavec)):
                    df.write("{0}, {1} \n".format(thetavec[i], lambdavec[i]))
        except OSError:
            warn("Cannot write to detail file {0}.".format(detail_file))


def warn(msg):
    """Issue warning (to logfile and python warning system) but continue."""
    write_to_logfile("WARNING: " + msg + "\n")
    warnings.warn(msg)


def die(msg):
    """Fatal error - write message to log file and then shut down."""
    write_to_logfile("FATAL ERROR: " + msg)
    raise RuntimeError(msg)


def translate_result(mat, inf=np.inf, nan=np.nan):
    """Translate inf and NaN values (e.g., for passing to Stata)"""
    newmat = np.copy(mat)
    msk1 = np.isinf(newmat)
    newmat[msk1] = np.sign(newmat[msk1])*inf
    msk2 = np.isnan(newmat)
    newmat[msk2] = nan
    return newmat


# Model calculation functions


def estimate_model(moment_vector, lambda_range):
    """Estimate the RCR model.

    Parameters
    ----------
    moment_vector : ndarray of floats
        its elements will be interpreted as the upper triangle of the
        (estimated) second moment matrix E(W'W), where W = [1 X Y Z].
        It is normally constructed by Stata.
    lambda_range : ndarray of floats
        its elements lambda values to consider

    Returns
    -------
    result_matrix : ndarray
        an array of parameter estimates and gradients

    Side effects
    ------------
    None.

    See also
    --------
    To be added.

    Notes
    -----
    To be added.

    Examples
    --------
    To be added.

    """
    write_to_logfile("Estimating model.\n")
    result_matrix = np.full((len(lambda_range) + 3,
                             len(moment_vector) + 1),
                            float('nan'))
    # Check to make sure the moments are consistent
    valid, identified = check_moments(moment_vector)
    # If moments are invalid, just stop there
    if not valid:
        return result_matrix
    # If model is not identified, just stop there
    # TODO: some model elements may still be identified here
    elif not identified:
        return result_matrix
    # We have closed forms for the global parameters lambda_star, theta_star,
    # and lambda(0), so we just estimate them directly.
    result_matrix[0, ] = estimate_parameter(lambdastar, moment_vector)
    result_matrix[1, ] = estimate_parameter(thetastar, moment_vector)
    result_matrix[2, ] = estimate_parameter(lambda0_fun, moment_vector)
    # Here we get to the main estimation problem.  We need to find the range
    # of theta values consistent with the lambda(theta) function falling in
    # lambda_range.  We have a closed form solution for lambda(theta), but
    # finding its inverse is an iterative problem.
    #
    # STEP 1: Estimate THETA_SEGMENTS, which is a global real vector
    #         indicating all critical points (i.e., points where the
    #         derivative is zero or nonexistent) of the function
    #         lambda(theta).  The function is continuous and monotonic
    #         between these points. Note that we don't know a priori how many
    #         critical points there will be, and so we don't know how big
    #         THETA_SEGMENTS will be.
    theta_segments, thetavec, lambdavec = \
        estimate_theta_segments(moment_vector)
    # STEP 2: For each row of lambda_range (i.e., each pair of lambda values):
    # do i=1,size(lambda_range,1)
    # j is the row in result_matrix corresponding to lambda_range(i,:)
    # j = 2+2*i
    #  Estimate the corresponding theta range, and put it in result_matrix
    result_matrix[3:5, :] = estimate_theta(moment_vector,
                                           lambda_range,
                                           theta_segments)
    return result_matrix, thetavec, lambdavec


def estimate_theta_segments(moment_vector):
    """Divide real line into segments over which lambda(theta) is monotonic"""
    imax = 30000   # A bigger number produces an FP overflow in fortran
    sm = simplify_moments(moment_vector)
    theta_star = thetastar(moment_vector)
    # THETAMAX is the largest value of theta for which we can calculate both
    # lambda(theta) and lambda(-theta) without generating a floating point
    # exception.
    thetamax = np.sqrt(sys.float_info.max / max(1.0, sm[4], sm[1] - sm[4]))
    # The calculation above seems clever, but it turns out not to always work.
    # So I've put in a hard limit as well
    thetamax = min(1.0e100, thetamax)
    # Create a starting set of theta values at which to calculate lambda
    thetavec = np.sort(np.append(np.linspace(-50.0, 50.0, imax - 2),
                                 (thetamax, -thetamax)))
    if (np.isfinite(theta_star)):
        # Figure out where theta_star lies in thetavec
        i = np.sum(thetavec < theta_star)
        # If i=0 or i=k, then theta_star is finite but outside of
        # [-thetamax,thetamax]. This is unlikely, but we should check.
        if ((i > 0) and (i < imax)):
            # Adjust i to ensure that -thetamax and thetamax are still
            # included in thetavec
            i = min(max(i, 2), imax - 2)
            # Replace the two elements of thetavec that bracket theta_star
            # with two more carefully-chosen numbers.  See BRACKET_THETA_STAR
            # for details
            bracket = bracket_theta_star(moment_vector)
            if (bracket is not None):
                thetavec[i-1: i+1] = bracket
            # TODO: There is a potential bug here.  The bracket_theta_star
            # function is used to take the two values in thetavec that are
            # closest to theta_star and replace them with values that are
            # guaranteed to give finite and nonzero lambda.  But there's
            # nothing to guarantee that these are still the two values in
            # thetavec that are the closest to theta_star.
            assert thetavec[i-2] < thetavec[i-1]
            assert thetavec[i] < thetavec[i+1]
        else:
            msg = "theta_star (={0}) > thetamax (={1})."
            warn(msg.format(theta_star, thetamax))
    # Re-sort thetavec
    thetavec = np.sort(thetavec)
    # Calculate lambda for every theta in thetavec
    lambdavec = lambdafast(thetavec, simplify_moments(moment_vector))
    # LOCALMIN = True if the corresponding element of THETAVEC appears to be
    # a local minimum
    localmin = ((lambdavec[1:imax-1] < lambdavec[0:imax-2]) &
                (lambdavec[1:imax-1] < lambdavec[2:imax]))
    # The end points are not local minima
    localmin = np.append(np.insert(localmin, [0], [False]), False)
    # LOCALMAX = True if the corresponding element of THETAVEC appears to be
    # a local maximum
    localmax = ((lambdavec[1:imax-1] > lambdavec[0:imax-2]) &
                (lambdavec[1:imax-1] > lambdavec[2:imax]))
    # The end points are not local max`ima
    localmax = np.append(np.insert(localmax, [0], [False]), False)
    # Figure out where theta_star lies in THETAVEC.  We need to do this
    # calculation again because we sorted THETAVEC
    if (np.isfinite(theta_star)):
        i = np.sum(thetavec < theta_star)
        if ((i > 0) and (i < imax)):
            # The two values bracketing theta_star are never local optima
            localmin[i-1:i+1] = False
            localmax[i-1:i+1] = False
    # Right now, we only have approximate local optima.  We need to apply
    # an iterative optimization algorithm to improve the precision.
    # do j=1,size(localmin)
    for j in range(1, len(localmin)):
        if localmin[j-1]:
            thetavec[j-1] = brent(thetavec[j-2],
                                  thetavec[j-1],
                                  thetavec[j],
                                  lambdafast,
                                  1.0e-10,
                                  simplify_moments(moment_vector))
        elif localmax[j-1]:
            thetavec[j-1] = brent(thetavec[j-2],
                                  thetavec[j-1],
                                  thetavec[j],
                                  negative_lambdafast,
                                  1.0e-10,
                                  simplify_moments(moment_vector))
    # Now we are ready to create THETA_SEGMENTS.
    if (np.isfinite(theta_star) and (i > 0) and (i < imax)):
        # THETA_SEGMENTS contains the two limits (-Inf,+Inf), the pair of
        # values that bracket theta_star, and any local optima
        theta_segments = np.append(np.concatenate([thetavec[i-1:i+1],
                                                   thetavec[localmin],
                                                   thetavec[localmax]]),
                                   (-thetamax, thetamax))
    else:
        # If theta_star is not finite, then we have two less elements in
        # THETA_SEGMENTS
        theta_segments = np.concatenate([thetavec[i-1:i+1],
                                         thetavec[localmin],
                                         thetavec[localmax]])
    # Sort the result (definitely necessary)
    theta_segments = np.sort(theta_segments)
    return theta_segments, thetavec, lambdavec


def bracket_theta_star(moment_vector):
    """Find theta valus close to theta_star"""
    # Get the value of theta_star.  If we are in this function it should be
    # finite.
    theta_star = thetastar(moment_vector)
    # Get the limit of lambda(theta) as theta approaches theta_star,from below
    # and from above. These limits are generally not finite.
    sm = simplify_moments(moment_vector)
    # If this condition holds, no need to find a bracket (and the code
    # below won't work anyway)
    if (sm[2] == sm[5] * sm[1]/sm[4]):
        return None
    # We may want to use np.inf here
    # NOTE: the np.sign seems extraneous here.
    true_limit = (np.array((1.0, -1.0)) *
                  np.sign(sm[2] - sm[5] * sm[1]/sm[4]) *
                  sys.float_info.max)
    # Pick a default value
    bracket = None
    j = 0
    for i in range(1, 101):
        # For the candidate bracket, consider theta_star plus or minus some
        # small number epsilon (epsilon gets smaller each iteration)
        candidate = (theta_star +
                     np.array((-1.0, 1.0)) * max(abs(theta_star), 1.0)*0.1**i)
        # To be a good bracket, candidate must satisfy some conditions:
        #    1. The bracket must be wide enough that the system can tell that
        #       CANDIDATE(1) < theta_star < CANDIDATE(2)
        #    2. The bracket must be narrow enough that lambda(candidate) is
        #       the same sign as true_limit.
        #    3. The bracket must be wide enough that lambda(candidate) is
        #       finite and nonzero. If candidate is very close to theta_star,
        #       then the calculated lambda(candidate) can be *either* NaN or
        #       zero.  The reason for this is that lambda(candidate) is a
        #       ratio of two things that are going to zero.  Approximation
        #       error will eventually make both the numerator and denominator
        #       indistingushable from zero (NaN), but sometimes the numerator
        #       will reach indistinguishable-from-zero faster (giving zero
        #       for the ratio).
        if ((candidate[0] < theta_star) and (candidate[1] > theta_star)):
            tmp2 = lambdafast(candidate, sm)
            if (np.isfinite(tmp2).all() and
               (tmp2[0]*np.sign(true_limit[0]) > 0.0) and
               (tmp2[1]*np.sign(true_limit[1]) > 0.0)):
                j = i
                bracket = candidate
            else:
                continue
    if (j == 0):
        msg = "Unable to find a good bracket for theta_star"
        warn(msg)
    return bracket


def estimate_theta(moment_vector,
                   lambda_range,
                   theta_segments):
    """Estimate theta"""
    ntab = 10
    nmax = 10
    con = 1.4
    con2 = con * con
    big = sys.float_info.max
    safe = 2.0
    h = 1.0e-1
    errmax = 0.0
    theta_estimate = np.zeros((2, len(moment_vector)+1))
    deps = np.zeros(len(moment_vector))
    dmoments = np.zeros(len(moment_vector))
    a = np.zeros((ntab, ntab))
    fac = geop(con2, con2, ntab - 1)
    errt = np.zeros(ntab-1)
    # Get lambda_star and theta_star
    lambda_star = lambdastar(moment_vector)
    theta_star = thetastar(moment_vector)
    # Check to make sure that lambda_star is not in lambda_range.  If so,
    # theta is completely unidentified.
    if (lambda_range[0] <= lambda_star) and (lambda_star <= lambda_range[1]):
        theta_estimate[0, 0] = -np.inf
        theta_estimate[1, 0] = np.inf
        theta_estimate[:, 1:] = 0.0
        return theta_estimate
    # IMPORTANT_THETAS is a list of theta values for which lambda(theta) needs
    # to be calculated. We don't know in advance how many important values
    # there will be, so we make IMPORTANT_THETAS way too big, and initialize
    # it to all zeros (this choice is arbitrary).
    # Get simplified moments
    simplified_moments = simplify_moments(moment_vector)
    # k is the number of actual important theta values in IMPORTANT_THETAS
    important_thetas = np.array([])
    k = 1
    # Go piece by piece through theta_segments
    for i in range(1, len(theta_segments)):
        # Get the next pair of thetas.  This represents a range of thetas to
        # check
        current_theta_range = theta_segments[i-1:i+1]
        # Skip ahead to the next pair if theta_star is in the current range
        if ((not np.isfinite(theta_star)) or
           (current_theta_range[0] >= theta_star) or
           (current_theta_range[1] <= theta_star)):
            # Otherwise, calculate the range of lambdas associated with that
            # range of thetas
            current_lambda_range = lambdafast(current_theta_range,
                                              simplified_moments)
            # For each of the values in lambda_range
            for j in range(1, 3):
                # See if that value satisfies lambda(theta)-lambda(j)=0 for
                # some theta in current_theta_range
                if (lambda_range[j-1] > min(current_lambda_range)) and \
                   (lambda_range[j-1] < max(current_lambda_range)):
                    # If so, find theta such that lambda(theta)-lambda(j)=0
                    # and put it inour list of IMPORTANT_THETAS.  Of course,
                    # we can't quite find the exact theta.
                    tmp = zbrent(lambda_minus_lambda,
                                 current_theta_range[0],
                                 current_theta_range[1],
                                 1.0e-200,
                                 np.insert(simplified_moments,
                                           0,
                                           lambda_range[j-1]))
                    important_thetas = np.append(important_thetas, tmp)
                    k = k + 1
    # Add THETA_SEGMENTS to the list of IMPORTANT_THETAS
    important_thetas = np.append(important_thetas, theta_segments)
    # Add the OLS theta to the list of IMPORTANT_THETAS?
    # simplified_moments(3)/simplified_moments(2)
    # Calculate lambda(theta) for every theta in IMPORTANT_THETAS
    lambda_segments = lambdafast(important_thetas, simplified_moments)
    # INRANGE = True if a particular value of theta satisfies the condition
    #     lambda_range(1) <= lambda(theta) <= lambda_range(2)
    # Notice that we have put a little error tolerance in here, since
    # zbrent won't find the exact root.
    # TODO: Make sure the tolerance is big enough for the error in zbrent.
    inrange = ((lambda_segments >= lambda_range[0]-0.001) &
               (lambda_segments <= lambda_range[1]+0.001))
    if (k > 1):
        inrange[0:k-1] = True
    # If no IMPORTANT_THETAS are in range, the identified set is empty
    if (sum(inrange) == 0):
        theta_estimate[0, 0] = np.nan
    # If the lowest value in IMPORTANT_THETAS is in range, then there is no
    # (finite) lower bound
    elif inrange[np.argmin(important_thetas)]:
        theta_estimate[0, 0] = -np.inf
    else:
        # Otherwise the the lower bound for theta is the minimum value in
        # IMPORTANT_THETAS that is in range
        theta_estimate[0, 0] = min(important_thetas[inrange])
    # If no IMPORTANT_THETAS are in range, the identified set is empty
    if (sum(inrange) == 0):
        theta_estimate[1, 0] = np.nan
    # If the highest value in IMPORTANT_THETAS is in range, then there is no
    # (finite) upper bound
    elif inrange[np.argmax(important_thetas)]:
        theta_estimate[1, 0] = np.inf
    else:
        # Otherwise the the upper bound for theta is the maximum value in
        # IMPORTANT_THETAS that is in range
        theta_estimate[1, 0] = max(important_thetas[inrange])
    # Now we find the gradient
    # Take the gradient at both theta_L and theta_H
    for j in range(1, 3):
        theta = theta_estimate[j-1, 0]
        # The gradient can only be calculated if theta is finite!
        if np.isfinite(theta):
            # Gradients are estimated using a simple finite central difference:
            #            df/dx = (f(x+e)-f(x-e))/2e
            # where e is some small step size.  The tricky part is getting the
            # right step size.  The algorithm used here is an adaptation of
            # dfridr in Numerical Recipes.  However, that algorithm needs an
            # input initial step size h.
            #
            # http://www.fizyka.umk.pl/nrbook/c5-7.pdf: "As a function of input
            # h, it is typical for the accuracy to get better as h is made
            # larger, until a sudden point is reached where nonsensical
            # extrapolation produces early return with a large error. You
            # should therefore choose a fairly large value for h, but monitor
            # the returned value err, decreasing h if it is not small. For
            # functions whose characteristic x scale is of order unity, we
            # typically take h to be a few tenths."
            # So we try out starting values (h) until we get one that gives an
            # acceptable estimated error.
            for n in range(1, nmax+1):
                # Our candidate initial stepsize is 0.1, 0.001, ...
                h = 0.1 ** n
                # Initialize errmax
                errmax = 0.0
                # Initialize the finite-difference vector
                deps[:] = 0.0
                # First, we calculate the scalar-as-vector (dlambda / dtheta)
                # hh is the current step size.
                hh = h
                # Calculate an approximate derivative using stepsize hh
                a[0, 0] = (lambdafast(theta + hh, simplified_moments) -
                           lambdafast(theta - hh, simplified_moments)) / \
                          (2.0 * hh)
                # Set the error to very large
                err = big
                # Now we try progressively smaller stepsizes
                for k in range(2, ntab + 1):
                    # The new stepsize hh is the old stepsize divided by 1.4
                    hh = hh / con
                    # Calculate an approximate derivative with the new
                    # stepsize
                    a[0, k-1] = ((lambdafast(theta + hh, simplified_moments) -
                                  lambdafast(theta - hh, simplified_moments)) /
                                 (2.0 * hh))
                    # Then use Neville's method to estimate the error
                    for m in range(2, k + 1):
                        a[m - 1, k - 1] = ((a[m - 2, k - 1] *
                                            fac[m - 2] -
                                            a[m - 2, k - 2]) /
                                           (fac[m - 2] - 1.0))
                    errt[0:k - 1] = np.maximum(abs(a[1:k, k - 1] -
                                                   a[0:k - 1, k - 1]),
                                               abs(a[1:k, k - 1] -
                                                   a[0:k - 1, k - 2]))
                    ierrmin = np.nanargmin(errt[0:k - 1]) if \
                        any(np.isfinite(errt[0:k - 1])) else 0
                    # If the approximation error is lower than any previous,
                    # use that value
                    if (errt[ierrmin] <= err):
                        err = errt[ierrmin]
                        dfridr = a[1 + ierrmin, k - 1]
                    if abs(a[k - 1, k - 1] - a[k - 2, k - 2]) >= (safe * err):
                        break
                # errmax is the biggest approximation error so far for the
                # current value of h
                errmax = max(errmax, err)
                # Now we have a candidate derivative dlambda/dtheta
                dtheta = dfridr
                # Second, estimate the vector (dlambda / dmoment_vector)
                for i in range(1, len(moment_vector) + 1):
                    hh = h
                    deps[i-1] = hh
                    a[0, 0] = ((lambdafun(moment_vector + deps, theta) -
                                lambdafun(moment_vector - deps, theta)) /
                               (2.0 * hh))
                    err = big
                    for k in range(2, ntab + 1):
                        hh = hh / con
                        deps[i-1] = hh
                        a[0, k - 1] = (lambdafun(moment_vector + deps,
                                                 theta) -
                                       lambdafun(moment_vector - deps,
                                                 theta)) / (2.0 * hh)
                        for m in range(2, k + 1):
                            a[m - 1, k - 1] = (a[m - 2, k - 1] * fac[m - 2] -
                                               a[m - 2, k - 2]) / \
                                               (fac[m - 2] - 1.0)
                        errt[0:k - 1] = np.maximum(abs(a[1:k, k - 1] -
                                                       a[0:k - 1, k - 1]),
                                                   abs(a[1:k, k - 1] -
                                                       a[0:k - 1, k - 2]))
                        ierrmin = np.nanargmin(errt[0:k - 1]) if \
                            any(np.isfinite(errt[0:k - 1])) else 0
                        if (errt[ierrmin] <= err):
                            err = errt[ierrmin]
                            dfridr = a[1 + ierrmin, k - 1]
                        if abs(a[k - 1, k - 1] - a[k - 2, k - 2]) >= \
                           (safe * err):
                            break
                    # errmax is the biggest approximation error so far for the
                    # current value of h
                    errmax = max(errmax, err)
                    dmoments[i - 1] = dfridr
                    deps[i - 1] = 0.0
                # At this point we have estimates of the derivatives stored in
                # dtheta and dmoments. We also have the maximum approximation
                # error for the current h stored in errmax. If that
                # approximation error is "good enough" we are done and can
                # exit the loop
                if (errmax < 0.01):
                    break
                # Otherwise we will try again with a smaller h
                if (n == nmax):
                    msg1 = "Inaccurate SE for thetaL/H."
                    msg2 = "Try normalizing variables."
                    warn(msg1 + " " + msg2)
            # Finally, we apply the implicit function theorem to calculate the
            # gradient that we actually need:
            #   dtheta/dmoments = -(dlambda/dmoments)/(dlambda/dtheta)
            theta_estimate[j-1, 1:] = -dmoments / dtheta
        else:
            # If theta is infinite, then the gradient is zero.
            theta_estimate[j - 1, 1:] = 0.0
    return theta_estimate


def simplify_moments(moment_vector):
    """Convert moment_vector into the six moments needed for the model"""
    # Get sizes
    m = len(moment_vector)
    k = int((np.sqrt(1 + 8 * m) + 1) / 2)
    assert 2*(m + 1) == k ** 2 + k
    mvtmp = np.append(1.0, moment_vector)
    xtmp = np.empty((k, k))
    # The array XTMP will contain the full cross-product matrix E(WW')
    # where W = [1 X Y Z]
    h = 0
    for i in range(0, k):
        for j in range(i, k):
            xtmp[i, j] = mvtmp[h]
            xtmp[j, i] = mvtmp[h]
            h = h + 1
    assert h == (m + 1)
    # The array XX will contain the symmetric matrix E(XX')
    XX = xtmp[0:(k - 2), 0:(k - 2)]
    # The array XY will contain the vector E(XY)
    XY = xtmp[(k - 2), 0:(k - 2)]
    # The array XZ will contain the vector E(XZ)
    XZ = xtmp[(k - 1), 0:(k - 2)]
    # Now we fill in simplify_moments with the various moments.
    simplified_moments = np.full(6, float("nan"))
    # varY
    simplified_moments[0] = (moment_vector[m - 3] -
                             (moment_vector[k - 3]) ** 2)
    # varZ
    simplified_moments[1] = (moment_vector[m - 1] -
                             (moment_vector[k - 2]) ** 2)
    # covYZ
    simplified_moments[2] = (moment_vector[m - 2] -
                             moment_vector[k - 2]*moment_vector[k - 3])
    # The XX matrix could be singular, so catch that exception
    try:
        invXX = inv(XX)
        # varYhat
        simplified_moments[3] = (XY.T @ invXX @ XY -
                                 moment_vector[k - 3] ** 2)
        # varZhat
        simplified_moments[4] = (XZ.T @ invXX @ XZ -
                                 moment_vector[k - 2] ** 2)
        # covYZhat
        simplified_moments[5] = (XY.T @ invXX @ XZ -
                                 moment_vector[k - 2] * moment_vector[k - 3])
    except np.linalg.LinAlgError:
        # These values will return as NaN
        pass
    # When there is only one control variable, yhat and zhat are perfectly
    # correlated (positively or negatively) With rounding error, this can lead
    # to a correlation that is > 1 in absolute value.  This can create
    # problems, so we force the correlation to be exactly 1.
    # TODO: This also could happen if there is more than one control variable
    # but only one happens to have a nonzero coefficient.  I don't know how to
    # handle that case.
    if k == 4:
        simplified_moments[5] = (np.sign(simplified_moments[5]) *
                                 np.sqrt(simplified_moments[3] *
                                         simplified_moments[4]))
    return simplified_moments


def check_moments(moment_vector):
    """Check to ensure moment_vector is valid"""
    sm = simplify_moments(moment_vector)
    # First make sure that moment_vector describes a valid covariance matrix
    valid = True
    if not all(np.isfinite(sm)):
        valid = False
        if all(np.isfinite(sm[0:3])) and all(np.isnan(sm[4:7])):
            warn("Invalid data: nonsingular X'X matrix.")
        else:
            warn("Invalid data: unknown issue")
    if sm[0] < 0.0:
        valid = False
        warn("Invalid data: var(y) = {0} < 0".format(sm[0]))
    if sm[1] < 0.0:
        valid = False
        warn("Invalid data: var(z) = {0} < 0".format(sm[1]))
    if sm[3] < 0.0:
        valid = False
        warn("Invalid data: var(yhat) = {0} < 0".format(sm[3]))
    if sm[4] < 0.0:
        valid = False
        warn("Invalid data: var(zhat) = {0} < 0".format(sm[4]))
    if np.abs(sm[2]) > np.sqrt(sm[0] * sm[1]):
        valid = False
        covyz = np.abs(sm[2])
        sdyz = np.sqrt(sm[0] * sm[1])
        msg = "Invalid data: |cov(y,z)| = {0} > {1} sqrt(var(y)*var(z))"
        warn(msg.format(covyz, sdyz))
    if np.abs(sm[5]) > np.sqrt(sm[3] * sm[4]):
        valid = False
        covyz = np.abs(sm[5])
        sdyz = np.sqrt(sm[3] * sm[4])
        msg = "Invalid data: cov(yh,zh) = {0} > {1} sqrt(var(yh)*var(zh))"
        warn(msg.format(covyz, sdyz))
    # Next make sure that the identifying conditions are satisfied.
    # TODO: Maybe these could be addressed with warnings rather than error
    # messages?
    identified = valid
    if sm[0] == 0.0:
        identified = False
        warn("Model not identified: var(y) = 0")
    if sm[1] == 0.0:
        identified = False
        warn("Model not identified: var(z) = 0")
    if sm[3] == 0.0:
        identified = False
        warn("Model not identified: var(yhat) = 0")
    if sm[3] == sm[0]:
        identified = False
        warn("Model not identified: y is an exact linear function of X")
    # TODO: We may also want to check for var(zhat)=0.
    # The model is identified in this case, but we may need to take special
    # steps to get the calculations right.
    return valid, identified


def lambdastar(moment_vector):
    """Calculate lambda_star"""
    sm = simplify_moments(moment_vector)
    # lambda_star is defined as sqrt( var(z)/var(zhat) - 1)
    # The check_moments subroutine should ensure that
    #   var(z) > 0 and that var(z) >= var(zhat) >= 0.
    # This implies that lambda_star >= 0.
    # Special values: If var(zhat) = 0, then lambda_star = +Infinity
    lambda_star = np.inf if sm[4] == 0.0 else \
        np.sqrt(np.maximum(sm[1] / sm[4], 1.0) - 1.0)
    return lambda_star


def thetastar(moment_vector):
    """Calculate theta_star"""
    sm = simplify_moments(moment_vector)
    # theta_star is defined as
    #   cov(yhat,zhat)/var(zhat)
    # The check_moments subroutine should ensure that
    # var(zhat) >= 0 and that if var(zhat)=0 -> cov(yhat,zhat)=0.
    # Special values: If var(zhat)=0, then theta_star = 0/0 = NaN.
    theta_star = np.nan if sm[4] == 0.0 else sm[5] / sm[4]
    return theta_star


def lambdafast(theta, simplified_moments):
    """Calculate lambda for each theta in the given array"""
    y = simplified_moments[0]
    z = simplified_moments[1]
    yz = simplified_moments[2]
    yhat = simplified_moments[3]
    zhat = simplified_moments[4]
    yzhat = simplified_moments[5]
    theta = np.atleast_1d(theta)
    lf0_num = (yhat -
               2.0 * theta * yzhat +
               theta ** 2 * zhat)
    lf0_denom = (y - yhat -
                 (2.0) * theta * (yz - yzhat) +
                 theta ** 2 * (z - zhat))
    lf1_num = (yz - yzhat - theta * (z - zhat))
    lf1_denom = (yzhat - theta * zhat)
    msk = ((lf0_denom != 0.0) &
           (lf1_denom != 0.0) &
           (np.sign(lf0_num) == np.sign(lf0_denom)))
    lambda_fast = np.full(len(theta), np.nan)
    lambda_fast[msk] = ((lf1_num[msk]/lf1_denom[msk]) *
                        np.sqrt(lf0_num[msk]/lf0_denom[msk]))
    return lambda_fast


def negative_lambdafast(theta, simplifiedMoments):
    return -lambdafast(theta, simplifiedMoments)


def lambdafun(moment_vector, theta):
    """Calculate lambda for the given theta"""
    lf = lambdafast(theta, simplify_moments(moment_vector))
    return lf


def lambda0_fun(moment_vector):
    """"Calculate lambda(theta) for theta = 0"""
    # lambda0 is defined as:
    # (cov(y,z)/cov(yhat,zhat)-1) / sqrt(var(y)/var(yhat)-1)
    # The check_moments subroutine should ensure that
    #  var(y) >= var(yhat) > 0, so the denominator is
    # always positive and finite.
    # Special values: If cov(yhat,zhat)=0, then lambda0 can
    #   be +Infinity, -Infinity, or NaN depending on the sign
    #   of cov(y,z).
    simplified_moments = simplify_moments(moment_vector)
    y = simplified_moments[0]
    yz = simplified_moments[2]
    yhat = simplified_moments[3]
    yzhat = simplified_moments[5]
    msk = ((y != yhat) &
           (yzhat != 0.0) &
           (np.sign(yhat) == np.sign((y - yhat))))
    lf0 = (((yz - yzhat)/yzhat) *
           np.sqrt(yhat/(y - yhat))) if msk else np.nan
    return lf0


def lambda_minus_lambda(theta, simplified_moments_and_lambda):
    """Calculate lamba(theta)-lambda given theta and lambda"""
    lambda1 = lambdafast(theta, simplified_moments_and_lambda[1:])
    lambda0 = simplified_moments_and_lambda[0]
    return lambda1 - lambda0


def estimate_parameter(func, moment_vector):
    """Estimate a parameter and its gradient"""
    parameter_estimate = np.zeros(len(moment_vector) + 1)
    parameter_estimate[0] = func(moment_vector)
    nmax = 10
    ntab = 10
    con = 1.4
    con2 = con ** 2
    h = 1.0e-4
    safe = 2.0
    big = 1.0e300
    deps = np.zeros(len(moment_vector))
    errt = np.zeros(ntab - 1)
    fac = geop(con2, con2, ntab - 1)
    a = np.zeros((ntab, ntab))
    if np.isfinite(parameter_estimate[0]):
        for n in range(1, nmax + 1):
            h = 0.1 ** n
            errmax = 0.0
            # We are estimating the gradient, i.e., a vector of derivatives
            # the same size as moment_vector
            for i in range(1, len(moment_vector) + 1):
                # Re-initialize DEPS
                deps[:] = 0.0
                # HH is the step size.  It is chosen by an algorithm borrowed
                # from the dfridr function in Numerical Recipes.  We start
                # with HH set to a predetermined value H.  After that, each
                # successive value of HH is the previous value divided by CON
                # (which is set to 1.4)
                hh = h
                # Set element i of DEPS to HH.
                deps[i - 1] = hh
                # Calculate the first approximation
                a[0, 0] = (func(moment_vector + deps) -
                           func(moment_vector - deps)) / (2.0*hh)
                dfridr = a[0, 0]   # WORKAROUND
                # The error is assumed to be a big number
                err = big
                # Try a total of NTAB different step sizes
                for j in range(2, ntab + 1):
                    # Generate the next step size
                    hh = hh / con
                    # Set DEPS based on that step size
                    deps[i - 1] = hh
                    # Calculate the approximate derivative for that step size
                    a[0, j - 1] = (func(moment_vector + deps) -
                                   func(moment_vector - deps)) / (2.0*hh)
                    # Next we estimate the approximation error for the current
                    # step size
                    for k in range(2, j + 1):
                        a[k - 1, j - 1] = (a[k - 2, j - 1] *
                                           fac[k - 2] -
                                           a[k - 2, j - 2]) / \
                                          (fac[k - 2] - 1.0)
                    errt[0:j - 1] = np.maximum(np.abs(a[1:j, j - 1] -
                                                      a[0:j - 1, j - 1]),
                                               np.abs(a[1:j, j - 1] -
                                                      a[0:j - 1, j - 2]))
                    ierrmin = np.nanargmin(errt[0:j - 1]) if \
                        any(np.isfinite(errt[0:j - 1])) else 0
                    # If the error is smaller than the lowest previous error,
                    # use that hh
                    if (errt[ierrmin] <= err):
                        err = errt[ierrmin]
                        dfridr = a[1 + ierrmin, j - 1]
                    # If the error is much larger than the lowest previous
                    # error, stop
                    if np.abs(a[j - 1, j - 1] - a[j - 2, j - 2]) >= \
                       (safe * err):
                        break
                errmax = max(errmax, err)
                parameter_estimate[i] = dfridr
            if (errmax < 0.01):
                break
            if (n == nmax):
                msg1 = "Inaccurate SE for {0}.".format(func.__name__)
                msg2 = "Try normalizing variables."
                warn(msg1 + " " + msg2)
    else:
        parameter_estimate[1:] = 0.0   # or change to internal_nan
    return parameter_estimate


# Standard numerical algorithms


def brent(ax, bx, cx, func, tol, xopt):
    """Maximize by Brent algorithm"""
    itmax = 1000
    cgold = 0.3819660
    zeps = 1.0e-3 * np.finfo(float).eps  # NOT SURE THIS WILL WORK
    a = min(ax, cx)
    b = max(ax, cx)
    v = bx
    w = v
    x = v
    e = 0.0
    fx = func(x, xopt)
    fv = fx
    fw = fx
    # NOTE: I've added the extraneous line below so that code-checking
    # tools do not flag the "e = d" statement below as referencing
    # a nonexistent variable. In practice, this statement will never
    # be reached in the first loop iteration, after which point d will be
    # defined.
    d = e
    for iter in range(1, itmax + 1):
        xm = 0.5 * (a + b)
        tol1 = tol * abs(x) + zeps
        tol2 = 2.0 * tol1
        if (abs(x - xm) <= (tol2 - 0.5 * (b - a))):
            brent_solution = x
            break
        if (abs(e) > tol1):
            r = (x - w) * (fx - fv)
            q = (x - v) * (fx - fw)
            p = (x - v) * q - (x - w) * r
            q = 2.0 * (q - r)
            if (q > 0.0):
                p = -p
            q = abs(q)
            etemp = e
            e = d     # See NOTE above
            if (abs(p) >= abs(0.5 * q * etemp)) or \
               (p <= q * (a - x)) or \
               (p >= q * (b - x)):
                e = (a - x) if (x >= xm) else (b - x)
                d = cgold * e
            else:
                d = p / q
                u = x + d
                if (u - a < tol2) or (b - u < tol2):
                    d = tol1 * np.sign(xm - x)
        else:
            e = (a - x) if (x >= xm) else (b - x)
            d = cgold * e
        u = (x + d) if (abs(d) >= tol1) else (x + tol1 * np.sign(d))
        fu = func(u, xopt)
        if (fu <= fx):
            if (u >= x):
                a = x
            else:
                b = x
            v = w
            w = x
            x = u
            fv = fw
            fw = fx
            fx = fu
        else:
            if (u < x):
                a = u
            else:
                b = u
            if (fu <= fw) or (w == x):
                v = w
                fv = fw
                w = u
                fw = fu
            elif (fu <= fv) or (v == x) or (v == w):
                v = u
                fv = fu
    if (iter == itmax):
        brent_solution = x
        write_to_logfile("Brent exceeded maximum iterations.\n")
    return brent_solution


def zbrent(func, x1, x2, tol, xopt):
    """Find a root using the Brent algorithm"""
    itmax = 1000
    eps = np.finfo(float).eps   # in fortran was epsilon(x1)
    a = x1
    b = x2
    fa = func(a, xopt)
    fb = func(b, xopt)
    if (((fa > 0.0) and (fb > 0.0)) or ((fa < 0.0) and (fb < 0.0))):
        write_to_logfile("Error in zbrent: Root is not bracketed")
        # call die("root must be bracketed for zbrent") # UPDATE
    c = b
    fc = fb
    for iter in range(1, itmax + 1):
        if (((fb > 0.0) and (fc > 0.0)) or ((fb < 0.0) and (fc < 0.0))):
            c = a
            fc = fa
            d = b - a
            e = d
        if (abs(fc) < abs(fb)):
            a = b
            b = c
            c = a
            fa = fb
            fb = fc
            fc = fa
        # check for convergence
        tol1 = 2.0 * eps * abs(b) + 0.5 * tol
        xm = 0.5 * (c - b)
        if (abs(xm) <= tol1) or (fb == 0.0):
            zbrent_solution = b
            break
        if (abs(e) >= tol1) and (abs(fa) > abs(fb)):
            s = fb / fa
            if (a == c):
                p = 2.0 * xm * s
                q = 1.0 - s
            else:
                q = fa / fc
                r = fb / fc
                p = s * (2.0 * xm * q * (q - r) - (b - a) * (r - 1.0))
                q = (q - 1.0) * (r - 1.0) * (s - 1.0)
            if (p > 0.0):
                q = -q
            p = abs(p)
            if (2.0 * p < min(3.0 * xm * q - abs(tol1 * q), abs(e * q))):
                e = d
                d = p / q
            else:
                d = xm
                e = d
        else:
            d = xm
            e = d
        a = b
        fa = fb
        b = (b + d) if (abs(d) > tol1) else (b + tol1 * np.sign(xm))
        fb = func(b, xopt)
    if (iter == itmax):
        zbrent_solution = b
        write_to_logfile("zbrent: exceeded maximum iterations")
    return zbrent_solution


def geop(first, factor, n):
    """Create a geometric series"""
    g = np.zeros(n)
    if (n > 0):
        g[0] = first
    for k in range(1, n):
        g[k] = g[k - 1] * factor
    return g


def get_column_names(arr, default_names=None):
    """
    Return column names for an array_like object, if available
    """
    cols = default_names
    if isinstance(arr, pd.DataFrame):
        cols = arr.columns.tolist()
    elif hasattr(arr, "design_info"):
        cols = arr.design_info.column_names
    return cols


def bkouter(arrow):
    """
    Given a vector, return its outer product with itself, as a vector
    """
    mat = np.outer(arrow, arrow)
    k = len(mat)
    msk = np.triu(np.full((k, k), True)).flatten()
    mat = mat.flatten()
    return mat[msk]


def check_lambda(lambda_range):
    """
    Check that the given lambda_range is valid
    """
    if type(lambda_range) != np.ndarray:
        msg1 = "lambda_range should be a numpy array"
        msg2 = " and is a {}.".format(type(lambda_range))
        raise TypeError(msg1 + msg2)
    elif lambda_range.ndim != 1:
        msg1 = "lambda_range should be 1-d array"
        msg2 = " and is a {}-d array.".format(lambda_range.ndim)
        raise TypeError(msg1 + msg2)
    elif lambda_range.shape[0] != 2:
        msg1 = "lambda_range should have 2 elements"
        msg2 = " and has {} element(s).".format(lambda_range.shape[0])
        raise TypeError(msg1 + msg2)
    elif lambda_range.shape[0] != 2:
        msg1 = "lambda_range should have 2 elements"
        msg2 = " and has {} element(s).".format(lambda_range.shape[0])
        raise TypeError(msg1 + msg2)
    elif any(np.isnan(lambda_range)):
        msg = "lambda_range cannot be NaN."
        raise ValueError(msg)
    elif lambda_range[0] > lambda_range[1]:
        msg1 = "elements of lambda_range ({0})".format(lambda_range)
        msg2 = " must be in (weakly) ascending order."
        raise ValueError(msg1 + msg2)
    else:
        return None


def check_endog(endog):
    """
    Check that the given endog matrix is valid
    """
    if type(endog) != np.ndarray:
        msg1 = "endog should be an array-like object"
        msg2 = " and is a {}.".format(type(endog))
        raise TypeError(msg1 + msg2)
    elif endog.ndim != 2:
        msg1 = "endog should be 2-d array"
        msg2 = " and is a {}-d array.".format(endog.ndim)
        raise TypeError(msg1 + msg2)
    elif endog.shape[1] != 2:
        msg1 = "endog should have 2 columns"
        msg2 = "and has {} column(s).".format(endog.shape[1])
        raise TypeError(msg1 + msg2)
    else:
        return None


def check_exog(exog, nobs):
    """
    Check that the given exog matrix is valid
    """
    if type(exog) != np.ndarray:
        msg1 = "exog should be an array-like object"
        msg2 = " and is a {}.".format(type(exog))
        raise TypeError(msg1 + msg2)
    elif exog.ndim != 2:
        msg = "exog should be 2-d array; is a {}-d array.".format(exog.ndim)
        raise TypeError(msg)
    elif exog.shape[1] < 2:
        msg1 = "exog should have at least 2 columns"
        msg2 = " and has {} column(s).".format(exog.shape[1])
        raise TypeError(msg1 + msg2)
    elif exog.shape[0] != nobs:
        msg1 = "endog has {} observations".format(nobs)
        msg2 = " and exog has {} observations.".format(exog.shape[0])
        raise TypeError(msg1 + msg2)
    elif any(exog[:, 0] != 1.0):
        msg = "first column of exog must be an intercept"
        raise ValueError(msg)
    else:
        return None


def check_covinfo(cov_type, vceadj):
    """
    Check that the given cov_type and vceadj are valid
    """
    if cov_type not in ("nonrobust", ):
        msg = "cov_type '{}' not yet supported.".format(cov_type)
        raise ValueError(msg)
    if type(vceadj) not in (float, int):
        msg = "vceadj must be a number, is a {}.".format(type(vceadj))
        raise TypeError(msg)
    elif vceadj < 0.:
        msg = "vceadj = {}, must be non-negative.".format(vceadj)
        raise ValueError(msg)
    else:
        return None


def check_ci(cilevel, citype=None):
    """
    Check that the given cilevel and citype are valid
    """
    if type(cilevel) not in (float, int):
        msg = "cilevel must be a number, is a {}.".format(type(cilevel))
        raise TypeError(msg)
    elif cilevel < 0.:
        msg = "cilevel = {}, should be between 0 and 100.".format(cilevel)
        raise ValueError(msg)
    if citype is None:
        return None
    elif citype not in ("conservative", "upper", "lower", "Imbens-Manski"):
        msg = "Unsupported CI type {}.".format(citype)
        raise ValueError(msg)
    else:
        return None


class RCR:
    """
    A class to represent a regression model for RCR analysis.

    Parameters
    ----------
    endog : array_like
        A nobs x 2 array where nobs is the number of observations.
        The first column represents the outcome (dependent variable)
        and the second column represents the treatment
        (explanatory variable of interest).
    exog : array_like
        a nobs x k array of control variables. The first column should
        be an intercept.  See :func:`statsmodels.tools.add_constant`
        to add an intercept.
    lambda_range: array_like
        a 1-d array of the form [lambdaL, lambdaH] where lambdaL
        is the lower bound and lambdaH is the upper bound
        for the RCR parameter lambda.  lambdaL can be -inf
        to indicate no lower bound, and lambdaH can be inf
        to indicate no upper bound.  lambdaL should be <=
        to lambdaH. Default is [0.0, 1.0].

    Attributes
    ----------
    endog : ndarray
        the array of endogenous variables.
    exog : ndarray
        the array of exogenous variables
    lambda_range : ndarray
        the array of lambda values.
    endog_names, exog_names : ndarray of str
        the names of the variables in endog and exog.
    depvar, treatvar, controlvars : str
        the names of the dependent, treatment and
        control variables (from endog_names and
        exog_names)
    nobs : float
        the number of observations.

    Methods
    ------------
    fit(lambda_range=None, cov_type="nonrobust", vceadj=1.0)
        Estimates the RCR model.

    See also
    --------
    To be added.

    Notes
    -----
    The RCR class is patterned after
    statsmodels.regression.linear_model.OLS.

    Examples
    --------
    To be added.
    """
    def __init__(self,
                 endog,
                 exog,
                 lambda_range=np.array([0.0, 1.0]),
                 cov_type="nonrobust",
                 vceadj=1.0,
                 citype="conservative",
                 cilevel=95):
        """
        Constructs the RCR object.
        """
        self.endog = np.asarray(endog)
        check_endog(self.endog)
        self.nobs = self.endog.shape[0]
        self.exog = np.asarray(exog)
        check_exog(self.exog, self.nobs)
        endog_names_default = ["y", "treatment"]
        self.endog_names = get_column_names(endog,
                                            default_names=endog_names_default)
        exog_names_default = ["x" + str(x) for
                              x in
                              list(range(1, exog.shape[1]))]
        exog_names_default = ["Intercept"] + exog_names_default
        self.exog_names = get_column_names(exog,
                                           default_names=exog_names_default)
        self.depvar = self.endog_names[0]
        self.treatvar = self.endog_names[1]
        self.controlvars = " ".join([str(item) for
                                     item in
                                     self.exog_names[1:]])
        self.lambda_range = np.asarray(lambda_range)
        self.cov_type = cov_type
        self.vceadj = vceadj
        self.citype = citype
        self.cilevel = cilevel
        check_lambda(self.lambda_range)
        check_covinfo(cov_type, vceadj)
        check_ci(cilevel, citype)

    def _mv(self, estimate_cov=False):
        xyz = np.concatenate((self.exog, self.endog), axis=1)
        xyzzyx = np.apply_along_axis(bkouter, 1, xyz)[:, 1:]
        mv = xyzzyx.mean(axis=0)
        if estimate_cov:
            cov_mv = np.cov(xyzzyx, rowvar=False)/self.nobs
            return mv, cov_mv
        else:
            return mv

    def fit(self,
            lambda_range=None,
            cov_type=None,
            vceadj=None,
            citype=None,
            cilevel=None):
        """
        Estimates an RCR model.

        Parameters
        ----------
        lambda_range : array_like
            if supplied, overrides the value of lambda_range in
            the RCR object.
        cov_type : str
            the method used to estimate the covariance matrix
            of parameter estimates. Currently-available options
            include 'nonrobust'.  Heteroscedasticity and
            cluster robust uptions to be added. Default
            is 'nonrobust'.
        vceadj : float
            degrees of freedom adjustment factor. The covariance
            matrix of parameters will be multiplied by vceadj.
            Default is no adjustment (vceadj = 1.0).

        Returns
        -------
        RCR_results
            the model estimation results.

        See Also
        --------
        RCR_results
            the results container.
        """
        if lambda_range is None:
            lambda_range = self.lambda_range
        else:
            lambda_range = np.asarray(lambda_range)
            check_lambda(lambda_range)
        if cov_type is None:
            cov_type = self.cov_type
        if vceadj is None:
            vceadj = self.vceadj
        check_covinfo(cov_type, vceadj)
        if cilevel is None:
            cilevel = self.cilevel
        if citype is None:
            citype = self.citype
        check_ci(cilevel, citype)
        xyz = np.concatenate((self.exog, self.endog), axis=1)
        xyzzyx = np.apply_along_axis(bkouter, 1, xyz)[:, 1:]
        mv = xyzzyx.mean(axis=0)
        cov_mv = np.cov(xyzzyx, rowvar=False)/self.nobs
        (result_matrix, thetavec, lambdavec) = estimate_model(mv, lambda_range)
        params = result_matrix[:, 0]
        cov_params = (vceadj *
                      result_matrix[:, 1:] @
                      cov_mv @
                      result_matrix[:, 1:].T)
        details = np.array([thetavec, lambdavec])
        return RCR_results(self,
                           params,
                           cov_params,
                           details,
                           cov_type,
                           vceadj,
                           lambda_range,
                           cilevel,
                           citype)


class RCR_results:
    """
    Results class for an RCR model.

    Parameters
    ----------
    endog : array_like
        A nobs x 2 array where nobs is the number of observations.
        The first column represents the outcome (dependent variable)
        and the second column represents the treatment
        (explanatory variable of interest).
    exog : array_like
        a nobs x k array of control variables. The first column should
        be an intercept.  See :func:`statsmodels.tools.add_constant`
        to add an intercept.
    lambda_range: array_like
        a 1-d array of the form [lambdaL, lambdaH] where lambdaL
        is the lower bound and lambdaH is the upper bound
        for the RCR parameter lambda.  lambdaL can be -inf
        to indicate no lower bound, and lambdaH can be inf
        to indicate no upper bound.  lambdaL should be <=
        to lambdaH. Default is [0.0, 1.0].

    Attributes
    ----------
    model : RCR object
        the model that has been estimated.
    params : ndarray
        the estimated parameters.
    param_names : list
        the parameter names.
    cov_params : ndarray
        the covariance matrix for the parameter estimates.
    cov_type : str
        the covariance estimator used in the results.
    vceadj : float
        the user-supplied adjustment factor used to
        calculate the covariance matrix.  Usually is
        1.0 (no adjustment).
    details : ndarray
        a d x 2 array representing the lambda(theta) function
        the first column is a set of theta values,
        the second column is the estimated lambda(theta)
        for that value.
    nobs : float
        the number of observations.

    Methods
    ------------
    se()
        standard errors for param.
    z()
        z-statistics for param.
    pz()
        asymptotic p-values for param.
    ci(cilevel=95)
        (cilevel)% confidence intervals for param.
    betaxCI_conservative(cilevel=95)
        conservative confidence interval for the causal effect.
    betaxCI_upper(cilevel=95)
        upper confidence interval for the causal effect.
    betaxCI_lower(cilevel=95)
        lower confidence interval for the causal effect.
    betaxCI_imbensmanski(cilevel=95)
        Imbens-Manski confidence interval for the causal effect.
    summary()
        Summary of results.

    See also
    --------
    RCR class.

    Notes
    -----
    The RCR_results class is patterned after
    statsmodels.regression.linear_model.RegressionResults.

    Examples
    --------
    To be added.
    """
    def __init__(self,
                 model,
                 params,
                 cov_params,
                 details,
                 cov_type,
                 vceadj,
                 lambda_range,
                 cilevel,
                 citype):
        """
        Constructs the RCR_results object.
        """
        self.model = model
        self.params = params
        self.param_names = ["lambdaInf",
                            "betaxInf",
                            "lambda0",
                            "betaxL",
                            "betaxH"]
        self.cov_params = cov_params
        self.details = details
        self.cov_type = cov_type
        self.vceadj = vceadj
        self.lambda_range = lambda_range
        self.cilevel = cilevel
        self.citype = citype

    def se(self):
        """
        Standard errors for RCR parameter estimates
        """
        return np.sqrt(np.diag(self.cov_params))

    def z(self):
        """
        z-statistics for RCR parameter estimates
        """
        return self.params / self.se()

    def pz(self):
        """
        asymptotic p-values for RCR parameter estimates
        """
        a = scipy.stats.norm.cdf(np.abs(self.params / self.se()))
        return 2 * (1.0 - a)

    def ci(self, cilevel=None):
        """
        asymptotic confidence intervals for RCR parameter estimates
        """
        if cilevel is None:
            cilevel = self.cilevel
        check_ci(cilevel)
        crit = scipy.stats.norm.ppf((100 + cilevel) / 200)
        return np.array([self.params - crit * self.se(),
                         self.params + crit * self.se()])

    def betaxCI(self,
                cilevel=None,
                citype="conservative"):
        if citype == "conservative":
            betaxCI = self.betaxCI_conservative(cilevel=cilevel)
        elif citype == "upper":
            betaxCI = self.betaxCI_upper(cilevel=cilevel)
        elif citype == "lower":
            betaxCI = self.betaxCI_lower(cilevel=cilevel)
        elif citype == "Imbens-Manski":
            betaxCI = self.betaxCI_imbensmanski(cilevel=cilevel)
        else:
            betaxCI = np.array([np.nan, np.nan])
        return betaxCI

    def betaxCI_conservative(self, cilevel=None):
        """
        conservative asymptotic confidence interval for causal effect.
        """
        if cilevel is None:
            cilevel = self.cilevel
        crit = scipy.stats.norm.ppf((100 + cilevel) / 200)
        betaxCI_L = self.params[3] - crit * self.se()[3]
        betaxCI_H = self.params[4] + crit * self.se()[4]
        return np.array([betaxCI_L, betaxCI_H])

    def betaxCI_upper(self, cilevel=None):
        """
        upper asymptotic confidence interval for causal effect.
        """
        if cilevel is None:
            cilevel = self.cilevel
        crit = scipy.stats.norm.ppf(cilevel / 100)
        betaxCI_L = self.params[3] - crit * self.se()[3]
        betaxCI_H = np.inf
        return np.array([betaxCI_L, betaxCI_H])

    def betaxCI_lower(self, cilevel=None):
        """
        lower asymptotic confidence interval for causal effect.
        """
        if cilevel is None:
            cilevel = self.cilevel
        crit = scipy.stats.norm.ppf(cilevel / 100)
        betaxCI_L = -np.inf
        betaxCI_H = self.params[4] + crit * self.se()[4]
        return np.array([betaxCI_L, betaxCI_H])

    def betaxCI_imbensmanski(self, cilevel=None):
        """
        Imbens-Manski confidence interval for causal effect.
        """
        if cilevel is None:
            cilevel = self.cilevel
        cv_min = scipy.stats.norm.ppf(1 - ((100 - cilevel) / 100.0))
        cv_max = scipy.stats.norm.ppf(1 - ((100 - cilevel) / 200.0))
        se = self.se()
        delta = (self.params[4] - self.params[3]) / max(se[3], se[4])
        cv = cv_min
        if np.isfinite(delta):
            while ((cv_max - cv_min) > 0.000001):
                cv = (cv_min + cv_max) / 2.0
                if (scipy.stats.norm.cdf(cv + delta) -
                   scipy.stats.norm.cdf(-cv)) < (cilevel / 100):
                    cv_min = cv
                else:
                    cv_max = cv
        if se[3] > 0:
            betaxCI_L = self.params[3]-(cv * se[3])
        else:
            betaxCI_L = -np.inf
        if se[4] > 0:
            betaxCI_H = self.params[4]+(cv * se[4])
        else:
            betaxCI_H = np.inf
        return np.array([betaxCI_L, betaxCI_H])

    def _lambdafun(self,
                   thetavals=np.linspace(-50, 50, 100),
                   include_thetastar=True):
        """
        Estimate lambda for a set of theta values
        """
        ts = self.params[1]
        sm0 = simplify_moments(self.model._mv())
        lambdavals = lambdafast(thetavals, sm0)
        if include_thetastar and ts >= min(thetavals) and ts <= max(thetavals):
            thetavals = np.append(thetavals, [ts])
            lambdavals = np.append(lambdavals, [np.nan])
        msk = np.argsort(thetavals)
        return thetavals[msk], lambdavals[msk]

    def test_betax(self, h0=0.0):
        """
        Perform a hypothesis test for betax

        This test works by inverting the Imbens-Manski confidence interval.
        That is, the function reports a p-value defined as (1 - L/100)
        where L is the highest confidence level at which h0 is outside
        of the L% confidence interval.  For example, the p-value will
        be less than 0.05 (reject the null at 5%) if h0 is outside of
        the 95% confidence interval.
        """
        low = 0.0
        high = 100.0
        mid = 50.0
        if h0 >= self.params[3] and h0 <= self.params[4]:
            pvalue = 1.0
        else:
            while (high - low) > 0.00001:
                mid = (high + low) / 2.0
                ci = self.betaxCI_imbensmanski(cilevel=mid)
                if h0 >= ci[0] and h0 <= ci[1]:
                    high = mid
                else:
                    low = mid
            pvalue = 1.0 - low/100.0
        return pvalue

    def rcrplot(self,
                ax=None,
                xlim=(-50, 50),
                ylim=None,
                tsline=False,
                lsline=False,
                idset=False,
                title=None,
                xlabel=r"Effect ($\beta_x$)",
                ylabel=r"Relative correlation ($\lambda$)",
                flabel=r"$\lambda(\beta_x)$ function",
                tslabel=r"$\beta_x^{\infty}$",
                lslabel=r"$\lambda^{\infty}$",
                idlabels=(r"assumed $[\lambda^L,\lambda^H]$",
                          r"Identified set $[\beta_x^L,\beta_x^H]$"),
                tss="--",
                lss="-.",
                fcolor="C0",
                tscolor="0.75",
                lscolor="0.75",
                idcolors=("C0", "C0"),
                idalphas=(0.25, 0.75),
                legend=False):
        """
        Create plot of RCR estimation results
        """
        xlim = np.sort(np.asarray(xlim))
        if len(xlim) == 2:
            xgrid = np.linspace(xlim[0], xlim[1], num=100)
        else:
            xgrid = xlim
        thetavals, lambdavals = self._lambdafun(thetavals=xgrid)
        if ax is None:
            ax = plt.gca()
            ax.clear()
        ax.plot(thetavals,
                lambdavals,
                label=flabel,
                color=fcolor)
        if ylim is not None:
            ax.set_ylim(ylim[0], ylim[1])
        if tsline is True:
            ts = self.params[1]
            if ts >= xlim[0] and ts <= xlim[-1]:
                ax.axvline(ts,
                           ls=tss,
                           color=tscolor,
                           label=tslabel)
        if lsline is True:
            ls = self.params[0]
            if any(lambdavals <= ls) and any(lambdavals >= ls):
                ax.axhline(ls,
                           ls=lss,
                           color=lscolor,
                           label=lslabel)
        if idset is True:
            ax.axhspan(self.lambda_range[0],
                       self.lambda_range[1],
                       color=idcolors[0],
                       alpha=idalphas[0],
                       label=idlabels[0])
            ax.axvspan(self.params[3],
                       self.params[4],
                       color=idcolors[1],
                       alpha=idalphas[1],
                       label=idlabels[1])
        if title is not None:
            ax.set_title(title)
        ax.set_xlabel(xlabel)
        ax.set_ylabel(ylabel)
        if legend:
            ax.legend()
        return ax

    def summary(self,
                citype="conservative",
                cilevel=95,
                tableformats=["%9.4f", "%9.3f", "%9.3f",
                              "%9.3f", "%9.3f", "%9.3f"]):
        """
        Display summary of RCR results and return a summary
        object.

        Parameters
        ----------
        cilevel : float
            the confidence level for the confidence intervals, on
            a scale of 0 to 100.  Default is the cilevel
            attribute of the RCR_results object.
        citype : "conservative", "upper", "lower" or "Imbens-Manski"
            the method to be used in calculating the confidence
            interval for the causal effect betax. Default is
            the citype attribute of the RCR_results object.
        tableformats: list
            a list of formatting strings to use for the table
            of parameter estimates. If the length of tableformats
            is <6, elements will be repeated as needed.  Default
            is ["%9.4f", "%9.3f", "%9.3f", "%9.3f", "%9.3f", "%9.3f"].

        See also
        --------
        RCR class, RCR_results class

        Notes
        -----
        The summary() method returns a
        statsmodels.iolib.summary.Summary object.

        Examples
        --------
        To be added.
        """
        tableformats = (tableformats*6)[0:6]
        outmat = pd.DataFrame(index=self.param_names)
        outmat["b"] = self.params
        outmat["se"] = self.se()
        outmat["z"] = self.z()
        outmat["pz"] = self.pz()
        ci = self.ci(cilevel=cilevel)
        outmat["ciL"] = ci[0, :]
        outmat["ciH"] = ci[1, :]
        betaxCI = self.betaxCI(cilevel=cilevel, citype=citype)
        table1data = [[self.model.depvar,
                       self.model.treatvar],
                      [datetime.now().strftime("%a, %d %b %Y"),
                       self.lambda_range[0]],
                      [datetime.now().strftime("%H:%M:%S"),
                       self.lambda_range[1]],
                      [self.model.nobs,
                       ""],
                      [self.cov_type,
                       self.vceadj]]
        table1stub1 = ["Dep. Variable",
                       "Date",
                       "Time",
                       "No. Observations",
                       "Covariance Type"]
        table1stub2 = ["Treatment Variable",
                       "Lower bound on lambda",
                       "Upper bound on lambda",
                       "",
                       "Cov. adjustment factor"]
        table1 = si.table.SimpleTable(table1data,
                                      stubs=table1stub1,
                                      title="RCR Regression Results")
        table1.insert_stubs(2, table1stub2)
        table2data = np.asarray(outmat)
        table2headers = ["coef",
                         "std err",
                         "z",
                         "P>|z|",
                         "[" + str((100 - cilevel)/200),
                         str((100 + cilevel)/200) + "]"]
        table2stubs = self.param_names
        table2 = si.table.SimpleTable(table2data,
                                      headers=table2headers,
                                      stubs=table2stubs,
                                      data_fmts=tableformats)
        table3data = [[betaxCI[0], betaxCI[1]]]
        table3stubs = ["betaxCI (" +
                       citype +
                       ")                            "]
        table3 = si.table.SimpleTable(table3data,
                                      stubs=table3stubs,
                                      data_fmts=tableformats[5:])
        obj = su.Summary()
        obj.tables = [table1, table2, table3]
        cstr = "Control Variables: {0}".format(self.model.controlvars)
        obj.add_extra_txt([cstr])
        return obj


#############################################################################
# Begin run code
#############################################################################


if __name__ == "__main__":
    # Load in arguments from call to program
    (infile, outfile, logfile, detail_file) = get_command_arguments(sys.argv)

    # Start the log file
    start_logfile(logfile)

    # Read in the data from INFILE
    (n_moments, n_lambda, external_big_number, moment_vector,
        lambda_range) = read_data(infile)

    # Perform the calculations and put the results in result_matrix
    (result_matrix, thetavec, lambdavec) = estimate_model(moment_vector,
                                                          lambda_range)

    # Write out the data to OUTFILE
    write_results(translate_result(result_matrix,
                                   inf=external_big_number,
                                   nan=0.0),
                  outfile)

    if detail_file != "":
        write_details(thetavec, lambdavec, detail_file)

    # Close the log file
    set_logfile(None)

#############################################################################
# End run code
#############################################################################
