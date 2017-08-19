#!/usr/bin/env python2
# -*- coding: utf-8 -*-
"""
@author: Felipe Espic

DESCRIPTION:
This script extracts low-dimensional acoustic features from a batch of wav files intended for using with the Merlin toolkit.
It runs the extraction in parallel mode, using all the cores available in the system.

The acoustic features extracted and used by Merlin are:
- '<file>.mag'  : Mel-scaled Log-Mag (dim=nbins_mel,   usually 60).
- '<file>.real' : Mel-scaled real    (dim=nbins_phase, usually 45).
- '<file>.imag' : Mel-scaled imag    (dim=nbins_phase, usually 45).
- '<file>.lf0'  : Log-F0 (dim=1).

Also, this script extracts the additional files:
- '<file>.est'  : File generated by REAPER containing epoch locations and voi/unvoi decisions (remove them if wanted).
- '<file>.shift': File that contains the shifts (hop-sizes) for each extracted frame (variable frame rate).
                  It is used to modify the label files in Merlin. Se .... for more information.

INSTRUCTIONS:
This demo should work out of the box. Just run it by typing: python <script name>
If wanted, you can modify the input options (directories, input files, etc.) See the main function below for details.
"""

import sys, os
curr_dir = os.getcwd()
sys.path.append(os.path.realpath(curr_dir + '/../../src'))

import numpy as np
import libutils as lu
import libaudio as la
import magphase as mp

def feat_extraction(in_wav_dir, file_name_token, out_feats_dir, fft_len, mvf, nbins_mel=60, nbins_phase=45):

    # Display:
    print("Analysing file: " + file_name_token + '.wav')

    # Files setup:
    wav_file = in_wav_dir    + '/' + file_name_token + '.wav'
    est_file = out_feats_dir + '/' + file_name_token + '.est'

    # Epochs detection:
    la.reaper(wav_file, est_file)

    # Feature extraction:
    m_mag_mel_log, m_real_mel, m_imag_mel, v_shift, v_lf0, fs = mp.analysis_with_del_comp__ph_enc__f0_norm__from_files2(wav_file, est_file, fft_len, mvf, f0_type='lf0', mag_mel_nbins=nbins_mel, cmplx_ph_mel_nbins=nbins_phase)

    # Zeros for unvoiced segments in phase features:
    v_voi = (np.exp(v_lf0) > 5.0).astype(int) # 5.0: tolerance (just in case)
    m_real_mel_zeros = m_real_mel * v_voi[:,None]
    m_imag_mel_zeros = m_imag_mel * v_voi[:,None]

    # Saving features:
    lu.write_binfile(m_mag_mel_log,    out_feats_dir + '/' + file_name_token + '.mag')
    lu.write_binfile(m_real_mel_zeros, out_feats_dir + '/' + file_name_token + '.real')
    lu.write_binfile(m_imag_mel_zeros, out_feats_dir + '/' + file_name_token + '.imag')
    lu.write_binfile(v_lf0,            out_feats_dir + '/' + file_name_token + '.lf0')

    # Saving auxiliary feature shift (hop length). It is useful for posterior modifications of labels in Merlin.
    lu.write_binfile(v_shift, out_feats_dir + '/' + file_name_token + '.shift')

    return


if __name__ == '__main__':  
    
    # CONSTANTS: So far, the vocoder has been tested only with the following constants:===
    fft_len = 4096
    fs      = 48000

    # INPUT:==============================================================================
    files_scp     = '../data/file_id.scp' # List of file names (tokens). Format used by Merlin.
    in_wav_dir    = '../data/wavs_nat'    # Directory with the wavfiles to extract the features from.
    out_feats_dir = '../data/params'      # Output directory that will contain the extracted features.
    mvf           = 4500               # Maximum voiced frequency (Hz)

    # FILES SETUP:========================================================================
    lu.mkdir(out_feats_dir)
    l_file_tokns = lu.read_text_file2(files_scp, dtype='string', comments='#').tolist()

    # MULTIPROCESSING EXTRACTION:==========================================================
    lu.run_multithreaded(feat_extraction, in_wav_dir, l_file_tokns, out_feats_dir, fft_len, mvf)
        
    print('Done!')
        