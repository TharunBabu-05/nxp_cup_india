# NXP Sign Model Share Package

## Instructions

1. Install the required Python packages from requirements.txt.
```bash
pip install -r requirements.txt
```

2. Place any input image inside the sample_images folder (or provide its path).

3. Run:

python inference/<inference_script>.py

or

python inference/<inference_script>.py --image sample_images/example.jpg

*(For example: `python inference/tflite_inference.py --image sample_images/capture_20260716_133446_885_png.rf.38198d725f747fed30a512c3a58cf741.jpg` or `python inference/infer.py --source sample_images/`)*

4. The detected image will be saved in the output folder.

5. Do not retrain the model.

6. Do not modify the model file.

7. Only use the provided model for inference.
