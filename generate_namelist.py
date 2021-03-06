#!/usr/bin/env python
import sys, os, glob, shutil, numpy
from optparse import OptionParser
from collections import defaultdict

def read_namelist(namelist_dict, filename):#{{{
	namelistfile = open(filename, 'r+')
	lines = namelistfile.readlines()
	namelistfile.close()

	record_name = 'NONE!!!'

	for line in lines:
		if line.find('&') >= 0:
			record_name = line.strip().strip('&').strip('\n')
			namelist_dict[record_name] = defaultdict(list)
		elif line.find('=') >= 0:
			opt, val = line.strip().strip('\n').split('=')
			if record_name != "NONE!!!":
				namelist_dict[record_name][opt].append(val)
#}}}

def set_namelist_value(namelist_dict, owningRecord, option, value):#{{{
	foundRecord = False
	foundOption = False
	for record, opts in namelist_dict.items():
#        if record.find(owningRecord) >= 0:
		if record.strip() == owningRecord.strip():
			foundRecord = True
			for opt, val in opts.items():
#                if opt.find(option) >= 0:
				if opt.strip() == option.strip() >= 0:
					foundOption = True
					val[0] = value
    
	if not foundRecord:
		namelist_dict[owningRecord] = defaultdict(list)
		namelist_dict[owningRecord][option].append(value)
	elif not foundOption:
		namelist_dict[owningRecord][option].append(value)
#}}}

def write_namelist(namelist_dict, infilename, outfilename):#{{{
	in_namelist = open(infilename, 'r')
	lines = in_namelist.readlines()
	in_namelist.close()

	out_namelist = open(outfilename, 'w+')

	record_name = 'NONE!!!'

	for line in lines:
		if line.find('&') >= 0:
			if record_name != "NONE!!!":
				out_namelist.write('/\n')

			record_name = line.strip().strip('&').strip('\n')
			out_namelist.write(line);
		elif line.find('=') >= 0:
			opt, val = line.strip().strip('\n').split('=')
			if record_name != "NONE!!!":
				out_namelist.write('    %s = %s\n'%(opt.strip(), namelist_dict[record_name][opt][0].strip()))

	if record_name != "NONE!!!":
		out_namelist.write('/\n')

#	for record, opts in namelist_dict.items():
#		out_namelist.write('&%s\n'%(record))
#
#		for opt, val in opts.items():
#			out_namelist.write('    %s = %s\n'%(opt.strip(), val[0].strip()))
#
#		out_namelist.write('/\n\n')
	out_namelist.close()
#}}}

def scaled_del4_value(min_resolution):#{{{
	return '%e'%(5.0e10 * (min_resolution / 15000.0)**3)
#}}}
def scaled_del2_value(min_resolution):#{{{
	return '%e'%(1.0e-3 * min_resolution)
#}}}

# *** Ocean specific setup functions *** #{{{
def setup_ocean_namelist(namlelist_dict, configuration, resolution, time_integrator):#{{{
	set_namelist_value(namelist_dict, 'run_modes', 'config_ocean_run_mode', "'forward'")
	if configuration == 'baroclinic_channel':
		setup_ocean_baroclinic_channel(namelist_dict, resolution, time_integrator)
	elif configuration == 'overflow':
		setup_ocean_overflow(namelist_dict, resolution, time_integrator)
	elif configuration == 'global_realistic':
		setup_ocean_global_realistic(namelist_dict, resolution, time_integrator)

#}}}

def setup_ocean_baroclinic_channel(namelist_dict, resolution, time_integrator):#{{{
	set_namelist_value(namelist_dict, 'time_integration', 'config_time_integrator', ("'%s'")%(time_integrator))
	set_namelist_value(namelist_dict, 'time_management', 'config_run_duration', "'0000-00-10_00:00:00'")
	set_namelist_value(namelist_dict, 'hmix_del2', 'config_use_mom_del2', '.true.')
	set_namelist_value(namelist_dict, 'hmix_del2', 'config_use_tracer_del2', '.false.')
	set_namelist_value(namelist_dict, 'hmix_del2', 'config_mom_del2', '10.0')

	set_namelist_value(namelist_dict, 'cvmix', 'config_use_cvmix', '.false.')

	if resolution == '10km':
		if time_integrator == 'split_explicit':
			set_namelist_value(namelist_dict, 'time_integration', 'config_dt', "'00:05:00'")
		elif time_integrator == 'unsplit_explicit' or time_integrator == 'RK4':
			set_namelist_value(namelist_dict, 'time_integration', 'config_dt', "'00:00:30'")
	elif resolution == '4km':
		if time_integrator == 'split_explicit':
			set_namelist_value(namelist_dict, 'time_integration', 'config_dt', "'00:02:00'")
		elif time_integrator == 'unsplit_explicit' or time_integrator == 'RK4':
			set_namelist_value(namelist_dict, 'time_integration', 'config_dt', "'00:00:10'")
	elif resolution == '1km':
		if time_integrator == 'split_explicit':
			set_namelist_value(namelist_dict, 'time_integration', 'config_dt', "'00:00:30'")
		elif time_integrator == 'unsplit_explicit' or time_integrator == 'RK4':
			set_namelist_value(namelist_dict, 'time_integration', 'config_dt', "'00:00:01'")

