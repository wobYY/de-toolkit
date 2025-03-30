"""This script creates a .env.sample file in the current directory from the .env file."""

import os

env_file = os.path.join(os.getcwd(), ".env")
sample_file = os.path.join(os.getcwd(), ".env.sample")

# Check if .env file exists
if not os.path.exists(env_file):
    raise FileNotFoundError(f"File {env_file} not found. Create the .env file first.")

# Get all the lines from the .env file
with open(env_file, "r") as f:
    lines = f.readlines()


# Write the lines to the .env.sample file
with open(sample_file, "w") as f:
    for line in lines:
        if not line.startswith("#"):
            # Replace everything past the = with "ENTER_YOUR_VALUE_HERE"
            line = line.split("=", 1)[0].strip() + " = ENTER_YOUR_VALUE_HERE\n"

        f.write(line)
