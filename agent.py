import datetime
from zoneinfo import ZoneInfo
from google.adk.agents import Agent
import subprocess
import re  # Import the regular expression module
import shlex # Using shlex is generally safer for command construction

def create_gcp_vm(
    project_id: str,
    zone: str,
    vm_name: str,
    # --- Parameters with defaults start here ---
    network: str = "test", # Default network name (use a valid one!)
    subnetwork: str = "test1", # Default subnetwork name (use a valid one or None!)
    machine_type: str = "n1-standard-1",
    image_family: str = "debian-11",
    image_project: str = "debian-cloud"
) -> dict:
    """Creates a new Google Compute Engine VM instance.

    Args:
        project_id (str): The Google Cloud Project ID.
        zone (str): The Google Cloud zone where the VM should be created.
        vm_name (str): The name of the new VM instance.
        network (str, optional): The name of the network to attach the VM to.
                                 Defaults to "test". Ignored if subnetwork is specified.
        subnetwork (str | None, optional): The name of the subnetwork to attach the VM to.
                                          Defaults to "test1". If specified, this is used
                                          instead of the network parameter.
        machine_type (str, optional): The machine type of the VM. Defaults to "n1-standard-1".
        image_family (str, optional): The OS image family. Defaults to "debian-11".
        image_project (str, optional): The project the image belongs to. Defaults to "debian-cloud".


    Returns:
        dict: status and result or error message.

    Notes:
        - It's recommended to specify the subnetwork directly for clarity, especially
          in networks with custom subnets.
        - Ensure the default values for 'network' and 'subnetwork' exist in your
          GCP project and specified zone, or override them when calling the function.
    """
    try:
        # Base command parts
        command_parts = [
            "gcloud", "compute", "instances", "create", vm_name,
            f"--project={project_id}",
            f"--zone={zone}",
            f"--machine-type={machine_type}",
            f"--image-family={image_family}",
            f"--image-project={image_project}",
            "--quiet"  # Suppress interactive prompts
        ]

        # Add network/subnetwork configuration
        network_info = ""
        if subnetwork:
            command_parts.append(f"--subnet={subnetwork}")
            network_info = f"subnet '{subnetwork}'"
        elif network:
             # Only add --network if --subnet is not specified
            command_parts.append(f"--network={network}")
            network_info = f"network '{network}'"
        else:
            # Should not happen if network has a default, but included for safety
             return {
                "status": "error",
                "error_message": "Network or Subnetwork must be specified."
             }

        # Using subprocess.run
        process = subprocess.run(
            command_parts,
            capture_output=True,
            text=True,
            check=False,
            timeout=180
        )

        if process.returncode == 0:
            success_message = f"Successfully created VM '{vm_name}' in zone '{zone}'"
            if network_info:
                success_message += f" on {network_info}."
            else:
                success_message += "." # Should include network info based on logic above

            return {
                "status": "success",
                "result": success_message,
                "stdout": process.stdout.strip()
            }
        else:
            error_message = process.stderr.strip()
            return {
                "status": "error",
                "error_message": f"Failed to create VM '{vm_name}': {error_message}",
                "stderr": error_message
             }
    except subprocess.TimeoutExpired:
        return {
            "status": "error",
            "error_message": f"Timeout occurred while trying to create VM '{vm_name}'."
        }
    except FileNotFoundError:
         return {
            "status": "error",
            "error_message": "Error: 'gcloud' command not found. Make sure Google Cloud SDK is installed and in your PATH."
        }
    except Exception as e:
        return {
            "status": "error",
            "error_message": f"An unexpected error occurred: {e}"
        }

def start_gcp_vm(project_id: str, vm_name: str, zone: str) -> dict:
    """Starts a Google Cloud Compute Engine VM instance.

    Args:
        project_id (str): The Google Cloud Project ID.
        vm_name (str): The name of the VM instance.
        zone (str): The Google Cloud zone where the VM is located.

    Returns:
        dict: status and result or error message.
    """
    try:
        command = f"gcloud compute instances start {vm_name} --project={project_id} --zone={zone}"
        process = subprocess.Popen(command, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        stdout, stderr = process.communicate(timeout=60)
        if process.returncode == 0:
            return {"status": "success", "result": f"Successfully started VM '{vm_name}' in zone '{zone}'."}
        else:
            error_message = stderr.decode('utf-8').strip()
            return {"status": "error", "error_message": f"Failed to start VM '{vm_name}': {error_message}"}
    except Exception as e:
        return {"status": "error", "error_message": f"An error occurred: {e}"}


def stop_gcp_vm(project_id: str, vm_name: str, zone: str) -> dict:
    """Stops a Google Cloud Compute Engine VM instance.

    Args:
        project_id (str): The Google Cloud Project ID.
        vm_name (str): The name of the VM instance.
        zone (str): The Google Cloud zone where the VM is located.

    Returns:
        dict: status and result or error message.
    """
    try:
        command = f"gcloud compute instances stop {vm_name} --project={project_id} --zone={zone} --quiet"  # Added --quiet
        process = subprocess.Popen(command, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        stdout, stderr = process.communicate(timeout=60)
        if process.returncode == 0:
            return {"status": "success", "result": f"Successfully stopped VM '{vm_name}' in zone '{zone}'."}
        else:
            error_message = stderr.decode('utf-8').strip()
            return {"status": "error", "error_message": f"Failed to stop VM '{vm_name}': {error_message}"}
    except Exception as e:
        return {"status": "error", "error_message": f"An error occurred: {e}"}


def delete_gcp_vm(project_id: str, vm_name: str, zone: str) -> dict:
    """Deletes a Google Cloud Compute Engine VM instance.

    Args:
        project_id (str): The Google Cloud Project ID.
        vm_name (str): The name of the VM instance.
        zone (str): The Google Cloud zone where the VM is located.

    Returns:
        dict: status and result or error message.
    """
    try:
        command = f"gcloud compute instances delete {vm_name} --project={project_id} --zone={zone} --quiet"  # Added --quiet
        process = subprocess.Popen(command, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        stdout, stderr = process.communicate(timeout=60)
        if process.returncode == 0:
            return {"status": "success", "result": f"Successfully deleted VM '{vm_name}' in zone '{zone}'."}
        else:
            error_message = stderr.decode('utf-8').strip()
            return {"status": "error", "error_message": f"Failed to delete VM '{vm_name}': {error_message}"}
    except Exception as e:
        return {"status": "error", "error_message": f"An error occurred: {e}"}



root_agent = Agent(
    name="gcp_vm_manager",
    model="gemini-2.0-flash",
    description="An agent that can manage Google Cloud Compute Engine virtual machines.",
    instruction=(
        "You can use your tools to manage Google Cloud virtual machines. You can create, start, stop, and delete VMs. "
        "To do this, you will need the Project ID,  the name of the VM, and its zone.  For creating a VM, you might also need the machine type and image information. "
        "Ask the user for any missing information."
    ),
    tools=[create_gcp_vm, start_gcp_vm, stop_gcp_vm, delete_gcp_vm],
)

