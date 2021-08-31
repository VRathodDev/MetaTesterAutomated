import json
import os, errno
import platform
import sys
import zipfile

from Input import InputReader
from RemoteConnection import RemoteConnection
from shutil import copy, unpack_archive, copytree
from zipfile import ZipFile
from getpass import getpass


def createDir(inDirPath: str, inMode: int = 0o777):
    try:
        os.makedirs(inDirPath, inMode)
    except OSError as err:
        # Reraise the error unless it's about an already existing directory
        if err.errno != errno.EEXIST or not os.path.isdir(inDirPath):
            raise


class Runner:
    def __init__(self, inUserName: str, inPassword: str, inputFileName: str):
        self.mUserName = inUserName
        self.mPassword = inPassword
        self.mInput = InputReader(inputFileName)

    def run(self):
        remoteConnection = RemoteConnection(self.mInput.mRemoteMachineAddress, self.mUserName, self.mPassword)
        systemBitness = platform.architecture()[0][:2]
        if True or remoteConnection.connect():
            corePathAltered = True
            extractedCorePath, coreBranch = None, None
            for packageName, pathInfo in self.mInput.mPathInfo.items():
                for path in pathInfo:
                    if not Runner.copyFile(path['SourcePath'], path['DestPath'], path['ForceUpdate']):
                        break
                    srcFilePath = os.path.abspath(path['SourcePath'])
                    destFolderPath = os.path.abspath(path['DestPath'])
                    if os.path.isfile(srcFilePath) and zipfile.is_zipfile(srcFilePath):
                        fileName = srcFilePath.split(os.sep)[-1]
                        fileBitness = fileName[-6:-4]
                        unpack_archive(os.path.join(destFolderPath, fileName), destFolderPath)
                        if packageName != 'Core':
                            if path['SetupMethod'] != '':
                                pass
                            else:
                                if Runner.setupDriverPackage(packageName, destFolderPath,
                                                          extractedCorePath, fileName.split('_')[0],
                                                          coreBranch, path['Brand']):
                                    pass
                        else:
                            extractedCorePath = destFolderPath
                            coreBranch = path['Branch']
                            corePathAltered = not corePathAltered
                            if corePathAltered:
                                print('Error: Multiple Core must not be used at a time')
                                return False
            # remoteConnection.disconnect()

    @staticmethod
    def copyFile(inSource: str, inDest: str, inForceUpdate: bool = False):
        if all(map(lambda inArg: inArg is not None and len(inArg) > 0, [inSource, inDest])):
            if os.path.exists(inSource):
                try:
                    if not os.path.exists(inDest):
                        createDir(inDest)
                    if os.path.isdir(inSource):
                        copytree(inSource, inDest)
                    else:
                        filePath = os.path.abspath(inDest)
                        fileName = os.path.abspath(inSource).split(os.sep)[-1]
                        if not os.path.exists(os.path.join(filePath, fileName)) or inForceUpdate:
                            copy(inSource, inDest)
                    return True
                except Exception as error:
                    print(error)
                    return False
            else:
                print(f"Error: Given Path {inSource} is Invalid!")
                return False
        else:
            print('Error: Invalid Arguments passed')
            return False

    @staticmethod
    def callCustomSetupMethod():
        pass

    @staticmethod
    def setupDriverPackage(inPackageType: str, inExtractedPluginPath: str,
                           inExtractedCorePath: str, inProductName: str, inBranch: str, inBrand: str):
        if all(map(lambda inArgs: inArgs is not None and len(inArgs) > 0,
                   [inPackageType, inExtractedPluginPath, inExtractedCorePath, inProductName])):
            hadFailure = False
            brand = None
            pluginLibFolderPath = os.path.join(inExtractedPluginPath, 'lib')
            if not os.path.exists(os.path.join(pluginLibFolderPath, f"Branding\\{inBrand}")):
                if os.path.exists(os.path.join(pluginLibFolderPath, f"Branding\\Simba")):
                    brand = 'Simba'
                else:
                    print('Error: ' + os.path.join(pluginLibFolderPath, f"Branding\\Simba") + ' and ' +
                          os.path.join(pluginLibFolderPath, f"Branding\\{inBrand}") + ' not found')
                    return False
            else:
                brand = inBrand
            pluginDIDPath = os.path.join(inExtractedPluginPath, f"Branding\\{brand}\\{inProductName}ODBC.did")
            pluginINIPath = os.path.join(inExtractedPluginPath, f"lib\\CoreBranding\\{brand}\\Setup\\rdf.rdfodbc.ini")
            coreLibPath = os.path.join(inExtractedCorePath, f"Core\\{inBranch}\\ODBC\\lib")
            coreThirdPartyPath = os.path.join(inExtractedCorePath, f"Core\\{inBranch}\\ODBC\\ThirdParty")
            pluginINIFileInLib = os.path.join(pluginLibFolderPath, f"{inBrand}.{inProductName}ODBC.ini")

            if all(map(lambda filePath: os.path.exists(filePath),
                       [pluginDIDPath, pluginINIPath, coreLibPath, coreThirdPartyPath])):
                copy(pluginDIDPath, pluginLibFolderPath)
                copy(pluginINIPath, pluginINIFileInLib)
                copytree(coreLibPath, pluginLibFolderPath, dirs_exist_ok=True)
                copytree(coreThirdPartyPath, pluginLibFolderPath, dirs_exist_ok=True)

                with open(pluginINIFileInLib, 'a') as file:
                    file.write('\n')
                    file.write(f"ErrorMessagesPath={os.path.join(inExtractedPluginPath, 'ErrorMessages')}\n")


                return True
            else:
                print('Error: Core or Plugin is not correctly extracted')
                return False
        else:
            print('Error: Invalid Arguments passed')
            return False

    @staticmethod
    def setupDriverInRegistry(inDriverBit: int):
        pass

if __name__ == '__main__':
    # userName = input()
    # password = getpass()
    userName = 'Simba\\vipulr'
    password = 'Edit321@#'
    Runner(userName, password, 'input.json').run()
