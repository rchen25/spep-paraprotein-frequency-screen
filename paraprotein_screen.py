import argparse
import numpy as np

import pandas as pd
from sklearn import preprocessing

from data_processing import DataProcessing
from model import HighFreqScreener



def main():
	parser = argparse.ArgumentParser()
	parser.add_argument("infile", help="input file with serum samples and control curves")
	args = parser.parse_args()

	df_input_samples_to_screen = pd.read_csv(args.infile)



	# print('Paraprotein screening tool ... ')
	# print('input filename:', args.infile)
	# print('number of samples to screen: ', len(df_input_samples_to_screen))


	# data processing #################################################################################################

	## convert curves from hex format to int array
	l_curves_features = ['sebiaSerumCurve', 'sebiaSerumGelControlCurve']

	for feature_name in l_curves_features:
	    df_input_samples_to_screen[feature_name + '_intArr'] = [DataProcessing.convert_hex_string_to_float_array_impute_landmarks(x)[0] for 
	                                                 x in df_input_samples_to_screen[feature_name]]

	    
	    df_input_samples_to_screen[feature_name + '_landmarks'] = [DataProcessing.convert_hex_string_to_float_array_impute_landmarks(x)[1] for 
	                                                 x in df_input_samples_to_screen[feature_name]]



	## create feature matrix
	ll_serum_curve = [x for x in df_input_samples_to_screen['sebiaSerumCurve_intArr']]
	ll_serum_gel_control_curve = [x for x in df_input_samples_to_screen['sebiaSerumGelControlCurve_intArr']]
	ll_gamma_landmarks = [x for x in df_input_samples_to_screen['sebiaSerumGelControlCurve_landmarks']]

	### serum and control curves in numeric form
	X_serum_curve = np.array(ll_serum_curve)
	X_serum_gel_control_curve = np.array(ll_serum_gel_control_curve)
	X_diff = X_serum_curve - X_serum_gel_control_curve

	### normalize
	X_serum_curve = preprocessing.normalize(X_serum_curve, axis = 1, norm = 'max')
	X_serum_control_curve = preprocessing.normalize(X_serum_gel_control_curve, axis = 1, norm = 'max')

	### serum curve - control curve difference
	X_serum_minus_control = X_serum_curve - X_serum_control_curve

	## compute gamma cutoffs
	### determine the X-axis cutoffs for the gamma region:
	gamma_cutoffs_X = np.zeros([X_serum_minus_control.shape[0]])

	cnt = 0
	for landmarks_this_patient in ll_gamma_landmarks:
	    list_of_C_8 = [k for k in landmarks_this_patient if k[1] == 'C' or k[1] == '8']
	    gamma_cutoff_this_pt = list_of_C_8[1][0]
	    gamma_cutoffs_X[cnt] = gamma_cutoff_this_pt
	    cnt += 1
	### impute if not found
	gamma_cutoffs_X[gamma_cutoffs_X == 0] = np.mean(gamma_cutoffs_X[gamma_cutoffs_X != 0])


	## zero out non-gamma fractions (different location cutoff on gel per sample)
	for idx in range(len(gamma_cutoffs_X)):
	    cutoff_this_sample = int(gamma_cutoffs_X[idx])
	    X_serum_curve[idx, cutoff_this_sample:] = 0
	    X_serum_control_curve[idx, cutoff_this_sample:] = 0
	    
	X_serum_minus_control_gamma_region = X_serum_curve - X_serum_control_curve


	# score samples with model ########################################################################################

    ## initialize model
	model_highpass = HighFreqScreener()

	y_proba = model_highpass.predict_proba(X_serum_minus_control_gamma_region)
	y_class = (y_proba > model_highpass.threshold_for_likelihood_ratio_90).astype(int)

	df_output = df_input_samples_to_screen.copy(deep=True)
	del df_output['sebiaSerumGelControlCurve_landmarks']
	del df_output['sebiaSerumCurve_landmarks']
	df_output['sebiaSerumCurve_intArr'] = [np.array2string(x, separator=',').replace('\n', '') for x in df_output['sebiaSerumCurve_intArr']]
	df_output['sebiaSerumGelControlCurve_intArr'] = [np.array2string(x, separator=',').replace('\n', '') for x in df_output['sebiaSerumGelControlCurve_intArr']]
	df_output['gamma_region_cutoff'] = gamma_cutoffs_X
	df_output['prediction'] = y_class

	# output
	df_output.to_csv('./output.csv', header = True, index = False)
	df_output.to_json('./output.json', orient = 'records')
	print(df_output.to_json(orient = 'records'))

if __name__ == "__main__":
	main()
