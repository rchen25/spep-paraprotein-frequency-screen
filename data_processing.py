import numpy as np

class DataProcessing(): 
    def only_numerics(seq):
        if seq == '':
            seq = '0'
        if seq != seq:
            seq = '0'
        seq = str(seq)
        seq_type= type(seq)
        return seq_type().join(filter(seq_type.isdigit, seq))        
        
    def convert_hex_string_to_float_array_impute_landmarks(hex_string):
        l_array_floats = []
        idx_hex_high = 0
        idx_float = 0
        l_dot_landmarks = []
        try:
            while idx_hex_high <  len(hex_string):
                idx_hex_low = idx_float * 4
                idx_hex_high = idx_hex_low + 4
                hex_this_elt = hex_string[idx_hex_low: idx_hex_high]
                type_of_dot_this_elt = hex_string[idx_hex_low] # can be 0, 8, 4, C
                if type_of_dot_this_elt != '0':
                    l_dot_landmarks.append((idx_float, type_of_dot_this_elt))
                    float_this_elt = l_array_floats[-1] if len(l_array_floats) >= 1 else 0 # impute by taking 
                                                                                           # the last value
                else:
                    float_this_elt = int(hex_this_elt, 16)
                l_array_floats = l_array_floats + [float_this_elt]
                idx_float += 1
            return [np.array(l_array_floats), l_dot_landmarks]
        except:
            print("cannot convert to int array: ", hex_string)
            return [np.nan, np.nan]

    def compute_fft(data):
        fft_of_data = abs(np.fft.rfft(data))
        freq_values = np.log10(np.arange(len(fft_of_data)))
        return freq_values, fft_of_data