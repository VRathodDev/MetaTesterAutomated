import platform
import winreg
import zipfile
from abc import ABC, abstractmethod
from GenUtility import isNoneOrEmpty, createDir, runExecutable
from shutil import unpack_archive, copy, copytree
import os
import sys


class Package(ABC):
    @abstractmethod
    def __init__(self, inSourcePath: str, inDestinationPath: str, inForceUpdate: bool = False):
        if (not isNoneOrEmpty(inSourcePath, inDestinationPath)) and inForceUpdate is not None:
            self.__mSourcePath = inSourcePath
            self.__mDestinationPath = inDestinationPath
            self.__mForceUpdate = inForceUpdate
            self.__mFileName = inSourcePath.split(os.sep)[-1]
        else:
            print('Error: Invalid Parameters')
            sys.exit(1)

    def getSourcePath(self):
        return self.__mSourcePath

    def getDestinationPath(self):
        return os.path.abspath(self.__mDestinationPath)

    def getFileName(self):
        return self.__mFileName

    def getPackageName(self):
        return self.__mFileName.split('_')[0]

    def getPackageBitCount(self):
        return int(self.__mFileName[-6:-4])

    def shouldForceUpdate(self):
        return self.__mForceUpdate

    def download(self):
        source = self.getSourcePath()
        if os.path.exists(source):
            destination = self.getDestinationPath()
            forceUpdate = self.shouldForceUpdate()
            filePath = os.path.join(destination, self.getFileName())
            try:
                if not os.path.exists(destination):
                    createDir(destination)
                if not os.path.exists(filePath) or forceUpdate:
                    copy(source, destination)
                    if zipfile.is_zipfile(filePath):
                        unpack_archive(filePath, destination)
                    else:
                        print('Error: Expected File Type mismatched. `Zip` required')
                        return False
                return True
            except Exception as error:
                print(f"Error: {error}")
                return False
        else:
            print(f"Error: Given Path {source} is Invalid!")
            return False


class Core(Package):
    def __init__(self, inSourcePath: str, inDestinationPath: str, inBranch: str, inForceUpdate: bool = False):
        super().__init__(inSourcePath, inDestinationPath, inForceUpdate)
        if not isNoneOrEmpty(inBranch):
            self.__mBranch = inBranch
        else:
            print('Error: Invalid Parameters')
            sys.exit(1)

    def getBranch(self):
        return self.__mBranch


