from scipy import signal

def butter_bandpass_filter(variable):
    print("Temporal filter...")
    order = 6  # order of filtering, 6 is common
    fs = 1/6  # sampling rate is 1 sample every six hours
    nyq = .5 * fs  # Nyquist frequency is 1/2 times the sampling rate
    big_period_day = 5.0    # band start (longer period)
    small_period_day = 3.0  # band end
    big_period_hr = big_period_day*24.0  # convert the days to hours
    small_period_hr = small_period_day*24.0
    low_frequency = (1/big_period_hr) / nyq     # 1 over the period to get the frequency and then
    high_frequency = (1/small_period_hr) / nyq  # divide by the Nyquist frequency to normalize
    print(low_frequency)
    print(high_frequency)
    b, a = signal.butter(order, [low_frequency, high_frequency], btype='bandpass')
    # works on axis 0 (time)
    filtered_variable = signal.lfilter(b, a, variable, axis=0)
    return filtered_variable