#}}}

def setup_ocean_overflow(namelist_dict, resolution, time_integrator):#{{{
	set_namelist_value(namelist_dict, 'time_integration', 'config_time_integrator', ("'%s'")%(time_integrator))
	set_namelist_value(namelist_dict, 'time_management', 'config_run_duration', "'0000_18:00:00'")

	set_namelist_value(namelist_dict, 'hmix_del2', 'config_use_mom_del2', '.true.')

	# Remove after PBC's don't exist anymore in the forward model
	set_namelist_value(namelist_dict, 'partial_bottom_cells', 'config_alter_ICs_for_pbcs', '.true.')
	set_namelist_value(namelist_dict, 'partial_bottom_cells', 'config_pbc_alteration_type', "'partial_cell'")

	if resolution == '10km':
		if time_integrator == 'split_explicit':
			set_namelist_value(namelist_dict, 'time_integration', 'config_dt', "'00:03:00'")
		elif time_integrator == 'unsplit_explicit' or time_integrator == 'RK4':
			set_namelist_value(namelist_dict, 'time_integration', 'config_dt', "'00:00:30'")

		set_namelist_value(namelist_dict, 'hmix_del2', 'config_mom_del2', '1.0e3')
	elif resolution == '1km':
		if time_integrator == 'split_explicit':
			set_namelist_value(namelist_dict, 'time_integration', 'config_dt', "'00:00:20'")
		elif time_integrator == 'unsplit_explicit' or time_integrator == 'RK4':
			set_namelist_value(namelist_dict, 'time_integration', 'config_dt', "'00:00:01'")
		set_namelist_value(namelist_dict, 'hmix_del2', 'config_mom_del2', '1.0e3')
#}}}

