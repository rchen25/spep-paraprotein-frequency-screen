import numpy as np


class HighFreqScreener():
    """
    Model to screen for high frequency components.

    The model is initialized with parameter values from model training process using the authors'
    private training set of SPEP samples:
        - high-frequency cutoff (freq_cutoff)
        - magnitude cutoff (magnitude_cutoff)
        - scoring threshold (tuned to achieve maximum likelihood ratio while maintaining
            sensitivity over 90%) for positive class given probability estimate from
            model (threshold_for_likelihood_ratio_90)
    """
    def __init__(self, 
               	 class_weight=None,
                 random_state=None,
                 high_freq_threshold=None,
                 freq_cutoff=0.0009824251069387255,
                 magnitude_cutoff=0.01001001001001001,
                 threshold_for_likelihood_ratio_90=0.01360544
                 ):

        self.class_weight = class_weight
        self.random_state = random_state
        self.high_freq_threshold = 0.0
        self.freq_cutoff = freq_cutoff
        self.magnitude_cutoff = magnitude_cutoff
        self.threshold_for_likelihood_ratio_90 = threshold_for_likelihood_ratio_90
    
    def _get_abs_freq_spectrum(self, sample):
        # Preprocessing
        xx = list(range(len(sample)))
        # Compute FFT
        npts = len(xx)
        # Forward transform: f(x) -> F(k)
        fk = np.fft.rfft(sample)
        # Normalize and isolate real component
        norm = 2.0/npts
        fk = fk*norm
        fk_r = fk.real
        fk_i = fk.imag
        abs_fk = np.abs(fk)
        # Extract frequencies
        k = np.fft.rfftfreq(npts)
        # Make dimensional (divide by dx)
        kfreq = k*npts/(max(xx) + xx[1])

        # Inverse transform: F(k) -> f(x) -- without the normalization
        fkinv = np.fft.irfft(fk/norm)
        return kfreq, abs_fk

    def _generate_probabilities_with_abs_mag_cutoff(self, X, cutoff):
        """
        Probability estimates given a cutoff
        """
        decision = np.zeros([X.shape[0], 1])
        
        for idx in list(range(X.shape[0])):
            sample = X[idx, :]
            
            kfreq, abs_fk = self._get_abs_freq_spectrum(sample)
            self.kfreq = kfreq
            # isolate high frequencies
            kfreq_high = kfreq[kfreq >= self.high_freq_threshold]
            n_high_freqs = len(kfreq_high)
            abs_fk_high = abs_fk[-n_high_freqs:]
            
            # screen for high-frequency components with cutoff (denoted by self.high_freq_threshold)
            fk_high_freq_above_cutoff = abs_fk_high[abs_fk_high>cutoff]
            num_fk_high_freq_total = len(kfreq_high)
            num_fk_high_freq_above_cutoff = len(fk_high_freq_above_cutoff)
            pct_fk_high_freq_above_cutoff = float(num_fk_high_freq_above_cutoff) / num_fk_high_freq_total
            binary_fk_high_freq_above_cutoff = 1 if pct_fk_high_freq_above_cutoff > 0 else 0
            decision[idx] = pct_fk_high_freq_above_cutoff
            
        return decision

    def _generate_probabilities_with_freq_cutoff(self, X, y, cutoff):
        """Probability estimates given a cutoff
        """
        decision = np.zeros([X.shape[0], 1]) # decisions (percentage of values above freq cutoff that are non-zero)
        
        for idx in list(range(X.shape[0])):
            sample = X[idx, :]
            
            kfreq, abs_fk = self._get_abs_freq_spectrum(sample)
            
            # isolate high frequencies
            kfreq_high = kfreq[kfreq >= cutoff]
            n_high_freqs = len(kfreq_high)
            abs_fk_high = abs_fk[-n_high_freqs:]
                
            # find high-frequency components t=given magnitude_cutoff
            fk_high_freq_nonzero = abs_fk_high[abs_fk_high>self.magnitude_cutoff] # find non-zero magnitudes among high freqs
            num_fk_high_freq_total = len(kfreq_high) 
            num_fk_high_freq_nonzero = len(fk_high_freq_nonzero)
            
            pct_fk_high_freq_nonzero = float(num_fk_high_freq_nonzero) / num_fk_high_freq_total
            decision[idx] = pct_fk_high_freq_nonzero
            
        return decision
    
        
    def fit(self, X, y, sample_weight=None):
        """Fit the model according to the given training data.

        Parameters
        ----------
        X : {array-like, sparse matrix}, shape (n_samples, n_features)
            Training vector, where n_samples is the number of samples and
            n_features is the number of features.

        y : array-like, shape (n_samples,)
            Target vector relative to X.

        sample_weight : array-like, shape (n_samples,) optional
            Array of weights that are assigned to individual samples.
            If not provided, then each sample is given unit weight.

        Returns
        -------
        self : object

        """
        
        
        # compute freq spectrum for a random sample, to get the possible frequencies self.kfreq
        kfreq, abs_fk = self._get_abs_freq_spectrum(X[0,:])
        self.kfreq = kfreq
        
        # tune the magnitude cutoff
        max_X = np.max(X) # maximum magnitude
        possible_magnitude_cutoffs = np.linspace(0, max_X/float(2), 1000)
        auc_values_per_magnitude_cutoff = np.zeros([len(possible_magnitude_cutoffs)])
        for mag_idx in list(range(len(possible_magnitude_cutoffs))):
            this_magnitude_cutoff = possible_magnitude_cutoffs[mag_idx]
            # 1. generate probabilities for all samples given the magnitude cutoff
            y_pred_probas_with_cutoff = self._generate_probabilities_with_abs_mag_cutoff(X, this_magnitude_cutoff)
            # 2. compute AUC
            fpr, tpr, thresholds = roc_curve(y, y_pred_probas_with_cutoff, pos_label=1)
            auc_score_this_magnitude_cutoff = roc_auc_score(y, y_pred_probas_with_cutoff)
            auc_values_per_magnitude_cutoff[mag_idx] = auc_score_this_magnitude_cutoff
        idx_best_magnitude_cutoff = np.argmax(auc_values_per_magnitude_cutoff)
        self.magnitude_cutoff = possible_magnitude_cutoffs[idx_best_magnitude_cutoff]
            
            
        # tune the frequency cutoff: Learn the cutoff for freq in freq spectrum based on train data
        possible_freq_cutoff_values = np.linspace(0, np.max(self.kfreq), 1000)
        
        auc_values_per_freq_cutoff = np.zeros([len(possible_freq_cutoff_values)])       
        for idx in list(range(len(possible_freq_cutoff_values))):
            this_cutoff = possible_freq_cutoff_values[idx]
            # 1. generate probabilities for all samples given the frequency cutoff  
            y_pred_probas_with_cutoff = self._generate_probabilities_with_freq_cutoff(X, y, this_cutoff)
            # 2. compute AUC
            fpr, tpr, thresholds = roc_curve(y, y_pred_probas_with_cutoff, pos_label=1)
            auc_score_this_cutoff = roc_auc_score(y, y_pred_probas_with_cutoff)
            auc_values_per_freq_cutoff[idx] = auc_score_this_cutoff
        idx_best_freq_cutoff = np.argmax(auc_values_per_freq_cutoff)
        self.freq_cutoff = possible_freq_cutoff_values[idx_best_freq_cutoff]
        self.freq_cutoff_AUC = auc_values_per_freq_cutoff[idx_best_freq_cutoff]
        return self
    
    def predict_proba(self, X):
        """
        Generate probability estimates.

        Parameters
        ----------
        X : array-like, shape = [n_samples, n_features]

        Returns
        -------
        T : array-like, shape = [n_samples, 1]
            Returns the probability of the sample being classified as positive.
        """
        
        decision = np.zeros([X.shape[0], 1])
        
        for idx in list(range(X.shape[0])):
            sample = X[idx, :]
            
            kfreq, abs_fk = self._get_abs_freq_spectrum(sample)
            # isolate high frequencies
            kfreq_high = kfreq[kfreq >= self.freq_cutoff]
            n_high_freqs = len(kfreq_high)
            abs_fk_high = abs_fk[-n_high_freqs:]
                
            #   2. screen for high frequency (fk)
            fk_with_abs_mag_above_cutoff = abs_fk_high[abs_fk_high>self.magnitude_cutoff]
            num_fk_high_freq_total = len(kfreq_high)
            num_fk_high_freq_with_abs_mag_above_cutoff = len(fk_with_abs_mag_above_cutoff)
            pct_fk_high_freq_above_mag_cutoff = float(num_fk_high_freq_with_abs_mag_above_cutoff) / num_fk_high_freq_total
            decision[idx] = pct_fk_high_freq_above_mag_cutoff
        return decision
    
