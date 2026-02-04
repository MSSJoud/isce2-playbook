import matplotlib.pyplot as plt
import numpy as np
from osgeo import gdal


def plot_complex_data(
    gdal_filename: str,
    output_filename: str,
    title: str = None,
    aspect: int = 1,
    datamin: int = None,
    datamax: int = None,
    interpolation: str = "nearest",
    draw_colorbar: bool = False,
    colorbar_orientation: str = "horizontal",
) -> None:
    # Load the data into numpy array
    ds = gdal.Open(gdal_filename, gdal.GA_ReadOnly)
    slc: np.ndarray = ds.GetRasterBand(1).ReadAsArray()
    transform = ds.GetGeoTransform()
    ds = None

    # getting the min max of the axes
    firstx = transform[0]
    firsty = transform[3]
    deltay = transform[5]
    deltax = transform[1]
    lastx = firstx + slc.shape[1] * deltax
    lasty = firsty + slc.shape[0] * deltay
    ymin = np.min([lasty, firsty])
    ymax = np.max([lasty, firsty])
    xmin = np.min([lastx, firstx])
    xmax = np.max([lastx, firstx])

    # put all zero values to nan and do not plot nan
    try:
        slc[slc == 0] = np.nan
    except:
        pass

    fig = plt.figure(figsize=(18, 16))
    ax = fig.add_subplot(1, 2, 1)
    cax1 = ax.imshow(
        np.abs(slc),
        vmin=datamin,
        vmax=datamax,
        cmap="gray",
        extent=[xmin, xmax, ymin, ymax],
        interpolation=interpolation,
    )
    ax.set_title(title + " (amplitude)")
    if draw_colorbar:
        _ = fig.colorbar(cax1, orientation=colorbar_orientation)
    ax.set_aspect(aspect)

    ax = fig.add_subplot(1, 2, 2)
    cax2 = ax.imshow(
        np.angle(slc),
        cmap="rainbow",
        vmin=-np.pi,
        vmax=np.pi,
        extent=[xmin, xmax, ymin, ymax],
        interpolation=interpolation,
    )
    ax.set_title(title + " (phase [rad])")
    if draw_colorbar:
        _ = fig.colorbar(cax2, orientation=colorbar_orientation)
    ax.set_aspect(aspect)

    # clearing the data
    slc = None

    plt.savefig(output_filename)


if __name__ == "__main__":
    from settings import OUTPUT_DIR

    plot_complex_data(
        gdal_filename=str(
            (OUTPUT_DIR / "merged" / "filt_topophase.flat.vrt").resolve()
        ),
        output_filename=str((OUTPUT_DIR / "filt_topophase_flat.png").resolve()),
        title="MERGED FILT IFG ",
        aspect=1,
        datamin=0,
        datamax=10000,
        draw_colorbar=True,
    )
