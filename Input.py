import json
import os
import sys
from abc import ABC, abstractmethod
from GenUtility import isNoneOrEmpty


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


class InputReader:

    # Class Variables
    RemoteMachineAddress = 'RemoteMachineAddress'
    Core = 'Core'
    Plugin = 'Plugin'
    Compile = 'Compile'
    SourcePath = 'SourcePath'
    DestPath = 'DestPath'
    ForceUpdate = 'ForceUpdate'
    Branch = 'Branch'
    Brand = 'Brand'
    DataSourceConfiguration = 'DataSourceConfiguration'
    WaitForUserToSetupDSN = 'WaitForUserToSetupDSN'

    def __init__(self, inInputFileName: str):
        if os.path.exists(inInputFileName):
            with open(inInputFileName) as file:
                inInputFile = json.load(file)
        else:
            print(f"Error: Given {inInputFileName} file not found")
            sys.exit(1)
        if InputReader.RemoteMachineAddress in inInputFile and \
                inInputFile[InputReader.RemoteMachineAddress] is not None \
                and len(inInputFile[InputReader.RemoteMachineAddress]) > 0:
            self.__mRemoteMachineAddress = inInputFile[InputReader.RemoteMachineAddress]
        else:
            print(f"Error: Invalid Attribute: `{InputReader.RemoteMachineAddress}`")
            sys.exit(1)
        try:
            self.__mCoreInfo = Core(inInputFile[InputReader.Core][InputReader.SourcePath],
                                    inInputFile[InputReader.Core][InputReader.DestPath],
                                    inInputFile[InputReader.Core][InputReader.Branch],
                                    inInputFile[InputReader.Core][InputReader.ForceUpdate])
        except Exception as e:
            print(f"Invalid Attribute: `{InputReader.Core}`\nError: {e}")
            sys.exit(1)
        if InputReader.Plugin in inInputFile and InputReader.Compile in inInputFile[InputReader.Plugin] \
                and len(inInputFile[InputReader.Plugin][InputReader.Compile]) > 0:
            self.__mPluginInfo = list()
            for pluginInfo in inInputFile[InputReader.Plugin][InputReader.Compile]:
                try:
                    self.__mPluginInfo.append(
                        Plugin(pluginInfo[InputReader.SourcePath], pluginInfo[InputReader.DestPath],
                               pluginInfo[InputReader.Brand], pluginInfo[InputReader.DataSourceConfiguration],
                               pluginInfo[InputReader.WaitForUserToSetupDSN], pluginInfo[InputReader.ForceUpdate])
                    )
                except KeyError as e:
                    print(f"Error: {e}")
                    sys.exit(KeyError)
        else:
            print(f'Error: Invalid Attribute: `{InputReader.Plugin}` or `{InputReader.Compile}`')
            sys.exit(1)

    def getRemoteMachineAddress(self):
        return self.__mRemoteMachineAddress

    def getCoreInfo(self):
        return self.__mCoreInfo

    def getPluginInfo(self):
        return self.__mPluginInfo
