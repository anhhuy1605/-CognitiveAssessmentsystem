import os
import pandas as pd
import random

def setup_m4a_labels():
    audio_dir = './backend/audio/'
    output_file = './backend/labels_m4a.csv'
    
    if not os.path.exists(audio_dir):
        print(f"Error: {audio_dir} does not exist.")
        return

    # List all audio files
    files = [f for f in os.listdir(audio_dir) if f.lower().endswith(('.m4a', '.wav', '.mp3'))]
    print(f"Found {len(files)} audio files.")

    data = []
    labels = ['MCI', 'AD', 'Normal']
    genders = ['M', 'F']
    
    # Deterministic randomness for reproducibility if rerunning on same files
    random.seed(42)

    for i, filename in enumerate(files):
        # Distribute labels
        label = labels[i % 3] 
        # Random age between 60 and 90
        age = random.randint(60, 90)
        # Random gender
        gender = random.choice(genders)
        
        data.append({
            'filename': filename,
            'age': age,
            'gender': gender,
            'label': label
        })
    
    df = pd.DataFrame(data)
    df.to_csv(output_file, index=False)
    print(f"Created {output_file} with {len(df)} entries.")
    print("Sample data:")
    print(df.head())

if __name__ == "__main__":
    setup_m4a_labels()
