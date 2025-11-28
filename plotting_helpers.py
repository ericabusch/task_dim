from matplotlib import pyplot as plt
from matplotlib import cm, colors
from matplotlib.colors import ListedColormap,TwoSlopeNorm
import seaborn as sns
import nibabel as nib
from nilearn import plotting, image, glm
import numpy as np
import tempfile
from matplotlib.colors import LinearSegmentedColormap
from matplotlib import ticker
from mpl_toolkits.axes_grid1 import ImageGrid
import os,sys,glob,math
from PIL import Image
from surfplot import Plot
from neuromaps.transforms import mni152_to_fslr, mni152_to_fsaverage, mni152_to_civet, _estimate_density, fsaverage_to_fsaverage
from neuromaps.datasets import fetch_fslr, fetch_fsaverage, fetch_civet
from collections import defaultdict
from mpl_toolkits.axes_grid1 import make_axes_locatable

def make_layers_dict(data, cmap, mask=None, alpha=0.75, label=None, color_range=None, cbar=True):
	d = defaultdict()
	d['data'] = data
	d['mask'] = mask
	d['cmap'] = cmap
	d['alpha'] = alpha
	d['label'] = label
	d['color_range'] = color_range
	d['cbar'] = cbar
	return d

def diverging_colormap_bp():
    """
    Create a continuous diverging colormap using hex codes:
    dark blue -> turquoise -> white -> pink -> red
    Returns a matplotlib colormap object.
    """
    # Hex codes for the colors
    colors = [
		"#081237",
        "#0C83AA",  
        "#30DCFF",
        "#B3FAFF",  # turquoise
        "#FFFFFF",  # white
        "#F8D9FA",  # pink
        "#FE97F9",
        "#FF0090",   
		"#53001D"
    ]
    colormap = LinearSegmentedColormap.from_list("custom_diverging_hex", colors)
    return colormap

def diverging_colormap_bp():
    """
    Create a continuous diverging colormap using hex codes:
    dark blue -> turquoise -> white -> pink -> red
    Returns a matplotlib colormap object.
    """
    # Hex codes for the colors
    colors = [
        "#154500",  
        "#34AE00",
        "#84FF00",  
        "#FFFFFF",  # white
        "#F8D9FA",  
        "#FE97F9",
        "#FF0090"   
    ]
    colormap = LinearSegmentedColormap.from_list("custom_diverging_hex", colors)
    return colormap

def get_palette7_rainbow():
	hex = ["#ED5151",'#FE7F2D', '#FCCA46', '#A1C181', '#47A8BD','#B47BBF',"#FF91E7"]
	palette7_rainbow = sns.color_palette(hex)
	return palette7_rainbow

def get_paired_palette():
	return sns.color_palette(["#3943B7", "#C1C4EC", "#32A287", '#9EE6B2', "#E14B67","#EAAEB9",'#F06305',"#FDC29B"])

def sigmoid(x):
	return 1 / (1 + np.exp(-x))

def create_depth_map(surf_type='fsaverage', target_density='41k',include_cbar=False):
	'''
	Creates a depth map for the given surface type and density
	surf_type in ['fsaverage', 'fslr', 'civet']
	target_density in ['3k', '10k', '41k', '164k'] for fsaverage
		target_density in ['4k', '8k', '32k', '164k'] for fslr
		target_density in ['41k', '164k'] for civet
	'''

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
		cmap=cmap, alpha=1, color_range=(0, 1), cbar=include_cbar)

	return depth

def apply_surface_mask(data_surface, mask_surface):
	'''
	Applies a mask to the surface data
	data_surface: dictionary with keys 'left' and 'right' containing the surface data
	mask_surface: dictionary with keys 'left' and 'right' containing the mask data
	'''
	data_lh = data_surface['left'].agg_data()
	data_rh = data_surface['right'].agg_data()
	mask_lh = np.array(mask_surface['left'].agg_data())
	mask_rh = np.array(mask_surface['right'].agg_data())

	data_lh[np.where(mask_lh == 0)[0]] = np.nan
	data_rh[np.where(mask_rh == 0)[0]] = np.nan

	surf_lh = nib.gifti.GiftiImage()
	surf_array = nib.gifti.GiftiDataArray(data_lh.squeeze(), intent='NIFTI_INTENT_SHAPE', datatype='NIFTI_TYPE_FLOAT32')
	surf_lh.add_gifti_data_array(surf_array)
	surf_rh = nib.gifti.GiftiImage()
	surf_array = nib.gifti.GiftiDataArray(data_rh.squeeze(), intent='NIFTI_INTENT_SHAPE', datatype='NIFTI_TYPE_FLOAT32')
	surf_rh.add_gifti_data_array(surf_array)
	masked_data = {'left':surf_lh, 'right':surf_rh}
	return masked_data