class Plugin(Package):
    def __init__(self, inSourcePath: str, inDestinationPath: str, inBrand: str,
                 inDataSourceConfiguration: dict, inWaitForUserToSetupDSN: bool = False, inForceUpdate: bool = False):
        super().__init__(inSourcePath, inDestinationPath, inForceUpdate)
        if not isNoneOrEmpty(inBrand, inDataSourceConfiguration):
            self.__mBrand = inBrand
            self.__mWaitForUserToSetupDSN = inWaitForUserToSetupDSN
            self.__mDataSourceConfiguration = inDataSourceConfiguration
        else:
            print('Error: Invalid Parameters')
            sys.exit(1)

    def getPluginBrand(self):
        return self.__mBrand

    def getDataSourceName(self):
        return f"{self.__mBrand} {self.getPackageName()}"

    def shouldWaitForUserToSetupDSN(self):
        return self.__mWaitForUserToSetupDSN

    def getDataSourceConfiguration(self):
        return self.__mDataSourceConfiguration

    def getLogsPath(self):
        """Returns the path to `DriverLogs` folder to save the logs generated during various tests"""
        logsPath = os.path.join(self.getDestinationPath(), 'DriverLogs')
        if os.path.exists(self.getDestinationPath()):
            if not os.path.exists(logsPath):
                os.mkdir(logsPath)
            return logsPath
        else:
            print('Error: Plugin is either not downloaded or set-up.')
            return None

    def __setRegistryConfigurations(self, inDriverDLLPath: str):
        """
        Writes Driver's registry configurations \n
        :param inDriverDLLPath: Driver's DLL Path from Plugin Package
        :return: True if succeeded else False
        """
        if not isNoneOrEmpty(inDriverDLLPath):
            driverBit = self.getPackageBitCount()
            if driverBit in [32, 64]:
                systemBit = int(platform.architecture()[0][:2])

                if systemBit < driverBit:
                    print(f"Error: Registry Configurations can not be altered for "
                          f"{driverBit}Bit Driver on {systemBit}Bit OS")
                    return False
                elif inDriverDLLPath is None or not os.path.exists(inDriverDLLPath):
                    print('Error: Invalid Driver DLL Path provided')
                    return False
                else:
                    dataSourceName = self.getDataSourceName()
                    try:
                        with winreg.ConnectRegistry(None, winreg.HKEY_LOCAL_MACHINE) as hkey:
                            with winreg.OpenKey(hkey, 'Software', 0, winreg.KEY_READ) as parentKey:
                                if systemBit != driverBit:
                                    parentKey = winreg.OpenKey(parentKey, 'Wow6432Node', 0, winreg.KEY_READ)
                                with winreg.OpenKey(parentKey, 'ODBC', 0, winreg.KEY_READ) as odbcKey:
                                    with winreg.OpenKey(odbcKey, 'ODBCINST.INI', 0, winreg.KEY_WRITE) as odbcInstIniKey:
                                        with winreg.CreateKeyEx(odbcInstIniKey, f"{dataSourceName} ODBC Driver",
                                                                0, winreg.KEY_ALL_ACCESS) as driverKey:
                                            winreg.SetValueEx(driverKey, 'Description', 0, winreg.REG_SZ,
                                                              f"{dataSourceName} ODBC Driver")
                                            winreg.SetValueEx(driverKey, 'Driver', 0, winreg.REG_SZ, inDriverDLLPath)
                                            winreg.SetValueEx(driverKey, 'Setup', 0, winreg.REG_SZ, inDriverDLLPath)

                                        with winreg.CreateKeyEx(odbcInstIniKey, 'ODBC Drivers', 0,
                                                                winreg.KEY_ALL_ACCESS) as odbcDriversKey:
                                            winreg.SetValueEx(odbcDriversKey, f"{dataSourceName} ODBC Driver",
                                                              0, winreg.REG_SZ, 'Installed')

                                    with winreg.OpenKey(odbcKey, 'ODBC.INI', 0, winreg.KEY_WRITE) as odbcIniKey:
                                        with winreg.CreateKeyEx(odbcIniKey, 'ODBC Data Sources', 0,
                                                                winreg.KEY_WRITE) as odbcDSkey:
                                            winreg.SetValueEx(odbcDSkey, f"{dataSourceName}",
                                                              0, winreg.REG_SZ, f"{dataSourceName} ODBC Driver")

                                        if self.shouldWaitForUserToSetupDSN():
                                            print(f"Provide Required Configurations for {dataSourceName} DSN")
                                            if not runExecutable('odbcad32.exe'):
                                                return False
                                        else:
                                            with winreg.CreateKeyEx(odbcIniKey, f"{dataSourceName}", 0,
                                                                    winreg.KEY_WRITE) as driverKey:
                                                for key, value in self.getDataSourceConfiguration().items():
                                                    winreg.SetValueEx(driverKey, key, 0, winreg.REG_SZ, value)
                    except Exception as error:
                        print(f"Error: {error}")
                        return False

                    return True
            else:
                print('Error: This function supports only 32 & 64 Drivers')
                return False
        else:
            print('Error: Invalid Arguments passed')
            return False

    def setup(self, inCoreInfo: Core):
        """
        Sets up the Plugin package with required `ThirdParty` & `Core` Package files
        and writes provided driver registry configurations\n
        :param inCoreInfo: Core's information
        :return: True if succeeded else False
        """
        if self.download() and inCoreInfo.download():
            brand = self.getPluginBrand()
            extractedPluginPath = self.getDestinationPath()
            driverName = self.getPackageName()

            coreBranch = inCoreInfo.getBranch()
            extractedCorePath = inCoreInfo.getDestinationPath()
            pluginLibFolderPath = os.path.join(extractedPluginPath, 'lib')

            if not os.path.exists(os.path.join(extractedPluginPath, f"Branding\\{brand}")):
                if os.path.exists(os.path.join(extractedPluginPath, f"Branding\\Simba")):
                    brand = 'Simba'
                else:
                    print('Error: ' + os.path.join(extractedPluginPath, f"Branding\\Simba") + ' and ' +
                          os.path.join(extractedPluginPath, f"Branding\\{brand}") + ' not found')
                    return False
            pluginDIDPath = os.path.join(extractedPluginPath, f"Branding\\{brand}\\{driverName}ODBC.did")
            pluginINIPath = os.path.join(extractedPluginPath, f"lib\\CoreBranding\\Simba\\Setup\\rdf.rdfodbc.ini")
            coreLibPath = os.path.join(extractedCorePath, f"Core\\{coreBranch}\\ODBC\\lib")
            coreThirdPartyPath = os.path.join(extractedCorePath, f"Core\\{coreBranch}\\ODBC\\ThirdParty")
            pluginINIFileInLib = os.path.join(pluginLibFolderPath, f"{brand}.{driverName}ODBC.ini")

            if all(map(lambda filePath: os.path.exists(filePath),
                       [pluginDIDPath, pluginINIPath, coreLibPath, coreThirdPartyPath])):
                copy(pluginDIDPath, pluginLibFolderPath)
                copy(pluginINIPath, pluginINIFileInLib)
                copytree(coreLibPath, pluginLibFolderPath, dirs_exist_ok=True)
                copytree(coreThirdPartyPath, pluginLibFolderPath, dirs_exist_ok=True)

                with open(pluginINIFileInLib, 'a') as file:
                    file.write('\n')
                    file.write(f"ErrorMessagesPath={os.path.join(extractedPluginPath, 'ErrorMessages')}\n")

                return self.__setRegistryConfigurations(os.path.join(pluginLibFolderPath, 'MPAPlugin.dll'))
            else:
                print('Error: Core or Plugin is not correctly extracted')
                return False
        else:
            return False
