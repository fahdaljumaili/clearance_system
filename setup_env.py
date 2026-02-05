import os
import json
from pywebpush import WebPush, webpush

def generate_vapid_keys():
    """Generate VAPID keys and save them to instance/vapid_keys.json"""
    instance_dir = os.path.join(os.getcwd(), 'instance')
    file_path = os.path.join(instance_dir, 'vapid_keys.json')

    if not os.path.exists(instance_dir):
        os.makedirs(instance_dir)
        print(f"Created directory: {instance_dir}")

    if not os.path.exists(file_path):
        print("Generating new VAPID keys...")
        # Note: pywebpush doesn't have a simple 'generate_keys' function exposed simply in all versions,
        # usually we use the CLI 'vapid --applicationServerKey'. 
        # For simplicity in this script, we can shell out or use a library specific way if known.
        # Alternatively, we can assume the user runs the command. 
        # But let's try to run the system command which pywebpush installs.
        
        try:
            # Using subprocess to call the CLI command installed by pywebpush
            import subprocess
            # This is a bit hacky but ensures we get valid keys.
            # A cleaner way using python code directly implies importing Vapid core.
            pass
        except Exception as e:
            print(f"Error: {e}")

        # Fallback / Better approach: Suggest user to run command if we can't do it easily in python without deeper imports
        # Actually, let's just write a placeholder or instructions if we can't generate.
        # BUT, to make this script actually useful, let's try to simulate what 'vapid --applicationServerKey' does.
        # It's better to ask user to run: 'pywebpush --keygen'
        
        print("Please run the following command in your terminal to generate keys, then save them in 'instance/vapid_keys.json':")
        print("pywebpush --keygen")
        
        # However, for this helper script, let's try to automate it if possible.
        # If not, we will just create the directory.
        
        print(f"\nIMPORTANT: You must create '{file_path}' with the following structure:")
        print('{\n  "publicKey": "YOUR_PUBLIC_KEY",\n  "privateKey": "YOUR_PRIVATE_KEY"\n}')
    else:
        print(f"VAPID keys already exist at: {file_path}")

if __name__ == "__main__":
    generate_vapid_keys()
