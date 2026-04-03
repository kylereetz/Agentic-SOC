# Proxmox VE Hardware Setup & Networking for OT Lab

Since you are using Proxmox VE to build the lab, you have full flexibility to create isolated environments and simulate as many endpoints as you want. 

## Phase 1: Installing Proxmox VE from ISO

If you are starting with bare-metal hardware (like an old Windows machine or a dedicated server), you need to install the Proxmox hypervisor first before you can configure the virtual networks.

### Step 1: Create a Bootable USB
1. Download the latest **Proxmox VE Installer ISO** from the [official Proxmox downloads page](https://www.proxmox.com/en/downloads/proxmox-virtual-environment/iso).
2. Download a flashing tool like **Rufus** (Windows) or **BalenaEtcher**.
3. Insert a USB flash drive (at least 8GB).
4. Open Rufus/BalenaEtcher, select the Proxmox ISO, select your USB drive, and click **Flash**. (Note: This will erase everything on the USB drive).

### Step 2: Boot & Install on the Host
1. Plug the bootable USB into your dedicated lab hardware.
2. Power on the machine and press the boot menu key (usually F12, F11, F8, or DEL) to boot from the USB.
3. Select **"Install Proxmox VE"** from the Proxmox boot menu.
4. Accept the EULA and select the target hard drive (Warning: This wipes the drive!).
5. Enter your Country, Timezone, and Keyboard Layout.
6. Set a **Root Password**. Make sure you remember this! Also enter an admin email address.
7. **Network Configuration**: Proxmox will try to pull a DHCP address. It is highly recommended to assign a **Static IP** here (e.g., `192.168.1.100`), set your home router as the Gateway, and set a DNS server (like `1.1.1.1` or `8.8.8.8`). This is how you will access the Web GUI.
8. Click **Install**. The machine will reboot when finished.

### Step 3: Access the Web GUI
Once the host reboots, it will display a URL on the physical screen. Go to your regular laptop, open a browser, and navigate to:
`https://<YOUR_PROXMOX_STATIC_IP>:8006`
*(Note: Your browser will warn you about an invalid certificate. Proceed anyway.)*
Log in with the username `root` and the password you set during installation.

---

## Phase 2: Configuring the Lab Network (SPAN & VLAN)

Proxmox relies on Virtual Bridges (like virtual switches) to connect VMs. To provide your Dedicated Ubuntu Sensor VM with visibility into all the factory traffic, we need to create a **SPAN/Mirror Port**.

## Method: Open vSwitch (OVS) Mirroring

Proxmox natively supports Linux Bridges, but Open vSwitch (OVS) makes port mirroring significantly easier and more reliable.

### Step 1: Install Open vSwitch on Proxmox
SSH into your Proxmox host (or use the web Shell) and run:
```bash
apt update && apt install openvswitch-switch -y
```

### Step 2: Create the OVS Bridge (OT_VLAN Switch)
1. Go to the Proxmox Web GUI -> **Node (your node name)** -> **Network**.
2. Click **Create** -> **OVS Bridge**.
3. Name it `vmbr1` (or whatever number is available).
4. Leave IPv4/IPv6 empty (this is purely layer 2 isolation for your lab).
5. Click **Create** and then **Apply Configuration**.

### Step 3: Attach VMs to the Switch
For every VM in the lab (pfSense LAN interface, pfSense SPAN interface, Windows Factory I/O, OpenPLC, Kali, and Ubuntu Sensor):
1. VM Hardware -> **Network Device** -> Select `vmbr1` as the bridge.
2. Ensure you check "Disconnect" for any VM you suspend so it doesn't flood traffic unnecessarily.

### Step 4: Configure the SPAN (Mirror) Port
We need to copy all traffic flowing through `vmbr1` to a specific interface assigned to your **Ubuntu Sensor VM**. 

1. **Find the Ubuntu Sensor VM's Interface name:**
   Start the Ubuntu Sensor VM. In the Proxmox shell, run `ip link show`. Look for the interface that corresponds to the Ubuntu Sensor VM (e.g., `tap105i0`, where 105 is the VM ID).

2. **Run the OVS Mirror Commands on Proxmox Shell:**
   *(Replace `tap105i0` with the actual tap interface of your Ubuntu Sensor VM)*
   ```bash
   # Create a mirror named 'span1'
   ovs-vsctl -- set Bridge vmbr1 mirrors=@m \
    -- --id=@m create Mirror name=span1 select-all=true output-port=@tap105i0 \
    -- --id=@tap105i0 get Port tap105i0
   ```

Now, every single Modbus packet sent from the Windows VM to the OpenPLC VM across `vmbr1` will be duplicated and sent to the Ubuntu Sensor VM. Zeek and Suricata will see *everything*.

> [!TIP]
> To disable the mirror later when you are done testing, run:
> `ovs-vsctl clear Bridge vmbr1 mirrors`
