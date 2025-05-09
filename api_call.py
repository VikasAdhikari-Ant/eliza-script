from flask import Flask, request, jsonify
import yaml
import subprocess
import uuid
import os
CHARACTER_DIR = "./characters"
app = Flask(__name__)
os.makedirs(CHARACTER_DIR, exist_ok=True)


COMPOSE_FILE_PATH = "/home/user/Desktop/eliza-starter/docker-compose.yaml"

def update_compose_env_vars(data, character_filename):
    username = data.get("TWITTER_USER")
    password = data.get("TWITTER_PASSWORD")
    email = data.get("TWITTER_EMAIL")

    if not all([username, password, email]):
        return False, "Missing one or more required parameters"
    
    # Load and update docker-compose
    with open(COMPOSE_FILE_PATH, 'r') as f:
        compose_data = yaml.safe_load(f)

    # Update --character argument
    command_list = compose_data['services']['eliza']['command']
    for i, item in enumerate(command_list):
        if item.startswith('--character='):
            command_list[i] = f"--character=./characters/{character_filename}"
            break
    else:
        command_list.append(f"--character=./characters/{character_filename}")

    env_list = compose_data['services']['eliza']['environment']
    
    # Function to update or insert environment variables
    def set_env_var(env_list, key, value):
        prefix = f"{key}="
        for i, item in enumerate(env_list):
            if item.startswith(prefix):
                env_list[i] = f"{key}={value}"
                return
        env_list.append(f"{key}={value}")

    set_env_var(env_list, "TWITTER_USERNAME", username)
    set_env_var(env_list, "TWITTER_PASSWORD", password)
    set_env_var(env_list, "TWITTER_EMAIL", email)

    with open(COMPOSE_FILE_PATH, 'w') as f:
        yaml.dump(compose_data, f, sort_keys=False)

    return True, "docker-compose.yml updated successfully"


# data = {
#     "TWITTER_USER":"chillguy0980",
#     "TWITTER_PASSWORD":"Vikas@ant30",
#     "TWITTER_EMAIL":"vikas.adhikari@antiersolutions.com"
# }

# update_compose_env_vars(data)

@app.route('/update-compose', methods=['POST'])
def update_compose():
    # Check if a file was uploaded
    
    file = request.files.get('file')


    if not file:
        return jsonify({"success": False, "message": "No file part"}), 400

    # Generate a unique filename
    character_id = str(uuid.uuid4())
    character_filename = f"{character_id}.character.json"
    character_path = os.path.join(CHARACTER_DIR, character_filename)

    # Save the uploaded file
    file.save(character_path)

    try:
        data = request.form
        success, message = update_compose_env_vars(data, character_filename)
            # Run docker-compose up (detached mode)
        subprocess.run(["docker","compose", "up"], check=True)
        
        return jsonify({"success": True, "message": "Updated and started Docker Compose."})

    except Exception as e:
        return jsonify({"success": False, "message": f"Error: {str(e)}"}), 500
    except subprocess.CalledProcessError as e:
        return jsonify({"success": False, "message": str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True)