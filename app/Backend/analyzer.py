# specific maths for event detection
# most likely won't require a class
from utils import recording
from config import config
import numpy as np
import datetime
from scipy import optimize
import time
import math

import matplotlib.pyplot as plt

from DataVisualizer import param_guide, trace_display  # remove this during deployment


### this module does all the calculations for event detection and modeling
### this module should be able to function on its own

def open_trace(filename, channel=0):
    global trace_file
    trace_file = recording.Trace(filename)
    trace_file.set_channel(channel)


def search_index(x, l, rate=None):
    if x < l[0]:
        return -1 # out of bounds
    if x > l[-1]:
        return len(l) + 1 # out of bounds
    if rate is None:
        rate = np.mean(l[1:6] - l[0:5])
    est = int((x - l[0]) * rate)
    if est >= len(l):
        return len(l)  # out of bounds
    elif l[est] == x:
        return int(est)
    elif l[est] > x:  # overshot
        while est >= 0:
            if l[est] < x:
                return int(est + 1)
            est -= 1
    elif l[est] < x:  # need to go higher
        while est < len(l):
            if l[est] > x:
                return int(est)
            est += 1
    return int(est)  # out of bounds


def find_mini_at(
        x,
        xs=None,
        ys=None,
        sampling_rate=None,
        x_unit='seconds',
        y_unit="",
        xlim=None,
        ylim=None,
        direction=1,
        lag=config.detector_points_baseline,
        points_search=config.detector_points_search,
        max_points_baseline=config.detector_max_points_baseline,
        max_points_decay=config.detector_max_points_decay,
        min_amp=config.detector_min_amp,
        min_decay=config.detector_min_decay,
        max_decay=config.detector_max_decay,
        min_hw=config.detector_min_hw,
        max_hw=config.detector_max_hw,
        min_rise=config.detector_min_rise,
        max_rise=config.detector_max_rise,
        # decay_func_type=config.detector_decay_func_type,
        # decay_func_constant=config.detector_decay_func_constant,
        # decay_fit_ftol=config.detector_decay_fit_ftol,
        df=None
):
    """
    searches for a synaptic event centered around x using the parameters given
    :param decay_func_type:
    :param decay_fit_percent:
    :param decay_func_constant:
    :param x: central x-coordinate used for the search. float. must be within the y-data of the trace
    :param xlim: x-axis search limit. tuple(min_x, max_x)
    :param ylim: y-axis search limit. tuple (min_y, max_y)
    :param direction: expected direction of the synaptic event. int 1 = positive, -1 = negative
    :param xs: x data, given as a 1D numpy array
    :param ys: y data, given as a 1D numpy array
    :param lag: number of points to average to find start/end (baseline) of the event. int > 10
    :param points_search: number of data points around central x to search for an event peak. (*not this is _not_ float in seconds)
    :param max_points_baseline: maximum number of data points from candidate peak to look for a baseline. If baseline is not found within this limit, the candidate peak is rejected
    :param max_points_decay: maximum number of data points from candidate peak to include for decay fitting. - used if the 'end' cannot be found (i.e. compound peaks)
    :param min_amp: minimum event amplitude. a candidate peak with a smaller amplitude is rejected
    :param min_decay: minimum decay constant. a candidate peak with a smaller decay constant is rejected. float >= 0
    :param max_decay: maximum decay constant. a candidate peak with a larger decay constant is rejected. float >= 0 or str 'None'
    :param min_hw: minimum halfwidth. a candidate peak with a  smaller halfwidth is rejected. float >= 0
    :param max_hw: maximum halfwidth. a candidate peak with a larger halfwidth is rejected. float >=0 or str 'None'
    :param min_rise: minimum rise constant. a candidate peak with a smaller rise is rejected. float >= 0
    :param max_rise: maximum rise constant. a candidate peak with a larger rise is rejected. float >=0 or str 'None'
    :return:
    """

    ######### find peak ##########
    data = filter_mini(
        peak_idx,
        start_idx,
        end_idx,
        xs=xs,
        ys=ys,
        x_unit=x_unit,
        y_unit=y_unit,
        direction=direction,
        lag=lag,
        max_points_baseline=max_points_baseline,
        max_points_decay=max_points_decay,
        min_amp=min_amp,
        min_decay=min_decay,
        max_decay=max_decay,
        min_hw=min_hw,
        max_hw=max_hw,
        min_rise=min_rise,
        max_rise=max_rise,
        # decay_func_type=decay_func_type,
        # decay_func_constant=decay_func_constant,
        # decay_fit_ftol=decay_fit_ftol,
        df=df
    )

    return data


