import json
import os
import sys
from abc import ABC, abstractmethod


def isNoneOrEmpty(*args):
    return any(map(lambda inArgs: inArgs is None or len(inArgs) == 0, args))


class Package(ABC):
    @abstractmethod
    def __init__(self, inSourcePath: str, inDestinationPath: str, inForceUpdate: bool = False):
        if (not isNoneOrEmpty(inSourcePath, inDestinationPath)) and inForceUpdate is not None:
            self.mSourcePath = inSourcePath
            self.mDestinationPath = inDestinationPath
            self.mForceUpdate = inForceUpdate
        else:
            print('Error: Invalid Parameters')
            sys.exit(1)


class Core(Package):
    def __init__(self, inSourcePath: str, inDestinationPath: str, inBranch: str, inForceUpdate: bool = False):
        super().__init__(inSourcePath, inDestinationPath, inForceUpdate)
        if not isNoneOrEmpty(inBranch):
            self.mBranch = inBranch
        else:
            print('Error: Invalid Parameters')
            sys.exit(1)


class Plugin(Package):
    def __init__(self, inSourcePath: str, inDestinationPath: str, inBrand: str,
                 inDataSourceConfiguration: dict, inWaitForUserToSetupDSN: bool = False, inForceUpdate: bool = False):
        super().__init__(inSourcePath, inDestinationPath, inForceUpdate)
        if not isNoneOrEmpty(inBrand, inDataSourceConfiguration):
            self.mBrand = inBrand
            self.mWaitForUserToSetupDSN = inWaitForUserToSetupDSN
            self.mDataSourceConfiguration = inDataSourceConfiguration
        else:
            print('Error: Invalid Parameters')
            sys.exit(1)


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
        if InputReader.RemoteMachineAddress in inInputFile and inInputFile[InputReader.RemoteMachineAddress] is not None\
                and len(inInputFile[InputReader.RemoteMachineAddress]) > 0:
            self.__mRemoteMachineAddress = inInputFile[InputReader.RemoteMachineAddress]
        else:
            print(f"Error: Invalid Attribute: `{InputReader.RemoteMachineAddress}`")
            sys.exit(1)
        try:
            self.__mCoreInfo = Core(inInputFile[InputReader.Core][InputReader.SourcePath], inInputFile[InputReader.Core][InputReader.DestPath],
                                    inInputFile[InputReader.Core][InputReader.Branch], inInputFile[InputReader.Core][InputReader.ForceUpdate])
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