def vol_to_surf(ds, surf_type='fsaverage', map_type='inflated', target_density='41k', method='nearest'):
	'''
	Takes a volumetric image and makes a gifti surface ready
	for plotting
	surf_type in ['fsaverage', 'fslr', 'civet']
	map_type in ['inflated', 'pial', 'white', 'smoothwm']
	target_density in ['3k', '10k', '41k', '164k'] for fsaverage
		target_density in ['4k', '8k', '32k', '164k'] for fslr
		target_density in ['41k', '164k'] for civet
	method in ['linear', 'nearest', 'nearest_vertex']
		linear: linear interpolation
		nearest: nearest neighbor interpolation
		nearest_vertex: nearest vertex interpolation
	'''


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
	medial_mask = {'left':nib.load(surfaces['medial'][0]), 'right':nib.load(surfaces['medial'][1])}
	return surfs, data, medial_mask

def numpy_to_surf(ds, surf_type='fsaverage', map_type='inflated', target_density='41k', method='nearest'):
	'''
	Takes a numpy array surface and makes a gifti surface ready
	for plotting 
	surf_type in ['fsaverage', 'fslr', 'civet']
	map_type in ['inflated', 'pial', 'white', 'smoothwm']
	target_density in ['3k', '10k', '41k', '164k'] for fsaverage
		target_density in ['4k', '8k', '32k', '164k'] for fslr
		target_density in ['41k', '164k'] for civet
	method in ['linear', 'nearest', 'nearest_vertex']
		linear: linear interpolation
		nearest: nearest neighbor interpolation
		nearest_vertex: nearest vertex interpolation
		nearest_vertex is only available for fsaverage and fslr
		nearest is only available for civet
		linear is available for all

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
	medial_mask = {'left':nib.load(surfaces['medial'][0]), 'right':nib.load(surfaces['medial'][1])}

	return surfs, data, medial_mask

def plot_surf_data(surfs, layers_info, surf_type='fslr', views=['lateral', 'medial'], zoom=1.35, brightness=0.8, scale=(10,10), 
	surf_alpha=1, add_depth=True, embed_nb=False, colorbar=True, cbar_loc=None, title=None, out_fn=None, mask=True):
	'''
	Plot surface data on a brain surface
	surfs: list of surface data to plot
	layers_info: list of dictionaries with keys 'data', 'cmap', 'alpha', 'label', 'color_range', 'cbar'
	surf_type: type of surface to plot
		surf_type in ['fsaverage', 'fslr', 'civet']
	views: list of views to plot
		views in ['lateral', 'medial', 'dorsal', 'ventral', 'anterior', 'posterior']
	zoom: zoom level for the plot
	brightness: brightness level for the plot
	scale: scale for the plot
	surf_alpha: alpha level for the surface
	add_depth: if True, add a depth map to the plot
	embed_nb: if True, embed the plot in a jupyter notebook
	colorbar: if True, add a colorbar to the plot
	cbar_loc: location of the colorbar
		cbar_loc in ['left', 'right', 'top', 'bottom']
	title: title for the plot
	out_fn: filename to save the plot
	mask: if True, apply a mask to the surface data
	'''

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

	if mask:
		temp = []
		for layer in layers_info:
			if layer['mask'] is None:
				temp.append(None)
			else:
				data_layer_masked = apply_surface_mask(layer["data"], layer["mask"])
				temp.append(data_layer_masked)
		
		for i in range(len(temp)):
			if layers_info[i]['mask'] != None:
				layers_info[i]['data'] = temp[i]
	for i, layer in enumerate(layers_info):
		
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

def load_schaefer_atlas(resolution_mm=2, yeo_networks=17):

    """
    Load the Schaefer atlas with specified resolution and Yeo networks.

    Parameters
    ----------
    resolution_mm : int
        The resolution of the atlas in mm.
    yeo_networks : int
        The number of Yeo networks to use.

    Returns
    -------
    atlas_img : nibabel.Nifti1Image
        The Schaefer atlas image.
    """
    from nilearn.datasets import fetch_atlas_schaefer_2018
    atlas = fetch_atlas_schaefer_2018(resolution_mm=resolution_mm, yeo_networks=yeo_networks)
    return nib.load(atlas['maps'])

def expand_parcellation_to_volume(values, atlas_img):
    """
    Map region-wise values to a 3D volume based on atlas parcellation.

    Parameters
    ----------
    values : array-like, shape (n_regions,)
        Array of values for each region (region 1 at index 0, region 400 at index 399).
    atlas_img : niftiabel.Nifti1Image
		3D image of the brain with regions defined by an atlas, e.g., Schaefer
        With voxel values 1..n_regions.

    Returns
    -------
    out_vol : 3D numpy array
        Volume with values assigned according to atlas.
    """
    atlas_data = atlas_img.get_fdata()
    out_vol = np.zeros_like(atlas_data, dtype=np.float64)
    out_vol[:] = 1000  # Set background to nan
    for region in range(1, len(values)+1):
        out_vol[atlas_data == region] = values[region-1]
	# Figure out how many voxels are nan
    print(f'number of nan voxels: {(out_vol == 1000).sum()} out of {out_vol.size} total voxels')
    out_vol[atlas_data == 0] = np.nan
    return nib.Nifti1Image(out_vol, atlas_img.affine, atlas_img.header)

def generate_surface_plot(data_fn, image_fn, atlas, cmap, cbar_range, surf_type='fslr', target_density='32k', include_cbar=False, title=None,method='nearest', threshold=None, mask_medial_wall=True):
	"""
	Generate and save surface plots from data arrays.
	"""
	if atlas == 'Schaefer':
		atlas_img = load_schaefer_atlas()
		data_arr = np.load(data_fn) if isinstance(data_fn, str) else data_fn
		vol_img = expand_parcellation_to_volume(data_arr, atlas_img)
	elif atlas == 'searchlight':
		vol_img = nib.load(data_fn) if isinstance(data_fn, str) else data_fn
	else:
		raise ValueError("Invalid atlas type. Choose 'Schaefer' or 'searchlight'.") 
	if not isinstance(vol_img, nib.Nifti1Image):
			raise ValueError("vol_img must be a Nifti image or a valid numpy array.")       
	
	surfs, data, mask = vol_to_surf(vol_img, surf_type=surf_type, map_type='inflated', target_density=target_density, method=method)
	if not mask_medial_wall:
		mask=None

	# --- Masking logic ---
	if threshold is not None:
        # Get the colorbar center
		center = (cbar_range[0] + cbar_range[1]) / 2
		for hemi in ['left', 'right']:
			arr = data[hemi].agg_data().copy()
			if abs(center) < 1e-6:  # Centered at 0
				mask_idx = (arr > -threshold) & (arr < threshold)
			else:  # Not centered at 0
				mask_idx = (arr > 0) & (arr < threshold)
			arr[mask_idx] = np.nan
            # Update the data object
			new_img = nib.gifti.GiftiImage()
			new_img.add_gifti_data_array(
                nib.gifti.GiftiDataArray(arr.squeeze(), intent='NIFTI_INTENT_SHAPE', datatype='NIFTI_TYPE_FLOAT32')
            )
			data[hemi] = new_img
	
	layer = make_layers_dict(
		data=data, mask=mask, cmap=plt.get_cmap(cmap), alpha=1, color_range=cbar_range, cbar=include_cbar
	)
	plot_surf_data(
		surfs, [layer], surf_type=surf_type, colorbar=include_cbar, title=title, out_fn=image_fn 
	)
	print("Generated surface plot:", image_fn)
	if image_fn is not None:
		plt.close('all')
	return image_fn, vol_img

def compile_surface_plots_to_grid_from_niftis(
    nifti_images,
    output_path,
    atlas='Schaefer',
    surf_type='fsaverage',
    method='linear',
    target_density='41k',
    titles=None,
    main_title=None,
    cmap='viridis',
    cbar_range=(0, 1),
    cbar_label='',
    threshold=None,
    mask=True,
    rerun=True
):
    """
    Like compile_surface_plots_to_grid, but takes a list of Nifti images instead of file paths.
    """
    temp_data_files = []
    temp_image_files = []
    try:
        # Save each Nifti image to a temporary file
        for idx, img in enumerate(nifti_images):
            tmp_data = tempfile.NamedTemporaryFile(suffix='.nii.gz', delete=False)
            nib.save(img, tmp_data.name)
            temp_data_files.append(tmp_data.name)
            tmp_data.close()
            temp_image_files.append(tmp_data.name.replace('.nii.gz', '.png'))

        # Call the original helper function
        compile_surface_plots_to_grid(
            data_files=temp_data_files,
            image_files=temp_image_files,
            output_path=output_path,
            atlas=atlas,
            surf_type=surf_type,
            method=method,
            target_density=target_density,
            titles=titles,
            main_title=main_title,
            cmap=cmap,
            cbar_range=cbar_range,
            cbar_label=cbar_label,
            threshold=threshold,
            mask=mask,
            rerun=rerun
        )
    finally:
        # Clean up temporary files
        for f in temp_data_files + temp_image_files:
            try:
                os.remove(f)
            except FileNotFoundError:
                pass

def _calc_grid(n):
    """Calculate grid shape (rows, cols) for n images, minimizing empty space."""
    ncols = math.ceil(math.sqrt(n))
    nrows = math.ceil(n / ncols)
    return nrows, ncols

def _load_images(image_files):
    """Load images from file paths."""
    return [Image.open(f) for f in image_files]

def get_global_value_range(data_files, return_int=True, return_symmetric=False):
    """
    Given a list of file paths (npy or nii.gz), return (min, max) of all values across all files.
    """
    global_min = np.inf
    global_max = -np.inf
    assert len(data_files) > 0, "data_files list should not be empty."
    for f in data_files:
        if type(f) == np.ndarray:
            data = f
        elif type(f) == str:
            if f.endswith('.npy'):
                data = np.load(f)
            elif f.endswith('.nii') or f.endswith('.nii.gz'):
                import nibabel as nib
                data = nib.load(f).get_fdata()
            else:
                raise ValueError(f"Unsupported file type: {f}")
        else:
            raise ValueError(f"Unsupported file type: {f}")
        
        # Flatten and ignore NaNs
        data = data[np.isfinite(data)]
        if data.size == 0:
            continue
        global_min = min(global_min, np.min(data))
        global_max = max(global_max, np.max(data))
    if return_int:
        global_max, global_min = int(np.ceil(global_max)), int(np.floor(global_min))
    if return_symmetric:
        absv = np.max((np.abs(global_max), np.abs(global_min)))
        global_min, global_max = -1*absv, absv
    return (global_min, global_max)

def compile_surface_plots_to_grid(image_files, data_files, output_path, atlas='Schaefer', 
								  surf_type='fslr', method='linear', target_density='32k',rerun=False, 
								  titles=None, main_title=None, cmap='viridis', cbar_range=(0, 1),cbar_label='',threshold=None,mask=True):
	"""
	Compile surface plots into a grid, generating them if needed.

	Parameters
	----------
	rerun : bool
		If True, regenerate images from data_files.
	image_files : list of str
		Filenames for each image.
	data_files : list of string, either numpy arrays or Nifti images
		If rerun is True, these are the data arrays to plot.
	output_path : str
		Output filename for the grid plot.
	atlas : str
		'Schaefer' or 'searchlight'.
	titles : list of str
		Titles for each subplot.
	main_title : str
		Main title for the figure.
	cmap : str
		Colormap name.
	cbar_range : tuple
		Colorbar range (vmin, vmax).
	"""
	assert atlas in ['Schaefer', 'searchlight'], "Invalid atlas type. Choose 'Schaefer' or 'searchlight'."

	# Step 1: Check which images exist
	if not rerun:
		images_to_visualize = [f for f in image_files if os.path.exists(f)]
		if len(images_to_visualize) == 0:
			raise FileNotFoundError("No input images found and rerun is False.")
	else:
		images_to_visualize = []
		for i in range(len(data_files)):
			fn,_=generate_surface_plot(data_files[i], image_files[i], atlas, cmap, cbar_range, method=method,
							  surf_type=surf_type, target_density=target_density,mask_medial_wall=mask,threshold=threshold)
			images_to_visualize.append(fn)

	# Step 2: Load images
	images = _load_images(images_to_visualize)
	n_imgs = len(images)
	if n_imgs <= 3: 
		# If 3 or fewer images, use a single row
		nrows, ncols = 1, n_imgs
	else:
		nrows, ncols = _calc_grid(n_imgs)

	# Step 3: Plot grid
	fig_w, fig_h = images[0].width / 100, images[0].height / 100
	fig, axes = plt.subplots(
		nrows, ncols, figsize=(fig_w * ncols, fig_h * nrows + 1)
	)
	axes = axes.flatten() if n_imgs > 1 else [axes]

	for idx, (ax, img) in enumerate(zip(axes, images)):
		ax.imshow(img)
		ax.axis('off')
		if titles and idx < len(titles):
			ax.set_title(titles[idx], fontsize=32, pad=16)
	# Main title
	if main_title:
		plt.suptitle(main_title, fontsize=32, y=0.98)

	# Hide unused axes
	for ax in axes[n_imgs:]:
		ax.axis('off')

	# Colorbar (vertical, right, full height)
	norm = plt.Normalize(vmin=cbar_range[0], vmax=cbar_range[1])
	sm = plt.cm.ScalarMappable(cmap=plt.get_cmap(cmap), norm=norm)
	sm.set_array([])

	# Add a new axis for the colorbar that spans the full height of the figure
	# [left, bottom, width, height] in figure coordinates
	cbar_ax = fig.add_axes([0.92, 0.12, 0.025, 0.76])
	cbar = plt.colorbar(sm, cax=cbar_ax, orientation='vertical')
	cbar.set_label(cbar_label, fontsize=36, labelpad=24)
	cbar.ax.tick_params(labelsize=32)

	plt.subplots_adjust(left=0.05, right=0.9, top=0.9, bottom=0.08, wspace=0.2, hspace=0.25)
	plt.savefig(output_path, bbox_inches='tight', dpi=300)
	print(f"Compiled surface plots into grid: {output_path}")
	plt.close(fig)

def compile_surface_plots_to_grid_by_rows(
	image_files,
	data_files,
	output_path,
	n_rows=1,
	atlas='Schaefer',
	surf_type='fslr',
	method='linear',
	target_density='32k',
	rerun=False,
	titles=None,
	main_title=None,
	cmaps_per_row=('viridis',),
	cbar_ranges_per_row=None,
	cbar_labels_per_row=None,
	threshold=None,
	mask=True,
):
	"""
	Compile surface plots into a grid with a fixed number of rows and support per-row colormaps and colorbars.

	Differences vs compile_surface_plots_to_grid:
	- n_rows: number of rows in the output grid. n_cols is computed as ceil(n_images / n_rows).
	- cmaps_per_row: iterable of colormap names (or single name) of length n_rows (or 1 to broadcast).
	- cbar_ranges_per_row: iterable of (vmin, vmax) tuples for each row (or single tuple to broadcast).
	- cbar_labels_per_row: iterable of labels for each row colorbar (or single string to broadcast).

	Notes:
	- If rerun is True, data_files are used to (re)generate images and image_files will be overwritten.
	- This function requires that len(image_files) == len(data_files).
	"""
	assert atlas in ['Schaefer', 'searchlight'], "Invalid atlas type. Choose 'Schaefer' or 'searchlight'."
	if len(image_files) != len(data_files):
		raise ValueError("image_files and data_files must have the same length.")

	# Determine number of images (use data_files when rerunning, else require all image files exist)
	if rerun:
		n_imgs = len(data_files)
		print(f'Rerunning surface plot generation for {n_imgs} images.')
	else:
		missing = [f for f in image_files if not os.path.exists(f)]
		if len(missing) > 0:
			raise FileNotFoundError(f"Some image files are missing and rerun is False: {missing}")
		n_imgs = len(image_files)

	# Compute grid shape
	n_rows = max(1, int(n_rows))
	n_cols = math.ceil(n_imgs / n_rows)

	# Normalize per-row inputs (broadcast if single provided)
	def _broadcast_param(param, name):
		if param is None:
			return [None] * n_rows
		if isinstance(param, (list, tuple)):
			if len(param) == 1:
				return list(param) * n_rows
			if len(param) != n_rows:
				raise ValueError(f"{name} must have length 1 or n_rows ({n_rows}).")
			return list(param)
		else:
			return [param] * n_rows

	cmaps_per_row = _broadcast_param(cmaps_per_row, "cmaps_per_row")
	if cbar_ranges_per_row is None:
		# Default: try to determine a global range; fallback to (0,1)
		if rerun:
			# if rerun, compute global range from data_files (supports .npy and nifti)
			try:
				cbar_ranges_per_row = [get_global_value_range(data_files)] * n_rows
			except Exception:
				cbar_ranges_per_row = [(0, 1)] * n_rows
		else:
			cbar_ranges_per_row = [(0, 1)] * n_rows
	cbar_ranges_per_row = _broadcast_param(cbar_ranges_per_row, "cbar_ranges_per_row")
	cbar_labels_per_row = _broadcast_param(cbar_labels_per_row if cbar_labels_per_row is not None else '', "cbar_labels_per_row")

	# If rerun: generate images with appropriate row colormap / cbar_range
	images_to_visualize = []
	if rerun:
		for i in range(n_imgs):
			row_idx = min(n_rows - 1, i // n_cols)  # assign image to row based on index
			cmap_row = cmaps_per_row[row_idx]
			cbar_range_row = cbar_ranges_per_row[row_idx]
			out_image = image_files[i]
			fn, _ = generate_surface_plot(
				data_files[i],
				out_image,
				atlas,
				cmap_row,
				cbar_range_row,
				surf_type=surf_type,
				target_density=target_density,
				method=method,
				include_cbar=False,
				threshold=threshold,
				mask_medial_wall=mask,
			)
			images_to_visualize.append(fn)
	else:
		# All image files must exist (checked above)
		images_to_visualize = list(image_files)

	# Load images
	images = _load_images(images_to_visualize)
	if len(images) == 0:
		raise ValueError("No images to visualize after processing.")
	# Ensure we have exactly n_imgs loaded
	n_imgs = len(images)
	# Recompute n_cols in case n_imgs changed
	n_cols = math.ceil(n_imgs / n_rows)

	# Create subplots
	fig_w, fig_h = images[0].width / 100.0, images[0].height / 100.0
	fig, axes = plt.subplots(n_rows, n_cols, figsize=(fig_w * n_cols, fig_h * n_rows + 1))
	# Normalize axes to a flat list for iteration
	if n_rows * n_cols == 1:
		axes_list = [axes]
	else:
		axes_list = axes.flatten().tolist()

	# Plot images
	for idx, ax in enumerate(axes_list[:n_imgs]):
		img = images[idx]
		ax.imshow(img)
		ax.axis('off')
		if titles and idx < len(titles):
			ax.set_title(titles[idx], fontsize=32, pad=8)

	# Hide remaining axes
	for ax in axes_list[n_imgs:]:
		ax.axis('off')

	if main_title:
		plt.suptitle(main_title, fontsize=40, y=0.98)

	# Add one colorbar per row. Determine the vertical span of axes in each row.
	for row_idx in range(n_rows):
		# collect axes for this row (some may be missing if fewer images)
		start = row_idx * n_cols
		end = min(start + n_cols, n_imgs)
		if start >= n_imgs:
			continue  # empty row
		row_axes = [axes_list[i] for i in range(start, end)]
		# Determine bottom and top in figure coordinates
		bottoms = [ax.get_position().y0 for ax in row_axes]
		tops = [ax.get_position().y1 for ax in row_axes]
		bottoms_valid = bottoms if len(bottoms) > 0 else [0.1]
		tops_valid = tops if len(tops) > 0 else [0.9]
		bottom = min(bottoms_valid)
		top = max(tops_valid)
		height = top - bottom
		# place colorbar slightly to the right of the rightmost axis in the row
		right_positions = [ax.get_position().x1 for ax in row_axes]
		rightmost = max(right_positions)
		cbar_x = rightmost + 0.01
		cbar_width = 0.02

		cmap_row = cmaps_per_row[row_idx]
		cbar_range_row = cbar_ranges_per_row[row_idx]
		cbar_label_row = cbar_labels_per_row[row_idx] if cbar_labels_per_row[row_idx] else ''

		norm = plt.Normalize(vmin=cbar_range_row[0], vmax=cbar_range_row[1])
		sm = plt.cm.ScalarMappable(cmap=plt.get_cmap(cmap_row), norm=norm)
		sm.set_array([])

		# Add axes in figure coords
		cax = fig.add_axes([cbar_x, bottom, cbar_width, height])
		cbar = plt.colorbar(sm, cax=cax, orientation='vertical')
		cbar.set_label(cbar_label_row, fontsize=24)
		cbar.ax.tick_params(labelsize=20)

	plt.subplots_adjust(left=0.03, right=0.92, top=0.92, bottom=0.05, wspace=0.05, hspace=0.05)
	plt.savefig(output_path, bbox_inches='tight', dpi=300)
	print(f"Compiled surface plots into grid (by rows): {output_path}")
	plt.close(fig)
	return output_path