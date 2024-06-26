#############################################################################
# 
# Component contains an implementation of SONiC Platform Base API and
# provides the components firmware management function
#
#############################################################################

try:
    import subprocess
    from sonic_platform_base.component_base import ComponentBase
except ImportError as e:
    raise ImportError(str(e) + "- required module not found")

CPLD_SYSFS = {
    "CPLD1": "/sys/kernel/pddf/devices/sysstatus/sysstatus_data/cpld1_version",
    "CPLD2": "/sys/kernel/pddf/devices/sysstatus/sysstatus_data/cpld2_version",
    "CPLD3": "/sys/kernel/pddf/devices/sysstatus/sysstatus_data/cpld3_version",
}

BMC_CMDS = {
    "BMC": "bash -c 'tmp=$(ipmitool raw 0x6 0x1) && r=($(echo \"$tmp\" | cut -d \" \" -f 4,5,16,15,14)) && echo ${r[0]}.${r[1]}.${r[4]}.${r[3]}${r[2]}'",
}

BIOS_VERSION_PATH = "/sys/class/dmi/id/bios_version"
COMPONENT_LIST= [
   ("CPLD1", "CPLD 1"),
   ("CPLD2", "CPLD 2"),
   ("CPLD3", "CPLD 3"),
   ("BIOS", "Basic Input/Output System"),
   ("BMC", "BMC"),
   
]

class Component(ComponentBase):
    """Platform-specific Component class"""

    DEVICE_TYPE = "component"

    def __init__(self, component_index=0):
        self.index = component_index
        self.name = self.get_name()

    def _run_command(self, command):
        # Run bash command and print output to stdout
        try:
            process = subprocess.Popen(
                shlex.split(command), stdout=subprocess.PIPE)
            while True:
                output = process.stdout.readline()
                if output == '' and process.poll() is not None:
                    break
            rc = process.poll()
            if rc != 0:
                return False
        except Exception:
            return False
        return True

    def _get_bios_version(self):
        # Retrieves the BIOS firmware version
        try:
            with open(BIOS_VERSION_PATH, 'r') as fd:
                bios_version = fd.read()
                return bios_version.strip()
        except Exception as e:
            return None
   
    def _get_cpld_version(self):
        # Retrieves the CPLD firmware version
        cpld_version = dict()
        for cpld_name in CPLD_SYSFS:            
            cmd = "cat {}".format(CPLD_SYSFS[cpld_name])
            status, value = subprocess.getstatusoutput(cmd)
            if not status:
                cpld_version_raw = value.rstrip()
                cpld_version_int = int(cpld_version_raw,16)
                cpld_version[cpld_name] = "{}.{:02d}".format(cpld_version_int >> 6,
                                                             cpld_version_int & 0b00111111)

        return cpld_version

    def _get_bmc_version(self):
        # Retrieves the BMC firmware version
        status, value = subprocess.getstatusoutput(BMC_CMDS["BMC"])
        if not status:
            return value
        else:
            return None

    def get_name(self):
        """
        Retrieves the name of the component
         Returns:
            A string containing the name of the component
        """
        return COMPONENT_LIST[self.index][0]

    def get_description(self):
        """
        Retrieves the description of the component
            Returns:
            A string containing the description of the component
        """
        return COMPONENT_LIST[self.index][1]

    def get_firmware_version(self):
        """
        Retrieves the firmware version of module
        Returns:
            string: The firmware versions of the module
        """
        fw_version = None

        if self.name == "BIOS":
            fw_version = self._get_bios_version()
        elif "CPLD" in self.name:
            cpld_version = self._get_cpld_version()
            fw_version = cpld_version.get(self.name)
        elif self.name == "BMC":
            fw_version = self._get_bmc_version()
        return fw_version

    def install_firmware(self, image_path):
        """
        Install firmware to module
        Args:
            image_path: A string, path to firmware image
        Returns:
            A boolean, True if install successfully, False if not
        """
        raise NotImplementedError