def find_window(x, points_search, xs=None, ys=None, sampling_rate=None,
                xlim=None, ylim=None):
    if xs is None:
        xs = trace_file.get_xs(mode='continuous')
    if ys is None:
        ys = trace_file.get_ys(mode='continuous')

    x_idx = search_index(x, xs, sampling_rate)

    # initialize search range for peak
    start_idx = x_idx - points_search
    end_idx = x_idx + points_search

    try:
        xlim_idx = (
            search_index(xlim[0], xs, sampling_rate),
            search_index(xlim[1], xs, sampling_rate)
        )
    except:
        xlim_idx = (0, len(xs))

    # narrow search range by xlim
    start_idx = max(start_idx, xlim_idx[0])
    end_idx = min(end_idx, xlim_idx[1])

    # find where y values are beyond limits
    try:
        y_high = ys[start_idx:end_idx] > ylim[1]
        y_low = ys[start_idx:end_idx] < ylim[0]

        ylim_idx = np.where(y_high | y_low)[0] + start_idx  # get all indices where y is outside of ylim
        y_left, y_right = None, None
        if len(ylim_idx) > 0:  # there are ys that are beyond ylim
            for i, y_idx in enumerate(ylim_idx):  # start from left to right
                if y_idx > x_idx:  # y_idx passed x_idx (right side of x_idx)
                    y_right = y_idx
                    if y_idx[i - 1] < y_right:
                        y_left = y_idx[i - 1]
                    break
            else:
                if y_idx[-1] < x_idx:
                    y_left = y_idx[-1]
        if y_left:
            start_idx = max(start_idx, y_left)
        if y_right:
            end_idx = min(end_idx, y_right)
    except:
        pass
    return start_idx, end_idx


def find_peak_recursive(
        xs,
        ys,
        start,
        end,
        direction
):
    ######## search candidate peak ##########
    peak_y = max(ys[start:end] * direction)
    peaks = np.where(ys[start:end] * direction == peak_y)[0] + start  # list of indices where ys is at peak
    peak_idx = peaks[int(len(peaks) / 2)]  # take the earliest time point as candidate

    FUDGE = 10  # adjust if needed

    if end - start < FUDGE * 2:
        return None

    # check if the peak is only a cut-off of a slope:
    # recursively narrow the search area and look for another local extremum within the range

    if peak_idx < start + FUDGE:  # peak is too close to the left end of search range
        return find_peak_recursive(xs, ys, start + FUDGE, end, direction=direction)
    if peak_idx > end - FUDGE:  # peak is too close to the right end of search range
        return find_peak_recursive(xs, ys, start, end - FUDGE, direction=direction)

    return peak_idx


def find_baseline(peak_idx, ys, lag, direction, max_points_baseline=None):
    base_idx = peak_idx - 1

    # y_avg is always going to be a positive peak

    if base_idx < lag:
        return None, None
    y_avg = np.mean(ys[base_idx - lag + 1:base_idx + 1] * direction)
    base_idx -= 1

    while base_idx > lag:
        y_avg = (y_avg * (lag) + (ys[base_idx - lag] - ys[base_idx]) * direction) / (lag)
        # equivalent to np.mean(ys[base_idx - lag: base_idx]))
        if y_avg >= ys[base_idx] * direction:
            break
        base_idx -= 1
    else:
        return None, None
    return base_idx, y_avg * direction


def find_end_of_mini(peak_idx, ys, lag, direction):
    end_idx = peak_idx
    y_avg = np.mean(ys[end_idx: end_idx + lag]) * direction
    end_idx += 1
    while end_idx < len(ys) - lag:
        y_avg = (y_avg * (lag) + (ys[end_idx + lag] - ys[end_idx]) * direction) / (
            lag)  # equivalent to np.mean(ys[end_idx + 1: end_idx + lag + 1])
        if y_avg > ys[end_idx] * direction:
            return end_idx, y_avg
        end_idx += 1
    else:
        return None, None


def find_halfwidth_idx(amp, ys, direction, baseline, offset):
    left_idx = [i + offset for i in range(1, len(ys) - 1) if ys[i - 1] * direction <= (baseline + amp / 2) * direction
                if ys[i + 1] * direction >= (baseline + amp / 2) * direction]
    right_idx = [i + offset for i in range(1, len(ys) - 1) if ys[i - 1] * direction >= (baseline + amp / 2) * direction
                 if ys[i + 1] * direction <= (baseline + amp / 2) * direction]
    return left_idx[0], right_idx[0]
    # mini analysis does closest 2 points, or we could do farthest 2 points.


