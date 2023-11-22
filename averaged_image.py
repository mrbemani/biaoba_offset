import cv2
import numpy as np
import glob
from scipy.ndimage import shift

def load_images(image_paths):
    """ Load images from the given paths. """
    images = []
    for path in image_paths:
        img = cv2.imread(path, cv2.IMREAD_GRAYSCALE)
        if img is not None:
            images.append(img)
        else:
            print(f"Warning: Unable to load image at {path}")
    return images

def align_images(images):
    """ Align images to the first image in the list. """
    if not images:
        print("No images to align.")
        return []

    aligned_images = [images[0]]

    for img in images[1:]:
        # Compute shift between images
        correlation = cv2.phaseCorrelate(np.float32(images[0]), np.float32(img))
        shift_y, shift_x = correlation[0]
        # Apply shift
        shifted_img = shift(img, shift=[shift_y, shift_x], mode='nearest')
        aligned_images.append(shifted_img)

    return aligned_images

def average_images(images):
    """ Compute the average of the aligned images. """
    if not images:
        print("No images to average.")
        return None

    avg_image = np.mean(np.array(images), axis=0)
    return np.uint8(avg_image)

# Example usage
image_paths = glob.glob('标靶/group03/*.bmp')  # Adjust the path and extension
images = load_images(image_paths)

if images:
    aligned_images = align_images(images)
    avg_image = average_images(aligned_images)

    if avg_image is not None:
        # Save the result
        cv2.imwrite('averaged_image.bmp', avg_image)
        # Display the averaged image for demonstration purposes
        avg_image
else:
    print("No images were loaded. Please check the file paths and formats.")
