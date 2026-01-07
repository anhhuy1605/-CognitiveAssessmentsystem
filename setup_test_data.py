import os
import pandas as pd
import random

def setup_test_data():
    audio_dir = './backend/audio/'
    output_file = './backend/labels.csv'
    
    if not os.path.exists(audio_dir):
        print(f"Error: {audio_dir} does not exist.")
        return

    files = [f for f in os.listdir(audio_dir) if f.endswith(('.m4a', '.wav', '.mp3'))]
    print(f"Found {len(files)} audio files.")

    data = []
    groups = ['Healthy', 'MCI', 'AD']
    tasks = ['QA', 'Naming', 'Repetition']
    
    for i, filename in enumerate(files):
        # Assign groups in a weighted random way to ensure we have all classes
        # or just round robin to guarantee distribution
        group = groups[i % 3] 
        task = tasks[i % 3]
        
        data.append({
            'file_name': filename,
            'participant_id': f'P{i:03d}',
            'group': group,
            'age': random.randint(60, 90),
            'gender': random.choice(['M', 'F']),
            'task_type': task
        })
    
    df = pd.DataFrame(data)
    df.to_csv(output_file, index=False)
    print(f"Created {output_file} with {len(df)} entries.")
    print("Sample data:")
    print(df.head())

if __name__ == "__main__":
    setup_test_data()