def fit_decay(xs, ys, direction, function, constant=True, fit_zero=True):
    decay_func = function
    decay_func_type = 1
    decay_func_constant = True

    # low_bounds = [0 for i in range(decay_func_type * 2)]
    # if decay_func_constant:
    #     low_bounds.append(-np.inf)
    #
    # high_bounds = [np.inf for i in range(decay_func_type * 2)]
    # # for i in range(decay_func_type):
    # #     high_bounds[i * 2] = data['amp'] * direction
    # if decay_func_constant:
    #     high_bounds.append(np.inf)

    ###################
    x_data = (xs - xs[0]) * 1000
    y_data = (ys) * direction

    y_weight = np.empty(len(y_data))
    y_weight.fill(10)

    if fit_zero:
        y_weight[0] = 0.001

    results = optimize.curve_fit(decay_func,
                                 x_data,
                                 y_data,
                                 # ftol=decay_fit_ftol,
                                 sigma=y_weight,
                                 absolute_sigma=True,
                                 # bounds=[tuple(low_bounds), tuple(high_bounds)],
                                 maxfev=15000)
    return results[0]


def filter_mini(
        start_idx=None,
        end_idx=None,
        xs=None,
        ys=None,
        x_unit=None,
        y_unit=None,
        direction=1,
        peak_idx=None,
        lag=config.detector_points_baseline,
        min_amp=config.detector_min_amp,
        min_rise=config.detector_min_rise,
        max_rise=config.detector_max_rise,
        min_hw=config.detector_min_hw,
        max_hw=config.detector_max_hw,
        min_decay=config.detector_min_decay,
        max_decay=config.detector_max_decay,
        max_points_decay=config.detector_max_points_decay,
        df=None
):
    data = {}
    data['search_xlim'] = (start_idx, end_idx)
    for i in ['direction',
              'lag', 'min_amp', 'min_decay', 'max_decay',
              'min_hw', 'max_hw', 'min_rise', 'max_rise',
              'max_points_decay'
              # 'decay_fit_ftol'
              ]:
        data[i] = locals()[i]

    if y_unit is None:
        y_unit = trace_file.y_unit
    if x_unit is None:
        x_unit = trace_file.x_unit

    data['t_unit'] = x_unit
    data['datetime'] = datetime.datetime.now().strftime('%m-%d-%y %H:%M:%S')

    ##### find peak #####
    if peak_idx is None:
        data['peak_idx'] = find_peak_recursive(xs, ys, start=start_idx, end=end_idx,
                                               direction=direction)
    else:
        data['peak_idx'] = peak_idx

    if data['peak_idx'] is None:
        return data, False

    data['t'] = xs[data['peak_idx']]
    try:
        if data['t'] in df.index:
            data['peak_coord_x'] = None
            return data, False
    except:
        pass
    data['peak_coord_x'] = xs[data['peak_idx']]
    data['peak_coord_y'] = ys[data['peak_idx']]

    ##### find baseline/start of event #####
    data['base_idx'], data['baseline'] = find_baseline(data['peak_idx'], ys, lag, direction)

    if data['base_idx'] is None:
        return data, False

    data['start_coord_x'] = xs[data['base_idx']]
    data['start_coord_y'] = data['baseline']

    data['baseline_unit'] = y_unit

    ##### calculate amplitude #####
    data['amp'] = ys[data['peak_idx']] - data['baseline']  # signed
    data['amp_unit'] = y_unit

    if data['amp'] * direction < data['baseline']:
        return data, False
    if data['amp'] * direction < min_amp:
        return data, False

    ###### find end of event #####
    data['base_end_idx'], data['end_coord_y'] = find_end_of_mini(data['peak_idx'], ys, lag, direction)
    if data['base_end_idx'] is None:
        return data, False
    data['end_coord_x'] = xs[data['base_end_idx']]

    ##### calculate rise #####
    data['rise_const'] = (data['peak_coord_x'] - data['start_coord_x']) * 1000
    data['rise_unit'] = 'ms' if x_unit in ['s', 'seconds', 'second', 'sec'] else '{} E-3'.format(
        x_unit)

    if data['rise_const'] < min_rise:
        return data, False
    if data['rise_const'] > max_rise:
        return data, False

    ##### calculate halfwidth #####
    try:
        data['halfwidth_idx'] = find_halfwidth_idx(data['amp'], ys[data['base_idx']:data['base_end_idx']],
                                                   direction, data['baseline'], data['base_idx'])
    except:
        data['halfwidth'] = None
        return data, False

    try:
        data['halfwidth'] = (xs[data['halfwidth_idx'][1]] - xs[data['halfwidth_idx'][0]]) * 1000
        data['halfwidth_unit'] = 'ms' if x_unit in ['s', 'seconds', 'second',
                                                    'sec'] else '{} E-3'.format(x_unit)
    except:
        data['halfwidth'] = None
        return data, False

    if data['halfwidth'] < min_hw:
        return data, False
    if data['halfwidth'] > max_hw:
        return data, False

    ################ DECAY!!!! ###################
    # scipy curve_fit: need to define a function

    try:
        data['decay_fit'] = fit_decay(xs[data['peak_idx']:min(data['peak_idx'] + data['max_points_decay'], len(xs))],
                                      ys[data['peak_idx']:min(data['peak_idx'] + data['max_points_decay'], len(ys))],
                                      direction,
                                      function=single_exponent_constant)
        data['decay_fit_idx'] = data['peak_idx']  # in case we want to change this
        data['decay_func'] = single_exponent_constant.__name__
        if data['decay_fit'] is None:
            return data, False

        e = data['decay_fit'][1]
        e_y = single_exponent_constant(e, *data['decay_fit'])

        data['decay_const'] = e

        data['decay_coord_x'] = xs[data['peak_idx']] + data['decay_const'] / 1000
        data['decay_coord_y'] = single_exponent_constant(e, *data['decay_fit']) * direction
        data['decay_unit'] = 'ms' if x_unit in ['s', 'seconds', 'second', 'sec'] else '{} E-3'.format(x_unit)
        if data['decay_const'] < min_decay or data['decay_const'] > max_decay:
            return data, False

    except Exception as e:
        data['decay_fit'] = None
        data['decay_error'] = e
        return data, False

    return data, True


