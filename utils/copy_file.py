import cli
import os
from netCDF4 import Dataset

def copy_netcdf_file(src_file_path, dst_file_path, time_index=None, force=True):
	if force and os.path.isfile(dst_file_path): os.remove(dst_file_path)

	src_file = Dataset(src_file_path, 'r')
	dst_file = Dataset(dst_file_path, 'w')

	if time_index == 'last': time_index = src_file.dimensions['Time'].size - 1

	dst_file.setncatts(src_file.__dict__)

	for name, dim in src_file.dimensions.items():
		if time_index == None or name != 'Time':
			dst_file.createDimension(name, (len(dim) if not dim.isunlimited() else None))
		else:
			dst_file.createDimension(name, 1)

	for name, var in src_file.variables.items():
		dst_file.createVariable(name, var.datatype, var.dimensions)
		if time_index == None:
			dst_file.variables[name][:] = src_file.variables[name][:]
		else:
			if var.dimensions[0] == 'Time' and len(var.dimensions) > 1:
				dst_file.variables[name][:] = src_file.variables[name][time_index,:]
			elif var.dimensions[0] == 'Time':
				dst_file.variables[name][:] = src_file.variables[name][time_index]
		dst_file.variables[name].setncatts(src_file.variables[name].__dict__)

	if time_index == None:
		cli.notice(f'Copy {src_file_path} to {dst_file_path}.')
	else:
		cli.notice(f'Copy time level {time_index} in {src_file_path} to {dst_file_path}.')

	src_file.close()
	return dst_file
