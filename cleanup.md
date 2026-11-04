# NVIDIA Driver Cleanup

Use this recipe before switching between Ubuntu and NVIDIA driver sources or
repairing leftover driver packages on Ubuntu 22.04, 24.04 or 26.04 x86_64.
Stop GPU workloads first.

It purges driver packages, libraries, kernel modules, branch pins and their
package configuration. CUDA Toolkit, Container Toolkit, repository keyrings and
source lists are preserved. Installations made with NVIDIA's `.run` installer
require its own uninstaller.

For Ansible, run from the repository root. Replace `gpu1.example.com` with the
inventory host to clean:

```bash
ansible-playbook cleanup.yml --limit gpu1.example.com --check --diff
ansible-playbook cleanup.yml --limit gpu1.example.com --diff
```

The playbook uses only [`nvidia_driver_cleanup`](roles/nvidia_driver_cleanup/).
It rejects unrelated APT changes and does not run `autoremove`.
The normal `site.yml` playbook does not include cleanup.

## 1. NVIDIA Driver Cleanup (Optional)

### 1.1 Discover driver packages

```bash
# Include installed packages and leftover package configuration
export NVIDIA_DRIVER_PACKAGES="$(
  dpkg-query -W -f='${binary:Package} ${db:Status-Status}\n' -- \
    'cuda-drivers*' 'cuda-compat*' \
    'nvidia-open*' 'nvidia-driver*' 'nvidia-dkms*' 'nvidia-kernel*' \
    'nvidia-headless*' 'nvidia-utils*' 'nvidia-compute-utils*' 'nvidia-firmware*' \
    'nvidia-modprobe' 'nvidia-persistenced' 'nvidia-settings' 'nvidia-xconfig' \
    'nvidia-prime*' 'nvidia-powerd' \
    'nvidia-fabricmanager*' 'nvidia-imex*' 'libnvidia-*' 'libxnvctrl*' 'libnvsdm*' \
    'xserver-xorg-video-nvidia*' 'linux-modules-nvidia*' \
    'linux-objects-nvidia*' 'linux-signatures-nvidia*' 2>/dev/null |
    awk '$2 ~ /^(installed|config-files|unpacked|half-configured|half-installed|triggers-awaited|triggers-pending)$/ &&
         $1 !~ /^libnvidia-container/ {print $1}'
)"
printf '%s\n' "$NVIDIA_DRIVER_PACKAGES"
```

If the list is empty, cleanup is unnecessary; skip the remaining steps.

### 1.2 Preview and purge the selected packages

Review APT's proposal. Only the selected driver packages should be removed.
Stop if APT proposes other removals, new packages or kernel changes.

<!-- ops-step
id: nvidia.cleanup.packages.remove
ansible_task: nvidia.cleanup.packages.remove | Purge driver packages and their configuration
kind: package
-->

```bash
# Preview the transaction, then review APT's confirmation before purging
apt-get --simulate purge $NVIDIA_DRIVER_PACKAGES &&
  sudo apt-get purge $NVIDIA_DRIVER_PACKAGES
```

### 1.3 Verify package cleanup

No selected package should remain installed or have leftover configuration.
Missing-package messages are expected; `dpkg --audit` should produce no output.

<!-- ops-step
id: nvidia.cleanup.absent.require
ansible_task: nvidia.cleanup.absent.require | Require driver packages and configuration to be absent
kind: verify
-->

<!-- ops-step
id: nvidia.cleanup.packages.audit
ansible_task: nvidia.cleanup.packages.audit | Require consistent package state
kind: verify
-->

```bash
# Verify package removal and package-manager state
dpkg-query -W -f='${binary:Package} ${db:Status-Status}\n' $NVIDIA_DRIVER_PACKAGES
sudo dpkg --audit
```

Continue with [`nvidia.md`](nvidia.md) to install the selected driver and reboot.
Package removal does not unload a running kernel module.

Reference: [NVIDIA driver removal](https://docs.nvidia.com/datacenter/tesla/driver-installation-guide/removing-the-driver.html).
