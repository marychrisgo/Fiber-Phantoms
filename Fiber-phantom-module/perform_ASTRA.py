import astra
import numpy as np
import pylab
import matplotlib.pyplot as plt
import nibabel as nib

def save_as_nifti(array, file_path): # for 3D Slicer visualization
    nifti_img = nib.Nifti1Image(array, affine=np.eye(4))  
    nib.save(nifti_img, file_path)


def perform_tomography(volume, volume_dimensions, num_angles, geometry_type, det_width_u, det_width_v, det_count_x, det_count_y, i0, gamma, algorithm, show_plots):
    vol_geom = astra.create_vol_geom(volume_dimensions)
    angles = np.linspace(0, np.pi, num_angles, False)
    proj_geom = astra.create_proj_geom(geometry_type, det_width_u, det_width_v, det_count_x, det_count_y, angles)
    
    proj_id_original, proj_data_original = astra.create_sino3d_gpu(volume, proj_geom, vol_geom)

    virtual_photon_count = i0 * np.exp(-gamma * proj_data_original)
    noisy_virtual_photon_counts = np.random.poisson(virtual_photon_count)
    noisy_virtual_photon_counts[noisy_virtual_photon_counts == 0] = 1
    proj_data_noisy = -np.log(noisy_virtual_photon_counts/i0)/gamma

    proj_id_noisy = astra.data3d.create('-sino', proj_geom, proj_data_noisy)


    rec_id_original, rec_id_noisy = [astra.data3d.create('-vol', vol_geom) for _ in range(2)]
    cfgs = {
        'original': {'ReconstructionDataId': rec_id_original, 'ProjectionDataId': proj_id_original},
        'noisy': {'ReconstructionDataId': rec_id_noisy, 'ProjectionDataId': proj_id_noisy}
    }
    
    results = {}
    for key, cfg in cfgs.items():
        cfg = astra.astra_dict(algorithm)
        cfg.update(cfgs[key])
        alg_id = astra.algorithm.create(cfg)
        astra.algorithm.run(alg_id, 150)
        rec = astra.data3d.get(cfg['ReconstructionDataId'])
        results[key] = rec
        # np.save(f'reconstructed_{key}.npy', rec)
        # save_as_nifti(rec, f'reconstructed_{key}.nii')
        astra.algorithm.delete(alg_id)
        astra.data3d.delete(cfg['ReconstructionDataId'])
        astra.data3d.delete(cfg['ProjectionDataId'])

    if show_plots:
        pylab.gray()
        pylab.figure(figsize=(10, 8))
        pylab.imshow(proj_data_original[:, int(proj_data_original.shape[1] / 2), :])
        pylab.figure(figsize=(10, 8))
        pylab.imshow(proj_data_noisy[:, int(proj_data_noisy.shape[1] / 2), :])

    return results['original'], results['noisy']
