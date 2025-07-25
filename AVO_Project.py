import pygame
import cv2
import os
import time
import shutil

# Initialize Pygame
pygame.init()

# Set up display
width, height = 800, 600 # Increased width for better layout with three buttons
button_height = 100 # Space allocated for buttons
video_height = height - button_height
window = pygame.display.set_mode((width, height))
pygame.display.set_caption('Live Feed with Record/Snap/Merge')

# Initialize camera
camera_index = 2 # Default camera index; change if necessary
camera = cv2.VideoCapture(camera_index)
if not camera.isOpened():
    print(f"Error: Could not open camera with index {camera_index}.")
    exit()

# Define colors
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
RED = (220, 20, 60)
GREEN = (34, 139, 34)
BLUE = (30, 144, 255)
GRAY = (50, 50, 50)

# Set fonts
font = pygame.font.SysFont(None, 40)

# Button states
is_recording = False
record_folder = None

# Determine the next dataset number
def get_next_dataset_number(base_name='dataset'):
    existing_folders = [folder for folder in os.listdir('.') if os.path.isdir(folder) and folder.startswith(base_name + '_')]
    numbers = []
    for folder in existing_folders:
        try:
            num = int(folder.split('_')[1])
            numbers.append(num)
        except (IndexError, ValueError):
            continue
    next_num = max(numbers) + 1 if numbers else 1
    return next_num

dataset_count = get_next_dataset_number()

# Create buttons
button_width = 150
button_height_actual = 60
padding = 20

# Positions for three buttons: Record, Snap, Merge
record_button = pygame.Rect(padding, video_height + (button_height - button_height_actual) // 2, button_width, button_height_actual)
snap_button = pygame.Rect((width - button_width) // 2, video_height + (button_height - button_height_actual) // 2, button_width, button_height_actual)
merge_button = pygame.Rect(width - button_width - padding, video_height + (button_height - button_height_actual) // 2, button_width, button_height_actual)

# Create directories if not exist
if not os.path.exists('snapshots'):
    os.makedirs('snapshots')

# Save a snapshot
def save_snapshot(frame):
    filename = f'snapshots/snapshot_{int(time.time())}.jpg'
    cv2.imwrite(filename, frame)
    print(f'Snapshot saved: {filename}')

# Start or stop recording
def toggle_recording():
    global is_recording, record_folder, dataset_count
    if is_recording:
        print(f"Stopped recording to {record_folder}")
        is_recording = False
    else:
        record_folder = f'dataset_{dataset_count}'
        os.makedirs(record_folder, exist_ok=True)
        print(f"Started recording to {record_folder}")
        is_recording = True

# Save frame to recording folder
def save_frame(frame):
    if is_recording and record_folder:
        filename = f'{record_folder}/frame_{int(time.time())}.jpg'
        cv2.imwrite(filename, frame)
        print(f"Frame saved: {filename}")

# Merge all datasets and snapshots into common_dataset
def merge_datasets():
    common_folder = 'common_dataset'
    os.makedirs(common_folder, exist_ok=True)
    # Merge snapshots
    snapshot_files = [f for f in os.listdir('snapshots') if os.path.isfile(os.path.join('snapshots', f))]
    for file in snapshot_files:
        src = os.path.join('snapshots', file)
        dst = os.path.join(common_folder, f'snapshot_{file}')
        shutil.copy2(src, dst)
    # Merge datasets
    dataset_folders = [folder for folder in os.listdir('.') if os.path.isdir(folder) and folder.startswith('dataset_')]
    for folder in dataset_folders:
        for file in os.listdir(folder):
            src = os.path.join(folder, file)
            dst = os.path.join(common_folder, f'{folder}_{file}')
            shutil.copy2(src, dst)
    print(f"All datasets and snapshots have been merged into '{common_folder}'.")

# Main loop
running = True
clock = pygame.time.Clock()

while running:
    ret, frame = camera.read()
    if not ret:
        print("Failed to grab frame.")
        break

    # Resize frame to fit the video area
    frame = cv2.resize(frame, (width, video_height))

    # Convert frame to RGB and then to Pygame surface
    frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    frame_rgb = pygame.surfarray.make_surface(frame_rgb)
    frame_rgb = pygame.transform.rotate(frame_rgb, -90) # Adjust rotation if needed

    # Event handling
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
        if event.type == pygame.MOUSEBUTTONDOWN:
            if record_button.collidepoint(event.pos):
                toggle_recording()
                if is_recording:
                    dataset_count += 1 # Prepare for next dataset
            if snap_button.collidepoint(event.pos):
                # Convert Pygame surface back to OpenCV format
                snapshot = pygame.surfarray.array3d(frame_rgb)
                snapshot = cv2.transpose(snapshot)
                snapshot = cv2.cvtColor(snapshot, cv2.COLOR_RGB2BGR)
                save_snapshot(snapshot)
            if merge_button.collidepoint(event.pos):
                merge_datasets()

    # Blit the video frame first
    window.blit(frame_rgb, (0, 0))

    # Draw a separator line between video and buttons
    pygame.draw.line(window, GRAY, (0, video_height), (width, video_height), 2)

    # Draw buttons on top of the video frame
    pygame.draw.rect(window, GREEN if is_recording else RED, record_button)
    pygame.draw.rect(window, BLUE, snap_button)
    pygame.draw.rect(window, (128, 0, 128), merge_button) # Purple color for Merge button

    # Draw button text
    record_text = font.render('Stop' if is_recording else 'Record', True, WHITE)
    snap_text = font.render('Snap', True, WHITE)
    merge_text = font.render('Merge', True, WHITE)

    # Center the text on the buttons
    record_text_rect = record_text.get_rect(center=record_button.center)
    snap_text_rect = snap_text.get_rect(center=snap_button.center)
    merge_text_rect = merge_text.get_rect(center=merge_button.center)

    window.blit(record_text, record_text_rect)
    window.blit(snap_text, snap_text_rect)
    window.blit(merge_text, merge_text_rect)

    # Save frame if recording
    frame_bgr = cv2.cvtColor(pygame.surfarray.array3d(frame_rgb), cv2.COLOR_RGB2BGR)
    frame_bgr = cv2.transpose(frame_bgr)
    save_frame(frame_bgr)

    # Update display
    pygame.display.update()

    # Cap the frame rate
    clock.tick(30)

# Release camera and quit Pygame
camera.release()
pygame.quit()