import fiona
import rasterio
import rasterio.mask
import shapely
from shapely.geometry import Polygon
import os

def create_file_list(num_features, filename_text):
    # Description: create list of file names from
    # number of features
    file_list = []
    print(filename_text)
    new_dir = os.getcwd() + '\\' + filename_text + '_clipped_rasters'
    os.mkdir(new_dir)
    for i in range(1,num_features+1):
        filename = new_dir + '\\' + filename_text + '_' + str(i) + '.tif'
        file_list.append(filename)
    return(file_list)

def raster_vector_intersect(raster_bounds, vector_bounds):
    # Description: Given bounds of raster and shapefile,
    # returns True if their bounds intersect.

    # Extract bounding points from raster
    raster_left_top = (raster_bounds.left, raster_bounds.top)
    raster_left_bottom = (raster_bounds.left, raster_bounds.bottom)
    raster_right_top = (raster_bounds.right, raster_bounds.top)
    raster_right_bottom = (raster_bounds.right, raster_bounds.bottom)

    # Extract bounding points from vector
    vector_left_top = (vector_bounds[0], vector_bounds[3])
    vector_left_bottom = (vector_bounds[0], vector_bounds[1])
    vector_right_top = (vector_bounds[2], vector_bounds[3])
    vector_right_bottom = (vector_bounds[2], vector_bounds[1])

    # Create polygon objects
    raster_polygon = Polygon([raster_left_top, raster_left_bottom, raster_right_bottom, raster_right_top, raster_left_top])
    vector_polygon = Polygon([vector_left_top, vector_left_bottom, vector_right_bottom, vector_right_top, vector_left_top])

    return (vector_polygon.intersects(raster_polygon))

# Consider creating function that takes as input shapefile and raster file,
# extracting all polygonal features as separate GeoTIFF files. But first get
# the code in one place and then get it to work.

def clip_mask_export(input_vector_file, input_raster_file):
    # Description: Given shapefile (iput_vector_file) and GeoTIFF
    # (input_raster_file), generate rasters masked for geometry of
    # each polygon.

    with fiona.open(input_vector_file, 'r') as shapefile:
        features = [feature["geometry"] for feature in shapefile]
        shapefile_crs = shapefile.crs['init'].lower()


    file_list = create_file_list(len(features), input_raster_file[:-4])

    feature_idx=0
    for single_feature in features:
        with rasterio.open(input_raster_file, 'r') as src:
            out_image, out_transform = rasterio.mask.mask(src, [single_feature], crop=True) # note: [single_feature]
            out_meta = src.meta.copy()
            raster_crs = str(src.crs).lower()
            raster_interleave = src.profile['interleave']

        # check that raster and vector file have same CRS.
        # [TO DO] Automatically reproject shapefile to CRS of raster
        # Do this once I understand fiona API.
        assert shapefile_crs == raster_crs, "shapefile and raster have different CRS!"

        out_meta.update({"driver": "GTiff",
                         "height": out_image.shape[1],
                         "width": out_image.shape[2],
                         "transform": out_transform,
                         "nodata": 0,
                         "interleave": raster_interleave})

        with rasterio.open(file_list[feature_idx], 'w', **out_meta) as dest:
            dest.write(out_image)

        feature_idx+=1

    # TODO: check that bounding box for features and raster intersect
    # For now, ensure this in QGIS.

def verify_clip_mask_export(input_vector_file, input_raster_file):
    # Description: Check if vector shapefile and raster GeoTIFF
    # intersect. If so, pass on to clip_mask_export function.

    with rasterio.open(input_raster_file, 'r') as src:
        with fiona.open(input_vector_file, 'r') as shapefile:
            raster_bounds = src.bounds
            vector_bounds = shapefile.bounds

    if raster_vector_intersect(raster_bounds, vector_bounds):
        clip_mask_export(input_vector_file, input_raster_file)
        print("intersection")
    else:
        print("no intersection")
