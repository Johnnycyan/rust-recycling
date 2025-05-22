import cv2
from pathlib import Path
from numba import jit, prange
import numpy as np

@jit(nopython=True)
def find_matches(result, threshold):
    """
    JIT-accelerated function to find locations where result exceeds threshold
    """
    matches = []
    h, w = result.shape
    for y in prange(h):
        for x in prange(w):
            if result[y, x] >= threshold:
                matches.append((x, y, result[y, x]))
    return matches

@jit(nopython=True)
def filter_overlapping_matches(matches, w, h, overlap_threshold=0.5):
    """
    JIT-accelerated function to remove overlapping detections using NumPy arrays.
    Ensures that only the highest score item is kept, even for overlaps between different items.
    """
    if len(matches) == 0:
        return np.empty((0, 3), dtype=np.float64)  # Return empty array with correct shape
    
    # Convert to numpy array for better handling in Numba
    matches_array = np.array(matches)
    
    # Sort by confidence (descending)
    sort_indices = np.argsort(-matches_array[:, 2])  # Negative for descending order
    matches_array = matches_array[sort_indices]
    
    keep = np.ones(len(matches_array), dtype=np.bool_)
    
    for i in range(len(matches_array)):
        if not keep[i]:
            continue
            
        for j in range(i+1, len(matches_array)):
            if not keep[j]:
                continue
                
            # Get coordinates
            x1, y1 = matches_array[i, 0], matches_array[i, 1]
            x2, y2 = x1 + w, y1 + h
            
            x1_b, y1_b = matches_array[j, 0], matches_array[j, 1]
            x2_b, y2_b = x1_b + w, y1_b + h
            
            # Calculate intersection area
            x_left = max(x1, x1_b)
            y_top = max(y1, y1_b)
            x_right = min(x2, x2_b)
            y_bottom = min(y2, y2_b)
            
            if x_right < x_left or y_bottom < y_top:
                intersection_area = 0
            else:
                intersection_area = (x_right - x_left) * (y_bottom - y_top)
            
            # Calculate union area
            box_area = w * h
            box_area_b = w * h
            union_area = box_area + box_area_b - intersection_area
            
            # If overlap ratio (IoU) is greater than threshold, suppress the lower confidence box
            if intersection_area / union_area > overlap_threshold:
                keep[j] = False
    
    # Return only the boxes we're keeping
    return matches_array[keep]

def find_icons_in_image(icons_folder, target_image_path, threshold=0.7, overlap_threshold=0.5):
    """
    Checks if any icon from icons_folder exists in the target image
    
    Parameters:
    icons_folder (str): Path to folder containing icon images
    target_image_path (str): Path to the image where we want to find icons
    threshold (float): Matching threshold (0-1), higher = more strict matching
    overlap_threshold (float): Threshold for removing overlapping detections
    
    Returns:
    dict: Dictionary of found icons with their positions and confidence scores
    """
    # Read the target image
    target_img = cv2.imread(target_image_path)
    if target_img is None:
        print(f"Error: Unable to read target image at {target_image_path}")
        return {}
        
    target_gray = cv2.cvtColor(target_img, cv2.COLOR_BGR2GRAY)
    
    # Collect all matches across all icons first
    all_matches = []
    icon_info = {}
    
    # Iterate through all icons in the folder
    for icon_file in Path(icons_folder).glob('*'):
        if icon_file.suffix.lower() in ['.png', '.jpg', '.jpeg', '.bmp']:
            icon_name = icon_file.stem
            
            # Read the icon image
            icon = cv2.imread(str(icon_file), cv2.IMREAD_GRAYSCALE)
            if icon is None:
                print(f"Warning: Unable to read icon image at {icon_file}")
                continue
            
            # Get icon dimensions
            h, w = icon.shape
            icon_info[icon_name] = {'dimensions': (w, h)}
            
            # Apply template matching
            result = cv2.matchTemplate(target_gray, icon, cv2.TM_CCOEFF_NORMED)
            
            # Find matches using np.where
            loc = np.where(result >= threshold)
            matches = [(pt[0], pt[1], result[pt[1], pt[0]], icon_name) for pt in zip(*loc[::-1])]
            
            # Add matches to the combined list
            all_matches.extend(matches)
    
    # Sort all matches by confidence (highest first)
    all_matches.sort(key=lambda x: x[2], reverse=True)
    
    # Filter overlapping matches across all icons
    filtered_matches = []
    if all_matches:
        used_areas = []
        
        for match in all_matches:
            x, y, conf, icon_name = match
            w, h = icon_info[icon_name]['dimensions']
            
            # Check if this match overlaps with any higher confidence match
            is_overlapping = False
            for used_x, used_y, used_w, used_h in used_areas:
                # Calculate intersection
                x_left = max(x, used_x)
                y_top = max(y, used_y)
                x_right = min(x + w, used_x + used_w)
                y_bottom = min(y + h, used_y + used_h)
                
                # Check if there's an overlap
                if x_left < x_right and y_top < y_bottom:
                    intersection_area = (x_right - x_left) * (y_bottom - y_top)
                    union_area = (w * h) + (used_w * used_h) - intersection_area
                    
                    # If overlap ratio is greater than threshold, skip this match
                    if intersection_area / union_area > overlap_threshold:
                        is_overlapping = True
                        break
            
            if not is_overlapping:
                filtered_matches.append(match)
                used_areas.append((x, y, w, h))
    
    # Organize results by icon
    found_icons = {}
    for x, y, conf, icon_name in filtered_matches:
        if icon_name not in found_icons:
            found_icons[icon_name] = {
                'positions': [],
                'confidence': [],
                'dimensions': icon_info[icon_name]['dimensions']
            }
        
        found_icons[icon_name]['positions'].append((int(x), int(y)))
        found_icons[icon_name]['confidence'].append(float(conf))
                
    print(f"Found {len(found_icons)} icons in the image")
    return found_icons

def visualize_results(target_image_path, found_icons, output_path='result.jpg'):
    """
    Draws bounding boxes around detected icons
    """
    # Read the target image
    img = cv2.imread(target_image_path)
    
    # Draw rectangles around found icons
    for icon_name, data in found_icons.items():
        w, h = data['dimensions']
        
        for idx, (x, y) in enumerate(data['positions']):
            confidence = data['confidence'][idx]
            
            # Draw rectangle
            cv2.rectangle(img, (x, y), (x + w, y + h), (0, 255, 0), 2)
            
            # Add text with icon name and confidence
            text = f"{icon_name}: {confidence:.2f}"
            cv2.putText(img, text, (x, y - 10), 
                        cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 2)
    
    # Save the result
    cv2.imwrite(output_path, img)
    print(f"Results saved to {output_path}")

# Example usage
if __name__ == "__main__":
    icons_folder = "C:\\Users\\john\\Documents\\Coding\\rust-recycling\\images-test"
    target_image = "C:\\Users\\john\\Documents\\Coding\\rust-recycling\\test2.png"
    
    # Find icons in the image
    results = find_icons_in_image(icons_folder, target_image, threshold=0.45, overlap_threshold=0)
    
    # Print results
    if results:
        print(f"Found {len(results)} icons in the image:")
        for icon, data in results.items():
            print(f"- {icon}: {len(data['positions'])} instances")
    else:
        print("No icons found in the image")
    
    # Visualize the results
    visualize_results(target_image, results)
