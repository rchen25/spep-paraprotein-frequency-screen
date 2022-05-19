import argparse
import numpy as np

import pandas as pd
from sklearn import preprocessing

from data_processing import DataProcessing
from model import HighFreqScreener



def main():
	parser = argparse.ArgumentParser()
	parser.add_argument("infile", help="input file with serum samples and control curves")
	parser.add_argument("--input_int", help="if set to 1, serum and control samples are input in integer format; \
										   note: gamma region cutoff is required input")
	args = parser.parse_args()

	df_input_samples_to_screen = pd.read_csv(args.infile)

	if args.input_int:
		if int(args.input_int) == 1:
			input_is_int = 1
		elif int(args.input_int) == 0:
			input_is_int = 0
		else:
			input_is_int = 1 # set as 1 by default if user entered a non-zero value 
	else:
		input_is_int = 0

	# data processing #################################################################################################
	if not input_is_int:
		## convert curves from hex format to int array
		l_curves_features = ['sebiaSerumCurve', 'sebiaSerumGelControlCurve']

		for feature_name in l_curves_features:
		    df_input_samples_to_screen[feature_name + '_intArr'] = [DataProcessing.convert_hex_string_to_float_array_impute_landmarks(x)[0] for 
		                                                 x in df_input_samples_to_screen[feature_name]]

		    
		    df_input_samples_to_screen[feature_name + '_landmarks'] = [DataProcessing.convert_hex_string_to_float_array_impute_landmarks(x)[1] for 
		                                                 x in df_input_samples_to_screen[feature_name]]

		## compute gamma cutoffs 
		ll_gamma_landmarks = [x for x in df_input_samples_to_screen['sebiaSerumGelControlCurve_landmarks']]

		### determine the X-axis cutoffs for the gamma region:
		gamma_cutoffs_X = np.zeros([df_input_samples_to_screen.shape[0]])

		cnt = 0
		for landmarks_this_patient in ll_gamma_landmarks:
		    list_of_C_8 = [k for k in landmarks_this_patient if k[1] == 'C' or k[1] == '8']
		    gamma_cutoff_this_pt = list_of_C_8[1][0]
		    gamma_cutoffs_X[cnt] = gamma_cutoff_this_pt
		    cnt += 1
		### impute if not found
		gamma_cutoffs_X[gamma_cutoffs_X == 0] = np.mean(gamma_cutoffs_X[gamma_cutoffs_X != 0])

		del df_input_samples_to_screen['sebiaSerumGelControlCurve_landmarks']
		del df_input_samples_to_screen['sebiaSerumCurve_landmarks']

	else:
		df_input_samples_to_screen['sebiaSerumCurve_intArr'] = [k.strip('[').strip(']').split(',') for k in df_input_samples_to_screen['sebiaSerumCurve_intArr']]
		df_input_samples_to_screen['sebiaSerumCurve_intArr'] = [np.array(x).astype(int) for x in df_input_samples_to_screen['sebiaSerumCurve_intArr']]

		df_input_samples_to_screen['sebiaSerumGelControlCurve_intArr'] = [k.strip('[').strip(']').split(',') for k in df_input_samples_to_screen['sebiaSerumGelControlCurve_intArr']]
		df_input_samples_to_screen['sebiaSerumGelControlCurve_intArr'] = [np.array(x).astype(int) for x in df_input_samples_to_screen['sebiaSerumGelControlCurve_intArr']]

		gamma_cutoffs_X = np.array(df_input_samples_to_screen['gamma_region_cutoff'])
		### impute any invalid cutoffs
		gamma_cutoffs_X[(gamma_cutoffs_X != gamma_cutoffs_X) | (gamma_cutoffs_X==0)] = np.mean(gamma_cutoffs_X[gamma_cutoffs_X != 0])

		### y labels - for calibrating the model on custom data
		y_label = np.array(df_input_samples_to_screen['label'])

	## create feature matrix
	ll_serum_curve = [x for x in df_input_samples_to_screen['sebiaSerumCurve_intArr']]
	ll_serum_gel_control_curve = [x for x in df_input_samples_to_screen['sebiaSerumGelControlCurve_intArr']]
	

	### serum and control curves in numeric form
	X_serum_curve = np.array(ll_serum_curve)
	X_serum_gel_control_curve = np.array(ll_serum_gel_control_curve)
	X_diff = X_serum_curve - X_serum_gel_control_curve

	### normalize
	X_serum_curve = preprocessing.normalize(X_serum_curve, axis = 1, norm = 'max')
	X_serum_control_curve = preprocessing.normalize(X_serum_gel_control_curve, axis = 1, norm = 'max')

	### serum curve - control curve difference
	X_serum_minus_control = X_serum_curve - X_serum_control_curve



	## zero out non-gamma fractions (different location cutoff on gel per sample)
	for idx in range(len(gamma_cutoffs_X)):
	    cutoff_this_sample = int(gamma_cutoffs_X[idx])
	    X_serum_curve[idx, cutoff_this_sample:] = 0
	    X_serum_control_curve[idx, cutoff_this_sample:] = 0
	    
	X_serum_minus_control_gamma_region = X_serum_curve - X_serum_control_curve


	# calibrate the model ########################################################################################

    ## initialize model
	model_highpass = HighFreqScreener()

	## calibrate
	model_highpass.fit(X_serum_minus_control_gamma_region, y_label)

	print("Model - trained on custom data")
	print("freq_cutoff:", model_highpass.freq_cutoff)
	print("magnitude_cutoff:", model_highpass.magnitude_cutoff)
	print("threshold_for_likelihood_ratio_90:", model_highpass.threshold_for_likelihood_ratio_90)

	# use model to score samples #################################################################################
	y_proba = model_highpass.predict_proba(X_serum_minus_control_gamma_region)
	y_class = (y_proba > model_highpass.threshold_for_likelihood_ratio_90).astype(int)


if __name__ == "__main__":
	main()
