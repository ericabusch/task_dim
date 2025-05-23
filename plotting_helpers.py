from matplotlib import pyplot as plt
from matplotlib import cm, colors
from matplotlib.colors import ListedColormap,TwoSlopeNorm
import seaborn as sns
import nibabel as nib
from nilearn import plotting, image, glm
import numpy as np
from matplotlib import ticker
from mpl_toolkits.axes_grid1 import ImageGrid
import os,sys,glob
from surfplot import Plot
from neuromaps.transforms import mni152_to_fslr, mni152_to_fsaverage, mni152_to_civet, _estimate_density, fsaverage_to_fsaverage
from neuromaps.datasets import fetch_fslr, fetch_fsaverage, fetch_civet
from collections import defaultdict

def make_layers_dict(data, cmap, alpha=0.75, label=None, color_range=None, cbar=True):

	d = defaultdict()
	d['data'] = data
	d['cmap'] = cmap
	d['alpha'] = alpha
	d['label'] = label
	d['color_range'] = color_range
	d['cbar'] = cbar
	
	return d

def sigmoid(x):
	return 1 / (1 + np.exp(-x))

def create_depth_map(surf_type='fsaverage', target_density='41k'):

	if surf_type == 'fsaverage':
		assert (target_density in ['3k', '10k', '41k', '164k'])
		surfaces = fetch_fsaverage(density=target_density)
	elif surf_type == 'fslr':
		assert (target_density in ['4k', '8k', '32k', '164k'])
		surfaces = fetch_fslr(density=target_density)
	elif surf_type == 'civet':
		assert (target_density in ['41k', '164k'])
		surfaces = fetch_civet(density=target_density)

	# create the cmap for the depth map
	cmap = plt.get_cmap('Greys_r')
	cmap = cmap(np.arange(0,256))
	cmap = ListedColormap(cmap)

	left = sigmoid(nib.load(surfaces['sulc'][0]).agg_data()) 
	right = sigmoid(nib.load(surfaces['sulc'][1]).agg_data())
	
	depth = make_layers_dict(data={'left': left, 'right': right},
		cmap=cmap, alpha=1, color_range=(0, 1), cbar=False)

	return depth

def vol_to_surf(ds, surf_type='fsaverage', map_type='inflated', target_density='41k', method='linear'):
	
	if surf_type == 'fsaverage':
		assert (target_density in ['3k', '10k', '41k', '164k'])
		surfaces = fetch_fsaverage(density=target_density)
		data_lh, data_rh = mni152_to_fsaverage(ds, method=method)
	elif surf_type == 'fslr':
		assert (target_density in ['4k', '8k', '32k', '164k'])
		surfaces = fetch_fslr(density=target_density)
		data_lh, data_rh = mni152_to_fslr(ds, method=method)
	elif surf_type == 'civet':
		assert (target_density in ['41k', '164k'])
		surfaces = fetch_civet(density=target_density)
		data_lh, data_rh = mni152_to_civet(ds, method=method)
		
	surfs = surfaces[map_type]
	data = {'left': data_lh, 'right': data_rh}
	
	return surfs, data

def numpy_to_surface(ds, surf_type='fsaverage', map_type='inflated', target_density='41k', method='linear'):
	'''
	Takes a numpy array surface and makes a gifti surface ready
	for plotting 
	'''

	ds = ds.astype('float32')
	hemis = np.split(ds, 2)

	data = []

	for hemi in hemis:
		# Create new surface data objects for left and right hemispheres
		surf = nib.gifti.GiftiImage()
		surf_array = nib.gifti.GiftiDataArray(hemi.squeeze(), intent='NIFTI_INTENT_SHAPE', datatype='NIFTI_TYPE_FLOAT32')
		surf.add_gifti_data_array(surf_array)
		data.append(surf)

	data = tuple(data)
	density, = _estimate_density((data,), hemi=None)

	if density != target_density:
		data = fsaverage_to_fsaverage(data, target_density=target_density, method=method)
		density = target_density

	if surf_type == 'fsaverage':
		assert (density in ['3k', '10k', '41k', '164k'])
		surfaces = fetch_fsaverage(density)
	elif surf_type == 'fslr':
		assert (density in ['4k', '8k', '32k', '164k'])
		surfaces = fetch_fslr(density=density)
	elif surf_type == 'civet':
		assert (density in ['41k', '164k'])
		surfaces = fetch_civet(density=density)

	surfs = surfaces[map_type]
	data_lh, data_rh = data
	data = {'left': data_lh, 'right': data_rh}

	return surfs, data

def plot_surf_data(surfs, layers_info, surf_type='fslr', views=['lateral', 'medial'], zoom=1.35, brightness=0.8, scale=(10,10), 
	surf_alpha=1, add_depth=False, embed_nb=False, colorbar=True, cbar_loc=None, title=None, out_fn=None):
	
	if len(views) == 1:
		zoom=2.35
		scale=(10, 5)

	p = Plot(*surfs, views=views, zoom=zoom, brightness=brightness)

	# if we want to add depth insert into the start of the list
	if add_depth:
		density_est = (layers_info[0]['data']['left'], layers_info[0]['data']['right'])
		density, = _estimate_density((density_est,), hemi=None)
		depth = create_depth_map(surf_type=surf_type, target_density=density)
		layers_info.insert(0, depth)
	
	for layer in layers_info:
		p.add_layer(data=layer['data'], 
					cmap=layer['cmap'], 
					cbar_label=layer['label'], 
					alpha=layer['alpha'], 
					color_range=layer['color_range'],
					cbar=layer['cbar']
					 )
	
	if cbar_loc == 'right':
		kws = {'location': 'right', 'label_direction': 45, 'decimals': 1,
				 'fontsize': 8, 'n_ticks': 2, 'shrink': .15, 'aspect': 8,
				 'draw_border': False}
	else:
		kws = {'aspect': 10}
	
	fig = p.build(cbar_kws=kws, scale=scale, colorbar=colorbar)

	if title:
		plt.title(title)

	#save and clean up all opened figures
	if out_fn:
		fig.savefig(out_fn, bbox_inches='tight', transparent=True, dpi=300)
		plt.close('all')
	
	return fig, p