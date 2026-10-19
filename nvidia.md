# NVIDIA Driver, CUDA Toolkit, and Container Toolkit

- **NVIDIA Driver** lets Linux and applications access the NVIDIA GPU.
- **CUDA Toolkit** provides the compiler and libraries for building CUDA applications.
- **NVIDIA Container Toolkit** lets Docker containers use the host's NVIDIA GPUs.

This is the human-readable pair for `site.yml`. It is written as an
executable Markdown recipe: read it top to bottom, set variables, then run the
shell blocks on the target Ubuntu host.

Run Ansible from the repository root for repeatable deployment. `ansible.cfg`
selects the local `hosts` inventory:

```bash
ansible-playbook site.yml --diff
```

Use this file for manual installation, review, repair, or learning.

The example variables target Ubuntu 24.04 x86_64, NVIDIA driver **615.x**, and
CUDA Toolkit **13.4.x**. Driver branch selection uses NVIDIA's
`nvidia-driver-pinning-615` package; `nvidia-open` is the driver metapackage.
`cuda-toolkit-13-4` includes `nvcc` and stays on CUDA 13.4. Patch updates within
both branches remain available through APT and when rerunning Ansible.

Use the versioned CUDA package below, not the rolling `cuda-toolkit` metapackage.
If an existing driver package is held with `apt-mark hold`, remove that specific
hold before changing its branch. Do not combine the recipe with another driver
branch pin.