def setup_ocean_global_realistic(namelist_dict, resolution, time_integrator):#{{{
	set_namelist_value(namelist_dict, 'time_integration', 'config_time_integrator', ("'%s'")%(time_integrator))

	# Remove after PBC's don't exist anymore in the forward model
	set_namelist_value(namelist_dict, 'partial_bottom_cells', 'config_alter_ICs_for_pbcs', '.true.')
	set_namelist_value(namelist_dict, 'partial_bottom_cells', 'config_pbc_alteration_type', "'partial_cell'")

	if resolution == 'QU_240km':
		min_res = 240000
		if time_integrator == 'split_explicit':
			set_namelist_value(namelist_dict, 'time_integration', 'config_dt', "'02:00:00'")
		elif time_integrator == 'unsplit_explicit' or time_integrator == 'RK4':
			set_namelist_value(namelist_dict, 'time_integration', 'config_dt', "'00:20:00'")
	elif resolution == 'QU_120km':
		min_res = 120000
		if time_integrator == 'split_explicit':
			set_namelist_value(namelist_dict, 'time_integration', 'config_dt', "'01:00:00'")
		elif time_integrator == 'unsplit_explicit' or time_integrator == 'RK4':
			set_namelist_value(namelist_dict, 'time_integration', 'config_dt', "'00:10:00'")
	elif resolution == 'QU_60km':
		min_res = 60000
		if time_integrator == 'split_explicit':
			set_namelist_value(namelist_dict, 'time_integration', 'config_dt', "'00:40:00'")
		elif time_integrator == 'unsplit_explicit' or time_integrator == 'RK4':
			set_namelist_value(namelist_dict, 'time_integration', 'config_dt', "'00:05:00'")
	elif resolution == 'QU_30km':
		min_res = 30000
		if time_integrator == 'split_explicit':
			set_namelist_value(namelist_dict, 'time_integration', 'config_dt', "'00:20:00'")
		elif time_integrator == 'unsplit_explicit' or time_integrator == 'RK4':
			set_namelist_value(namelist_dict, 'time_integration', 'config_dt', "'00:02:30'")
	elif resolution == 'QU_15km':
		min_res = 15000
		if time_integrator == 'split_explicit':
			set_namelist_value(namelist_dict, 'time_integration', 'config_dt', "'00:10:00'")
		elif time_integrator == 'unsplit_explicit' or time_integrator == 'RK4':
			set_namelist_value(namelist_dict, 'time_integration', 'config_dt', "'00:01:15'")
	elif resolution == 'NA_15km_75km':
		min_res = 15000
		if time_integrator == 'split_explicit':
			set_namelist_value(namelist_dict, 'time_integration', 'config_dt', "'00:10:00'")
		elif time_integrator == 'unsplit_explicit' or time_integrator == 'RK4':
			set_namelist_value(namelist_dict, 'time_integration', 'config_dt', "'00:01:15'")

	# Setup del4 and del2 values
	del4 = scaled_del4_value(min_res)
	del2 = scaled_del2_value(min_res)
	set_namelist_value(namelist_dict, 'hmix_del2', 'config_use_mom_del2', '.false.')
	set_namelist_value(namelist_dict, 'hmix_del2', 'config_use_tracer_del2', '.false.')
	set_namelist_value(namelist_dict, 'hmix_del4', 'config_use_tracer_del4', '.false.')
	set_namelist_value(namelist_dict, 'hmix_del4', 'config_use_mom_del4', '.true.')
	set_namelist_value(namelist_dict, 'hmix_del4', 'config_mom_del4', del4)
	set_namelist_value(namelist_dict, 'hmix_del4', 'config_tracer_del4', del4)
	set_namelist_value(namelist_dict, 'hmix_del4_tensor', 'config_mom_del4_tensor', del4)
	set_namelist_value(namelist_dict, 'hmix_del2', 'config_mom_del2', del2)
	set_namelist_value(namelist_dict, 'hmix_del2', 'config_tracer_del2', del2)
	set_namelist_value(namelist_dict, 'hmix_del2_tensor', 'config_mom_del2_tensor', del2)

	# Setup forcing
	set_namelist_value(namelist_dict, 'forcing', 'config_forcing_type', "'restoring'")
	set_namelist_value(namelist_dict, 'forcing', 'config_restoreT_timescale', '30.0')
	set_namelist_value(namelist_dict, 'forcing', 'config_restoreS_timescale', '30.0')

	# Setup the EOS
	set_namelist_value(namelist_dict, 'eos', 'config_eos_type', "'jm'")

	# Setup vertical mixing
	set_namelist_value(namelist_dict, 'vmix_const', 'config_use_const_visc', '.false.')
	set_namelist_value(namelist_dict, 'vmix_const', 'config_use_const_diff', '.false.')
	set_namelist_value(namelist_dict, 'vmix_rich', 'config_use_rich_visc', '.true.')
	set_namelist_value(namelist_dict, 'vmix_rich', 'config_use_rich_diff', '.true.')

	# Setup bottom drag
	set_namelist_value(namelist_dict, 'bottom_drag', 'config_bottom_drag_coeff', '1.0e-3')
#}}}

#}}}

parser = OptionParser()
parser.add_option("-i", "--input", dest="namelist_in", help="Namelist input file", metavar="FILE")
parser.add_option("-o", "--output", dest="namelist_out", help="Namelist output file", metavar="FILE")
parser.add_option("-c", "--configuration", dest="configuration", help="Configuration to apply", metavar="CONF")
parser.add_option("-r", "--resolution", dest="resolution", help="Resolution of configuration to use", metavar="RES")
parser.add_option("-t", "--time_integrator", dest="time_integrator", help="Time integrator to use in the run", metavar="TIME_INT")

options, args = parser.parse_args()

if not options.namelist_in:
	parser.error("Two namelist files are required as inputs.")

if not options.namelist_out:
	parser.error("Two namelist files are required as inputs.")

if not options.configuration:
	parser.error("A configuration is a required input.")

if not options.resolution:
	parser.error("A resolution is a required input.")

if not options.time_integrator:
	time_integrator = 'split_explicit'
else:
	time_integrator = options.time_integrator

# Read in namelist:
namelist_dict = defaultdict(lambda : defaultdict(list))

read_namelist(namelist_dict, options.namelist_in)

setup_ocean_namelist(namelist_dict, options.configuration, options.resolution, time_integrator)

write_namelist(namelist_dict, options.namelist_in, options.namelist_out)

