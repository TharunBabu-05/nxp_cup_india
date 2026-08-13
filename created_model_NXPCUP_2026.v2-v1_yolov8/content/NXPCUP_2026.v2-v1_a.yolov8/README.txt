The dataset includes 2167 images.
Images are annotated in YOLOv8 format.

The following pre-processing was applied to each image:
* Auto-orientation of pixel data (with EXIF-orientation stripping)
* Resize to 512x512 (Fit (black edges))

The following augmentation was applied to create 3 versions of each source image:
* Randomly crop between 0 and 20 percent of the image
* Random shear of between -15° to +15° horizontally and -10° to +10° vertically
* Random brigthness adjustment of between -25 and +25 percent
* Random exposure adjustment of between -15 and +15 percent
* Random Gaussian blur of between 0 and 0.4 pixels
* Salt and pepper noise was applied to 0.5 percent of pixels