References: [NVIDIA driver branch selection](https://docs.nvidia.com/datacenter/tesla/driver-installation-guide/ubuntu.html#selecting-a-branch-or-a-specific-driver-version)
and [CUDA package upgrades](https://docs.nvidia.com/cuda/cuda-installation-guide-linux/#package-upgrades).

Select the Ubuntu release with `NVIDIA_UBUNTU_VERSION` below, or
`nvidia_driver_ubuntu_version` in Ansible. Use `2204`, `2404` (default), or `2604`.

| Ubuntu version | OS value | NVIDIA repository (x86_64) |
|---|---|---|
| 22.04 | `2204` | [`ubuntu2204`](https://developer.download.nvidia.com/compute/cuda/repos/ubuntu2204/x86_64/) |
| 24.04 | `2404` | [`ubuntu2404`](https://developer.download.nvidia.com/compute/cuda/repos/ubuntu2404/x86_64/) |
| 26.04 | `2604` | [`ubuntu2604`](https://developer.download.nvidia.com/compute/cuda/repos/ubuntu2604/x86_64/) |

Repository metadata, keyrings, driver 615 packages, and CUDA 13.4 packages were
checked on 2026-10-19. Availability does not confirm installation on each OS.

## 1. NVIDIA Driver

Ansible role: [`nvidia_driver`](roles/nvidia_driver/).

### 1.1 Configure driver settings

```bash
# Configure role settings
export NVIDIA_UBUNTU_VERSION="2404"
export NVIDIA_DRIVER_PACKAGE="nvidia-open"
export NVIDIA_DRIVER_BRANCH="615"
export NVIDIA_DRIVER_KEYRING_URL="https://developer.download.nvidia.com/compute/cuda/repos/ubuntu${NVIDIA_UBUNTU_VERSION}/x86_64/cuda-keyring_1.1-1_all.deb"
```

### 1.2 Install prerequisites and the NVIDIA repository

<!-- ops-step
id: nvidia.driver.prerequisites
ansible_task: nvidia.driver.prerequisites | Install NVIDIA driver prerequisites
kind: package
-->

<!-- ops-step
id: nvidia.driver.keyring
ansible_task: nvidia.driver.keyring | Install NVIDIA driver repository keyring package
kind: package
-->

```bash
# Install Driver Prerequisites
sudo apt-get update
sudo apt-get install -y ca-certificates curl linux-headers-generic build-essential dkms ubuntu-drivers-common

# Install NVIDIA Driver Repository Keyring
curl -fsSLO "$NVIDIA_DRIVER_KEYRING_URL" &&
  sudo apt-get install -y ./cuda-keyring_1.1-1_all.deb &&
  rm -f cuda-keyring_1.1-1_all.deb
```

### 1.3 Pin the driver branch and install the driver

Install the pin before the driver so APT selects only the configured branch.

<!-- ops-step
id: nvidia.driver.branch_pin
ansible_task: nvidia.driver.branch_pin | Pin NVIDIA driver branch
kind: package
-->

<!-- ops-step
id: nvidia.driver.install
ansible_task: nvidia.driver.install | Install NVIDIA driver package
kind: package
-->

```bash
# Pin NVIDIA Driver Branch
sudo apt-get update
sudo apt-get install -y "nvidia-driver-pinning-$NVIDIA_DRIVER_BRANCH"

# Install NVIDIA Driver
sudo apt-get install -y "$NVIDIA_DRIVER_PACKAGE"
```

### 1.4 Reboot manually and verify the driver

After installing or updating the driver, reboot the host manually and reconnect
before running this check.

<!-- ops-step
id: nvidia.driver.reboot_notice
ansible_task: nvidia.driver.reboot_notice | Report required driver reboot
kind: report
-->

<!-- ops-step
id: nvidia.driver.verify_smi
ansible_task: nvidia.driver.verify_smi | Verify NVIDIA SMI visibility
kind: verify
-->

```bash
# Verify the loaded driver after the manual reboot
nvidia-smi
```

Ansible reports the reboot requirement and defers this check when the driver
package changes. Rerun the playbook after reboot to verify the loaded driver.
A successful package installation alone does not verify the running kernel module.

## 2. CUDA Toolkit

Ansible role: [`cuda_toolkit`](roles/cuda_toolkit/).

### 2.1 Configure CUDA settings

```bash
# Configure role settings
export CUDA_TOOLKIT_HOME="/usr/local/cuda-13.4"
export CUDA_TOOLKIT_KEYRING_URL="$NVIDIA_DRIVER_KEYRING_URL"
export CUDA_TOOLKIT_PACKAGES="cuda-toolkit-13-4"
export CUDA_TOOLKIT_PROFILE="/etc/profile.d/cuda.sh"
```

### 2.2 Install the repository and CUDA toolkit

Both driver and CUDA use the same NVIDIA repository. This step is idempotent and
also allows the CUDA role to run independently of the driver role.

<!-- ops-step
id: nvidia.cuda.keyring
ansible_task: nvidia.cuda.keyring | Install CUDA repository keyring package
kind: package
-->

<!-- ops-step
id: nvidia.cuda.toolkit
ansible_task: nvidia.cuda.toolkit | Install CUDA toolkit packages
kind: package
-->

```bash
# Install CUDA Repository Keyring
curl -fsSLO "$CUDA_TOOLKIT_KEYRING_URL" &&
  sudo apt-get install -y ./cuda-keyring_1.1-1_all.deb &&
  rm -f cuda-keyring_1.1-1_all.deb

# Install CUDA Toolkit
sudo apt-get update
sudo apt-get install -y $CUDA_TOOLKIT_PACKAGES
```

### 2.3 Configure the environment and verify the compiler

<!-- ops-step
id: nvidia.cuda.environment
ansible_task: nvidia.cuda.environment | Configure CUDA shell environment
kind: file
-->

<!-- ops-step
id: nvidia.cuda.nvcc_link
ansible_task: nvidia.cuda.nvcc_link | Expose nvcc in non-login PATH
kind: file
-->

<!-- ops-step
id: nvidia.cuda.verify_nvcc
ansible_task: nvidia.cuda.verify_nvcc | Verify CUDA compiler visibility
kind: verify
-->

```bash
# Configure CUDA Shell Environment
printf 'export PATH=%s/bin:$PATH\nexport LD_LIBRARY_PATH=%s/lib64:$LD_LIBRARY_PATH\n' \
  "$CUDA_TOOLKIT_HOME" "$CUDA_TOOLKIT_HOME" | sudo tee "$CUDA_TOOLKIT_PROFILE"

# Expose nvcc in Non-login PATH
sudo ln -sf "$CUDA_TOOLKIT_HOME/bin/nvcc" /usr/local/bin/nvcc

# Verify CUDA Compiler
nvcc --version
```

## 3. NVIDIA Container Toolkit (Optional)

Ansible role: [`nvidia_container_toolkit`](roles/nvidia_container_toolkit/).

Run this section only for Docker GPU workloads. For a native vLLM service,
stop after section 2. The full `site.yml` playbook includes this role by default.

### 3.1 Configure Container Toolkit settings

```bash
# Configure role settings
export NVIDIA_CONTAINER_TOOLKIT_KEYRING="/usr/share/keyrings/nvidia-container-toolkit-keyring.gpg"
export NVIDIA_CONTAINER_TOOLKIT_SOURCE="/etc/apt/sources.list.d/nvidia-container-toolkit.list"
```

### 3.2 Install the repository and Container Toolkit

<!-- ops-step
id: nvidia.container.apt_dependencies
ansible_task: nvidia.container.apt_dependencies | Install NVIDIA container toolkit apt dependencies
kind: package
-->

<!-- ops-step
id: nvidia.container.apt_key
ansible_task: nvidia.container.apt_key | Install NVIDIA container toolkit apt key
kind: file
-->

<!-- ops-step
id: nvidia.container.apt_repository
ansible_task: nvidia.container.apt_repository | Configure NVIDIA container toolkit apt repository
kind: file
-->

<!-- ops-step
id: nvidia.container.toolkit
ansible_task: nvidia.container.toolkit | Install NVIDIA container toolkit
kind: package
-->

```bash
# Install Container Toolkit Apt Dependencies
sudo apt-get update
sudo apt-get install -y ca-certificates curl gnupg2

# Install Container Toolkit Apt Key
if [ ! -e "$NVIDIA_CONTAINER_TOOLKIT_KEYRING" ]; then
  curl -fsSL https://nvidia.github.io/libnvidia-container/gpgkey \
    | sudo gpg --dearmor -o "$NVIDIA_CONTAINER_TOOLKIT_KEYRING"
fi

# Configure Container Toolkit Apt Repository
if [ ! -e "$NVIDIA_CONTAINER_TOOLKIT_SOURCE" ]; then
  curl -s -L https://nvidia.github.io/libnvidia-container/stable/deb/nvidia-container-toolkit.list \
    | sed "s#deb https://#deb [signed-by=$NVIDIA_CONTAINER_TOOLKIT_KEYRING] https://#g" \
    | sudo tee "$NVIDIA_CONTAINER_TOOLKIT_SOURCE" >/dev/null
fi

# Install Container Toolkit
sudo apt-get update
sudo apt-get install -y nvidia-container-toolkit
```

### 3.3 Configure the NVIDIA runtime and restart Docker

Docker must be installed and running. Add `--set-as-default` to the configure
command if NVIDIA should be Docker's default runtime.

<!-- ops-step
id: nvidia.docker.runtime_configure
ansible_task: nvidia.docker.runtime_configure | Configure Docker NVIDIA runtime
kind: command
-->

<!-- ops-step
id: nvidia.docker.runtime_apply
ansible_task: nvidia.docker.runtime_apply | Apply Docker runtime configuration
kind: handler
-->

```bash
# Configure Docker's NVIDIA runtime
sudo nvidia-ctk runtime configure --runtime=docker

# Apply the runtime configuration
sudo systemctl restart docker
```

### 3.4 Verify the NVIDIA Docker runtime

The runtime list must include `nvidia`.

<!-- ops-step
id: nvidia.docker.runtime_read_after
ansible_task: nvidia.docker.runtime_read_after | Read Docker runtime state after configuration
kind: check
-->

<!-- ops-step
id: nvidia.docker.runtime_require
ansible_task: nvidia.docker.runtime_require | Require NVIDIA Docker runtime
kind: verify
-->

```bash
docker info --format 'default={{.DefaultRuntime}} runtimes={{json .Runtimes}}'
```
