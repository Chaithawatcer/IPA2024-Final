import subprocess

def showrun():
    # read https://www.datacamp.com/tutorial/python-subprocess to learn more about subprocess
    command = ['ansible-playbook', 'playbook.yaml', '-i', 'hosts']
    result = subprocess.run(command, capture_output=True, text=True)
    result = result.stdout
    print(result)
    if 'ok=3' in result:
        return {"status": "OK", "msg":"ok"}
    else:
        return {"status": "FAIL", "msg":"Error: Ansible"}
    
if __name__ == "__main__":
    showrun()