def single_exponent_constant(x, a, t, d):
    return a * np.exp(-(x) / t) + d


def single_exponent(x, a, t):
    return a * np.exp(-(x) / t)


def double_exponent_constant(x, a_1, t_1, a_2, t_2, c):
    return a_1 * np.exp(-(x) / t_1) + a_2 * np.exp(-((x) / t_2)) + c


def double_exponent(x, a_1, t_1, a_2, t_2):
    return a_1 * np.exp(-(x) / t_1) + a_2 * np.exp(-(x) / t_2)


def triple_exponent_constant(x, a_1, t_1, a_2, t_2, a_3, t_3, c):
    return a_1 * np.exp(-(x) / t_1) + a_2 * np.exp(-(x) / t_2) + a_3 * np.exp(-(x) / t_3) + c


# def triple_exponent_constant(x, a, t_1,t_2, t_3, c):
#     return a * np.exp(-(x ) / t_1) + a * np.exp(-(x ) / t_2) + a * np.exp(-(x ) / t_3) + c


def triple_exponent(x, a_1, t_1, a_2, t_2, a_3, t_3):
    return a_1 * np.exp(-(x) / t_1) + a_2 * np.exp(-(x) / t_2) + a_3 * np.exp(-(x) / t_3)


def rise_decay(x, a, t_2, t_1):
    return a * (1 - np.exp(-x / t_1)) * (np.exp(-(x) / t_2))


# def single_exponent(x, V, s, t, b, d):
#     #V = Vm
#     #s= start
#     #t =tau
#     #b = baseline
#     #d = adjust at the end
#     return V * np.exp(-(x-s)/t) + b + d

from DataVisualizer import trace_display


def point_line_min_distance(x, y, offset, xs, ys, x2y=1, rate=None):
    # finds the minimum square difference between a point and a line.
    idx = search_index(x, xs, rate)
    min_d = np.inf
    min_i = None
    for i in range(max(idx - offset, 0), min(idx + offset, len(xs))):
        d = distance((x, y), (xs[i], ys[i]), x2y)
        if d < min_d:
            min_d = d
            min_i = i
    return min_d, min_i


def distance(coord1, coord2, x2y=1):  # (x1,y1), (x2, y2)
    # return math.sqrt(sum([(coord1[i] - coord2[i])**2 for i in range(len(coord1))]))

    return math.hypot((coord2[0] - coord1[0]) / x2y, coord2[1] - coord1[1])


def contains_line(xlim, ylim, xs, ys, rate=None):
    if xlim:
        xlim_idx = (search_index(xlim[0], xs, rate), search_index(xlim[1], xs, rate))
    else:
        xlim_idx = (0, len(xs))
    if xlim_idx[0] < 0 or xlim_idx[-1] > len(xs):
        return False
    if ylim:
        for y in ys[xlim_idx[0]:xlim_idx[1]]:
            if ylim[0] < y < ylim[1]:
                return True
        return False
    return True
